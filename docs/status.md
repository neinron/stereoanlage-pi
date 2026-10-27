# Zustand am 27.10.2026

Quelle: gezielte, ausschließlich lesende SSH-Abfrage des laufenden Pi; ergänzende Hardware- und Fehlerangaben aus der Übergabe. Ältere lokale Statusdateien sind keine aktuelle Quelle für den Spotify-Status.

## Live bestätigt

| Komponente | Zustand |
| --- | --- |
| Hostname | spotify-pi |
| Betriebssystem | Debian GNU/Linux 13.7 (Trixie), laut Übergabe Raspberry Pi OS Lite 64-bit |
| tailscaled / ssh | active, enabled |
| nqptp | active |
| shairport-sync / pipewire / wireplumber / soloist | Benutzer-Dienste active und enabled |
| Benutzer-Linger | yes |
| Shairport Sync | 5.6.1, AirPlay2, PipeWire, soxr |
| AirPlay-Name / Backend | Stereoanlage AirPlay / pipewire |
| PipeWire-Standardausgang | Stereoanlage Cinch, Lautstärke 0.40 |
| Boot-Audio | dtparam=audio=off; dtoverlay=iqaudio-dacplus |

Soloist verwendet `/usr/local/bin/soloist`, den Ausgang `alsa_output.platform-soc_sound.stereo-fallback`, Startlautstärke 40, Cachegröße 500 und einen lokalen WebSocket `127.0.0.1:0`. Der Schlüssel wird aus einer privaten Environment-Datei geladen; deren Inhalt wurde nicht gelesen.

Tailscale-Verbindung auf Pi und Mac sowie SSH sind bestätigt. Die private Geräteadresse und lokale Schlüsselpfade werden nicht für die Vorlagen benötigt. Der Tailscale-Admin zeigte laut Übergabe Schlüsselablauf in sechs Monaten; diese Einstellung wurde nicht verändert.

## Offen: AirPlay und Sonos

Früher funktionierte die synchrone Multiroom-Wiedergabe. Später berichtete Papa: Nach Neustart spielt AirPlay auf dem Pi. Zusätzliches Auswählen von Sonos entfernt die Pi-Auswahl. Zurückwechseln auf den Pi gelingt erst nach Neustart.

**Nicht als behoben bestätigt.** Bei dieser Bestandsaufnahme wurde kein Wiedergabetest durchgeführt und kein Dienst neu gestartet.

Ein historischer Versuch mit angekündigtem Modell `One` und Hersteller `Sonos` ist nur eine mögliche Spur. Die aktuellen Werte dafür wurden nicht bestätigt; ein Zusammenhang ist keine Diagnose.

## Nächste sinnvolle Prüfung

Den Fehler mit Sendergerät, Betriebssystem, App, Sonos-Modell, Reihenfolge und Zeitpunkten reproduzieren. Erst anschließend gezielte Journalausschnitte lokal prüfen und eine einzelne begründete Änderung testen. Keine pauschale Neuinstallation.

## Spätere Änderung am 27.10.2026: vorerst nur AirPlay

Auf ausdrücklichen Wunsch Spotify pausiert, ohne Deinstallation: `soloist.service` ist jetzt inactive und disabled. Die obige Tabelle beschreibt die vorherige Bestandsaufnahme.

Zusätzlicher Benutzer-Drop-in `~/.config/systemd/user/soloist.service.d/90-airplay-only.conf`:

```ini
[Unit]
# Temporary AirPlay-only operation. Re-enable explicitly after review.
ConditionPathExists=%h/.config/soloist-spotify-enabled
```

Die Markerdatei existiert nicht. Dadurch verhindert die Startbedingung auch eine Reaktivierung durch den weiterhin eingerichteten System-Timer `soloist-update.timer`. Der Timer selbst wurde nicht deaktiviert und kann weiterhin Updates versuchen. Installation, Schlüsseldatei und Musik wurden nicht gelöscht. Für spätere Reaktivierung nach Prüfung den Marker anlegen und den Benutzer-Dienst mit `systemctl --user enable --now soloist` aktivieren.

Shairport Sync blieb durchgehend mit derselben PID aktiv; auch PipeWire und WirePlumber laufen weiter. Kein Pi- oder Audio-Dienst-Neustart.

### Befunde im AirPlay-Fehlerzustand vor der Änderung

- iPhone-Test mit Apple Music: Pi spielt nach Reboot; zusätzliches Sonos-Auswählen entfernt Pi-Auswahl; Rückkehr zum Pi scheitert, Sonos und iPhone spielen weiter.
- Shairport Sync nimmt weitere Steuerverbindungen an, aber PipeWire zeigt keinen AirPlay-Audiostream.
- Eine eigene lokale GET-/info-Abfrage antwortet mit RTSP 200 OK und Modell ShairportSync. Keine aktuelle Sonos-Modellkennung bestätigt.
- Keine aussagekräftigen AirPlay-Fehlerprotokolle vorhanden. NQPTP 1.2.9 und Shairport melden beide smi11.
- Ursache nicht eindeutig belegt; Spotify-Abschaltung ist keine bestätigte Reparatur des Sonos-Wechselfehlers. Wiedergabetest steht aus.

## Spotify Connect wieder aktiviert (27.10.2026)

Auf ausdrücklichen Wunsch wurde die bestehende Installation wieder aktiviert. Der lokale Marker `~/.config/soloist-spotify-enabled` ist angelegt; `soloist.service` ist wieder active und enabled. Der Startbedingungs-Drop-in bleibt bestehen und wird durch den Marker erfüllt. AirPlay lief mit unveränderter PID weiter. Hörbarer Spotify-Wiedergabetest steht noch aus. Die vorherige AirPlay-only-Phase ist damit beendet.
