"""Thai 8-line mode batching must preserve pixels, snapshots and GC state."""
exec((__import__('pathlib').Path(__file__).parent/'verify_vga.py').read_text().split('\nm=Machine()')[0])
def setup(disable=False):
 q=Machine();q.word('VIDBUF',0xa000);q.word('VID_SEG',0xb800);q.word('CRTBASE',0x3d4)
 for row in range(26):q.u.mem_write(0x10000+symbols['L0506H']+row*2,((0xe000+row*19*80)&65535).to_bytes(2,'little'))
 q.word('VID_OFFSET',0x7470);q.crt[14],q.crt[15]=7,0xd0
 q.u.mem_write(0x10000+symbols['DISPMODE'],b'\x01')
 if disable:
  def standalone(u,address,size,_):u.mem_write(0x10000+symbols['VGA_BATCH_ACTIVE'],b'\0')
  q.u.hook_add(UC_HOOK_CODE,standalone,begin=0x10000+symbols['L4F51H'],end=0x10000+symbols['L4F51H'])
 return q
ref=setup(True);opt=setup();counts=[0,0]
for i,q in enumerate((ref,opt)):
 def count(u,port,size,value,_,i=i):
  if port==0x3ce:counts[i]+=1
 q.u.hook_add(UC_HOOK_INSN,count,None,1,0,UC_X86_INS_OUT)
for turn in range(5):
 page=bytearray()
 for cell in range(2000):
  code=65 if turn==0 else ([65,0xa1,0xd4,0xe8,32,66,0xb3,0xb0][(cell+turn)%8])
  page+=bytes([code,((cell//8+turn)%16)*16+(cell%15+1)])
 for q in (ref,opt):
  for plane in q.planes:plane[0x8000:0x8000+4000]=page
  q.u.mem_write(0x10000+symbols['CURRENT_MODE'],b'\0')
  q.call('UPDATE_SCREEN_THAI_8',ds=0x1000)
  assert q.gc[5]==0 and q.gc[1]==0
  assert q.u.mem_read(0x10000+symbols['VGA_BATCH_ACTIVE'],1)==b'\0'
  assert q.u.mem_read(0x10000+symbols['VGA_BATCH_VALID'],1)==b'\0'
 assert ref.planes==opt.planes,turn
 assert ref.u.mem_read(0x10000+symbols['VID_SAVE'],4000)==opt.u.mem_read(0x10000+symbols['VID_SAVE'],4000)
 if turn==0:
  assert counts==[14000,8003],counts
  print('PASS: Thai-8 full ASCII redraw GC OUT count 14000 -> 8003')
# Unchanged-screen paths with hidden, moved and stationary cursor.
for hi,lo in ((0,0),(3,40),(3,40),(7,0xd0)):
 for q in (ref,opt):
  q.crt[14],q.crt[15]=hi,lo
  q.call('UPDATE_SCREEN_THAI_8',ds=0x1000)
  assert q.gc[5]==0 and q.gc[1]==0
  assert q.u.mem_read(0x10000+symbols['VGA_BATCH_ACTIVE'],1)==b'\0'
 assert ref.planes==opt.planes
# Switch to the composed updater and back.
for mode,label in ((2,'UPDATE_SCREEN_THAI_25'),(1,'UPDATE_SCREEN_THAI_8')):
 for q in (ref,opt):
  q.u.mem_write(0x10000+symbols['DISPMODE'],bytes([mode]))
  q.call(label,ds=0x1000)
 assert ref.planes==opt.planes
print('PASS: Thai-8 mixed glyphs/attributes, blank flushes, cursor exits and updater switching match standalone rendering')
