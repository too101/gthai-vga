from pathlib import Path
exec(compile((Path(__file__).parent/'verify_vga.py').read_text().split('\nm=Machine()')[0], 'verify_vga.py', 'exec'))
current_symbols=symbols.copy()
def parse_listing(filename):
    result={}
    for line in (root/'work'/filename).read_text(errors='replace').splitlines():
        proc=re.match(r'^([0-9A-F]{8})\s+(\w+)\s+PROC\b',line)
        if proc: result[proc[2]]=int(proc[1],16)
        m=re.match(r'^(\w+)\s+(?:\.\s+)+.*?\s([0-9A-Fa-f]+)h\s+Code_Seg\s*$',line)
        if m: result[m[1]]=int(m[2],16)
    return result
content=b''.join(bytes([65+i%26,1+i%7]) for i in range(2000))
def fixture():
    m=Machine()
    m.word('VID_SEG',0xb800); m.word('VIDBUF',0xa000); m.word('CRTBASE',0x3d4)
    m.u.mem_write(0x10000+symbols['DISPMODE'],b'\0')
    m.u.mem_write(0x400,bytes([0x5a,0xc3])*2000)
    m.u.mem_write(0x450,b'\x0c\x07')
    m.u.mem_write(0x1e000,b'\xcf')
    m.u.mem_write(0x10000+symbols['OLDINT10'],b'\x00\xe0\x00\x10')
    for plane in m.planes: plane[0x8000:0x8000+4000]=content
    return m
# Prove that the old binary saved BIOS bytes instead of the user's screen.
baseline=root/'work/GTHAI.pre-switchfix.COM'
if baseline.exists():
    symbols=parse_listing('GTHAI.pre-switchfix.lst')
    m=fixture(); m.u.mem_write(0x10100,baseline.read_bytes())
    # Reapply state because loading the original image restores defaults.
    m.word('VID_SEG',0xb800); m.word('VIDBUF',0xa000)
    m.u.mem_write(0x10000+symbols['DISPMODE'],b'\0')
    m.u.mem_write(0x10000+symbols['OLDINT10'],b'\x00\xe0\x00\x10')
    m.call('SAVE_SCREEN')
    assert bytes(m.u.mem_read(0x10000+symbols['VID_SAVE'],4000))!=content
    print('REPRODUCED: 3.25 saves BIOS data instead of B800 text')
symbols=current_symbols
for target in (0,1,2):
    m=fixture()
    m.call('SAVE_SCREEN',ds=0x2222)
    assert bytes(m.u.mem_read(0x10000+symbols['VID_SAVE'],4000))==content
    assert int.from_bytes(m.u.mem_read(0x10000+symbols['CURSOR_SAVE'],2),'little')==0x070c
    # Emulate drawing a dialog over the text-storage area to require restoration.
    for plane in m.planes: plane[0x8000:0x8000+4000]=bytes(4000)
    m.u.mem_write(0x10000+symbols['DISPMODE'],bytes([target]))
    m.call('RESTORE_SCREEN')
    assert all(plane[0x8000:0x8000+4000]==content for plane in m.planes)
    if target:
        origin=0xe000
        for row in range(26):
            m.u.mem_write(0x10000+symbols['L0506H']+row*2,((origin+row*19*80)&65535).to_bytes(2,'little'))
        m.word('L0538H',(origin+25*19*80)&65535)
        m.word('VID_OFFSET',(origin+25*19*80)&65535)
        m.crt[14],m.crt[15]=2000>>8,2000&255
        m.call('UPDATE_SCREEN_THAI_8' if target==1 else 'UPDATE_SCREEN_THAI_25')
        for cell in range(2000):
            code,attr=content[cell*2:cell*2+2]
            glyph=m.u.mem_read(0x10000+symbols['FONT_2']+code*19,19)
            for y,bits in enumerate(glyph):
                off=(origin+(cell//80*19+y)*80+cell%80)&65535
                for plane in range(4):
                    assert m.planes[plane][off]==(bits if attr&(1<<plane) else 0),(target,cell,y,plane)
    print(f'PASS: English panel -> mode {target}, all 2000 text cells preserved'+(' and all glyph pixels verified' if target else ''))

for source_mode in (1,2):
    m=fixture()
    m.u.mem_write(0x10000+symbols['DISPMODE'],bytes([source_mode]))
    m.u.mem_write(0x10000+symbols['VID_SAVE'],content)
    m.call('SAVE_SCREEN')
    assert bytes(m.u.mem_read(0x10000+symbols['VID_SAVE'],4000))==content
    m.u.mem_write(0x10000+symbols['DISPMODE'],b'\0')
    m.call('RESTORE_SCREEN')
    assert all(plane[0x8000:0x8000+4000]==content for plane in m.planes)
    print(f'PASS: Thai mode {source_mode} -> English preserves all 2000 text cells')
