# Changelog

Alle wichtigen Änderungen an der Home-Assistant-Konfiguration werden hier kurz dokumentiert.

## 2026-10-04

### Bad-Heizung · manueller 30-Minuten-Lauf

- Regelmäßige Heizungsprüfung Mo–Fr 04:30–07:00 weiterhin minütlich, außerhalb nur um :00 und :30; Sensor-, Neustart- und Reload-Auslöser erhalten.
- Manuelles Einschalten oder Sollwertänderung außerhalb des Morgenfensters erlaubt 30 Minuten Betrieb mit persistentem Endzeitpunkt; Wiederverbindung verlängert nicht.
- Morgenautomatik unverändert, Abschaltung am Endzeitpunkt und Wiederanlaufprüfung nach HA-Neustart.
- Original gesichert; Konfigurationsprüfung sowie Zeitfenster-, Frist- und Erkennungstests erfolgreich. Kein physischer Heiztest.


### Bereinigte Veröffentlichung

- Routinen-Dashboard, Helfer, QNAP-Prüfung und BMW-Korrektur gemeinsam veröffentlicht.
- Lokale Netzwerk-/Gerätekennungen und persönliche Benachrichtigungsziele in geänderten YAML-Dateien durch Secrets ersetzt; private Werte bleiben lokal.
- Noch unveröffentlichte Zwischencommits vor Veröffentlichung zusammengeführt, damit private Werte nicht in deren Historie exportiert werden.

### BMW erneute Anmeldung

- Manuellen BimmerData-Streamline-Anmeldevorgang mit dem bestehenden Konfigurationseintrag verknüpft: `entry_id` steht jetzt auch im Flow-Kontext, wie von Home Assistant verlangt.
- Originaldatei und Konfiguration vorab auf dem Pi gesichert; bestehende Zugangsdaten und Entitäts-IDs erhalten.
- Python-Syntax, gezielter Test des Anmeldekontexts und Home-Assistant-Konfigurationsprüfung erfolgreich. BMW hat den frischen Code akzeptiert, Home Assistant meldet `reauth_successful`; der Stream ist anschließend wieder `connected`.

## 2026-10-04

### QNAP · UniFi-Sonntagsprüfung

- Wake-on-LAN auf der angeschlossenen QNAP-Schnittstelle aktiviert und geprüft.
- Sonntagslauf um 12:00 Uhr mit editierbarer, persistenter Uhrzeit eingerichtet.
- Start per Wake-on-LAN, begrenztes Warten auf den Controller, direkte Abfrage der gemeldeten Geräte- und Controller-Updates; keine Installation.
- Bei Updates iPhone informieren und QNAP anlassen; bei bestätigtem Status ohne Updates geordnet über QTS-API herunterfahren und Erreichbarkeit kontrollieren.
- Fehler, unvollständige Update-Daten und laufende Firmware-Aktualisierung verhindern Shutdown; Fehlerbenachrichtigung ans iPhone.
- QNAP-Ansicht im Routinen-Dashboard mit Status, Prüftermin und manuellen Startmöglichkeiten ergänzt.
- Vorhandene Integrationszugänge werden zur Laufzeit verwendet; keine Zugangsdaten im Adapter oder Repository. Der UniFi-Lesezugang kann keine Firmware-Neusuche erzwingen; es wird der vom Controller gemeldete Status geprüft.
- Konfigurationsprüfung und 8 gezielte Adaptertests erfolgreich. Live-Tests und Testbenachrichtigung in lokaler Prüfdokumentation protokolliert.

## 2026-10-04

### Routinen & Zeiten

- Neue Dashboard-Ansichten für Übersicht, Flur, Gästezimmer, Rollos, Warnungen, Küche, Wohnzimmer und native Hue-Zeitprofile.
- 124 persistente Helfer für Zeiten, Helligkeit, Farbe, Übergänge, Zielpositionen, Nachlauf und Warnschwellen angelegt.
- 15 Automationen und gemeinsame Rollo-Zielwerte auf die Helfer umgestellt; bisherige Standardwerte, Trigger, IDs und Logik erhalten.
- Küchen-Zeitprofile und feste Wohnzimmer-Tastenprofile einbezogen; native Hue-Profile nur dokumentiert, nicht migriert.
- Originale vor Änderungen auf dem Pi unter `/config/codex-backups/routinen-20261004/` gesichert.
- Konfigurationscheck erfolgreich; 169 Laufzeit-Template/Wert-Prüfungen erfolgreich, ohne Gerätebefehle. Flur über alle Wochenminuten und Gästezimmer über alle Tagesminuten mit Originalen verglichen.
- Helfer-Persistenz bei Reload und Dashboard im Browser geprüft. Keine physischen Funktionstests durchgeführt.

## 2026-09-29

### Verschlüsseltes Backup hinzugefügt

- Verschlüsseltes Backup unter `backups/home-assistant-2026-09-29.tar.gz.enc` hinzugefügt.
- Enthält die sensible HA-Konfiguration einschließlich Secrets und ESPHome-Dateien.
- Datenbank, Logs, Cache, Abhängigkeiten und vorhandene Backups ausgeschlossen.
- Verschlüsselung: AES-256-CBC mit PBKDF2 und zufälligem Salt.
- Entschlüsselung und gzip-Integrität vor dem Push erfolgreich geprüft.

## 2026-09-29

### Aktueller Pi-Stand synchronisiert

- Aktive `automations.yaml` und `scripts.yaml` übernommen.
- Aktive Packages, Szenen und Utility-Meter-Konfiguration übernommen.
- Alle aktiven Lovelace-Dashboards und Dashboard-Ressourcen übernommen.
- Aktive Custom Components und `www`-Ressourcen übernommen.
- Home-Assistant-Konfigurationscheck auf dem Raspberry Pi erfolgreich ausgeführt.
- Datenbanken, Logs, Caches, Backups und `secrets.yaml` ausgeschlossen.
- ESPHome-Dateien wegen enthaltenen WLAN-Zugangsdaten ausgeschlossen.

## 2026-09-29

### Erster Repository-Import

- Vorhandene Home-Assistant-Arbeitsstände, Dashboard-Entwürfe, Automationen, Skripte und Tests importiert.
