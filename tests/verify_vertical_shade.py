from pathlib import Path
exec(compile((Path(__file__).parent/'verify_vga.py').read_text().split('\nm=Machine()')[0], 'verify_vga.py', 'exec'))
u=Uc(UC_ARCH_X86,UC_MODE_16); u.mem_map(0,0x100000)
u.mem_write(0x10100,(root/'work/GTHAI.COM').read_bytes())
accesses=[]
def memory(u,access,addr,size,value,data):
    accesses.append((addr,size))
u.hook_add(UC_HOOK_MEM_READ,memory,begin=0xb8000,end=0xc7fff)
u.hook_add(UC_HOOK_MEM_WRITE,memory,begin=0xb8000,end=0xc7fff)
count=0
def check(cells,expected,scan=True,seed=0,direct=None):
    global count
    screen=bytearray(bytes([32,7])*2000)
    for cell,code,attr in cells: screen[cell*2:cell*2+2]=bytes([code,attr])
    # Outside the text page deliberately resembles a continued shade run.
    u.mem_write(0xb8000,bytes(screen)+bytes([0xb0,7])*2048)
    u.mem_write(0xc7f60,bytes([0xb0,7])*80)
    for reg,val in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0xb800),(UC_X86_REG_ES,0x1000),
                    (UC_X86_REG_SS,0x7000),(UC_X86_REG_SP,0xfffc),(UC_X86_REG_CX,2000),
                    (UC_X86_REG_SI,0 if scan and not direct else seed*2),(UC_X86_REG_EFLAGS,2)]: u.reg_write(reg,val)
    u.mem_write(0x7fffc,b'\x00\xf0')
    if direct: u.reg_write(UC_X86_REG_AX,int.from_bytes(screen[seed*2:seed*2+2],'little')|0x8000)
    accesses.clear()
    u.emu_start(0x10000+symbols[direct or ('L4C0EH' if scan else 'L4B7FH')],0x1f000,count=2000000)
    assert u.reg_read(UC_X86_REG_IP)==0xf000
    result=bytes(u.mem_read(0xb8000,4000))
    if scan:
        marked={i for i in range(2000) if result[2*i+1]&128 and not screen[2*i+1]&128}
        assert marked==set(expected),(cells,marked,set(expected))
        assert result[::2]==screen[::2]
        assert all((a&127)==(b&127) for a,b in zip(result[1::2],screen[1::2]))
    else:
        assert (not bool(u.reg_read(UC_X86_REG_EFLAGS)&64))==bool(expected)
    assert all(0xb8000<=addr and addr+size<=0xb8000+4000 for addr,size in accesses),accesses[-10:]
    count+=1
for code in (0xb0,0xb1,0xb2):
    for row in (0,1,10,21,22,23,24):
        for col in (0,1,39,78,79):
            for n in (1,2,3,25-row):
                n=min(n,25-row)
                cells=[((row+y)*80+col,code,1+y%7) for y in range(n)]
                check(cells,[cell for cell,_,_ in cells] if n>=3 else [])
    # Direct detector at every screen cell must never look outside the page.
    for cell in range(2000): check([(cell,code,7)],[],scan=False,seed=cell)
    for row in (0,12,24):
        for col,n in ((0,3),(77,3),(78,2),(79,1)):
            cells=[(row*80+col+x,code,7) for x in range(n)]
            check(cells,[c for c,_,_ in cells] if n>=3 else [])
    # Three linear cells straddling a row must not form a horizontal run.
    check([(79,code,7),(80,code,7),(81,code,7)],[])
    # Do not cross into the next row after marking a valid right-edge run.
    check([(77,code,7),(78,code,7),(79,code,7),(80,code,7),(81,code,7)],[77,78,79])
# Adjacent shade types are not a three-cell vertical seed.
check([(80,0xb0,7),(160,0xb1,7),(240,0xb2,7)],[])
# A gap stops vertical propagation.
check([(0,0xb1,7),(80,0xb1,7),(160,0xb1,7),(320,0xb1,7)],[0,80,160])
# Mark upward from a seed in the middle without corrupting caller loop count.
check([(0,0xb2,7),(80,0xb2,7),(160,0xb2,7),(240,0xb2,7)],True,scan=False,seed=80)
# Existing Thai letters outside the three opted-in codes remain ordinary text.
check([(i*80+10,0xa1,7) for i in range(25)],[])
check([(0,0xb2,1),(80,0xb2,2),(160,0xb2,3),(240,0xb2,4)],[0,80,160,240],seed=80,direct='MARK_SHADE_VERTICAL')
print(f'PASS: {count} shade cases; B0/B1/B2, lengths, colours, all-cell detector bounds, top/bottom/row edges, gaps and Thai text')
