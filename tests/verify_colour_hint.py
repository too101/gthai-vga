from pathlib import Path
exec(compile((Path(__file__).parent/'verify_vga.py').read_text().split('\nm=Machine()')[0], 'verify_vga.py', 'exec'))

def check(left, right, left_colour, right_colour, expected, row=5, col=10):
    m=Machine()
    page=bytearray(bytes([32,7])*2000)
    for y in range(min(3,25-row)):
        offset=((row+y)*80+col)*2
        page[offset:offset+2]=b'\xb3\x07'
    offset=(row*80+col)*2
    if col: page[offset-2:offset]=bytes([left,left_colour])
    if col<79: page[offset+2:offset+4]=bytes([right,right_colour])
    for plane in m.planes: plane[0x8000:0x8000+4000]=page
    m.call('L4B7FH',ds=0xb800,si=offset)
    detected=not bool(m.u.reg_read(UC_X86_REG_EFLAGS)&64)
    assert detected==expected,(left,right,left_colour,right_colour,row,col,detected)

check(32,65,7,7,True)
check(0xa1,0xa1,7,7,False)
check(0xa1,0xa1,1,1,True)
check(0xa1,0xa1,1,7,False)
check(0xa1,0xa1,7,1,False)
check(0xa1,0xa1,1,2,True)
check(0xa1,0xa1,0x17,0x27,True)
check(32,0x40,7,7,True)
check(32,0x5b,7,7,False)
check(32,0x5b,1,1,True)
for row in (23,24): check(32,65,1,1,False,row=row)
print('PASS: vertical colour hints, character fallback, side/background colours and bottom-row bounds')
