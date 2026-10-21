from pathlib import Path
exec(compile((Path(__file__).parent/'verify_vga.py').read_text().split('\nm=Machine()')[0], 'verify_vga.py', 'exec'))
m=Machine()
assert symbols['FONT_2']-symbols['FONT_1']==256*19
assert symbols['MAXOPT0']-symbols['FONT_2']==256*19
for code in range(256):
    actual=int.from_bytes(m.u.mem_read(0x10000+symbols['FONT_OFFSETS']+code*2,2),'little')
    assert actual==code*19
print('PASS: 256 table offsets and raw 4864-byte Font 1 bank')
reads=[]
def read_trace(u,access,addr,size,value,data): reads.append((addr,size))
m.u.hook_add(UC_HOOK_MEM_READ,read_trace)
buf=symbols['GLYPH_COMPOSE']
for bank in ('FONT_1','FONT_2'):
    for code in range(256):
        source=symbols[bank]+code*19
        glyph=bytes(m.u.mem_read(0x10000+source,19))
        for routine,raise_by in [('COPY_GLYPH19',0),('OR_GLYPH_ROWS',0),('OR_GLYPH_ROWS',3)]:
            initial=bytes((y*37+code)&255 for y in range(19))
            m.u.mem_write(0x10000+buf,initial+b'\0\x5a\xa5')
            reads.clear()
            m.call(routine,bx=source+raise_by,bp=buf,cx=19-raise_by)
            # CS must address the source even though the screen path uses DS=B800.
            source_reads=[(addr,size) for addr,size in reads if 0x10000+symbols['FONT_1']<=addr<0x10000+symbols['FONT_2']+4864]
            assert sum(size for addr,size in source_reads)==19-raise_by,(bank,code,routine,source_reads)
            assert all(0x10000+source+raise_by<=addr and addr+size<=0x10000+source+19 for addr,size in source_reads)
            want=glyph if routine=='COPY_GLYPH19' else bytes(a|b for a,b in zip(initial,glyph[raise_by:]+bytes(raise_by)))
            assert bytes(m.u.mem_read(0x10000+buf,22))==want+b'\0\x5a\xa5'
print('PASS: 1536 bounded composition cases; no font read crosses a glyph; bottom rows and adjacent guard preserved')
