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
  def no_groups(u,address,size,_):u.reg_write(UC_X86_REG_IP,symbols['THAI8_SPACE_SINGLE'])
  q.u.hook_add(UC_HOOK_CODE,no_groups,begin=0x10000+symbols['THAI8_SPACE_GROUP'],end=0x10000+symbols['THAI8_SPACE_GROUP'])
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

# Position cache agrees with integer row/column arithmetic at every cell.
q=setup();visits=[0]
def new_row(u,address,size,_):visits[0]+=1
q.u.hook_add(UC_HOOK_CODE,new_row,begin=0x10000+symbols['T8P_NEW_ROW'],end=0x10000+symbols['T8P_NEW_ROW'])
for cell in range(2000):
 q.call('THAI8_POSITION',si=cell*2)
 assert q.u.reg_read(UC_X86_REG_DI)==(0xe000+(cell//80)*1520+cell%80)&65535,cell
assert visits[0]==25,visits
print('PASS: all 2000 Thai-8 positions match, with 25 row divisions instead of 2000')
for pattern in (0,1,2):
 ref=setup(True);opt=setup();page=bytearray()
 for cell in range(2000):
  code=65 if pattern==2 and cell%80 in (0,79) else 32
  attr=7 if pattern==0 else (cell%16)*16+7
  page+=bytes([code,attr])
 for q in (ref,opt):
  for plane in q.planes:plane[0x8000:0x8000+4000]=page
  q.call('UPDATE_SCREEN_THAI_8',ds=0x1000)
 assert ref.planes==opt.planes,pattern
 assert ref.u.mem_read(0x10000+symbols['VID_SAVE'],4000)==opt.u.mem_read(0x10000+symbols['VID_SAVE'],4000)
print('PASS: Thai-8 grouped blanks match single-cell rendering across colours and row edges')
if build_artifact=='GTHAI386':
 q=Machine();a=0x6000;b=0x7000
 for words in (1,3,79,1999):
  data=bytes([65,7])*words;q.u.mem_write(0x16000,data);q.u.mem_write(0x17000,data)
  for byte in range(words*2):
   q.u.mem_write(0x17000+byte,b'\xff')
   q.call('COMPARE_TEXT386_ANY',ds=0x1000,es=0x1000,si=a,di=b,cx=words)
   cell=byte//2
   assert q.u.reg_read(UC_X86_REG_SI)==a+2*(cell+1)
   assert q.u.reg_read(UC_X86_REG_CX)==words-cell-1
   assert not q.u.reg_read(UC_X86_REG_EFLAGS)&64
   q.u.mem_write(0x17000+byte,data[byte:byte+1])
  q.call('COMPARE_TEXT386_ANY',ds=0x1000,es=0x1000,si=a,di=b,cx=words)
  assert q.u.reg_read(UC_X86_REG_CX)==0 and q.u.reg_read(UC_X86_REG_EFLAGS)&64
 print('PASS: odd-length CMPSD tail comparison finds every differing byte with exact positions/counts')
