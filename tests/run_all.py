"""Run the same verifiers against both outputs produced by build.ps1."""
import os, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
checks=('verify_vga.py','verify_mode3.py','verify_packed19.py','verify_mode_switch.py','verify_vertical_shade.py','verify_colour_hint.py','verify_screen_batch.py','verify_benchmark_scenarios.py')
for target in ('GTHAI','GTHAI386'):
    print(f'=== {target} ===',flush=True)
    env=dict(os.environ,GTHAI_TARGET=target)
    for name in checks:
        subprocess.run([sys.executable,str(root/'tests'/name)],cwd=root,env=env,check=True)
subprocess.run([sys.executable,str(root/'tests/verify_dual_build.py')],cwd=root,check=True)
