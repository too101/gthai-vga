"""Latch scroll runs in bounded pieces and keeps our own redraw/hotkeys out while partial."""
exec((__import__('pathlib').Path(__file__).parent/'verify_vga.py').read_text().split('\nm=Machine()')[0])
import random
CHUNK=760;PIECES=24*19*80//CHUNK
assert CHUNK*PIECES==24*19*80 and PIECES==48
origin=0xe000
for pic,busy in ((0xb8,0),(0xba,0),(0xb8,1)):
    m=Machine();m.pic_mask=pic
    m.word('VIDBUF',0xa000);m.word('L0506H',origin);m.word('L0508H',origin+19*80)
    m.u.mem_write(0x10000+symbols['TIMER_BUSY'],bytes([busy]))
    rng=random.Random(2027)
    for p in m.planes: p[:]=rng.randbytes(65536)
    before=[bytes(p) for p in m.planes]
    st={'run':0,'max':0,'windows':0,'prev':0}
    def code(u,address,size,_):
        iff=1 if u.reg_read(UC_X86_REG_EFLAGS)&0x200 else 0
        if iff:
            st['run']=0
            if not st['prev']:
                st['windows']+=1
                # No text/hotkey code may run now: timer redraw suppressed, IRQ1 masked, GC restored.
                assert u.mem_read(0x10000+symbols['TIMER_BUSY'],1)==b'\x01'
                assert m.pic_mask&2
                assert m.gc[5]==0 and m.gc[1]==0
        st['prev']=iff
    def write(u,access,addr,size,value,_):
        if not u.reg_read(UC_X86_REG_EFLAGS)&0x200:
            st['run']+=size;st['max']=max(st['max'],st['run'])
    m.u.hook_add(UC_HOOK_CODE,code,begin=0x10000,end=0x1ffff)
    m.u.hook_add(UC_HOOK_MEM_WRITE,write,begin=0xa0000,end=0xbffff)
    m.u.reg_write(UC_X86_REG_BP,0x1234)
    m.call('L6314H')
    assert len(m.writes)==24*19*80
    for p in range(4):
        for n in range(24*19*80):
            assert m.planes[p][(origin+n)&65535]==before[p][(origin+19*80+n)&65535]
    assert st['max']<=CHUNK,st
    assert st['windows']==PIECES-1,st
    assert m.pic_mask==pic,(hex(m.pic_mask),hex(pic))
    assert m.u.mem_read(0x10000+symbols['TIMER_BUSY'],1)==bytes([busy])
    assert not m.u.reg_read(UC_X86_REG_EFLAGS)&0x200
    assert m.u.reg_read(UC_X86_REG_BP)==0x1234 and m.gc[5]==0
print('PASS: latch scroll uses 48 pieces of 760 bytes, opens 47 IRQ windows with timer redraw suppressed and IRQ1 masked, restores mask/flags/BP')

# End to end: SCRL_UP1 scrolls B800, VID_SAVE and pixels, then restores timer/PIC/interrupt state.
m=Machine();m.pic_mask=0xb8
m.word('VIDBUF',0xa000);m.word('VID_SEG',0xb800);m.word('L0506H',origin);m.word('L0508H',origin+19*80)
m.word('VID_OFFSET',0x7470);m.word('L0538H',0x7470)          # hidden cursor: no XOR work
rng=random.Random(99)
text=rng.randbytes(4000);save=rng.randbytes(4000)
for pl in m.planes:
    pl[:]=rng.randbytes(65536);pl[0x8000:0x8000+4000]=text
m.u.mem_write(0x10000+symbols['VID_SAVE'],save)
before=[bytes(pl) for pl in m.planes]
m.call('SCRL_UP1',bx=0x1e00)
for pl in m.planes:
    assert bytes(pl[0x8000:0x8000+3840])==text[160:]
    assert bytes(pl[0x8000+3840:0x8000+4000])==bytes([32,0x1e])*80
assert bytes(m.u.mem_read(0x10000+symbols['VID_SAVE'],3840))==save[160:]
for p in range(4):
    for n in range(24*19*80):
        assert m.planes[p][(origin+n)&65535]==before[p][(origin+19*80+n)&65535]
assert m.pic_mask==0xb8 and m.u.mem_read(0x10000+symbols['TIMER_BUSY'],1)==b'\x00'
assert not m.u.reg_read(UC_X86_REG_EFLAGS)&0x200 and m.gc[5]==0
print('PASS: SCRL_UP1 scrolls B800, VID_SAVE and all four planes; timer flag, PIC mask and IF are restored')
