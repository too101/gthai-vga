"""Staged rows must match direct B800 rendering, including classifier effects."""
exec((__import__('pathlib').Path(__file__).parent/'verify_vga.py').read_text().split('\nm=Machine()')[0])
assert symbols['ROW_TEXT_BUFFER']%16==0

def setup(direct=False):
 q=Machine();q.word('VIDBUF',0xa000);q.word('VID_SEG',0xb800);q.word('CRTBASE',0x3d4)
 for row in range(26):q.u.mem_write(0x10000+symbols['L0506H']+row*2,((0xe000+row*19*80)&65535).to_bytes(2,'little'))
 q.word('VID_OFFSET',0x7470);q.crt[14],q.crt[15]=7,0xd0
 if direct:
  q.u.mem_write(0x1ee00,b'\xc3')
  def no_stage(u,address,size,_):u.reg_write(UC_X86_REG_IP,0xee00)
  q.u.hook_add(UC_HOOK_CODE,no_stage,begin=0x10000+symbols['STAGE_ROW_TEXT'],end=0x10000+symbols['STAGE_ROW_TEXT'])
 return q
for adjust in (0,1,2,7):
 ref=setup(True);opt=setup()
 for turn in range(4):
  for q in (ref,opt):
   q.u.mem_write(0x10000+symbols['DISPLAY_COLUMN_ADJUST'],bytes([adjust]))
   for row in range(25):
    if turn==2 and row not in (0,12,24):continue
    cells=bytearray()
    for col in range(80):
     codes=([65,66,32,32,0xa1,0xd4,0xe8,67] if turn==0 else [0xb3,0xa1,0xd8,0xe8,32,65,32,32])
     cells+=bytes([codes[(col+row)%8],((col//8+turn)&7)*16+7])
    if row in (0,1,2,22,23,24):cells[0:2]=bytes([0xb0,7]);cells[158:160]=bytes([0xb3,7])
    for plane in q.planes:plane[0x8000+row*160:0x8000+(row+1)*160]=cells
   # Exercise pending marker detection and subsequent marking/redraw.
   for attempt in range(3):q.call('UPDATE_SCREEN_THAI_25',ds=0x1000)
  assert ref.planes==opt.planes,(adjust,turn)
  assert ref.u.mem_read(0x10000+symbols['VID_SAVE'],4000)==opt.u.mem_read(0x10000+symbols['VID_SAVE'],4000)
  assert opt.u.mem_read(0x10000+symbols['VGA_ROW_ACTIVE'],1)==bytes(1)
print('PASS: staged/direct rows match across Thai composition, spaces, colours, boundary frame/shade markers and dirty-row updates')
q=setup();count=[0];during=[0]
for plane in q.planes:plane[0x8000:0x8000+4000]=bytes([65,7])*2000
q.u.mem_write(0x10000+symbols['CURRENT_MODE'],bytes(1))
def out_count(u,port,size,value,_):
 if port==0x3ce:count[0]+=1
def text_read(u,access,address,size,value,_):
 if u.mem_read(0x10000+symbols['VGA_ROW_ACTIVE'],1)==b'\x01':during[0]+=1
def latch_atomic(u,address,size,_):
 if u.mem_read(0x10000+symbols['VGA_LATCH_VALID'],1)==b'\x01' and u.mem_read(0x10000+symbols['VGA_ROW_ACTIVE'],1)==b'\x01':
  assert not u.reg_read(UC_X86_REG_EFLAGS)&0x200
 elif u.reg_read(UC_X86_REG_EFLAGS)&0x200:
  # Model an unrelated ISR that restores GC registers but destroys VGA latches.
  q.latch=[0x55,0xaa,0x33,0xcc]
q.u.hook_add(UC_HOOK_CODE,latch_atomic)
q.u.hook_add(UC_HOOK_INSN,out_count,None,1,0,UC_X86_INS_OUT)
q.u.hook_add(UC_HOOK_MEM_READ,text_read,begin=0xb8000,end=0xbffff)
entry=0xed00
rel=(symbols['UPDATE_SCREEN_THAI_25']-(entry+4))&65535
q.u.mem_write(0x10000+entry,b'\xfb\xe8'+rel.to_bytes(2,'little')+b'\xc3');symbols['ROW_IRQ_TEST']=entry
q.call('ROW_IRQ_TEST',ds=0x1000)
assert q.u.reg_read(UC_X86_REG_EFLAGS)&0x200
assert q.u.mem_read(0x10000+symbols['ROW_GROUP_HELD'],1)==bytes(1)
assert during[0]==0,during
# The first glyph of each group seeds latches; the following seven reuse them.
# Eight-glyph groups invalidate latch state before restoring interrupts; rows also reseed.
assert count[0]<2200,count
print('PASS: ASCII rendering reads no B800 while staged row is active; whole-screen GC OUT count',count[0])

font=q.u.mem_read(0x10000+symbols['FONT_2']+65*19,19)
for y in range(475):
 for x in range(80):
  off=(0xe000+y*80+x)&65535
  for p in range(4):assert q.planes[p][off]==(font[y%19] if p<3 else 0)
print('PASS: latch cache never spans an enabled interrupt window; simulated unrelated ISR cannot corrupt the image')

# Operand-size MOVSD must retain 16-bit addressing/counts and upper register halves.
q=setup()
page=bytes([65,7])*2000
for plane in q.planes:plane[0x8000:0x8000+4000]=page
wide=(UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP)
for i,reg in enumerate(wide):q.u.reg_write(reg,(0xa510+i)<<16)
q.call('UPDATE_SCREEN_THAI_25',ds=0x1000)
for i,reg in enumerate(wide):assert q.u.reg_read(reg)>>16==0xa510+i,(build_artifact,reg)
assert bytes(q.u.mem_read(0x10000+symbols['VID_SAVE'],4000))==page
assert bytes(q.u.mem_read(0x10000+symbols['ROW_TEXT_BUFFER'],160))==page[:160]
print('PASS: row staging and snapshot copy preserve upper register halves and all 160 bytes')
