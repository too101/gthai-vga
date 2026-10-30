"""Compare grouped blank rendering with the previous per-cell path."""
exec((__import__('pathlib').Path(__file__).parent/'verify_vga.py').read_text().split('\nm=Machine()')[0])
for attr in range(256):
    ref=Machine();opt=Machine()
    for length,di in ((1,0xe000),(2,0xfffe),(17,0xfffa),(80,0x7470)):
        ref.planes=[bytearray([0x5a])*65536 for _ in range(4)]
        opt.planes=[bytearray([0x5a])*65536 for _ in range(4)]
        for cell in range(length): ref.call('L6289H',ax=(attr<<8)|32,di=(di+cell)&65535)
        opt.call('VGA_BLANK_RUN',ax=(attr<<8)|32,cx=length,di=di)
        assert ref.planes==opt.planes,(attr,length,hex(di))
        assert opt.u.reg_read(UC_X86_REG_DI)==(di+length)&65535
        assert opt.u.reg_read(UC_X86_REG_CX)==length
        assert opt.gc[1]==0 and opt.gc[5]==0
print('PASS: grouped blank pixels match per-cell writer for all attributes, lengths 1/2/17/80 and 64K wrap')

def setup(legacy):
    q=Machine();q.word('VIDBUF',0xa000);q.word('VID_SEG',0xb800);q.word('CRTBASE',0x3d4)
    for row in range(26):q.u.mem_write(0x10000+symbols['L0506H']+row*2,((0xe000+row*19*80)&65535).to_bytes(2,'little'))
    q.word('VID_OFFSET',0x7470);q.crt[14],q.crt[15]=7,0xd0
    q.u.mem_write(0x10000+symbols['CURRENT_MODE'],bytes(1))
    if legacy:
        # LODSW / CALL L6289H / INC DI / DEC BX / JNZ / RET: previous loop.
        start=0xee00;rel=(symbols['L6289H']-(start+4))&65535
        q.u.mem_write(0x10000+start,b'\xad\xe8'+rel.to_bytes(2,'little')+b'\x47\x4b\x75\xf8\xc3')
        def old_loop(u,address,size,_):u.reg_write(UC_X86_REG_IP,start)
        q.u.hook_add(UC_HOOK_CODE,old_loop,begin=0x10000+symbols['BLANK_TEXT_RUN'],end=0x10000+symbols['BLANK_TEXT_RUN'])
    return q
for adjust in range(8):
    ref=setup(True);opt=setup(False)
    for turn in range(3):
        for q in (ref,opt):
            q.u.mem_write(0x10000+symbols['DISPLAY_COLUMN_ADJUST'],bytes([adjust]))
            for row in range(25):
                cells=bytearray()
                for col in range(80):
                    mode=row%5
                    code=32 if mode!=4 or col%13>3 else (0xa1,0xd4,0xe8,65)[col%13]
                    attr=7 if mode==0 else ((col+turn)&15 if mode==1 else (((col//(1 if mode==2 else 8)+turn)&7)<<4)|7)
                    cells+=bytes([code,attr])
                for plane in q.planes:plane[0x8000+row*160:0x8000+(row+1)*160]=cells
            q.call('UPDATE_SCREEN_THAI_25',ds=0x1000)
        if ref.planes!=opt.planes:
            for pn in range(4):
                diff=[(hex(i),a,b) for i,(a,b) in enumerate(zip(ref.planes[pn],opt.planes[pn])) if a!=b]
                print('DIFF',pn,diff[:12])
            print('save same',ref.u.mem_read(0x10000+symbols['VID_SAVE'],4000)==opt.u.mem_read(0x10000+symbols['VID_SAVE'],4000))
        assert ref.planes==opt.planes,(adjust,turn)
        assert ref.u.mem_read(0x10000+symbols['VID_SAVE'],4000)==opt.u.mem_read(0x10000+symbols['VID_SAVE'],4000)
print('PASS: complete mixed screens match old space loop for all 8 vowel-compensation settings, foreground/background changes and redraws')
q=Machine();count=[0]
def outs(u,port,size,value,_):
    if port==0x3ce:
        count[0]+=1
        assert not u.reg_read(UC_X86_REG_EFLAGS)&0x200
q.u.hook_add(UC_HOOK_INSN,outs,None,1,0,UC_X86_INS_OUT)
start=0xed00;rel=(symbols['VGA_BLANK_RUN']-(start+4))&65535
q.u.mem_write(0x10000+start,b'\xfb\xe8'+rel.to_bytes(2,'little')+b'\xc3');symbols['BLANK_IRQ_TEST']=start
q.call('BLANK_IRQ_TEST',ax=0x1720,cx=80,di=0xe000)
assert q.u.reg_read(UC_X86_REG_EFLAGS)&0x200
assert count[0]==3,count
print('PASS: 80-cell blank run uses 3 GC OUTs, stays atomic, and restores IF')

# BLANK_TEXT_RUN must not hold one CLI window across a whole 80-cell run.
BLANK_CHUNK_CELLS=16
q=Machine();ref=Machine();state={'run':0,'max':0,'outs':0}
def watch_code(u,address,size,_):
    if u.reg_read(UC_X86_REG_EFLAGS)&0x200: state['run']=0
def watch_write(u,access,addr,size,value,_):
    if not u.reg_read(UC_X86_REG_EFLAGS)&0x200:
        state['run']+=1;state['max']=max(state['max'],state['run'])
def watch_out(u,port,size,value,_):
    if port==0x3ce: state['outs']+=1
q.u.hook_add(UC_HOOK_CODE,watch_code,begin=0x10000,end=0x1ffff)
q.u.hook_add(UC_HOOK_MEM_WRITE,watch_write,begin=0xa0000,end=0xbffff)
q.u.hook_add(UC_HOOK_INSN,watch_out,None,1,0,UC_X86_INS_OUT)
start=0xec00;rel=(symbols['BLANK_TEXT_RUN']-(start+4))&65535
q.u.mem_write(0x10000+start,b'\xfb\xe8'+rel.to_bytes(2,'little')+b'\xc3');symbols['BLANK_RUN_IRQ_TEST']=start
for attr in (0x07,0x1f,0xe3):
    for machine in (q,ref):
        machine.planes=[bytearray([0x5a])*65536 for _ in range(4)]
        machine.u.mem_write(0x10000+symbols['ROW_PLAN_MODE'],bytes(1))
        machine.u.mem_write(0x19000,bytes([32,attr])*80)
    state.update(run=0,max=0,outs=0);q.writes.clear()
    q.call('BLANK_RUN_IRQ_TEST',bx=80,si=0x9000,di=0x7470)
    for cell in range(80): ref.call('L6289H',ax=(attr<<8)|32,di=(0x7470+cell)&65535)
    assert q.planes==ref.planes,hex(attr)
    assert len(q.writes)==80*19,len(q.writes)
    assert state['max']<=BLANK_CHUNK_CELLS*19,state
    assert state['outs']==3*((80+BLANK_CHUNK_CELLS-1)//BLANK_CHUNK_CELLS),state
    assert q.u.reg_read(UC_X86_REG_EFLAGS)&0x200
    assert q.u.reg_read(UC_X86_REG_BX)==0 and q.u.reg_read(UC_X86_REG_DI)==(0x7470+80)&65535
print('PASS: 80-cell blank run keeps each interrupt-masked window to 16 cells (304 byte stores), matches per-cell pixels and restores IF')
