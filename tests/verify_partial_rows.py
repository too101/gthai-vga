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

# Eight changes remain eligible; nine leading changes reject before full parsing.
for changed in (8,9,80):
 ref=setup(True);opt=setup();seen=[0]
 def full_scan(u,address,size,_):seen[0]+=1
 opt.u.hook_add(UC_HOOK_CODE,full_scan,begin=0x10000+symbols['PPR_FULL_SCAN'],end=0x10000+symbols['PPR_FULL_SCAN'])
 screen=bytearray(bytes([65,7])*2000)
 for q in (ref,opt):put(q,screen);update(q)
 for col in range(changed):screen[(12*80+col)*2]=66
 for q in (ref,opt):put(q,screen);update(q)
 equal(ref,opt,('leading changed-cell threshold',changed))
 assert seen[0]==(1 if changed==8 else 0),(changed,seen)
print('PASS: 8 leading changes retain partial scan; 9/80 changes bypass it with exact pixels')

# Four associative slots survive alternating edits; a fifth distinct row evicts.
ref=setup(True);opt=setup();seen=[0]
def capture(u,address,size,_):seen[0]+=1
opt.u.hook_add(UC_HOOK_CODE,capture,begin=0x10000+symbols['CAPTURE_OLD_GLYPH'],end=0x10000+symbols['CAPTURE_OLD_GLYPH'])
screen=bytearray(bytes([0xa1,7,0xd4,7,0xe8,7,65,7])*500)
for q in (ref,opt):put(q,screen);update(q)
for turn,row in enumerate((3,12,21,22,3,12,21,22,7,3)):
 seen[0]=0;screen[(row*80+41)*2]^=0x0c
 for q in (ref,opt):put(q,screen);update(q)
 equal(ref,opt,('four-row descriptor cache',turn,row))
 assert (seen[0]==0)==(4<=turn<8),(turn,row,seen)
print('PASS: four complex rows retain descriptors across alternating edits; a fifth distinct row rebuilds safely')

# Composed glyphs are built only after their exact output descriptor differs.
ref=setup(True);opt=setup();calls=[0,0]
for i,label in enumerate(('COPY_GLYPH19','OR_GLYPH_ROWS')):
 def count_bitmap(u,address,size,_,i=i):
  calls[i]+=1
  if u.mem_read(0x10000+symbols['ROW_PLAN_MODE'],1)==b'\x02':
   assert not u.reg_read(UC_X86_REG_EFLAGS)&0x200

 opt.u.hook_add(UC_HOOK_CODE,count_bitmap,begin=0x10000+symbols[label],end=0x10000+symbols[label])
screen=bytearray(bytes([0xa1,7,0xd4,7,0xe8,7,65,7])*500)
for q in (ref,opt):put(q,screen);update(q)
calls[:]=[0,0]
screen[(12*80+41)*2+1]=4
for q in (ref,opt):put(q,screen);update(q)
equal(ref,opt,'unchanged composed bitmap')
assert calls==[0,0],calls
calls[:]=[0,0];screen[(12*80+41)*2]=0xd8
for q in (ref,opt):put(q,screen);update(q)
equal(ref,opt,'changed composed bitmap')
assert 0<calls[0]<=2 and 0<calls[1]<=6,calls
print('PASS: unchanged composed cells perform zero bitmap copies/ORs; changed cells compose on demand')

# Any four rows can coexist; touch promotes and fifth insertion evicts the LRU.
ref=setup(True);opt=setup();seen=[0]
def lru_capture(u,address,size,_):seen[0]+=1
opt.u.hook_add(UC_HOOK_CODE,lru_capture,begin=0x10000+symbols['CAPTURE_OLD_GLYPH'],end=0x10000+symbols['CAPTURE_OLD_GLYPH'])
screen=bytearray(bytes([0xa1,7,0xd4,7,0xe8,7,65,7])*500)
for q in (ref,opt):put(q,screen);update(q)
for turn,row in enumerate((3,7,11,15,3,7,11,15,3,19,3,7)):
 seen[0]=0;screen[(row*80+41)*2]^=0x0c
 for q in (ref,opt):put(q,screen);update(q)
 equal(ref,opt,('LRU composed-row cache',turn,row))
 hit=turn in (4,5,6,7,8,10)
 assert (seen[0]==0)==hit,(turn,row,seen)
 assert sorted(opt.u.mem_read(0x10000+symbols['ROW_CACHE_RANK'],4))==[0,1,2,3]
print('PASS: four formerly colliding rows coexist; touches promote MRU and replacement evicts the LRU')

# Every overlay glyph in the classification table matches eager full composition.
ref=setup(True);opt=setup();screen=bytearray(bytes([65,7])*2000)
for q in (ref,opt):put(q,screen);update(q)
types=bytes(opt.u.mem_read(0x10000+symbols['L152FH'],256))
cases=0
for kind in (7,8,9):
 for code in range(256):
  if types[code]!=kind:continue
  chars=([0xa1,code,0xd4,0xe8] if kind==7 else [0xa1,code,0xe8,65] if kind==8 else [0xa1,0xd4,code,65])
  for i,ch in enumerate(chars):screen[(12*80+i)*2]=ch
  for q in (ref,opt):put(q,screen);update(q)
  equal(ref,opt,('all deferred overlay glyphs',kind,code));cases+=1
print('PASS: all',cases,'classified overlay glyphs match eager composition')
