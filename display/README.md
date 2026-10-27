# TV-Verbindungsanleitung

Zwei große mittige Karten mit AirPlay-Audiosymbol, Spotify-Logo, Verbindungsschritten, Sonos-Auswahl, Garten-Anwendungsfall und Qualitätsangaben. Kein Browser und keine grafische Desktopinstallation nötig.

## Aktivierung

Vorbereitet auf dem Pi unter `~/.local/share/stereoanlage-display/`. Einmal im SSH-Terminal:

```sh
sudo sh ~/.local/share/stereoanlage-display/install-display.sh
```

Das Skript prüft Bild und Python-Syntax, kopiert die Anzeige nach `/opt/stereoanlage-display`, installiert und aktiviert den Systemdienst. Die lokale Login-Konsole tty1 wird während der Bildanzeige gestoppt. SSH bleibt verfügbar. Kein Audio-Dienst und kein Pi wird neu gestartet.

Die Anzeige skaliert das Bild mit erhaltenem Seitenverhältnis auf `/dev/fb0`. Unterstützt RGB565 und BGRX32; bei anderen Pixelformaten bricht sie ab. Formatwechsel nach HDMI-Neuverbindung werden erneut eingelesen. KD_GRAPHICS hält Konsolentext von der laufenden Anzeige fern. Beim Beenden wird KD_TEXT wiederhergestellt.

Weniger Boottext wird für den nächsten Neustart in `cmdline.txt` vorgemerkt; vorherige Datei bekommt eine datierte Sicherung. Frühe Firmware-/Fehlermeldungen werden nicht durch einen eigenen grafischen Bootloader ersetzt. Die 16:9-TV-Auflösung wurde separat vorbereitet. Ein kurzzeitiger Test des Bildes ist auch ohne Administratorrechte möglich; dauerhaft benötigt die Konsole den Systemdienst.

## Rückweg

```sh
sudo systemctl disable --now stereoanlage-display.service
sudo systemctl start getty@tty1.service
```

Für ursprüngliche Bootmeldungen die Display-Optionen aus `cmdline.txt` entfernen bzw. die passende Sicherung nach Prüfung zurückspielen. Keine Dateien müssen zur Deaktivierung gelöscht werden.

## Grafik ändern

`python3 render.py` benötigt Pillow und eine Helvetica-TTC auf macOS oder DejaVu Sans auf Linux. Alternative Schrift mit `--font` angeben. Ausgabe ist `welcome.png` (3840 × 2160). Die Grafik ist statisch, keine Live-Bereitschaftsanzeige.

## Quellen und Grenzen

- Offizielles AirPlay-Audiosymbol: https://cdsassets.apple.com/live/7WUAS350/images/inline-icons/ios14-airplay-icon-gray.png (Apple Support https://support.apple.com/en-gb/105068). Für dunklen Hintergrund weiß dargestellt.
- Offizielles Spotify-Logo unverändert: https://newsroom.spotify.com/media-kit/logo-and-brand-assets/ und https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Full_Logo_RGB_Green.png
- Empfänger unterstützt bis 24 Bit / 48 kHz: https://github.com/mikebrady/shairport-sync . Tatsächliches AirPlay-Format hängt vom Sender und Stream ab; kein Nachweis, dass Apple Music hier verlustfrei spielt.
- Soloist unterstützt bis 24 Bit / 44,1 kHz mit Premium: https://github.com/spotify/soloist . Lossless muss gewählt sein, tatsächliche Wiedergabequalität ist nicht live gemessen.
- Sonos-Auswahl beschreibt die beabsichtigte Bedienung bei AirPlay-2-fähigen Sonos-Geräten. Der dokumentierte Wechselfehler ist weiterhin nicht als behoben bestätigt.

Marken und Symbole gehören ihren jeweiligen Rechteinhabern; dies ist eine private Bedienhilfe.
