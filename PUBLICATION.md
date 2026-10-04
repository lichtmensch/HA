# Veröffentlichungsstand vom 2026-10-04

Enthält Routinen-Dashboard, editierbare Helfer, zugehörige Automationen, QNAP-Sonntagsprüfung und BMW-Anmeldekorrektur.

Die laufende Home-Assistant-Instanz behält ihre lokal gesicherten Werte. Der GitHub-Stand ersetzt Benachrichtigungsziele, Gerätekennungen, QNAP-MAC und Broadcast-Adresse in den geänderten YAML-Dateien durch `!secret`. Diese Schlüssel müssen vor Wiederherstellung aus den lokalen Originalen in eine nicht veröffentlichte `secrets.yaml` übernommen werden. Der QNAP-Adapter liest Host und bestehende Zugangsdaten ausschließlich aus den lokalen Integrationseinträgen.

Nicht enthalten: aktuelle Integrationseinträge, Anmeldecodes, Passwörter, Tokens, private Wertezuordnung und unverschlüsselte Sicherungen. Bereits veröffentlichte Historie wird nicht umgeschrieben.
