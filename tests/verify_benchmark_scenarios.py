"""Check that each 'scenarios' benchmark workload exercises the driver path it claims to."""
import sys
exec((__import__('pathlib').Path(__file__).parent/'verify_vga.py').read_text().split('\nm=Machine()')[0])
sys.path.insert(0,str(root/'tools'))
from bench_scenarios import SCREENS,EDIT_ROW,EDIT_COL,CURSOR_A,CURSOR_B
origin=0xe000
def machine():
    q=Machine();q.word('VIDBUF',0xa000);q.word('VID_SEG',0xb800);q.word('CRTBASE',0x3d4)
    for row in range(26):q.u.mem_write(0x10000+symbols['L0506H']+row*2,((origin+row*19*80)&65535).to_bytes(2,'little'))
    hidden=(origin+25*19*80)&65535
    q.word('VID_OFFSET',hidden);q.word('L0538H',hidden);q.crt[14],q.crt[15]=7,0xd0
    q.u.mem_write(0x10000+symbols['CURRENT_MODE'],bytes(1))
    q.calls={}
    for name in ('L4B7FH','COPY_GLYPH19'):
        q.calls[name]=0
        def count(u,address,size,_,name=name):q.calls[name]+=1
        q.u.hook_add(UC_HOOK_CODE,count,begin=0x10000+symbols[name],end=0x10000+symbols[name])
    return q
def load(q,data,saved=True):
    for pl in q.planes:pl[0x8000:0x8000+4000]=data
    q.u.mem_write(0x10000+symbols['VID_SAVE'],data if saved else bytes(4000))
def update(q):
    q.writes.clear();q.calls={k:0 for k in q.calls};q.call('UPDATE_SCREEN_THAI_25',ds=0x1000)
    return len(q.writes)
def saved(q):return bytes(q.u.mem_read(0x10000+symbols['VID_SAVE'],4000))
def chars(data):return data[0::2]

for name,minwrites in (('norton',30000),('thai',20000),('blank',38000)):
    q=machine();data=SCREENS[name]();load(q,data,saved=False)
    for _ in range(4):update(q)                     # frame scan aborts/marks first; settle like the timer would
    assert not q.u.mem_read(0x10000+symbols['CURRENT_MODE'],1)[0]&1,name
    q.u.mem_write(0x10000+symbols['VID_SAVE'],bytes(4000))   # dirty screen: the measured full redraw
    writes=update(q)
    assert writes>=minwrites,(name,writes)
    assert chars(saved(q))==chars(data),name
    if name=='norton': assert q.calls['L4B7FH']>500,q.calls
    if name=='thai': assert q.calls['COPY_GLYPH19']>100,q.calls
    if name=='blank': assert writes==2000*19 and q.calls['COPY_GLYPH19']==0,(writes,q.calls)
    assert update(q)==0,name+' idle redraw'          # nothing changed: nothing drawn
print('PASS: norton/thai/blank full redraws draw the screen, reach frame/composition paths, and go idle afterwards')

q=machine();data=bytearray(SCREENS['edit']());load(q,bytes(data))
off=(EDIT_ROW*80+EDIT_COL)*2
for turn in range(4):
    data[off]^=1
    for pl in q.planes:pl[0x8000+off]=data[off]
    writes=update(q)
    assert 0<writes<=80*20,(turn,writes)               # one row at most (19 stores per cell + a latch-seed write per glyph)
    assert chars(saved(q))==chars(bytes(data)),turn
print('PASS: edit_cell toggles one character, redraws at most one row, and keeps the saved screen in step')

q=machine();load(q,SCREENS['edit']());before=saved(q)
for turn,pos in enumerate((CURSOR_A,CURSOR_B,CURSOR_A,CURSOR_B)):
    q.crt[14],q.crt[15]=pos>>8,pos&255
    writes=update(q)
    assert 0<writes<=2*19+2,(turn,writes)
    assert saved(q)==before
print('PASS: cursor_move changes only cursor pixels and never the saved text')

q=machine();load(q,SCREENS['edit']());q.writes.clear()
q.call('SCRL_UP1',bx=0x0700,ds=0x1000)
assert len(q.writes)>=24*19*80,len(q.writes)
print('PASS: scroll_line performs the 24-row planar latch copy')
