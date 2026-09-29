# Einmaliger Aufheiztest Bad, 28.09.2026

- Nutzer: Test jetzt mit 24 °C; beide Thermometer beobachten.
- Startskript ausgeführt 19:10:40 MESZ. Gerätetimer 60 Minuten mit 24 °C.
- Während dieses Tests interner Sensor aktiv, damit Thermostat und Netatmo unabhängige Werte liefern. Keine Änderung des Temperatur-Offsets.
- 19:11 MESZ: Netatmo 21,4 °C; Thermostat intern 22,2 °C. ZHA meldet hvac_action=heating, obwohl climate state=off und temperature=None (Timer-Sondermodus). Timer-Ziel 24,0 °C, Dauer 60,0 Minuten bestätigt.
- Erwartetes Timerende ca.20:11 MESZ; feste einmalige Ausnahme der Morgenroutine endet um20:15 MESZ. Danach normale Routine (Mo–Fr05:30–07:00 auf23, sonst Aus). Frostschutz7 °C bleibt.
- Gerätetimer soll in vorherigen Zustand Aus zurückkehren; noch nicht physisch verifiziert.
- Backup ursprünglicher Morgenroutine: /config/codex-backups/bad-heizung-20260928/bad_heizung_morgens-vor-test.yaml.
- Automatische Nachbeobachtung NUR LESEND alle10Minuten: bad-aufheiztest-messwerte-beobachten. Hintergrundsteuerung/-Konfigurationsänderung wurde von Sicherheitsprüfung abgelehnt. Nicht umgehen. Nach20:20 letzte lesende Prüfung und Beobachtung beenden.
- Auswertung: gemessene Dauer bis Netatmo22/23/24 °C nur nennen falls tatsächlich erreicht; interner24°C-Sollwert kann Heizkörper früher drosseln. Keine Extrapolation als tatsächliche morgendliche Aufheizzeit darstellen.
- Fußbodenheizung laut Nutzer Stufe3. Fenster/Tür möglichst unverändert lassen.
