"""Exact-pixel partial updates versus the same renderer forced to draw whole rows."""
exec((__import__('pathlib').Path(__file__).parent/'verify_vga.py').read_text().split('\nm=Machine()')[0])
def setup(full=False):
 q=Machine();q.word('VIDBUF',0xa000);q.word('VID_SEG',0xb800);q.word('CRTBASE',0x3d4)
 for row in range(26):q.u.mem_write(0x10000+symbols['L0506H']+row*2,((0xe000+row*19*80)&65535).to_bytes(2,'little'))
 q.word('VID_OFFSET',0x7470);q.crt[14],q.crt[15]=7,0xd0
 if full:
  q.u.mem_write(0x1ee00,b'\xc3')
  def no_plan(u,address,size,_):u.reg_write(UC_X86_REG_IP,0xee00)
  q.u.hook_add(UC_HOOK_CODE,no_plan,begin=0x10000+symbols['PREPARE_PARTIAL_ROW'],end=0x10000+symbols['PREPARE_PARTIAL_ROW'])
 return q

def put(q,screen):
 for plane in q.planes:plane[0x8000:0x8000+4000]=screen

def update(q):
 q.call('UPDATE_SCREEN_THAI_25',ds=0x1000)
 assert q.u.mem_read(0x10000+symbols['ROW_PLAN_GUARD'],2)==b'\x5a\xa5'
 assert q.u.mem_read(0x10000+symbols['ROW_GROUP_HELD'],1)==bytes(1)

def equal(ref,opt,label):
 assert ref.planes==opt.planes,label
 assert ref.u.mem_read(0x10000+symbols['VID_SAVE'],4000)==opt.u.mem_read(0x10000+symbols['VID_SAVE'],4000),label

ref=setup(True);opt=setup();screen=bytearray(bytes([65,7])*2000)
for q in (ref,opt):put(q,screen);update(q);q.writes.clear()
screen[(12*80+40)*2]=66
for q in (ref,opt):put(q,screen);update(q)
equal(ref,opt,'one ASCII cell')
assert len(opt.writes)==20,len(opt.writes)
assert len(ref.writes)==1530,len(ref.writes)
print('PASS: one changed ASCII cell writes 20 VGA bytes instead of 1530; exact complete image preserved')

for adjust in (0,1,2,7):
 ref=setup(True);opt=setup();screen=bytearray(bytes([32,7])*2000)
 codes=[0xa1,0xd4,0xe8]+[65+n%26 for n in range(77)]
 for row in (0,12,24):
  for col,code in enumerate(codes):screen[(row*80+col)*2]=code
 for q in (ref,opt):
  q.u.mem_write(0x10000+symbols['DISPLAY_COLUMN_ADJUST'],bytes([adjust]));put(q,screen);update(q)
 for turn,(col,code) in enumerate(((1,65),(1,0xd8),(1,0xd4),(2,0xec),(79,32),(0,0xa2))):
  screen[(12*80+col)*2]=code
  for q in (ref,opt):put(q,screen);update(q)
  equal(ref,opt,('Thai reflow',adjust,turn))
 # Changed combining-mark colour does not necessarily change visible output.
 screen[(12*80+1)*2+1]=3
 opt.writes.clear()
 for q in (ref,opt):put(q,screen);update(q)
 equal(ref,opt,('mark colour',adjust))
 assert not opt.writes,('combining mark colour',adjust)
print('PASS: sparse Thai edits reflow the entire row correctly for all tested vowel-compensation modes, including first/last cells')

ref=setup(True);opt=setup();screen=bytearray(bytes([65,7])*2000)
for q in (ref,opt):put(q,screen);update(q)
for row in (0,24):
 screen[(row*80+79)*2+1]=0x17
 for q in (ref,opt):put(q,screen);update(q)
 equal(ref,opt,('edge colour',row))
# More than eight source changes bypasses the two-pass planner.
for col in range(9):screen[(12*80+col)*2]=67
for q in (ref,opt):put(q,screen);update(q)
equal(ref,opt,'dense change')
for q in (ref,opt):
 q.u.mem_write(0x10000+symbols['DISPLAY_COLUMN_ADJUST'],b'\x07')
 q.call('INVALIDATE_ROW_IMAGES')
screen[(12*80+40)*2]=68
for q in (ref,opt):put(q,screen);update(q)
equal(ref,opt,'invalidated image and configuration')
print('PASS: attributes, screen edges, dense-change fallback, configuration and explicit invalidation remain correct')

# Model a popup/graphics write interrupting a sparse update; next tick must repair
# every row even if VID_SAVE was partly committed after the interruption.
fired=[False]
def invalidate_mid_row(u,address,size,_):
 if fired[0]:return
 fired[0]=True
 epoch=int.from_bytes(u.mem_read(0x10000+symbols['DISPLAY_EPOCH'],2),'little')+1
 u.mem_write(0x10000+symbols['DISPLAY_EPOCH'],epoch.to_bytes(2,'little'))
 u.mem_write(0x10000+symbols['ROW_IMAGE_VALID'],bytes(25))
 u.mem_write(0x10000+symbols['ROW_FORCE_REDRAW'],b'\x01')
 for plane in opt.planes:plane[0xe000:0xe010]=bytes([0x55])*16
opt.u.hook_add(UC_HOOK_CODE,invalidate_mid_row,begin=0x10000+symbols['PARTIAL_GLYPH'],end=0x10000+symbols['PARTIAL_GLYPH'])
# First complete redraw establishes valid metadata again.
for q in (ref,opt):q.u.mem_write(0x10000+symbols['VID_SAVE'],bytes(4000));update(q)
opt.u.ctl_remove_cache(0x10000,0x1ffff)
screen[(12*80+41)*2]=69
for q in (ref,opt):put(q,screen);update(q)
assert fired[0]
update(opt)
equal(ref,opt,'popup epoch recovery')
print('PASS: epoch change during a partial row forces a complete repair on the next update')

# Exercise a normal enabled-interrupt caller, including forced snapshot recovery.
q=setup();put(q,bytearray(bytes([65,7])*2000));update(q)
q.call('INVALIDATE_ROW_IMAGES');q.u.mem_write(0x10000+symbols['ROW_FORCE_REDRAW'],b'\x01')
entry=0xed00;rel=(symbols['UPDATE_SCREEN_THAI_25']-(entry+4))&65535
q.u.mem_write(0x10000+entry,b'\xfb\xe8'+rel.to_bytes(2,'little')+b'\xc3');symbols['PARTIAL_IRQ_TEST']=entry
q.call('PARTIAL_IRQ_TEST',ds=0x1000)
assert q.u.reg_read(UC_X86_REG_EFLAGS)&0x200
assert q.u.mem_read(0x10000+symbols['ROW_FORCE_REDRAW'],1)==bytes(1)
print('PASS: forced repair preserves enabled interrupts and clears the pending redraw flag')

import random
rng=random.Random(335)
ref=setup(True);opt=setup();screen=bytearray(bytes([65,7])*2000)
for q in (ref,opt):put(q,screen);update(q)
for turn in range(60):
 col=rng.randrange(3,80)
 screen[(12*80+col)*2]=rng.choice([32,65,66,67,0xa1,0xa2,0xd4,0xd8,0xe8,0xec])
 if turn%5==0:screen[(12*80+col)*2+1]=rng.randrange(16)*16+7
 if turn in (15,30,45):
  for q in (ref,opt):q.u.mem_write(0x10000+symbols['DISPXLAT'],bytes([turn%2]))
 for q in (ref,opt):
  put(q,screen)
  for _ in range(3):update(q)
 equal(ref,opt,('random sparse edit',turn))
for code,col in ((0xb3,10),(0xb0,20),(0xc4,30)):
 for row in (3,4,5):screen[(row*80+col)*2]=code
 for q in (ref,opt):
  put(q,screen)
  for _ in range(3):update(q)
 equal(ref,opt,('frame/shade edit',code))
print('PASS: deterministic random sparse edits, translation changes and frame/shade context match full-row rendering')

# Alternate complex rows to exercise cache replacement and subsequent reuse.
ref=setup(True);opt=setup();screen=bytearray(bytes([0xa1,7,0xd4,7,0xe8,7,65,7])*500)
for q in (ref,opt):put(q,screen);update(q)
for row in (3,3,12,12,3,20,12,20):
 screen[(row*80+41)*2]^=0x0c
 for q in (ref,opt):put(q,screen);update(q)
 equal(ref,opt,('complex cache replacement',row))
print('PASS: alternating complex rows replace and reuse the descriptor cache safely')
