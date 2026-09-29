#!/bin/sh
set -eu
hue_backup=/config/dashboard-backups/2026-09-26-hue-close-fridge
mkdir -p "$hue_backup"
hue_host=$(jq -r '.data.entries[] | select(.domain=="hue") | .data.host' /config/.storage/core.config_entries)
hue_key=$(jq -r '.data.entries[] | select(.domain=="hue") | .data.api_key' /config/.storage/core.config_entries)
for hue_rule in 9 10; do
  test ! -e "$hue_backup/hue-rule-$hue_rule.json"
  curl -fsS "http://$hue_host/api/$hue_key/rules/$hue_rule" -o "$hue_backup/hue-rule-$hue_rule.json"
  hue_old=2000
  hue_new=2002
  if [ "$hue_rule" = 10 ]; then hue_old=3000; hue_new=3002; fi
  jq -e --arg old "$hue_old" '
    .status == "enabled" and
    (.conditions | length == 2) and
    any(.conditions[]; .address=="/sensors/68/state/buttonevent" and .operator=="eq" and .value==$old) and
    all(.actions[]; .method=="PUT" and (.body|has("bri_inc")))
  ' "$hue_backup/hue-rule-$hue_rule.json" >/dev/null
done
for hue_behavior in 36d1ec11-631d-4a81-8494-f24582880553 f37adad1-c35e-46d8-8cb1-d127d595a616; do
  test ! -e "$hue_backup/behavior-$hue_behavior.json"
  curl -fsSk -H "hue-application-key: $hue_key" "https://$hue_host/clip/v2/resource/behavior_instance/$hue_behavior" -o "$hue_backup/behavior-$hue_behavior.json"
  jq -e '.errors==[] and (.data|length==1) and ([.data[0].configuration.buttons[] | select(.on_repeat.action=="dim_up" or .on_repeat.action=="dim_down")]|length==2)' "$hue_backup/behavior-$hue_behavior.json" >/dev/null
  jq '{configuration:(.data[0].configuration | .buttons |= with_entries(if (.value.on_repeat.action=="dim_up" or .value.on_repeat.action=="dim_down") then .value |= (del(.on_repeat) | .on_short_release={action:"do_nothing"} | .on_long_press={action:"do_nothing"}) else . end))}' "$hue_backup/behavior-$hue_behavior.json" > "$hue_backup/behavior-$hue_behavior-payload.json"
done
for hue_rule in 9 10; do
  hue_new=2002
  if [ "$hue_rule" = 10 ]; then hue_new=3002; fi
  jq --arg new "$hue_new" '{conditions: [.conditions[] | if .address=="/sensors/68/state/buttonevent" then .value=$new else . end]}' \
    "$hue_backup/hue-rule-$hue_rule.json" |
    curl -fsS -X PUT -H 'Content-Type: application/json' --data-binary @- \
      "http://$hue_host/api/$hue_key/rules/$hue_rule" |
    jq -e 'length > 0 and all(.[]; has("success"))' >/dev/null
  curl -fsS "http://$hue_host/api/$hue_key/rules/$hue_rule" -o "$hue_backup/hue-rule-$hue_rule-after.json"
  jq -e --arg new "$hue_new" --slurpfile before "$hue_backup/hue-rule-$hue_rule.json" '
    .actions==$before[0].actions and .status==$before[0].status and
    .conditions==[$before[0].conditions[] | if .address=="/sensors/68/state/buttonevent" then .value=$new else . end]
  ' "$hue_backup/hue-rule-$hue_rule-after.json" >/dev/null
  printf 'Hue rule %s verified: short release %s, light actions unchanged\n' "$hue_rule" "$hue_new"
done
for hue_behavior in 36d1ec11-631d-4a81-8494-f24582880553 f37adad1-c35e-46d8-8cb1-d127d595a616; do
  curl -fsSk -X PUT -H "hue-application-key: $hue_key" -H 'Content-Type: application/json' --data-binary "@$hue_backup/behavior-$hue_behavior-payload.json" "https://$hue_host/clip/v2/resource/behavior_instance/$hue_behavior" |
    jq -e '.errors==[] and (.data|length>0)' >/dev/null
  curl -fsSk -H "hue-application-key: $hue_key" "https://$hue_host/clip/v2/resource/behavior_instance/$hue_behavior" -o "$hue_backup/behavior-$hue_behavior-after.json"
  jq -e --slurpfile expected "$hue_backup/behavior-$hue_behavior-payload.json" '.errors==[] and .data[0].configuration==$expected[0].configuration' "$hue_backup/behavior-$hue_behavior-after.json" >/dev/null
  printf 'Hue behavior %s verified: native dim holding removed; other buttons preserved\n' "$hue_behavior"
done
