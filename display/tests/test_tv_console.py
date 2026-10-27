import importlib.util,pathlib,sys,unittest,random
ROOT=pathlib.Path(__file__).resolve().parent
if (ROOT/'tv_console.py').exists():sys.path.insert(0,str(ROOT))
else:sys.path.insert(0,str(ROOT.parent))
import tv_console as app
from PIL import Image
from framebuffer import pack_pixels
class Tests(unittest.TestCase):
 def key(self,k,**mods):
  kb=app.Keyboard()
  for name,val in mods.items():setattr(kb,name,val)
  for row,keys in enumerate(app.ROWS):
   if k in keys:kb.row=row;kb.col=keys.index(k);return kb.press()
  self.fail('Key missing: '+k)
 def test_ctrl_and_escape(self):
  self.assertEqual(self.key('c',ctrl=True),b'\x03')
  self.assertEqual(self.key('d',ctrl=True),b'\x04')
  self.assertEqual(self.key('Tab'),b'\t');self.assertEqual(self.key('Esc'),b'\x1b')
  self.assertEqual(self.key('←'),b'\x1b[D');self.assertEqual(self.key('Entf'),b'\x1b[3~')
  self.assertEqual(self.key('F12'),b'\x1b[24~')
 def test_german_symbols(self):
  for key,expected in [('q','@'),('e','€'),('ß','\\'),('7','{'),('8','['),('9',']'),('0','}'),('+','~'),('<','|')]:
   self.assertEqual(self.key(key,altgr=True),expected.encode())
  self.assertEqual(self.key('ä',shift=True),'Ä'.encode())
  self.assertEqual(self.key('a',caps=True,shift=True),b'a')
  self.assertEqual(self.key('1',shift=True),b'!')
  self.assertEqual(self.key('b',alt=True),b'\x1bb')
 def test_all_keys_and_modifiers(self):
  for row,keys in enumerate(app.ROWS):
   for col,_ in enumerate(keys):
    kb=app.Keyboard();kb.row=row;kb.col=col
    self.assertIsInstance(kb.press(),(bytes,str,type(None)))
  kb=app.Keyboard()
  for k in ['UP','LEFT','DOWN','RIGHT']*200:
   kb.move(k);self.assertIn(kb.key,app.ROWS[kb.row])
 def test_cec(self):
  for code,key in app.CEC_KEYS.items():
   self.assertEqual(app.parse_cec(f'User Control Pressed (0x44): ui-cmd: Test (0x{code:02x})'),key)
   self.assertEqual(app.parse_cec(f'0b:44:{code:02x}'),key)
  self.assertIsNone(app.parse_cec('User Control Released (0x45)'))
  self.assertIsNone(app.parse_cec('unrelated message'))
 def test_ansi(self):
  screen=app.pyte.Screen(30,4);stream=app.pyte.ByteStream(screen)
  stream.feed(b'hello\r\n\x1b[31mred\x1b[0m')
  self.assertTrue(screen.display[1].startswith('red'));self.assertEqual(screen.buffer[1][0].fg,'red')
  stream.feed(b'\x1b[2J\x1b[Hdone');self.assertTrue(screen.display[0].startswith('done'))
 def test_terminal_replies(self):
  t=app.Terminal('unused');sent=[];t.screen.write_process_input=sent.append
  t.stream.feed(b'\x1b[6n')
  self.assertTrue(sent and sent[-1].endswith('R'))
 def test_hidden_input(self):
  # The emulator displays bytes sent by the shell, not the keyboard itself.
  t=app.Terminal('unused');t.stream.feed(b'Password: ')
  t.send(b'fake-test-password')
  self.assertNotIn('fake-test-password','\n'.join(t.screen.display))
 def test_rgb565(self):
  v=[0]*20;v[6]=16;v[8:11]=[11,5,0];v[11:14]=[5,6,0];v[14:17]=[0,5,0]
  pixels=[(random.randrange(256),random.randrange(256),random.randrange(256)) for _ in range(80)]
  im=Image.new('RGB',(80,1));im.putdata(pixels)
  expected=b''.join((((r>>3)<<11)|((g>>2)<<5)|(b>>3)).to_bytes(2,'little') for r,g,b in pixels)
  self.assertEqual(pack_pixels(im,tuple(v)),expected)
if __name__=='__main__':unittest.main()
