from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument('--font',default='/System/Library/Fonts/Helvetica.ttc' if Path('/System/Library/Fonts/Helvetica.ttc').exists() else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--preview',type=Path);a=p.parse_args()
S=2;ROOT=a.root
im=Image.new('RGB',(3840,2160),'#090b0d');d=ImageDraw.Draw(im)
def f(n,b=False):
 path=a.font
 if b and path.endswith('Sans.ttf'):path=path.replace('Sans.ttf','Sans-Bold.ttf')
 return ImageFont.truetype(path,n*S,index=1 if b and path.endswith('.ttc') else 0)
def text(x,y,s,n=30,c='#f4f5f6',b=False):d.text((x*S,y*S),s,font=f(n,b),fill=c,anchor='lt')
def rect(box,fill,r=0,outline=None):d.rounded_rectangle(tuple(int(v*S) for v in box),r*S,fill,outline,width=S)
def icon(file,x,y,w,h,white=False):
 p=Image.open(ROOT/'assets'/file).convert('RGBA');p=p.crop(p.getbbox())
 if white:
  alpha=p.getchannel('A');p=Image.new('RGBA',p.size,'#f4f5f6');p.putalpha(alpha)
 ratio=min(w*S/p.width,h*S/p.height);p=p.resize((round(p.width*ratio),round(p.height*ratio)),Image.Resampling.LANCZOS)
 im.paste(p,(x*S,y*S),p)
for x in (90,985):rect((x,110,x+845,970),'#000000',28,'#262b30')
icon('airplay-audio.png',142,165,90,90,True)
text(267,185,'AirPlay',60,b=True)
icon('spotify-logo.png',1037,177,310,85)
for x,steps in ((142,[['iPhone mit dem Heim-WLAN verbinden.'],['Musik starten und das AirPlay-Symbol','antippen.'],['„Stereoanlage AirPlay“ auswählen.']]),(1037,[['Spotify öffnen und Musik starten.'],['„Mit einem Gerät verbinden“ antippen.'],['„Stereoanlage Spotify“ auswählen.']])):
 y=325
 for i,lines in enumerate(steps,1):
  text(x,y,str(i),30,'#9da7b0',True)
  for j,line in enumerate(lines):text(x+47,y+j*40,line,30)
  y+=len(lines)*40+30
text(142,609,'Zusammen mit Sonos',32,b=True)
text(142,665,'4',30,'#9da7b0',True)
text(189,665,'In derselben AirPlay-Liste zusätzlich',30)
text(189,705,'die Sonos-Boxen anhaken.',30)
text(189,754,'Bei beiden muss ein Häkchen stehen.',25,'#a6afb7')
text(1037,609,'Für den Garten',32,b=True)
text(1037,665,'Der Pi spielt selbstständig weiter, auch',30)
text(1037,705,'wenn dein Handy das WLAN verliert.',30)
text(1037,754,'Der Pi braucht weiterhin Internet.',25,'#a6afb7')
for x in (142,1037):d.line((x*S,822*S,(x+741)*S,822*S),fill='#30353a',width=2)
text(142,852,'Qualität: je nach App AAC oder Lossless',27,'#a6afb7')
text(142,899,'Empfänger unterstützt bis 24 Bit / 48 kHz.',27,'#a6afb7')
text(1037,852,'Qualität: bis 24 Bit / 44,1 kHz verlustfrei',27,'#a6afb7')
text(1037,899,'Mit Premium und aktivierter Lossless-Qualität.',27,'#a6afb7')
im.save(ROOT/'welcome.png')
if a.preview:
 a.preview.parent.mkdir(parents=True,exist_ok=True);im.resize((1600,900),Image.Resampling.LANCZOS).save(a.preview)
print('3840 x 2160 rendered')
