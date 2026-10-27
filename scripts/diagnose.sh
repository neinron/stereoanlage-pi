#!/usr/bin/env bash
# Nur ausgewählte Statuswerte, keine Environment-Dateien oder Journale.
set -u
if ! command -v systemctl >/dev/null 2>&1; then
  printf '%s\n' 'Diese Diagnose auf dem Pi mit systemd ausführen.' >&2
  exit 2
fi
printf '%s\n' 'Systemdienste (active / enabled):'
for unit in tailscaled ssh nqptp; do
  printf '\n%s\n' "$unit"
  systemctl is-active "$unit" || true
  systemctl is-enabled "$unit" || true
done
printf '\n%s\n' 'Benutzer-Dienste (active / enabled):'
for unit in shairport-sync pipewire wireplumber soloist; do
  printf '\n%s\n' "$unit"
  systemctl --user is-active "$unit" || true
  systemctl --user is-enabled "$unit" || true
done
printf '\n%s\n' 'Shairport-Version:'
if [ -x /usr/local/bin/shairport-sync ]; then
  /usr/local/bin/shairport-sync -V
fi
printf '\n%s\n' 'Für Ausgang und Streams lokal wpctl status prüfen.'
