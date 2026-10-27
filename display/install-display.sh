#!/bin/sh
set -eu
if [ "$(id -u)" -ne 0 ]; then
 echo 'Bitte mit sudo ausführen.' >&2
 exit 1
fi
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python3 -c 'from PIL import Image; import ast,pathlib,sys; Image.open(sys.argv[1]).verify(); ast.parse(pathlib.Path(sys.argv[2]).read_text())' "$src/welcome.png" "$src/framebuffer.py"
python3 -c 'import ast,pathlib,sys; p=pathlib.Path(sys.argv[1]); sys.path.insert(0,str(p/"vendor")); import pyte; ast.parse((p/"tv_console.py").read_text())' "$src"
command -v cec-ctl >/dev/null || { echo 'cec-ctl fehlt'; exit 1; }
install -d -m 755 /opt/stereoanlage-display
install -m 644 "$src/framebuffer.py" "$src/tv_console.py" "$src/welcome.png" /opt/stereoanlage-display/
cp -R "$src/vendor" /opt/stereoanlage-display/
chmod -R a+rX /opt/stereoanlage-display/vendor
chown -R root:root /opt/stereoanlage-display
install -m 644 "$src/stereoanlage-display.service" /etc/systemd/system/stereoanlage-display.service
python3 - <<'PY'
from pathlib import Path
from datetime import datetime
import shutil
p=Path('/boot/firmware/cmdline.txt')
s=p.read_text()
if len(s.strip().splitlines())!=1:raise SystemExit('Unerwartete cmdline-Struktur')
args=[x for x in s.split() if not x.startswith(('loglevel=','systemd.show_status=','vt.global_cursor_default='))]
for x in ('quiet','loglevel=3','logo.nologo','systemd.show_status=false','vt.global_cursor_default=0'):
 if x not in args:args.append(x)
new=' '.join(args)+'\n'
if new!=s:
 shutil.copy2(p,str(p)+'.backup-display-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
 p.write_text(new)
PY
systemctl daemon-reload
systemctl enable stereoanlage-display.service
systemctl restart stereoanlage-display.service
systemctl --no-pager --full status stereoanlage-display.service
printf '\nTV-Anzeige mit Bildschirmtastatur eingerichtet. Kein Neustart, keine Audio-Dienste verändert.\n'
printf 'Leiser Bootbildschirm und neue HDMI-Auflösung gelten ab nächstem Neustart.\n'
