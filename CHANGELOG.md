# Changelog

Alle wichtigen Änderungen an der Home-Assistant-Konfiguration werden hier kurz dokumentiert.

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
