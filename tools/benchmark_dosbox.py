"""Compare shared-source 8086/386 routines in identically configured DOSBox-X.
Uses BIOS ticks (about 54.9 ms), so this is emulated timing, not hardware timing.
No installed driver is replaced: generated benchmark copies run in fresh emulators.
"""
from pathlib import Path
import argparse,subprocess,struct,time,json,statistics,hashlib

parser=argparse.ArgumentParser()
parser.add_argument('--assembler',required=True)
parser.add_argument('--dosbox',required=True)
parser.add_argument('--cycles',type=int,default=10000)
parser.add_argument('--repetitions',type=int,default=3)
parser.add_argument('--scale',type=int,default=1,help='Multiply loop counts for finer BIOS tick resolution')
parser.add_argument('--source',type=Path,help='Alternate source snapshot for before/after comparisons')
parser.add_argument('--work-dir',type=Path,default=Path('work/benchmark'))
parser.add_argument('--target',choices=('both','GTHAI','GTHAI386'),default='both')
parser.add_argument('--profile',choices=('glyph','screen','blanks','rows','partial','frames','thai8','cache4'),default='glyph')
args=parser.parse_args()
if args.cycles<=0 or not 1<=args.repetitions<=20 or not 1<=args.scale<=20: parser.error('Invalid cycles, repetitions, or scale')
root=Path(__file__).resolve().parents[1]
work=root/args.work_dir; work.mkdir(parents=True,exist_ok=True)
source=(args.source or root/'GTHAI.ASM').read_text(encoding='latin1')
cases=[(name,count*args.scale) for name,count in [('copy19',500000),('compose_thai',250000),('draw_ascii',200000),('draw_thai',100000)]]
# Same 16-bit loop/argument setup in both variants; only the driver code differs.
body="""
BENCH_START:
         CLD
         MOV AX,12H
         INT 10H
         PUSH CS
         POP DS
         MOV AX,0A000H
         MOV ES,AX
         MOV WORD PTR [VIDBUF],AX
         MOV WORD PTR [VID_OFFSET],VGA_ORIGIN
         MOV BYTE PTR [TEXT_COLOR],7
         MOV DX,OFFSET BENCH_FILE
         XOR CX,CX
         MOV AH,3CH
         INT 21H
         JC BENCH_ERROR
         MOV [BENCH_HANDLE],AX
         MOV WORD PTR [BENCH_REPEAT],0
BENCH_ROUND:
"""
loops=[
 """         MOV BX,OFFSET FONT_2+0A1H*CELL_HEIGHT
         MOV BP,OFFSET GLYPH_COMPOSE
         CALL COPY_GLYPH19
""",
 """         MOV BX,OFFSET FONT_2+0A1H*CELL_HEIGHT
         MOV BP,OFFSET GLYPH_COMPOSE
         CALL COPY_GLYPH19
         MOV BX,OFFSET FONT_2+0D4H*CELL_HEIGHT
         MOV CX,CELL_HEIGHT
         CALL OR_GLYPH_ROWS
         MOV BX,OFFSET FONT_2+0E8H*CELL_HEIGHT+TONE_RAISE
         MOV CX,CELL_HEIGHT-TONE_RAISE
         CALL OR_GLYPH_ROWS
""",
 """         MOV AX,0741H
         MOV SI,OFFSET FONT_2
         MOV DI,VGA_ORIGIN
         CALL L62B3H
""",
 """         MOV SI,OFFSET BENCH_THAI
         CALL DO_MSG
"""]
if args.profile in ('screen','blanks','rows','partial','frames','thai8','cache4'):
    cases=[('screen_idle',5000*args.scale),('screen_redraw',500*args.scale)]
    setup="""
         MOV WORD PTR [VID_SEG],0B800H
         MOV WORD PTR [CRTBASE],03D4H
; Match GTHAI's VGA memory mapping, not the BIOS mode-12h A000-only default.
         MOV DX,03CEH
         MOV AX,0106H
         OUT DX,AX
         MOV BYTE PTR [CURRENT_MODE],0
         MOV BX,OFFSET L0506H
         MOV AX,VGA_ORIGIN
         MOV CX,26
BENCH_ROWS:
         MOV [BX],AX
         ADD AX,CELL_HEIGHT*80
         ADD BX,2
         LOOP BENCH_ROWS
         MOV [VID_OFFSET],AX
         SUB WORD PTR [VID_OFFSET],CELL_HEIGHT*80
         MOV DX,03D4H
         MOV AX,070EH
         OUT DX,AX
         MOV AX,0D00FH
         OUT DX,AX
         MOV AX,0B800H
         MOV ES,AX
         XOR DI,DI
         MOV AX,0741H
         MOV CX,2000
         REP STOSW
         PUSH CS
         POP ES
         MOV DI,OFFSET VID_SAVE
         MOV AX,0741H
         MOV CX,2000
         REP STOSW
         MOV AX,0A000H
         MOV ES,AX
"""
    body=body.replace('BENCH_ROUND:',setup+'\nBENCH_ROUND:')
    call="""         PUSH DS
         PUSH ES
         PUSH DX
         PUSH CS
         POP DS
         CALL UPDATE_SCREEN_THAI_25
         POP DX
         POP ES
         POP DS
"""
    dirty="""         PUSH ES
         PUSH CS
         POP ES
         MOV DI,OFFSET VID_SAVE
         XOR AX,AX
         MOV CX,2000
         REP STOSW
         POP ES
"""
    loops=[call,dirty+call]
if args.profile=='blanks':
    cases=[(name,200*args.scale) for name in ('blank_long','blank_mixed','blank_alternating','ascii_control')]
    loops=[dirty+call]*len(cases)
if args.profile=='rows':
    cases=[(name,200*args.scale) for name in ('row_ascii_same','row_ascii_foreground','row_ascii_background','row_thai')]
    loops=[dirty+call]*len(cases)
if args.profile=='thai8':
    cases=[(name,200*args.scale) for name in ('row_ascii_same','row_thai','blank_long','blank_mixed','blank_alternating')]
    loops=[dirty+call.replace('UPDATE_SCREEN_THAI_25','UPDATE_SCREEN_THAI_8')]*len(cases)
    body=body.replace('MOV BYTE PTR [CURRENT_MODE],0','MOV BYTE PTR [DISPMODE],1\n         MOV BYTE PTR [CURRENT_MODE],0')
if args.profile=='partial':
    cases=[(name,2000*args.scale) for name in ('partial_ascii','partial_colour','partial_thai','partial_dense','partial_blank')]
    loops=[]
    for name,_ in cases:
        offsets=([12*160+col*2 for col in range(32,48)] if name=='partial_dense' else [12*160+(41 if name=='partial_thai' else 40)*2])
        mask={'partial_ascii':3,'partial_colour':0x100,'partial_thai':12,'partial_dense':3,'partial_blank':0x61}[name]
        mutate="         PUSH ES\n         MOV AX,0B800H\n         MOV ES,AX\n"
        mutate+=''.join(f"         XOR WORD PTR ES:[{offset}],{mask}\n" for offset in offsets)
        loops.append(mutate+"         POP ES\n"+call)
if args.profile=='cache4':
    cases=[('cache_four',2000*args.scale),('cache_collision',2000*args.scale),('cache_query',2000*args.scale)]
    loops=[]
    for rows in ((3,12,21,22),(3,7),(12,)):
        code=''
        for row in rows:
            code+=f'''         PUSH ES
         MOV AX,0B800H
         MOV ES,AX
         XOR WORD PTR ES:[{row*160+82}],12
         POP ES
'''+call
        if rows==(12,):
            code='''         PUSH AX
         PUSH BX
         PUSH ES
         MOV AX,8000H
         XOR BX,BX
         PUSHF
         PUSH CS
         CALL CSTM_VID
         POP ES
         POP BX
         POP AX
'''+code
        loops.append(code)
if args.profile=='frames':
    cases=[(name,200000*args.scale) for name in ('frame_shade','frame_vertical')]
    loops=['''         PUSH DS
         MOV AX,0B800H
         MOV DS,AX
         MOV SI,2000
         CALL L4B7FH
         POP DS
''']*len(cases)
for index,(name,iterations) in enumerate(cases):
    inner=min(50000,iterations)
    assert iterations%inner==0
    if args.profile in ('blanks','rows','partial','frames','thai8','cache4'):
        body+="""         MOV AX,0B800H
         MOV ES,AX
         XOR DI,DI
         MOV CX,2000
"""
        if name in ('frame_shade','frame_vertical'):
            body+=f"         MOV AX,{('07B0H' if name=='frame_shade' else '07B3H')}\n         REP STOSW\n"
        elif name in ('blank_long','ascii_control','row_ascii_same','partial_ascii','partial_colour','partial_dense','partial_blank'):
            body+=f"         MOV AX,{('0741H' if name in ('ascii_control','row_ascii_same','partial_ascii','partial_colour','partial_dense') else '0720H')}\n         REP STOSW\n"
        elif name=='row_ascii_foreground':
            body+=f"         MOV AX,0141H\nBENCH_FILL_{index}:\n         STOSW\n         INC AH\n         AND AH,0FH\n         LOOP BENCH_FILL_{index}\n"
        elif name in ('row_thai','partial_thai','cache_four','cache_collision','cache_query'):
            body+=f"""         XOR BX,BX
BENCH_FILL_{index}:
         MOV BP,BX
         AND BP,3
         MOV AL,CS:[BENCH_ROW_THAI+BP]
         MOV AH,07H
         STOSW
         INC BX
         LOOP BENCH_FILL_{index}
"""
        elif name in ('blank_alternating','row_ascii_background'):
            body+=f"         MOV AX,{('0741H' if name=='row_ascii_background' else '0720H')}\nBENCH_FILL_{index}:\n         STOSW\n         XOR AH,10H\n         LOOP BENCH_FILL_{index}\n"
        else:
            body+=f"""         XOR BX,BX
BENCH_FILL_{index}:
         MOV AX,0720H
         TEST BX,15
         JNZ BENCH_FILL_STORE_{index}
         MOV AL,41H
BENCH_FILL_STORE_{index}:
         STOSW
         INC BX
         LOOP BENCH_FILL_{index}
"""
        expected={'cache_query':'07A1H','cache_four':'07A1H','cache_collision':'07A1H','frame_shade':'07B0H','frame_vertical':'07B3H','blank_mixed':'0741H','ascii_control':'0741H','row_ascii_same':'0741H','row_ascii_foreground':'0141H','row_ascii_background':'0741H','row_thai':'07A1H','partial_thai':'07A1H','partial_ascii':'0741H','partial_colour':'0741H','partial_dense':'0741H'}.get(name,'0720H')
        body+=f"""         CMP WORD PTR ES:[0],{expected}
         JE BENCH_FILL_OK_{index}
         JMP BENCH_ERROR
BENCH_FILL_OK_{index}:
         MOV AX,0A000H
         MOV ES,AX
"""
    if args.profile in ('partial','cache4'): body+=dirty+call
    body+=f"         MOV WORD PTR [BENCH_CASE],{index}\n"
    body+="""         CALL BENCH_SYNC
         MOV [BENCH_BEGIN],AX
"""
    body+=f"         MOV DX,{iterations//inner}\nBENCH_OUTER_{index}:\n         MOV CX,{inner}\nBENCH_INNER_{index}:\n         PUSH CX\n"
    body+=loops[index]
    body+=f"         POP CX\n         LOOP BENCH_INNER_{index}\n         DEC DX\n         JNZ BENCH_OUTER_{index}\n"
    body+="""         CALL BENCH_CLOCK
         SUB AX,[BENCH_BEGIN]
         MOV [BENCH_ELAPSED],AX
         CALL BENCH_WRITE
"""
body+="""         INC WORD PTR [BENCH_REPEAT]
"""+f"         CMP WORD PTR [BENCH_REPEAT],{args.repetitions}\n"
body+="""         JB BENCH_ROUND
         MOV BX,[BENCH_HANDLE]
         MOV AH,3EH
         INT 21H
         MOV AX,3H
         INT 10H
         MOV AX,4C00H
         INT 21H
BENCH_ERROR:
         MOV AX,4C01H
         INT 21H
BENCH_CLOCK:
         PUSH ES
         MOV AX,40H
         MOV ES,AX
         MOV AX,WORD PTR ES:[6CH]
         POP ES
         RET
BENCH_SYNC:
         CALL BENCH_CLOCK
         MOV BX,AX
BENCH_SYNC_WAIT:
         CALL BENCH_CLOCK
         CMP AX,BX
         JE BENCH_SYNC_WAIT
         RET
BENCH_WRITE:
         MOV BX,[BENCH_HANDLE]
         MOV DX,OFFSET BENCH_CASE
         MOV CX,6
         MOV AH,40H
         INT 21H
         RET
BENCH_FILE DB 'RESULT.BIN',0
BENCH_HANDLE DW 0
BENCH_BEGIN DW 0
BENCH_CASE DW 0
BENCH_REPEAT DW 0
BENCH_ELAPSED DW 0
BENCH_ROW_THAI DB 0A1H,0D4H,0E8H,41H
BENCH_THAI DB (0A1H XOR 5),(0D4H XOR 5),(0E8H XOR 5),5
"""
variant=source.replace('JMP   INIT','JMP   BENCH_START',1)
end=variant.lower().rfind('code_seg ends')
variant=variant[:end]+body+variant[end:]
benchmark_source=work/'benchmark.asm'; benchmark_source.write_text(variant,encoding='latin1')
all_results={}
for target in (('GTHAI','GTHAI386') if args.target=='both' else (args.target,)):
    directory=work/target; directory.mkdir(exist_ok=True)
    binary=directory/'BENCH.COM'
    command=[args.assembler,'-bin',f'-Fo{binary}',str(benchmark_source)]
    if target=='GTHAI386': command.insert(2,'-DCPU_386=1')
    subprocess.run(command,cwd=root,check=True)
    output=directory/'RESULT.BIN'
    if output.exists(): output.unlink()
    config=directory/'dosbox.conf'
    config.write_text(f'[sdl]\noutput=surface\nvideodriver=dummy\nshowmenu=false\n[dosbox]\nmachine=svga_s3\nmemsize=16\nfastbioslogo=true\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed {args.cycles}\n[autoexec]\nmount c {directory}\nc:\nbench\nexit\n')
    startup=subprocess.STARTUPINFO(); startup.dwFlags=subprocess.STARTF_USESHOWWINDOW; startup.wShowWindow=0
    process=subprocess.Popen([args.dosbox,'-conf',str(config),'-fastlaunch','-nogui'],cwd=directory,startupinfo=startup,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    seen=0; started=time.monotonic(); records=[]
    try:
        while process.poll() is None:
            if time.monotonic()-started>240: raise TimeoutError(f'{target} benchmark timeout')
            data=output.read_bytes() if output.exists() else b''
            while len(data)>=seen+6:
                case,repeat,ticks=struct.unpack_from('<HHH',data,seen); seen+=6
                assert case<len(cases) and repeat<args.repetitions and ticks>0,(case,repeat,ticks)
                records.append(dict(case=cases[case][0],repeat=repeat,ticks=ticks))
                print(f'{target} {cases[case][0]} sample {repeat+1}: {ticks} ticks',flush=True)
            time.sleep(0.1)
        data=output.read_bytes() if output.exists() else b''
        while len(data)>=seen+6:
            case,repeat,ticks=struct.unpack_from('<HHH',data,seen); seen+=6
            records.append(dict(case=cases[case][0],repeat=repeat,ticks=ticks))
            print(f'{target} {cases[case][0]} sample {repeat+1}: {ticks} ticks',flush=True)
        assert len(records)==len(cases)*args.repetitions,(target,records)
        all_results[target]=records
    finally:
        if process.poll() is None: process.terminate(); process.wait(timeout=5)
report={'source_sha256':hashlib.sha256(source.encode('latin1')).hexdigest(),'include_sha256':hashlib.sha256((root/'GTHAI.INC').read_bytes()).hexdigest(),'environment':dict(core='normal',cpu='386',cycles=args.cycles,repetitions=args.repetitions,scale=args.scale,profile=args.profile,timer='BIOS tick',tick_seconds=65536/1193182),'cases':dict(cases),'samples':all_results}
(work/'results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for name,iterations in (cases if args.target=='both' else []):
    before=statistics.median(x['ticks'] for x in all_results['GTHAI'] if x['case']==name)
    after=statistics.median(x['ticks'] for x in all_results['GTHAI386'] if x['case']==name)
    print(f'{name}: median {before} -> {after} ticks, elapsed time change {(after/before-1)*100:+.1f}%',flush=True)
print('Saved',work/'results.json',flush=True)
