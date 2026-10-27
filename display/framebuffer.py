#!/usr/bin/env python3
"""Static console image; no network, browser, or audio access."""
import argparse,array,ctypes,fcntl,mmap,os,signal,struct,sys,time
from PIL import Image,ImageOps
class Fix(ctypes.Structure):
 _fields_=[('id',ctypes.c_char*16),('smem_start',ctypes.c_ulong),('smem_len',ctypes.c_uint32),('type',ctypes.c_uint32),('type_aux',ctypes.c_uint32),('visual',ctypes.c_uint32),('xpanstep',ctypes.c_uint16),('ypanstep',ctypes.c_uint16),('ywrapstep',ctypes.c_uint16),('line_length',ctypes.c_uint32),('mmio_start',ctypes.c_ulong),('mmio_len',ctypes.c_uint32),('accel',ctypes.c_uint32),('capabilities',ctypes.c_uint16),('reserved',ctypes.c_uint16*2)]
def framebuffer_info(fd):
 raw=bytearray(160);fcntl.ioctl(fd,0x4600,raw,True)
 v=struct.unpack_from('20I',raw)
 fix=Fix();fcntl.ioctl(fd,0x4602,fix,True)
 return v,fix

def pack_pixels(image,v):
 bpp=v[6];red=v[8:11];green=v[11:14];blue=v[14:17]
 if bpp==16 and red==(11,5,0) and green==(5,6,0) and blue==(0,5,0):
  r,g,b=(band.tobytes() for band in image.split())
  return array.array('H',(((rr>>3)<<11)|((gg>>2)<<5)|(bb>>3) for rr,gg,bb in zip(r,g,b))).tobytes()
 if bpp==32 and red==(16,8,0) and green==(8,8,0) and blue==(0,8,0):
  return image.tobytes('raw','BGRX')
 raise RuntimeError('Unsupported framebuffer pixel format; console left unchanged')

def main():
 p=argparse.ArgumentParser();p.add_argument('image');p.add_argument('--once',action='store_true');p.add_argument('--no-console',action='store_true');args=p.parse_args()
 source=Image.open(args.image).convert('RGB');tty=None;fd=None;memory=None;running=True;last=None
 def stop(*_):
  nonlocal running
  running=False
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 try:
  fd=os.open('/dev/fb0',os.O_RDWR)
  while running:
   v,fix=framebuffer_info(fd)
   w,h,xv,yv,xo,yo,bpp=v[:7]
   key=(tuple(v),fix.line_length,fix.smem_len)
   if key!=last:
    if w<=0 or h<=0 or fix.line_length<w*bpp//8:raise RuntimeError('Invalid display geometry')
    image=ImageOps.pad(source,(w,h),method=Image.Resampling.LANCZOS,color='black')
    pixels=pack_pixels(image,v)
    if not args.no_console and tty is None:
     tty=os.open('/dev/tty1',os.O_RDWR|os.O_NOCTTY)
     os.write(tty,b'\x1b[?25l\x1b[9;0]\x1b[14;0]')
     fcntl.ioctl(tty,0x4B3A,1) # KD_GRAPHICS: keep console text off the image
    if memory:memory.close()
    memory=mmap.mmap(fd,fix.smem_len)
    rowbytes=w*bpp//8
    start=yo*fix.line_length+xo*bpp//8
    if start+(h-1)*fix.line_length+rowbytes>fix.smem_len:raise RuntimeError('Framebuffer too small')
    for y in range(h):
     offset=start+y*fix.line_length
     memory[offset:offset+rowbytes]=pixels[y*rowbytes:(y+1)*rowbytes]
    last=key
    print(f'Displaying {w}x{h}, {bpp} bpp',flush=True)
   if args.once:break
   time.sleep(2)
 finally:
  if memory:memory.close()
  if fd is not None:os.close(fd)
  if tty is not None:
   fcntl.ioctl(tty,0x4B3A,0)
   os.write(tty,b'\x1b[?25h');os.close(tty)
if __name__=='__main__':main()
