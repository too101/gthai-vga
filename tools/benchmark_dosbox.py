"""Compare shared-source 8086/386 routines in identically configured DOSBox-X.
Uses BIOS ticks (about 54.9 ms), so this is emulated timing, not hardware timing.
No installed driver is replaced: generated benchmark copies run in fresh emulators.
"""
from pathlib import Path
import argparse,subprocess,struct,time,json,statistics

parser=argparse.ArgumentParser()
parser.add_argument('--assembler',required=True)
parser.add_argument('--dosbox',required=True)
parser.add_argument('--cycles',type=int,default=10000)
parser.add_argument('--repetitions',type=int,default=3)
parser.add_argument('--scale',type=int,default=1,help='Multiply loop counts for finer BIOS tick resolution')
args=parser.parse_args()
if args.cycles<=0 or not 1<=args.repetitions<=20 or not 1<=args.scale<=20: parser.error('Invalid cycles or repetitions')
root=Path(__file__).resolve().parents[1]
work=root/'work/benchmark'; work.mkdir(parents=True,exist_ok=True)
source=(root/'GTHAI.ASM').read_text(encoding='latin1')
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
for index,(name,iterations) in enumerate(cases):
    assert iterations%50000==0
    body+=f"         MOV WORD PTR [BENCH_CASE],{index}\n"
    body+="""         CALL BENCH_SYNC
         MOV [BENCH_BEGIN],AX
"""
    body+=f"         MOV DX,{iterations//50000}\nBENCH_OUTER_{index}:\n         MOV CX,50000\nBENCH_INNER_{index}:\n         PUSH CX\n"
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
BENCH_THAI DB (0A1H XOR 5),(0D4H XOR 5),(0E8H XOR 5),5
"""
variant=source.replace('JMP   INIT','JMP   BENCH_START',1)
end=variant.lower().rfind('code_seg ends')
variant=variant[:end]+body+variant[end:]
benchmark_source=work/'benchmark.asm'; benchmark_source.write_text(variant,encoding='latin1')
all_results={}
for target in ('GTHAI','GTHAI386'):
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
report={'environment':dict(core='normal',cpu='386',cycles=args.cycles,repetitions=args.repetitions,scale=args.scale,timer='BIOS tick',tick_seconds=65536/1193182),'cases':dict(cases),'samples':all_results}
(work/'results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for name,iterations in cases:
    before=statistics.median(x['ticks'] for x in all_results['GTHAI'] if x['case']==name)
    after=statistics.median(x['ticks'] for x in all_results['GTHAI386'] if x['case']==name)
    print(f'{name}: median {before} -> {after} ticks, elapsed time change {(after/before-1)*100:+.1f}%',flush=True)
print('Saved',work/'results.json',flush=True)
