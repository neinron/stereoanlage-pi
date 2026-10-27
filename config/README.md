# Vorlagen

Die systemd-Dateien entsprechen den am 27.10.2026 gelesenen Benutzer-Dienstdefinitionen. Sie enthalten keine Schlüssel. Vor einer Übernahme Pfade, installierte Programmversionen und Ausgang prüfen.

- `systemd/user/`: Ziel wäre `~/.config/systemd/user/` des Audio-Benutzers.
- `shairport-sync.conf.example`: nur bestätigte Einstellungen, keine vollständige Kopie der aktiven Konfiguration.
- `boot-audio.txt`: nur relevante Audio-Zeilen; nicht als komplette Boot-Konfiguration verwenden.
- `.env.example`: Platzhalter für eine ausschließlich lokal zu erstellende `~/.soloist.env` mit Dateirechten 600. Kein echter Schlüssel in Git, Shell-Historie oder Diagnoseausgaben.

Keine Vorlage wird automatisch installiert. Bestehende NQPTP-, PipeWire- und WirePlumber-Konfiguration wird nicht ersetzt.
