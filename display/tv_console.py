#!/usr/bin/env python3
"""HDMI-CEC controlled PTY terminal with a German onscreen keyboard.
Terminal sessions run as the configured non-root user, never as the display service.
"""
from pathlib import Path
import argparse,fcntl,json,os,pwd,pty,queue,re,select,signal,struct,subprocess,sys,threading,time
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'vendor'))
import pyte
from PIL import Image,ImageDraw,ImageFont
from framebuffer import Display

# HDMI CEC User Control codes, not Samsung-specific scan codes.
CEC_KEYS={0x00:'OK',0x01:'UP',0x02:'DOWN',0x03:'LEFT',0x04:'RIGHT',0x09:'MENU',0x0a:'MENU',0x0d:'BACK',0x53:'BACK'}
SPECIAL={'Esc':'\x1b','Tab':'\t','Rück':'\x7f','Entf':'\x1b[3~','Einfg':'\x1b[2~','Enter':'\r','Leer':' ', '↑':'\x1b[A','↓':'\x1b[B','→':'\x1b[C','←':'\x1b[D','Pos1':'\x1b[H','Ende':'\x1b[F','Bild↑':'\x1b[5~','Bild↓':'\x1b[6~'}
SPECIAL.update(dict(zip(('F'+str(i) for i in range(1,13)),['\x1bOP','\x1bOQ','\x1bOR','\x1bOS','\x1b[15~','\x1b[17~','\x1b[18~','\x1b[19~','\x1b[20~','\x1b[21~','\x1b[23~','\x1b[24~'])))
SHIFT={'^':'°','1':'!','2':'"','3':'§','4':'$','5':'%','6':'&','7':'/','8':'(','9':')','0':'=','ß':'?','´':'`','+':'*','ü':'Ü','ö':'Ö','ä':'Ä','#':"'",'<':'>',',':';','.':':','-':'_'}
ALTGR={'2':'²','3':'³','q':'@','e':'€','7':'{','8':'[','9':']','0':'}','ß':'\\','+':'~','<':'|','m':'µ'}
ROWS=[['Esc']+['F'+str(i) for i in range(1,13)],
 list('^1234567890ß´')+['Rück'],
 ['Tab']+list('qwertzuiopü+'),
 ['Fest']+list('asdfghjklöä#')+['Enter'],
 ['Shift']+list('<yxcvbnm,.-')+['Shift'],
 ['Strg','Alt','AltGr','Leer','←','↓','↑','→','Pos1','Ende','Einfg','Entf'],
 ['Bild↑','Bild↓','Strg+C','Strg+D','Strg+L','Verlauf↑','Verlauf↓','Anleitung','Kreuz']]
PRESETS=[('Status','systemctl --user is-active shairport-sync soloist pipewire wireplumber'),('AirPlay-Log','journalctl -b _COMM=shairport-sync -n 60 --no-pager'),('Audio','wpctl status'),('Netzwerk','ip -br address'),('Tastatur',None),('Anleitung',None)]
PALETTE={'black':'#15191d','red':'#ed7b83','green':'#a4d48a','brown':'#dec388','blue':'#86b8fa','magenta':'#c6a1ea','cyan':'#85ccce','white':'#e5e9ef','brightblack':'#7c8793','brightred':'#ff8b90','brightgreen':'#b5e798','brightbrown':'#eed199','brightblue':'#a2c9ff','brightmagenta':'#d8b9f8','brightcyan':'#a4e4e4','brightwhite':'#ffffff','default':'#e5e9ef'}
def color(value,default):
 if value=='default':return default
 if value in PALETTE:return PALETTE[value]
 if re.fullmatch('[0-9a-fA-F]{6}',str(value)):return '#'+value
 return default

def parse_cec(line):
 if 'User Control Pressed' not in line and 'ui-cmd' not in line:
  # Raw cec-ctl format, if enabled.
  m=re.search(r'\b[0-9a-fA-F]{2}:44:([0-9a-fA-F]{2})\b',line)
  return CEC_KEYS.get(int(m[1],16)) if m else None
 tail=line.split('ui-cmd',1)[-1]
 codes=re.findall(r'0x([0-9a-fA-F]{2})',tail)
 if codes:return CEC_KEYS.get(int(codes[-1],16))
 for word,key in [('Right','RIGHT'),('Left','LEFT'),('Down','DOWN'),('Up','UP'),('Select','OK'),('Exit','BACK')]:
  if re.search(r'\b'+word+r'\b',tail,re.I):return key
 return None

class Keyboard:
 def __init__(self):self.row=0;self.col=0;self.shift=False;self.ctrl=False;self.alt=False;self.altgr=False;self.caps=False
 @property
 def key(self):return ROWS[self.row][self.col]
 def move(self,key):
  if key in ('LEFT','RIGHT'):self.col=(self.col+(-1 if key=='LEFT' else 1))%len(ROWS[self.row])
  else:
   x,w=qwertz_geometry(self.row)[self.col];center=x+w/2
   self.row=(self.row+(-1 if key=='UP' else 1))%len(ROWS)
   self.col=min(range(len(ROWS[self.row])),key=lambda i:abs(sum((qwertz_geometry(self.row)[i][0],qwertz_geometry(self.row)[i][1]/2))-center))
 def label(self,k):
  if len(k)==1:
   if self.altgr:return ALTGR.get(k,k)
   if self.shift:return k.lower() if self.caps and k.isalpha() else SHIFT.get(k,k.upper())
   if self.caps and k.isalpha():return k.upper()
  return k
 def press(self):
  return self.activate(self.key)
 def activate(self,k):
  if k in ('Shift','Strg','Alt','AltGr','Fest'):
   attr={'Shift':'shift','Strg':'ctrl','Alt':'alt','AltGr':'altgr','Fest':'caps'}[k];setattr(self,attr,not getattr(self,attr));return None
  if k in ('Anleitung','Verlauf↑','Verlauf↓','Kreuz'):return k
  if k.startswith('Strg+'):
   return chr(ord(k[-1].upper())-64).encode()
  text=SPECIAL.get(k,self.label(k))
  if self.ctrl and len(text)==1:
   v=ord(text.upper())
   if 64<=v<=95:text=chr(v-64)
   elif text==' ':text='\0'
   elif text=='?':text='\x7f'
  if self.alt:text='\x1b'+text
  self.shift=self.ctrl=self.alt=self.altgr=False
  return text.encode('utf-8')

RADIAL_PAGES={
 'ABC':list('abcdefghijklmnopqrstuvwxyzäöüß')+['Leer','Rück'],
 '123':list('1234567890')+['+','-','*','/','=','.',',',':',';','(',')','[',']','{','}','<','>','%','Leer','Rück','Tab','Enter'],
 '#+=':list('!"§$%&/()=?`*+-_,.:;<>|@€{}[]\\~^'),
 'Tasten':['Esc','Tab','Enter','Rück','Entf','Leer','↑','↓','←','→','Pos1','Ende','Bild↑','Bild↓','Einfg','Shift','Strg','Alt','AltGr','Fest']+['F'+str(i) for i in range(1,13)]}
RADIAL_POS=[(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]
RADIAL_DIRS=['UP','RIGHT','DOWN','LEFT']
RADIAL_OPTIONS=['ABC','123','#+=','Tasten','QWERTZ','Diagnose','Anleitung']
class Radial:
 def __init__(self):self.page='ABC';self.group=None;self.index=0;self.options=False;self.option=0
 def reset(self):self.group=None;self.index=0;self.options=False
 def groups(self):
  values=RADIAL_PAGES[self.page]
  return [values[i:i+8] for i in range(0,len(values),8)]
 def handle(self,key):
  if key=='MENU':self.options=not self.options;return None
  if key=='BACK':
   if self.options or self.group is not None:self.reset();return None
   return 'Anleitung'
  if self.options:
   if key in ('UP','LEFT'):self.option=(self.option-1)%len(RADIAL_OPTIONS)
   elif key in ('DOWN','RIGHT'):self.option=(self.option+1)%len(RADIAL_OPTIONS)
   elif key=='OK':
    value=RADIAL_OPTIONS[self.option];self.reset()
    if value in RADIAL_PAGES:self.page=value
    else:return value
   return None
  if self.group is None:
   if key in RADIAL_DIRS:self.group=RADIAL_DIRS.index(key);self.index=0
   elif key=='OK':self.options=True
   return None
  values=self.groups()[self.group]
  if key=='OK':
   value=values[self.index];self.reset();return value
  if key in RADIAL_DIRS:
   x,y=RADIAL_POS[self.index];axis=0 if key in ('LEFT','RIGHT') else 1
   direction=-1 if key in ('UP','LEFT') else 1
   same=[(i,point) for i,point in enumerate(RADIAL_POS[:len(values)]) if point[1-axis]==(x,y)[1-axis]]
   ahead=[(i,pt) for i,pt in same if (pt[axis]-(x,y)[axis])*direction>0]
   if ahead:self.index=min(ahead,key=lambda pair:abs(pair[1][axis]-(x,y)[axis]))[0]
   else:self.index=min(same,key=lambda pair:pair[1][axis]*direction)[0]
  return None

# Approximate ISO German keyboard geometry: staggered letter rows, wide modifiers.
def qwertz_geometry(row):
 units={0:[1]*13,1:[1]*13+[2],2:[1.5]+[1]*12,3:[1.8]+[1]*12+[1.7],4:[1.3]+[1]*11+[2.7],5:[1.4,1.4,1.4,4,1,1,1,1,1,1,1,1],6:[1.2,1.2,1.4,1.4,1.4,1.6,1.6,1.6,1.6]}
 cursor=54;scale=111
 result=[]
 for width in units[row]:
  result.append((cursor,width*scale-8));cursor+=width*scale
 return result

class Terminal:
 def __init__(self,user):
  self.user=user;self.fd=None;self.pid=None
  self.screen=pyte.HistoryScreen(110,16,history=1000,ratio=0.5);self.stream=pyte.ByteStream(self.screen)
 def start(self):
  if self.fd is not None:return
  account=pwd.getpwnam(self.user)
  if account.pw_uid==0:raise RuntimeError('The terminal user must not be root')
  # A fresh helper process claims the PTY; no unsafe fork of our input threads.
  fd,slave=os.openpty()
  fcntl.ioctl(slave,0x5414,struct.pack('HHHH',16,110,0,0))
  try:
   self.process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--shell-fd',str(slave),'--user',self.user],pass_fds=(slave,),start_new_session=True)
  except BaseException:
   os.close(fd);raise
  finally:os.close(slave)
  self.pid=self.process.pid;self.fd=fd;os.set_blocking(fd,False)
  # Terminal replies (cursor position and device attributes) go back to its PTY.
  self.screen.write_process_input=self.send_text
 def send_text(self,text):self.send(text.encode('utf-8'))
 def send(self,data):
  if self.fd is not None:
   try:os.write(self.fd,data)
   except OSError:pass
 def read(self):
  if self.fd is None:return False
  changed=False
  while select.select([self.fd],[],[],0)[0]:
   try:data=os.read(self.fd,32768)
   except (OSError,BlockingIOError):data=b''
   if not data:
    os.close(self.fd);self.fd=None
    if self.pid:self.process.poll()
    self.pid=None;self.stream.feed(b'\r\n[Sitzung beendet. OK startet eine neue Sitzung.]');return True
   self.stream.feed(data);changed=True
  return changed
 def close(self):
  if self.pid:
   try:os.killpg(self.pid,signal.SIGHUP)
   except ProcessLookupError:pass
  if self.fd is not None:os.close(self.fd);self.fd=None

def shell_child(fd,user):
 account=pwd.getpwnam(user)
 if account.pw_uid==0:raise SystemExit('Refusing a root terminal session')
 os.login_tty(fd)
 if os.geteuid()==0:
  os.initgroups(account.pw_name,account.pw_gid);os.setgid(account.pw_gid);os.setuid(account.pw_uid)
 elif os.geteuid()!=account.pw_uid:raise SystemExit('Terminal user mismatch')
 env={'HOME':account.pw_dir,'USER':account.pw_name,'LOGNAME':account.pw_name,'SHELL':'/bin/bash','PATH':'/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin','TERM':'xterm-256color','LANG':'de_DE.UTF-8','XDG_RUNTIME_DIR':f'/run/user/{account.pw_uid}','DBUS_SESSION_BUS_ADDRESS':f'unix:path=/run/user/{account.pw_uid}/bus','HISTFILE':'/dev/null'}
 os.chdir(account.pw_dir)
 os.execve('/bin/bash',['bash','--login'],env)

class CEC:
 def __init__(self,events,device=None):self.events=events;self.device=device;self.process=None;self.running=True
 def run(self):
  while self.running:
   try:
    dev=self.device
    if dev is None:
     for p in sorted(Path('/dev').glob('cec*')):
      data=subprocess.run(['cec-ctl','-d',str(p),'-x'],capture_output=True,text=True,timeout=4)
      if re.search(r'Physical Address\s*:\s*(?!f\.f\.f\.f)[0-9a-f]\.[0-9a-f]\.[0-9a-f]\.[0-9a-f]',data.stdout,re.I):dev=str(p);break
    if dev is None:raise RuntimeError('No connected CEC adapter')
    subprocess.run(['cec-ctl','-d',dev,'--playback','--osd-name','Stereoanlage','--no-rc-passthrough','--rc-src-dev-root'],capture_output=True,timeout=6,check=True)
    # No Active Source, standby or volume messages: TV/audio state is not changed.
    self.process=subprocess.Popen(['stdbuf','-oL','cec-ctl','-s','-d',dev,'--wait-for-msgs'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    self.events.put(('cec','Fernbedienung: HDMI-CEC'))
    last_key=None;last_time=0
    for line in self.process.stdout:
     if not self.running:break
     if 'State Change:' in line and ('PA: f.f.f.f' in line or 'LA mask: 0x0000' in line):break
     key=parse_cec(line)
     if key:
      now=time.monotonic()
      if key!=last_key or now-last_time>0.16:
       self.events.put(('key',key));last_key=key;last_time=now
    if self.process.poll() is None:self.process.terminate()
   except (OSError,RuntimeError,subprocess.SubprocessError):self.events.put(('cec','Fernbedienung: Verbindung wird gesucht'))
   for _ in range(20):
    if not self.running:break
    time.sleep(0.25)
 def close(self):
  self.running=False
  if self.process and self.process.poll() is None:self.process.terminate()

# Standard Linux input key codes; physical keyboards continue to work too.
PHYSICAL={1:'Esc',**dict(zip(range(2,14),list('1234567890ß´'))),14:'Rück',15:'Tab',**dict(zip(range(16,28),list('qwertzuiopü+'))),28:'Enter',**dict(zip(range(30,42),list('asdfghjklöä^'))),43:'#',**dict(zip(range(44,54),list('yxcvbnm,.-'))),55:'*',57:'Leer',71:'7',72:'8',73:'9',74:'-',75:'4',76:'5',77:'6',78:'+',79:'1',80:'2',81:'3',82:'0',83:',',86:'<',87:'F11',88:'F12',96:'Enter',98:'/',102:'Pos1',103:'↑',104:'Bild↑',105:'←',106:'→',107:'Ende',108:'↓',109:'Bild↓',110:'Einfg',111:'Entf'}
PHYSICAL.update({59+i:'F'+str(i+1) for i in range(10)})
class USBKeyboard:
 def __init__(self,events):self.events=events;self.running=True;self.fds={}
 def run(self):
  last_scan=0;event=struct.Struct('llHHI')
  try:
   while self.running:
    if time.monotonic()-last_scan>3:
     for path in Path('/dev/input/by-id').glob('*event-kbd'):
      device=str(path.resolve())
      if device not in self.fds.values():
       try:self.fds[os.open(device,os.O_RDONLY|os.O_NONBLOCK)]=device
       except OSError:pass
     last_scan=time.monotonic()
    if not self.fds:time.sleep(.2);continue
    ready,_,_=select.select(list(self.fds),[],[],.2)
    for fd in ready:
     try:data=os.read(fd,event.size*32)
     except OSError:data=b''
     if not data:
      os.close(fd);self.fds.pop(fd,None);continue
     for offset in range(0,len(data)-event.size+1,event.size):
      _,_,typ,code,value=event.unpack_from(data,offset)
      if typ==1:self.events.put(('physical',(code,value)))
  finally:
   for fd in self.fds:os.close(fd)
 def close(self):self.running=False

class UI:
 def __init__(self,user,font_root='/usr/share/fonts/truetype/dejavu'):
  self.term=Terminal(user);self.kb=Keyboard();self.radial=Radial();self.layout='radial';self.mode='home';self.focus='keys';self.preset=0;self.cec_status='Fernbedienung: HDMI-CEC';self.font_root=Path(font_root)
  self.welcome=Image.open(ROOT/'welcome.png').convert('RGB').resize((1920,1080),Image.Resampling.LANCZOS)
  self.fonts={};self.physical_mods=set();self.physical_caps=False
 def font(self,n,mono=False,bold=False):
  key=(n,mono,bold)
  if key not in self.fonts:self.fonts[key]=ImageFont.truetype(str(self.font_root/('DejaVuSans'+('Mono' if mono else '')+('-Bold' if bold else '')+'.ttf')),n)
  return self.fonts[key]
 def key(self,k):
  if self.mode=='home':
   if k in ('OK','MENU'):
    self.term.start();self.mode='terminal'
   return
  if self.layout=='radial' and self.focus=='keys':
   action=self.radial.handle(k)
   if action=='QWERTZ':self.layout='qwertz'
   elif action=='Diagnose':self.focus='presets'
   elif action=='Anleitung':self.mode='home'
   elif action is not None:
    if self.term.fd is None:self.term.start()
    result=self.kb.activate(action)
    if isinstance(result,bytes):self.term.send(result)
   return
  if k in ('BACK','MENU'):self.mode='home';return
  if self.focus=='presets':
   if k=='LEFT':self.preset=(self.preset-1)%len(PRESETS)
   elif k=='RIGHT':self.preset=(self.preset+1)%len(PRESETS)
   elif k=='DOWN':self.focus='keys';self.kb.row=0
   elif k=='UP':self.focus='keys';self.kb.row=len(ROWS)-1
   elif k=='OK':
    label,cmd=PRESETS[self.preset]
    if label=='Anleitung':self.mode='home'
    elif label=='Tastatur':self.layout='qwertz' if self.layout=='radial' else 'radial';self.focus='keys'
    else:self.term.send((cmd+'\r').encode())
   return
  if k=='UP' and self.kb.row==0:self.focus='presets';return
  if k in ('UP','DOWN','LEFT','RIGHT'):self.kb.move(k)
  elif k=='OK':
   if self.term.fd is None:self.term.start()
   result=self.kb.press()
   if result=='Anleitung':self.mode='home'
   elif result=='Kreuz':self.layout='radial';self.radial.reset()
   elif result=='Verlauf↑':self.term.screen.prev_page()
   elif result=='Verlauf↓':self.term.screen.next_page()
   elif isinstance(result,bytes):self.term.send(result)
 def physical(self,code,value):
  mods={29:'ctrl',97:'ctrl',42:'shift',54:'shift',56:'alt',100:'altgr'}
  if code in mods:
   if value:self.physical_mods.add(code)
   else:self.physical_mods.discard(code)
   return
  if not value:return
  if code==88:
   if self.mode=='home':self.term.start();self.mode='terminal'
   else:self.mode='home'
   return
  if code==58:
   if value==1:self.physical_caps=not self.physical_caps
   return
  key=PHYSICAL.get(code)
  if self.mode!='terminal' or key is None:return
  if self.term.fd is None:self.term.start()
  kb=Keyboard()
  for attr in ('ctrl','shift','alt','altgr'):
   setattr(kb,attr,any(mods.get(c)==attr for c in self.physical_mods))
  kb.caps=self.physical_caps
  # Feed the same key encoder used by the onscreen keyboard.
  for row,keys in enumerate(ROWS):
   if key in keys:
    kb.row=row;kb.col=keys.index(key);data=kb.press()
    if isinstance(data,bytes):self.term.send(data)
    return
  if len(key)==1:self.term.send(key.encode())

 def render_radial(self,im,d):
  r=self.radial
  def txt(x,y,t,size=23,c='#e5ecf4'):
   d.text((x,y),t,font=self.font(size),fill=c,anchor='mm')
  for i,label in enumerate(RADIAL_OPTIONS):
   y=694+i*44
   chosen=r.options and r.option==i
   d.rounded_rectangle((54,y,300,y+36),7,fill='#97caff' if chosen else '#1c2936')
   txt(177,y+18,label,21,'#08131d' if chosen else '#e5ecf4')
  cx,cy=1000,843
  if r.group is None:
   for i,((dx,dy),values) in enumerate(zip([(0,-1),(1,0),(0,1),(-1,0)],r.groups())):
    x=cx+dx*265;y=cy+dy*107
    d.rounded_rectangle((x-119,y-43,x+119,y+43),12,fill='#223447')
    labels=[self.kb.label(k) for k in values]
    txt(x,y-15,'  '.join(labels[:4]),23);txt(x,y+17,'  '.join(labels[4:]),23)
   txt(cx,cy-14,r.page,26);txt(cx,cy+20,'OK: Optionen',19,'#9caebf')
  else:
   values=r.groups()[r.group]
   for i,((dx,dy),key) in enumerate(zip(RADIAL_POS,values)):
    x=cx+dx*190;y=cy+dy*103;chosen=r.index==i
    d.rounded_rectangle((x-84,y-40,x+84,y+40),10,fill='#97caff' if chosen else '#223447')
    txt(x,y,self.kb.label(key),29,'#08131d' if chosen else '#e5ecf4')
   txt(cx,cy-12,'OK: tippen',20);txt(cx,cy+17,'Zurück: Gruppen',16,'#9caebf')
  txt(1630,760,'1. Richtung: Gruppe öffnen',20,'#aab7c5')
  txt(1630,803,'2. Pfeile: Zeichen wählen',20,'#aab7c5')
  txt(1630,846,'3. OK: Zeichen tippen',20,'#aab7c5')
  txt(1630,904,'Danach zurück zur Mitte.',19,'#aab7c5')
  txt(960,1037,'OK in der Mitte: Zahlen, Sonderzeichen, Terminaltasten und QWERTZ auswählen.',20,'#9caebf')

 def render(self):
  if self.mode=='home':
   im=self.welcome.copy();d=ImageDraw.Draw(im);d.text((960,1020),'OK: Terminal und Bildschirmtastatur',font=self.font(22),fill='#aab3bd',anchor='mm');return im
  im=Image.new('RGB',(1920,1080),'#080c10');d=ImageDraw.Draw(im)
  def txt(x,y,t,n=22,c='#e4eaf1',mono=False,bold=False):d.text((x,y),t,font=self.font(n,mono,bold),fill=c,anchor='lt')
  txt(54,25,'Terminal',30,bold=True);txt(1240,32,'Zurück: Anleitung · OK: Taste drücken',21,c='#a4b0bd')
  for i,(label,_) in enumerate(PRESETS):
   x=54+i*302
   d.rounded_rectangle((x,76,x+287,120),10,fill='#315879' if self.focus=='presets' and i==self.preset else '#17222e')
   txt(x+15,86,label,22)
  d.rounded_rectangle((44,137,1876,630),10,fill='#10171e')
  screen=self.term.screen;terminal_font=self.font(26,mono=True)
  cellw=terminal_font.getlength("M");cellh=29;ox=62;oy=149
  baseline=terminal_font.getmetrics()[0]
  # Cell rendering preserves ANSI colours, cursor, full-screen terminal programs.
  for y in range(screen.lines):
   line=screen.buffer[y]
   for x in range(screen.columns):
    cell=line[x];fg=color(cell.fg,'#e5e9ef');bg=color(cell.bg,'#10171e')
    if cell.reverse:fg,bg=bg,fg
    if bg!='#10171e':d.rectangle((ox+x*cellw,oy+y*cellh,ox+(x+1)*cellw,oy+(y+1)*cellh),fill=bg)
    if cell.data.strip():d.text((ox+x*cellw,oy+y*cellh+baseline),cell.data,font=self.font(26,True,cell.bold),fill=fg,anchor='ls')
    if cell.underscore:d.line((ox+x*cellw,oy+(y+1)*cellh-2,ox+(x+1)*cellw,oy+(y+1)*cellh-2),fill=fg)
  if not screen.cursor.hidden:
   cx=ox+min(screen.cursor.x,screen.columns-1)*cellw;cy=oy+min(screen.cursor.y,screen.lines-1)*cellh
   d.rectangle((cx,cy,cx+cellw-1,cy+cellh-1),outline='#d5e9ff',width=2)
  txt(54,648,self.cec_status,19,'#9caebf')
  mods=' · '.join(k for k,v in [('Shift',self.kb.shift),('Strg',self.kb.ctrl),('Alt',self.kb.alt),('AltGr',self.kb.altgr),('Feststelltaste',self.kb.caps)] if v)
  txt(1140,648,mods,19,'#9bceff')
  if self.layout=='radial':
   self.render_radial(im,d)
  else:
   for row,keys in enumerate(ROWS):
    for col,key in enumerate(keys):
     x,width=qwertz_geometry(row)[col];y=684+row*47
     selected=self.focus=='keys' and row==self.kb.row and col==self.kb.col
     active={'Shift':self.kb.shift,'Strg':self.kb.ctrl,'Alt':self.kb.alt,'AltGr':self.kb.altgr,'Fest':self.kb.caps}.get(key,False)
     d.rounded_rectangle((x,y,x+width,y+39),7,fill='#97caff' if selected else '#304b62' if active else '#1c2936')
     label=self.kb.label(key)
     d.text((x+width/2,y+19),label,font=self.font(19 if len(label)>6 else 21),fill='#08131d' if selected else '#e5ecf4',anchor='mm')
   txt(54,1032,'Strg / Shift / Alt / AltGr auswählen, dann die gewünschte Taste. Zurück blendet das Terminal aus.',20,'#9caebf')
  return im

def main():
 p=argparse.ArgumentParser();p.add_argument('--shell-fd',type=int);p.add_argument('--user',default='jaron');p.add_argument('--cec-device');p.add_argument('--preview');p.add_argument('--font-root',default='/usr/share/fonts/truetype/dejavu');a=p.parse_args()
 if a.shell_fd is not None:shell_child(a.shell_fd,a.user);return
 ui=UI(a.user,a.font_root)
 if a.preview:
  ui.mode='terminal';ui.term.stream.feed(b'jaron@spotify-pi:~$ systemctl --user is-active shairport-sync soloist\r\nactive\r\nactive\r\njaron@spotify-pi:~$ ')
  ui.render().save(a.preview);return
 events=queue.Queue();cec=CEC(events,a.cec_device);threading.Thread(target=cec.run,daemon=True).start()
 usb=USBKeyboard(events);threading.Thread(target=usb.run,daemon=True).start()
 running=True
 def stop(*_):
  nonlocal running
  running=False
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 display=Display();dirty=True;last=0;last_check=0
 try:
  while running:
   try:
    kind,value=events.get(timeout=0.04)
    batch=[(kind,value)]
    for _ in range(63):
     try:batch.append(events.get_nowait())
     except queue.Empty:break
    for kind,value in batch:
     if kind=='key':ui.key(value)
     elif kind=='cec':ui.cec_status=value
     elif kind=='physical':ui.physical(*value)
    dirty=True
   except queue.Empty:pass
   if ui.term.read() and ui.mode=='terminal':dirty=True
   now=time.monotonic()
   if now-last_check>2:
    if display.changed():dirty=True
    last_check=now
   if dirty and now-last>0.12:
    display.show(ui.render());dirty=False;last=time.monotonic()
 finally:
  cec.close();usb.close();ui.term.close();display.close()
if __name__=='__main__':main()
