"""Deterministic 80x25 text screens (char,attr words) for the 'scenarios' benchmark profile.
Also imported by tests/verify_benchmark_scenarios.py so the screens are checked against the driver."""
import random

def _blank(attr=0x07):
    return [[0x20,attr] for _ in range(80*25)]

def _put(cells,row,col,text,attr):
    for i,ch in enumerate(text):
        code=ch if isinstance(ch,int) else ord(ch)
        cells[row*80+col+i]=[code,attr]

def _flat(cells):
    out=bytearray()
    for ch,attr in cells:
        assert 0<=attr<0x80,'attribute bit 7 is the driver frame marker'
        out+=bytes((ch,attr))
    return bytes(out)

def norton():
    """Two double-line panels, file lists, shade scroll bars, command line and function-key bar."""
    c=_blank(0x1F)
    names=['..','AUTOEXEC.BAT','COMMAND.COM','CONFIG.SYS','DOS','GTHAI.COM','GTHAI386.COM','NC.EXE','NC.INI','README.TXT','TEMP','TOOLS','WORK']
    for left in (0,40):
        _put(c,0,left,[0xC9]+[0xCD]*37+[0xBB],0x1B)
        for r in range(1,22): _put(c,r,left,[0xBA],0x1B);_put(c,r,left+37,[0xBA],0x1B)
        _put(c,22,left,[0xC8]+[0xCD]*37+[0xBC],0x1B)
        for r in range(1,22):
            name=names[(r+left)%len(names)]
            _put(c,r,left+1,name.ljust(14),0x1F)
            _put(c,r,left+16,str(1000+r*173+left).rjust(9),0x1E)
            _put(c,r,left+27,'10-22-26',0x13)
            _put(c,r,left+36,[0xB1 if r%7 else 0xDB],0x17)
    _put(c,23,0,'C:\\NC>'.ljust(80),0x07)
    keys=['Help','Menu','View','Edit','Copy','RenMov','MkDir','Delete','PullDn','Quit']
    for i,k in enumerate(keys): _put(c,24,i*8,f'{i+1}'+k.ljust(6),0x30)
    return _flat(c)

def thai():
    """Seeded Thai text: consonants with optional upper vowels/tone marks, spaces and ASCII digits."""
    rng=random.Random(2026); c=_blank(0x07)
    for r in range(25):
        col=0
        while col<78:
            kind=rng.random()
            if kind<0.15: seq=[0x20]
            elif kind<0.25: seq=[ord(rng.choice('0123456789'))]
            else:
                seq=[rng.randrange(0xA1,0xCF)]
                if rng.random()<0.5: seq.append(rng.choice((0xD4,0xD5,0xD6,0xD7)))
                if rng.random()<0.4: seq.append(rng.choice((0xE8,0xE9,0xEA,0xEB)))
            if col+len(seq)>80: break
            for code in seq: c[r*80+col]=[code,0x07];col+=1
    return _flat(c)

def edit():
    """Source-code-like English text with indentation, a title bar and a status bar."""
    c=_blank(0x07)
    _put(c,0,0,' File  Edit  Search  Run  Options'.ljust(80),0x70)
    lines=['MAIN PROC NEAR','        MOV  AX,DATA','        MOV  DS,AX','        CALL INIT','LOOP1:  CMP  CX,0','        JE   DONE','        DEC  CX','        JMP  LOOP1','DONE:   RET']
    for r in range(1,24): _put(c,r,0,lines[(r-1)%len(lines)],0x07 if r%5 else 0x1F)
    _put(c,24,0,' Line 11  Col 41  Insert'.ljust(80),0x70)
    return _flat(c)

def blank(): return _flat(_blank(0x07))

SCREENS={'norton':norton,'thai':thai,'edit':edit,'blank':blank}
EDIT_ROW,EDIT_COL=11,40                 # one character is toggled here by edit_cell
CURSOR_A,CURSOR_B=5*80+10,5*80+11       # cursor_move alternates between these cells
