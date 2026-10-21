"""Execute the COM's actual 16-bit routines against a VGA planar memory model."""
import sys, re, random
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *

root = Path(__file__).resolve().parent.parent
listing = (root/'work/GTHAI.lst').read_text(errors='replace')
symbols = {}
for line in listing.splitlines():
    proc = re.match(r'^([0-9A-F]{8})\s+(\w+)\s+PROC\b', line)
    if proc:
        symbols[proc[2]] = int(proc[1],16)
    m = re.match(r'^(\w+)\s+(?:\.\s+)+.*?\s([0-9A-Fa-f]+)h\s+Code_Seg\s*$', line)
    if m:
        symbols[m[1]] = int(m[2], 16)

class Machine:
    def __init__(self):
        self.u = u = Uc(UC_ARCH_X86, UC_MODE_16)
        u.mem_map(0, 0x100000)
        u.mem_write(0x10100, (root/'work/GTHAI.COM').read_bytes())
        self.planes = [bytearray(65536) for _ in range(4)]
        self.gc = [0]*9
        self.gc[8] = 255
        self.index = 0
        self.crt_index = 0
        self.crt = [0]*32
        self.latch = [0]*4
        self.writes = []
        u.hook_add(UC_HOOK_INSN, self.out, None, 1, 0, UC_X86_INS_OUT)
        u.hook_add(UC_HOOK_INSN, self.inp, None, 1, 0, UC_X86_INS_IN)
        u.hook_add(UC_HOOK_MEM_READ, self.read, begin=0xa0000, end=0xbffff)
        u.hook_add(UC_HOOK_MEM_WRITE, self.write, begin=0xa0000, end=0xbffff)
        for reg, val in [(UC_X86_REG_CS,0x1000), (UC_X86_REG_DS,0x1000),
                         (UC_X86_REG_ES,0xa000), (UC_X86_REG_SS,0x7000)]:
            u.reg_write(reg,val)
    def out(self,u,port,size,value,_):
        if size == 2:
            self.out(u,port,1,value&255,None)
            self.out(u,port+1,1,value>>8,None)
        elif port == 0x3ce: self.index=value
        elif port == 0x3cf: self.gc[self.index]=value
        elif port == 0x3d4: self.crt_index=value
        elif port == 0x3d5: self.crt[self.crt_index]=value
        else: raise AssertionError(f'unexpected OUT {port:04x}')
    def inp(self,u,port,size,_):
        assert port == 0x3d5
        return self.crt[self.crt_index]
    def read(self,u,access,addr,size,value,_):
        assert size in (1,2)
        values=[]
        for n in range(size):
            offset=(addr+n-0xa0000)&65535
            self.latch=[p[offset] for p in self.planes]
            values.append(self.latch[self.gc[4]&3])
        u.mem_write(addr,bytes(values))
    def write(self,u,access,addr,size,value,_):
        for n in range(size):
            offset=(addr+n-0xa0000)&65535
            byte=(value>>(8*n))&255
            self.writes.append(offset)
            for p in range(4):
                if self.gc[5]&3 == 1:
                    result=self.latch[p]
                elif self.gc[5]&3 == 3:
                    rotate=self.gc[3]&7
                    mask=(((byte>>rotate)|(byte<<(8-rotate)))&255)&self.gc[8]
                    data=255 if self.gc[0]&(1<<p) else 0
                    result=(data&mask)|(self.latch[p]&(~mask&255))
                else:
                    rotate=self.gc[3]&7
                    data=((byte>>rotate)|(byte<<(8-rotate)))&255
                    if self.gc[1]&(1<<p): data=255 if self.gc[0]&(1<<p) else 0
                    fn=(self.gc[3]>>3)&3
                    if fn==1: data &= self.latch[p]
                    elif fn==2: data |= self.latch[p]
                    elif fn==3: data ^= self.latch[p]
                    mask=self.gc[8]
                    result=(data&mask)|(self.latch[p]&(~mask&255))
                self.planes[p][offset]=result
    def call(self,name,**regs):
        u=self.u
        for name_,val in regs.items(): u.reg_write(globals()['UC_X86_REG_'+name_.upper()],val)
        u.reg_write(UC_X86_REG_SP,0xfffc)
        u.mem_write(0x7fffc,b'\x00\xf0')
        u.reg_write(UC_X86_REG_EFLAGS,2)
        u.emu_start(0x10000+symbols[name],0x1f000,count=1000000)
        assert u.reg_read(UC_X86_REG_IP)==0xf000, name
    def word(self,name,value): self.u.mem_write(0x10000+symbols[name],value.to_bytes(2,'little'))

m=Machine()
bank1=(root/'fonts/GTHAI1-19.FON').read_bytes()
assert len(bank1)==256*19
for code in range(256):
    assert m.u.mem_read(0x10000+symbols['FONT_1']+code*19,19)==bank1[code*19:(code+1)*19]
print('PASS: all 256 Font 1 glyphs match supplied 8x19 file byte-for-byte')
supplied=(root/'fonts/GTHAI2-19.FON').read_bytes()
assert len(supplied)==256*19
for code in range(256):
    assert m.u.mem_read(0x10000+symbols['FONT_2']+code*19,19)==supplied[code*19:(code+1)*19]
print('PASS: all 256 Font 2 glyphs match supplied 8x19 file byte-for-byte')
origin=int(re.search(r'VGA_ORIGIN = ([0-9A-F]+)H', (root/'GTHAI.INC').read_text())[1],16)
visible={(origin+y*80+x)&65535 for y in range(480) for x in range(80)}
text=set(range(0x8000,0xe000))
assert not visible & text
for y in range(480):
    m.call('VGA_CURSOR_CALC',dx=y,cx=632)
    assert m.u.reg_read(UC_X86_REG_DI)==(origin+y*80+79)&65535
print('PASS: 480 scanline coordinates and B800 isolation')

for bank in ('FONT_1','FONT_2'):
    for code in range(256):
        font=m.u.mem_read(0x10000+symbols[bank]+code*19,19)
        # Diverse attributes, including bright foreground and background.
        for attr in (0x07,0x1e,0xf0,0xa5):
            di=(origin+(code%25)*19*80+code%80)&65535
            m.call('L62B3H',ax=(attr<<8)|code,si=symbols[bank],di=di,es=0xa000)
            assert m.u.reg_read(UC_X86_REG_DI)==di
            for row in range(19):
                bits=font[row]
                off=(di+row*80)&65535
                for p in range(4):
                    fg=255 if (attr&15)&(1<<p) else 0
                    bg=255 if (attr>>4)&(1<<p) else 0
                    assert m.planes[p][off]==((bits&fg)|((~bits&255)&bg)),(bank,code,attr,row,p)
            assert m.gc[1]==0 and m.gc[8]==255 and m.gc[5]==0
print('PASS: 2,048 glyph/colour combinations, 19 scanlines, both banks')

for attr in (0x07,0x1e,0xf0,0xa5):
    di=(origin+24*19*80+79)&65535
    m.call('L6289H',ax=(attr<<8)|32,di=di)
    assert m.u.reg_read(UC_X86_REG_DI)==di
    for row in range(19):
        for p in range(4):
            assert m.planes[p][(di+row*80)&65535] == (255 if (attr>>4)&(1<<p) else 0)
print('PASS: blank cell background fills all 19 scanlines')

m.word('VIDBUF',0xa000)
m.word('L0506H',origin)
m.word('L0508H',origin+19*80)
rng=random.Random(2026)
for p in m.planes: p[:]=rng.randbytes(65536)
before=[bytes(p) for p in m.planes]
m.writes.clear()
m.call('L6314H')
assert len(m.writes)==24*19*80
for p in range(4):
    for n in range(24*19*80):
        assert m.planes[p][(origin+n)&65535]==before[p][(origin+19*80+n)&65535]
    for off in text: assert m.planes[p][off]==before[p][off]
assert m.gc[5]==0
print('PASS: 24-row planar latch scroll wraps at 64K and preserves B800')

m.word('L0538H',(origin+25*19*80)&65535)
for mode in (0,4):
    m.u.mem_write(0x10000+symbols['CURRENT_MODE'],bytes([mode]))
    di=(origin+24*19*80+79)&65535
    before=[bytes(p) for p in m.planes]
    m.writes.clear()
    m.call('DRAW_CURSOR_VGA',di=di)
    expected_rows=range(19) if mode==4 else (17,18)
    assert set(m.writes)=={(di+row*80)&65535 for row in expected_rows}
    m.call('DRAW_CURSOR_VGA',di=di)
    assert all(bytes(p)==b for p,b in zip(m.planes,before))
m.writes.clear()
m.call('DRAW_CURSOR_VGA',di=(origin+25*19*80)&65535)
assert not m.writes
print('PASS: Thai cursor fills 19 rows, English cursor 2 rows; XOR reversible; hidden cursor safe')

# Run the complete dirty-screen renderer through its actual B800 reads.
m=Machine()
m.word('VIDBUF',0xa000)
m.word('VID_SEG',0xb800)
m.word('CRTBASE',0x3d4)
for row in range(26):
    m.u.mem_write(0x10000+symbols['L0506H']+row*2,((origin+row*19*80)&65535).to_bytes(2,'little'))
m.word('VID_OFFSET',(origin+25*19*80)&65535)
m.crt[14],m.crt[15]=2000>>8,2000&255
for plane in m.planes:
    plane[0x8000:0x8000+4000]=bytes([65,7])*2000
    # VALET backs up the 4000-byte screen at B800:2000 (VGA A000h).
    plane[0xa000:0xa000+4000]=bytes([0x5a,0x17])*2000
m.u.mem_write(0x10000+symbols['VID_SAVE'],bytes(4000))
m.u.mem_write(0x10000+symbols['CURRENT_MODE'],b'\x00')
m.call('UPDATE_SCREEN_THAI_25')
font=m.u.mem_read(0x10000+symbols['FONT_2']+65*19,19)
for row in range(475):
    for col in range(80):
        off=(origin+row*80+col)&65535
        for p in range(4):
            assert m.planes[p][off]==(font[row%19] if p<3 else 0),(row,col,p)
assert m.u.mem_read(0x10000+symbols['VID_SAVE'],4000)==bytes([65,7])*2000
assert all(p[0xa000:0xa000+4000]==bytes([0x5a,0x17])*2000 for p in m.planes)
print('PASS: complete redraw preserves VALET backup at B800:2000')
m.writes.clear()
m.call('UPDATE_SCREEN_THAI_25')
assert not m.writes
print('PASS: complete 80x25 dirty redraw and zero VRAM writes on unchanged screen')

row_bytes=bytes([0xa1,7,0xd4,7,0xe8,7,65,7])+bytes([32,7])*76
for plane in m.planes: plane[0x8000:0x8000+160]=row_bytes
m.word('USER_WIDTH',0xa55a) # Guard immediately after the composition buffer.
m.call('UPDATE_SCREEN_THAI_25')
assert m.u.mem_read(0x10000+symbols['USER_WIDTH'],2)==b'\x5a\xa5'
bank=0x10000+symbols['FONT_2']
base=m.u.mem_read(bank+0xa1*19,19)
upper=m.u.mem_read(bank+0xd4*19,19)
tone=(m.u.mem_read(bank+0xe8*19,19)+bytes(3))[3:22]
combined=bytes(base[n]|upper[n]|tone[n] for n in range(19))
for y in range(19):
    for p in range(4):
        expected=combined[y] if p<3 else 0
        assert m.planes[p][origin+y*80]==expected,('Thai composition',y,p)
        assert m.planes[p][origin+y*80+1]==(font[y] if p<3 else 0)
print('PASS: Thai base + upper vowel + tone composition, followed by ASCII')

# Dialog strings have their own composition path; check that separately.
m=Machine()
m.word('VID_OFFSET',origin)
m.word('USER_WIDTH',0xa55a)
m.u.mem_write(0x10000+symbols['TEXT_COLOR'],b'\x07')
m.u.mem_write(0x1d000,bytes(x^5 for x in (0xa1,0xd4,0xe8,65,0)))
m.call('DO_MSG',si=0xd000)
for y in range(19):
    for p in range(4):
        assert m.planes[p][(origin+y*80)&65535]==(combined[y] if p<3 else 0)
assert m.u.mem_read(0x10000+symbols['USER_WIDTH'],2)==b'\x5a\xa5'
print('PASS: native 19-row dialog composition preserves the adjacent buffer guard')

# Every tone-like mark must stay low without an upper vowel and move up with one.
for mark in range(0xe8,0xed):
    for has_upper in (False,True):
        codes=[0xa1]+([0xd4] if has_upper else [])+[mark]
        gbase=supplied[0xa1*19:(0xa1+1)*19]
        gupper=supplied[0xd4*19:(0xd4+1)*19] if has_upper else bytes(19)
        gtone=supplied[mark*19:(mark+1)*19]
        if has_upper: gtone=(gtone+bytes(3))[3:22]
        want=bytes(a|b|c for a,b,c in zip(gbase,gupper,gtone))
        for path in ('screen','dialog'):
            t=Machine()
            t.word('VIDBUF',0xa000)
            t.word('VID_OFFSET',origin)
            t.word('USER_WIDTH',0xa55a)
            if path=='dialog':
                t.u.mem_write(0x10000+symbols['TEXT_COLOR'],b'\x07')
                t.u.mem_write(0x1d000,bytes(x^5 for x in codes+[0]))
                t.call('DO_MSG',si=0xd000)
            else:
                t.word('VID_SEG',0xb800)
                t.word('CRTBASE',0x3d4)
                for row in range(26):
                    t.u.mem_write(0x10000+symbols['L0506H']+row*2,((origin+row*19*80)&65535).to_bytes(2,'little'))
                t.word('VID_OFFSET',(origin+25*19*80)&65535)
                t.crt[14],t.crt[15]=2000>>8,2000&255
                content=b''.join(bytes([c,7]) for c in codes)+bytes([32,7])*(2000-len(codes))
                for plane in t.planes: plane[0x8000:0x8000+4000]=content
                t.call('UPDATE_SCREEN_THAI_25')
            for y in range(19):
                for p in range(4):
                    assert t.planes[p][(origin+y*80)&65535]==(want[y] if p<3 else 0),(mark,has_upper,path,y,p)
            assert t.u.mem_read(0x10000+symbols['USER_WIDTH'],2)==b'\x5a\xa5'
print('PASS: E8-EC low without an upper vowel and raised three rows with one, screen/dialog paths')

# Simulated original BIOS entry: validate our mode call, CRTC and BDA setup.
m=Machine()
m.u.mem_write(0x1e000,b'\xcf') # original BIOS stub = IRET
m.u.mem_write(0x10000+symbols['OLDINT10'],b'\x00\xe0\x00\x10')
bios_calls=[]
def bios(u,address,size,_):
    bios_calls.append(u.reg_read(UC_X86_REG_AX))
m.u.hook_add(UC_HOOK_CODE,bios,begin=0x1e000,end=0x1e000)
m.call('VGA_SET_VIDEO_MODE',ax=3)
assert bios_calls==[0x12]
assert (m.crt[12]<<8|m.crt[13])==origin
assert m.gc[6]==1
assert m.u.mem_read(0x449,1)==b'\x03'
assert m.u.mem_read(0x44a,6)==b'\x50\x00\x00\x10\x00\x00'
assert m.u.mem_read(0x484,3)==b'\x18\x13\x00'
print('PASS: BIOS mode 12h request, scanout origin, 80x25 BIOS geometry')

# Execute the INT 10h handler with a real interrupt return frame. The old
# BIOS stub resets both CRTC start registers, as DOSBox-X AH=05h actually does.
m=Machine()
m.u.mem_write(0x1e000,bytes.fromhex('BA D4 03 B8 0C 00 EF B8 0D 00 EF CF'))
m.u.mem_write(0x10000+symbols['OLDINT10'],b'\x00\xe0\x00\x10')
m.u.mem_write(0x10000+symbols['VMODEFLAG'],b'\x03')
m.u.reg_write(UC_X86_REG_AX,0x0500)
m.u.reg_write(UC_X86_REG_BX,0x1234)
m.u.reg_write(UC_X86_REG_DX,0x5678)
m.u.reg_write(UC_X86_REG_SP,0xfff8)
m.u.mem_write(0x7fff8,b'\x00\xf0\x00\x10\x02\x02')
m.u.emu_start(0x10000+symbols['VIDINT10'],0x1f000,count=10000)
assert m.u.reg_read(UC_X86_REG_IP)==0xf000
assert (m.crt[12]<<8|m.crt[13])==origin
assert m.u.reg_read(UC_X86_REG_AX)==0x0500
assert m.u.reg_read(UC_X86_REG_BX)==0x1234
assert m.u.reg_read(UC_X86_REG_DX)==0x5678
print('PASS: INT 10h/AH=05h page 0 retains VGA origin and caller registers')

# EDIT uses AX=1130h/BH=06h and consumes DL as the last text row.
# Decimal 30 (1Eh) would swallow this query and leave DL at its input 4Eh.
m=Machine()
m.u.mem_write(0x1e000,b'\xcf')
m.u.mem_write(0x10000+symbols['OLDINT10'],b'\x00\xe0\x00\x10')
m.u.mem_write(0x10000+symbols['VMODEFLAG'],b'\x03')
queries=[]
def font_info(u,address,size,_):
    queries.append(u.reg_read(UC_X86_REG_AX))
    u.reg_write(UC_X86_REG_CX,19)
    u.reg_write(UC_X86_REG_DX,24)
    u.reg_write(UC_X86_REG_ES,0xf000)
    u.reg_write(UC_X86_REG_BP,0x1234)
m.u.hook_add(UC_HOOK_CODE,font_info,begin=0x1e000,end=0x1e000)
for reg,value in ((UC_X86_REG_AX,0x1130),(UC_X86_REG_BX,0x0600),
                  (UC_X86_REG_CX,0x0f09),(UC_X86_REG_DX,0x1f4e),
                  (UC_X86_REG_SP,0xfff8)):
    m.u.reg_write(reg,value)
m.u.mem_write(0x7fff8,b'\x00\xf0\x00\x10\x02\x02')
m.u.emu_start(0x10000+symbols['VIDINT10'],0x1f000,count=10000)
assert queries==[0x1130]
assert m.u.reg_read(UC_X86_REG_CX)==19 and m.u.reg_read(UC_X86_REG_DX)==24
assert m.u.reg_read(UC_X86_REG_ES)==0xf000 and m.u.reg_read(UC_X86_REG_BP)==0x1234
print('PASS: EDIT font-info query reaches BIOS and returns 19-row glyphs / 25 text rows')
print('All VGA routine checks passed. This models CPU/VGA operations, not a complete DOS BIOS.')




