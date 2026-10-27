# Betrieb und Diagnose

## Zugriff

Auf dem Mac den bestehenden SSH-Schlüssel und den bereits verifizierten Hostschlüssel verwenden. Bei Zugriff über eine andere Adresse den vorhandenen HostKeyAlias beibehalten. Niemals die Hostschlüsselprüfung abschalten. Tailscale dient hier dem SSH-Zugang; AirPlay-Erkennung und Sonos-Multiroom werden im Heimnetz geprüft.

Passwörter, SSH-Schlüssel, Tailscale-Geräteschlüssel und Soloist-API-Schlüssel gehören nicht in Git. Alte lokale Passwortnotizen sind veraltet.

## Zustandsprüfung auf dem Pi

Als Audio-Benutzer:

```sh
bash scripts/diagnose.sh
```

Das Skript liefert Status, Autostart und Shairport-Version. Bei PipeWire-Fragen zusätzlich lokal `wpctl status` prüfen. Nummerische Sink-IDs können sich ändern; für Vorlagen den dokumentierten stabilen Ausgangsnamen verwenden.

## AirPlay-/Sonos-Fehler eingrenzen

1. Sendergerät, Betriebssystem, App und Sonos-Modell notieren.
2. Pi alleine auswählen; hörbare Ausgabe und Uhrzeit notieren.
3. Sonos hinzufügen; Auswahlzustand, Ton und Synchronität notieren.
4. Wieder nur Pi auswählen und Ergebnis notieren.
5. Bei Fehler den Zustand vor einem Neustart sichern. Relevante Journale lokal mit `journalctl --user -u shairport-sync --since '10 minutes ago'` und `journalctl -u nqptp --since '10 minutes ago'` lesen.

Journale können private Geräte- oder Netzwerkdaten enthalten. Nicht ungeprüft committen oder teilen. Private Ausgaben unter `.local/` halten. Während einer laufenden Wiedergabe keine Dienste neu starten.

## Änderungen und Updates

Vor Änderungen betroffene Konfigurationsdateien privat sichern, Diff prüfen und einen Rückweg festhalten. Vorlagen sind Ausschnitte bzw. übernommene Dienstdefinitionen, keine vollständige Installationsanleitung. Nichts automatisch überschreiben. Paket-, Soloist- oder Shairport-Updates benötigen einen eigenen Wartungstermin mit Wiedergabetest; die historischen Helfer aus `/tmp` wurden nicht übernommen.

Nach einer genehmigten Änderung AirPlay alleine, Spotify alleine, Wechsel zwischen beiden und Sonos-Multiroom testen. Neustart und anschließender Wiederanlauf separat testen. Ein aktiver Dienst ist kein Audiotest.
