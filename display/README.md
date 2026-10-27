# TV-Verbindungsanleitung

Zwei große mittige Verbindungskarten als Startbildschirm. Mit OK öffnet sich ein echtes Terminal mit vollständiger deutscher Bildschirmtastatur. Kein Browser und keine grafische Desktopinstallation nötig.

## Aktivierung

Vorbereitet auf dem Pi unter `~/.local/share/stereoanlage-display/`. Einmal im SSH-Terminal:

```sh
sudo sh ~/.local/share/stereoanlage-display/install-display.sh
```

Das Skript prüft Bild und Python-Syntax, kopiert die Anzeige nach `/opt/stereoanlage-display`, installiert bzw. aktualisiert den Systemdienst und startet nur den Anzeigedienst neu. Die lokale Login-Konsole tty1 wird während der Bildanzeige gestoppt. SSH bleibt verfügbar. Kein Audio-Dienst und kein Pi wird neu gestartet.

Die Anzeige skaliert die Oberfläche mit erhaltenem Seitenverhältnis auf `/dev/fb0`. Unterstützt RGB565 und BGRX32; bei anderen Pixelformaten bricht sie ab. Formatwechsel nach HDMI-Neuverbindung werden erneut eingelesen. KD_GRAPHICS hält Konsolentext von der laufenden Anzeige fern. Beim Beenden wird KD_TEXT wiederhergestellt.

Weniger Boottext wird für den nächsten Neustart in `cmdline.txt` vorgemerkt; vorherige Datei bekommt eine datierte Sicherung. Frühe Firmware-/Fehlermeldungen werden nicht durch einen eigenen grafischen Bootloader ersetzt. Die 16:9-TV-Auflösung wurde separat vorbereitet. Ein kurzzeitiger Test des Bildes ist auch ohne Administratorrechte möglich; dauerhaft benötigt die Konsole den Systemdienst.

## Fernbedienung und Tastatur

- **OK** auf der Startansicht öffnet das Terminal.
- Standard ist die **Kreuztastatur**: Eine Richtung öffnet eine der vier Buchstabengruppen. Mit Pfeilen ein Zeichen wählen und mit OK schreiben. Danach wird die Gruppenauswahl wieder angezeigt.
- **OK in der Gruppenauswahl** öffnet die Ebenenauswahl links: ABC, 123, Sonderzeichen, Terminaltasten, QWERTZ, Diagnose oder Anleitung. Dort mit Pfeilen wählen und mit OK bestätigen.
- **Zurück** innerhalb einer Gruppe oder der Ebenenauswahl bricht nur diese Auswahl ab.
- **QWERTZ** ist die Alternative mit natürlicher ISO-Anordnung: versetzte Reihen, breite Modifikatortasten; Pfeile navigieren zur räumlich nächsten Taste. Die Taste **Kreuz** wechselt direkt zurück zur Kreuztastatur.
- **Zurück** in der Gruppenauswahl bzw. bei QWERTZ blendet das Terminal aus; die Sitzung läuft weiter.
- Bei QWERTZ gelangt man oberhalb der F-Tasten mit **Pfeil hoch** zu den Diagnose-Abkürzungen. Diese schreiben normale Befehle in dieselbe Terminalsitzung.
- **Shift**, **Strg**, **Alt**, **AltGr** gelten jeweils für die nächste Zeichentaste; **Fest** bleibt aktiv. Erneutes Auswählen schaltet den Modifikator aus.
- QWERTZ einschließlich Umlauten, ß, Zahlen, Sonderzeichen, F1–F12, Esc, Tab, Rücktaste, Entf, Einfg, Enter, Leertaste, Pos1/Ende, Bild hoch/runter und Pfeiltasten.
- AltGr bietet insbesondere `@ € { [ ] } \ ~ |`; Strg+C/D/L sind zusätzlich direkt auswählbar. Auch Strg+Z und andere Kombinationen funktionieren über Strg plus Zeichentaste.
- **Verlauf hoch/runter** scrollt die Terminalhistorie; die normalen Pfeile und Bild-Tasten werden an das laufende Terminalprogramm gesendet.
- Eine angeschlossene USB-Tastatur funktioniert weiter; **F12** wechselt zwischen Terminal und Anleitung.
- SSH über Tailscale bleibt unabhängig davon erreichbar.

Das Terminal ist eine echte PTY-Sitzung mit Bash als `jaron`, kein Root-Terminal und keine eingeschränkte Befehlsliste. Interaktive Programme und normale sudo-Passwortabfragen sind möglich. Die Anzeige zeichnet weder Tastendrücke noch Terminalausgaben in Dateien oder im Journal auf. Shell-History wird für die Sitzung standardmäßig nach `/dev/null` geleitet; übliche System-/sudo-Protokolle bleiben unverändert.

Der Anzeigedienst benötigt Root für die lokale Konsole und öffnet für das Terminal einen separaten Prozess mit UID/Gruppen von `jaron`. Deshalb erzwingt der neue Dienst keine Mount- oder NoNewPrivileges-Sperre, die normale Terminal-/sudo-Nutzung blockieren würde.

## HDMI-CEC und noch ausstehender Test

Der angeschlossene Port ist aktuell `/dev/cec1`, HDMI-A-2. Die Software sucht den verbundenen CEC-Adapter automatisch und meldet einen Wiedergabeempfänger „Stereoanlage“ an. Sie verwendet die Standardcodes Select=0x00, Up=0x01, Down=0x02, Left=0x03, Right=0x04, Exit=0x0d. Wiederholungen werden begrenzt; bei verlorener HDMI-Verbindung wird neu angemeldet. TV-Eingang, Lautstärke, Standby und Audio-Dienste werden dabei nicht umgeschaltet.

**Noch nicht mit der echten Samsung-Fernbedienung getestet.** Anynet+ (HDMI-CEC) muss am TV aktiv sein. Je nach TV-Menü kann die Auswahl des HDMI-Geräts nötig sein. Kein erfolgreicher Tastentest wird behauptet.

## Prüfungen

`python3 tests/test_tv_console.py` prüft Sonderzeichen, Modifikatoren, Funktionstasten, CEC-Zuordnung, ANSI-Ausgabe und Framebuffer-Farben. Auf dem Pi außerdem erfolgreich geprüft: echte PTY als UID 1000, Befehlsausführung, Strg+C sowie Bildaufbereitung in ungefähr 0,8 Sekunden für den aktuellen 4096×2160-Framebuffer. Audio-Dienste blieben aktiv.

Terminalbibliotheken sind mit festen Versionen und Lizenztexten unter `vendor/` enthalten: pyte 0.8.2 und wcwidth 0.2.13. Die Pi-Installation lädt keine Pakete nach.

## Rückweg

```sh
sudo systemctl disable --now stereoanlage-display.service
sudo systemctl start getty@tty1.service
```

Für ursprüngliche Bootmeldungen die Display-Optionen aus `cmdline.txt` entfernen bzw. die passende Sicherung nach Prüfung zurückspielen. Keine Dateien müssen zur Deaktivierung gelöscht werden.

## Grafik ändern

`python3 render.py` benötigt Pillow und eine Helvetica-TTC auf macOS oder DejaVu Sans auf Linux. Alternative Schrift mit `--font` angeben. Ausgabe ist `welcome.png` (3840 × 2160). Die Verbindungsgrafik ist statisch, keine Live-Bereitschaftsanzeige; die Terminalansicht wird dagegen laufend aktualisiert.

## Quellen und Grenzen

- Offizielles AirPlay-Audiosymbol: https://cdsassets.apple.com/live/7WUAS350/images/inline-icons/ios14-airplay-icon-gray.png (Apple Support https://support.apple.com/en-gb/105068). Für dunklen Hintergrund weiß dargestellt.
- Offizielles Spotify-Logo unverändert: https://newsroom.spotify.com/media-kit/logo-and-brand-assets/ und https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Full_Logo_RGB_Green.png
- Empfänger unterstützt bis 24 Bit / 48 kHz: https://github.com/mikebrady/shairport-sync . Tatsächliches AirPlay-Format hängt vom Sender und Stream ab; kein Nachweis, dass Apple Music hier verlustfrei spielt.
- Soloist unterstützt bis 24 Bit / 44,1 kHz mit Premium: https://github.com/spotify/soloist . Lossless muss gewählt sein, tatsächliche Wiedergabequalität ist nicht live gemessen.
- Sonos-Auswahl beschreibt die beabsichtigte Bedienung bei AirPlay-2-fähigen Sonos-Geräten. Der dokumentierte Wechselfehler ist weiterhin nicht als behoben bestätigt.

Marken und Symbole gehören ihren jeweiligen Rechteinhabern; dies ist eine private Bedienhilfe.

Die elf Tests prüfen zusätzlich die Erreichbarkeit sämtlicher 128 Einträge der Kreuztastatur, die Rückkehr zur Gruppenauswahl und die natürliche QWERTZ-Geometrie. Echte TV-Fernbedienung weiterhin noch nicht getestet.

## Aktuelle Auswahl

Auf Nutzerwunsch ist ausschließlich die natürliche QWERTZ-Anordnung über die Oberfläche erreichbar. Die Kreuz-Umschaltung wurde entfernt; QWERTZ ist wieder Standard.
