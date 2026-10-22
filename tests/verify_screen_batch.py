"""Boundary equivalence for CMPSD and latch-safe batched drawing."""
import os
os.environ.setdefault('GTHAI_TARGET','GTHAI386')
exec((__import__('pathlib').Path(__file__).parent/'verify_vga.py').read_text().split('\nm=Machine()')[0])
if build_artifact=='GTHAI386':
    m=Machine()
    a=0x6000; b=0x7000
    m.u.mem_write(0x16000,bytes([65,7])*2000)
    m.u.mem_write(0x17000,bytes([65,7])*2000)
    for byte in range(4000):
        m.u.mem_write(0x17000+byte,b'\xff')
        m.call('COMPARE_TEXT386',ds=0x1000,es=0x1000,si=a,di=b,cx=2000,eax=0x89abcdef)
        cell=byte//2
        assert m.u.reg_read(UC_X86_REG_SI)==a+2*(cell+1),byte
        assert m.u.reg_read(UC_X86_REG_DI)==b+2*(cell+1),byte
        assert m.u.reg_read(UC_X86_REG_CX)==1999-cell,byte
        assert not m.u.reg_read(UC_X86_REG_EFLAGS)&64,byte
        assert m.u.reg_read(UC_X86_REG_EAX)==0x89abcdef
        m.u.mem_write(0x17000+byte,bytes([65 if byte%2==0 else 7]))
    m.call('COMPARE_TEXT386',ds=0x1000,es=0x1000,si=a,di=b,cx=2000)
    assert m.u.reg_read(UC_X86_REG_CX)==0 and m.u.reg_read(UC_X86_REG_EFLAGS)&64
    print('PASS: CMPSD finds every one of 4000 differing bytes with exact CMPSW positions/counts and preserves EAX')
reference=Machine(); batch=Machine()
count=[0,0]
for index,machine in enumerate((reference,batch)):
    def out_count(u,port,size,value,_,i=index):
        if port==0x3ce: count[i]+=1
    machine.u.hook_add(UC_HOOK_INSN,out_count,None,1,0,UC_X86_INS_OUT)
    machine.u.mem_write(0x10000+symbols['VGA_BATCH_ACTIVE'],bytes([index]))
    for cell in range(256):
        # Read VGA text between glyphs: its latch contents must never be reused.
        if build_artifact=='GTHAI386':
            machine.call('COMPARE_TEXT386',ds=0xb800,es=0x1000,si=0,di=symbols['VID_SAVE'],cx=2)
        else:
            machine.u.mem_write(0x1ef00,bytes.fromhex('B8 00 B8 8E D8 A0 00 00 C3'))
            symbols['BENCH_READ_TEXT']=0xef00
            machine.call('BENCH_READ_TEXT')
        machine.call('L62B3H',ds=0x1000,es=0xa000,ax=(cell<<8)|65,si=symbols['FONT_2'],di=0xe000+cell%80)
    machine.call('VGA_BATCH_FLUSH')
assert reference.planes==batch.planes
assert batch.gc[5]==0 and batch.gc[1]==0
assert count==[256*7,5+255*4+2],count
print('PASS: all 256 attributes batch identically despite intervening B800 reads; OUT count',count)

# Whole-screen mixed Thai/ASCII/space runs, colour changes, cursor and dirty rows.
def screen_machine(disable_batch):
    q=Machine(); q.word('VIDBUF',0xa000); q.word('VID_SEG',0xb800); q.word('CRTBASE',0x3d4)
    origin=0xe000
    for row in range(26):
        q.u.mem_write(0x10000+symbols['L0506H']+row*2,((origin+row*19*80)&65535).to_bytes(2,'little'))
    q.word('VID_OFFSET',origin)
    q.crt[14],q.crt[15]=0,0
    q.u.mem_write(0x10000+symbols['CURRENT_MODE'],b'\x00')
    if disable_batch:
        def disable(u,address,size,_): u.mem_write(0x10000+symbols['VGA_BATCH_ACTIVE'],b'\x00')
        q.u.hook_add(UC_HOOK_CODE,disable,begin=0x10000+symbols['L4CA3H'],end=0x10000+symbols['L4CA3H'])
    return q
ref=screen_machine(True); opt=screen_machine(False)
for iteration in range(3):
    for q in (ref,opt):
        for row in range(25):
            if iteration==1 and row not in (0,12,24): continue
            cells=bytearray()
            codes=[0xa1,0xd4,0xe8,65,32,66,67,32]
            for col in range(80): cells+=bytes([codes[(col+iteration)%8],((row+col//8+iteration)%8)*16+7])
            for plane in q.planes: plane[0x8000+row*160:0x8000+(row+1)*160]=cells
        q.call('UPDATE_SCREEN_THAI_25',ds=0x1000)
        assert q.gc[5]==0 and q.gc[1]==0
        assert q.u.mem_read(0x10000+symbols['VGA_BATCH_ACTIVE'],2)==bytes(2)
    assert ref.planes==opt.planes,iteration
    assert ref.u.mem_read(0x10000+symbols['VID_SAVE'],4000)==opt.u.mem_read(0x10000+symbols['VID_SAVE'],4000)
print('PASS: mixed Thai, ASCII, spaces, colours, visible cursor and dirty rows match unbatched rendering')

# Reproduce a hotkey popup arriving between two glyphs of a timer batch.
q=Machine(); q.word('VIDBUF',0xa000);q.word('VID_SEG',0xb800)
q.u.mem_write(0x10000+symbols['DISPMODE'],b'\x02')
q.u.mem_write(0x10000+symbols['VGA_BATCH_ACTIVE'],b'\x01\x01')
q.gc[5]=3;q.gc[1]=15
q.call('SAVE_SCREEN')
assert q.u.mem_read(0x10000+symbols['VGA_BATCH_ACTIVE'],2)==bytes(2)
# A button outline leaves a narrow mask, as in the reported unload dialog.
q.gc[8]=1
q.call('L62B3H',ds=0x1000,es=0xa000,ax=0xf041,si=symbols['FONT_2'],di=0xe000)
font=q.u.mem_read(0x10000+symbols['FONT_2']+65*19,19)
for y in range(19):
    for plane in q.planes: assert plane[0xe000+y*80]==(~font[y]&255)
assert q.gc[8]==255 and q.gc[5]==0 and q.gc[1]==0
print('PASS: popup cancels interrupted timer batch; button glyph resets narrow frame bit mask')
# Enter with interrupts enabled, verify VGA OUTs run atomically and IF is restored.
for routine in ('L62B3H','L6289H','DRAW_CURSOR_VGA'):
    q=Machine();q.word('VIDBUF',0xa000);q.word('L0538H',0x7470)
    entry=0xee00
    relative=(symbols[routine]-(entry+4))&65535
    q.u.mem_write(0x10000+entry,b'\xfb\xe8'+relative.to_bytes(2,'little')+b'\xc3')
    symbols['IRQ_TEST']=entry
    def atomic(u,port,size,value,_):
        if port==0x3ce: assert not u.reg_read(UC_X86_REG_EFLAGS)&0x200,routine
    q.u.hook_add(UC_HOOK_INSN,atomic,None,1,0,UC_X86_INS_OUT)
    q.call('IRQ_TEST',ax=0x0741,si=symbols['FONT_2'],di=0xe000)
    assert q.u.reg_read(UC_X86_REG_EFLAGS)&0x200,routine
print('PASS: glyph, blank and cursor VGA updates mask interrupts briefly and restore IF')
