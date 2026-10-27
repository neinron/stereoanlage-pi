# Papas Stereoanlage · Raspberry Pi

Privates Betriebs- und Konfigurationsarchiv für die vorhandene Stereoanlage bei Papa. Kein WG-Projekt und kein automatischer Installer.

## Aufbau

Raspberry Pi 4 Model B Rev 1.2 (4 GB) → IQaudIO Pi-DAC Pro → Cinch → Denon AVR-1803.
Raspberry Pi OS Lite 64-bit / Debian 13 (Trixie); DAC-Overlay `iqaudio-dacplus`.

- **AirPlay:** Stereoanlage AirPlay, Shairport Sync mit AirPlay 2, NQPTP und PipeWire.
- **Spotify:** Stereoanlage Spotify, Soloist mit PipeWire.
- **Fernwartung:** normales SSH mit Schlüssel über Tailscale; Host `spotify-pi`.
- Kodi wurde entfernt und soll nicht wieder installiert werden.

## Einstieg

- [Verifizierter Zustand und offene Punkte](docs/status.md)
- [Wartung, Diagnose und AirPlay-/Sonos-Test](docs/operations.md)
- [Konfigurationsvorlagen](config/README.md)
- [TV-Verbindungsanleitung und Autostart](display/README.md)

`scripts/diagnose.sh` auf dem Pi als Audio-Benutzer ausführen. Es liest nur ausgewählte Zustände und gibt keine Dienstdefinitionen, Umgebungsvariablen oder Journale aus. Ausgabe vor Weitergabe trotzdem prüfen; lokale Mitschnitte ausschließlich in `.local/` ablegen.

Die Vorlagen werden durch Klonen nicht aktiviert. Änderungen an der Anlage sind ein eigener Auftrag. Aktive Dienste bestätigen keine hörbare Wiedergabe und keinen behobenen Multiroom-Fehler.
