from pathlib import Path
exec(compile((Path(__file__).parent/'verify_vga.py').read_text().split('\nm=Machine()')[0], 'verify_vga.py', 'exec'))
m=Machine()
rng=random.Random(323)
for plane in m.planes: plane[:]=rng.randbytes(65536)
for attr in range(256):
    for code in (0,32,65,0xa1,0xd4,0xe8,0xec,255):
        for bank in ('FONT_1','FONT_2'):
            di=(0xfff0 if attr&1 else 0xe04f)
            m.gc[8]=(attr+code)&255 # Simulate a preceding dialog edge/fill
            glyph=m.u.mem_read(0x10000+symbols[bank]+code*19,19)
            m.call('L62B3H',ax=(attr<<8)|code,si=symbols[bank],di=di)
            assert m.u.reg_read(UC_X86_REG_DI)==di
            assert m.u.reg_read(UC_X86_REG_SI)==symbols[bank]+code*19+18
            for y,bits in enumerate(glyph):
                for p in range(4):
                    fg=255 if attr&(1<<p) else 0
                    bg=255 if attr&(16<<p) else 0
                    assert m.planes[p][(di+y*80)&65535]==((bits&fg)|((~bits&255)&bg)),(attr,code,bank,y,p)
            assert m.gc[5]==0 and m.gc[1]==0 and m.gc[8]==255
print('PASS: mode 3, all 256 attributes, both banks, 4096 cases, random previous VRAM, 64K wrap, SI/DI and GC restored')

# Regression: a preceding dialog edge may leave any of the 256 bit masks.
for mask in range(256):
    m.gc[8]=mask
    m.call('L62B3H',ax=0x1e41,si=symbols['FONT_2'],di=0xe000)
    glyph=m.u.mem_read(0x10000+symbols['FONT_2']+65*19,19)
    for y,bits in enumerate(glyph):
        for p in range(4):
            fg=255 if 14&(1<<p) else 0
            bg=255 if 1&(1<<p) else 0
            assert m.planes[p][(0xe000+y*80)&65535]==((bits&fg)|((~bits&255)&bg)),(mask,y,p)
print('PASS: regression, all 256 incoming VGA bit masks render identically')
