"""Run the control-panel and unload dialog drawing code against a VGA plane model.

The raised text boxes are drawn by one shared routine (DRAW_BOX) and the
menu messages are placed by another (SHOW_MSG).  This check
executes the real PANEL and UNLOAD dialog code until each first waits for a key
and compares a digest of the resulting VGA planes with digests recorded from the
build that still had a separate copy of the drawing code for every box.
"""
import sys, os, hashlib
from pathlib import Path
src = (Path(__file__).resolve().parent/'verify_vga.py').read_text()
exec(compile(src[:src.index('\nm=Machine()')], 'verify_vga.py', 'exec'))
from unicorn import UC_HOOK_INTR

def run(start, setup=None, **regs):
    m = Machine()
    u = m.u
    u.mem_write(0x1e000, b'\xcf')                       # original BIOS = IRET
    u.mem_write(0x10000+symbols['OLDINT10'], b'\x00\xe0\x00\x10')
    u.mem_write(0x10000+symbols['VMODEFLAG'], b'\x03')
    state = {'key': False}
    def intr(uc, intno, _):
        if intno == 0x16:
            state['key'] = True
            uc.emu_stop()
    u.hook_add(UC_HOOK_INTR, intr)
    u.mem_write(0x10000+symbols['TEXT_COLOR'], b'\x1e')  # visible text when a path starts after its colour setup
    m.word('MENU_LEFT_COLUMN', 16)
    m.word('MENU_TOP_ROW', 24)
    m.word('BBSMSG_COLUMN', 0x0030)
    if setup: setup(m)
    u.reg_write(UC_X86_REG_SP, 0xfff0)
    u.reg_write(UC_X86_REG_BP, 0x1234)
    for name, value in regs.items(): u.reg_write(globals()['UC_X86_REG_'+name.upper()], value)
    u.reg_write(UC_X86_REG_EFLAGS, 2)
    u.emu_start(0x10000+symbols[start], 0x1f000, count=3000000)
    assert state['key'], f'{start} never reached its key wait'
    assert u.reg_read(UC_X86_REG_BP) in (0x1234,) or start == 'PANEL', 'BP changed'
    h = hashlib.sha256()
    for plane in m.planes: h.update(bytes(plane))
    return h.hexdigest()[:16], sum(1 for p in m.planes for b in p if b)

# Digest of (planes) recorded from the build before DRAW_BOX was introduced, using the
# current fonts/GTHAI*-19.FON.  Re-record from that build when the fonts or version text change.
GOLDEN = {
    'GTHAI': {'PANEL': '5b24b5053be30916', 'CANT_UNLOAD': '81b14e2b79250ed1',
              'OK_TO_UNLOAD': '9a0f32e24bd152be', 'CANT_UNLOAD_SKIP3': 'bf129eb31d4ae393',
              'OK_SKIP2': '586219842b827ff2', 'OK_SKIP3': '81bfc8c5ba08ce9b'},
    'GTHAI386': {'PANEL': '1bea47bf91763976', 'CANT_UNLOAD': '81b14e2b79250ed1',
                 'OK_TO_UNLOAD': '9a0f32e24bd152be', 'CANT_UNLOAD_SKIP3': 'bf129eb31d4ae393',
                 'OK_SKIP2': '586219842b827ff2', 'OK_SKIP3': '81bfc8c5ba08ce9b'},
}
cases = ('PANEL', 'CANT_UNLOAD', 'OK_TO_UNLOAD', 'CANT_UNLOAD_SKIP3', 'OK_SKIP2', 'OK_SKIP3')
got = {name: run(name, ax=0x1000) for name in cases}
if os.environ.get('GTHAI_RECORD'):
    print(build_artifact, got)
    sys.exit(0)
for name in cases:
    digest, lit = got[name]
    assert lit > 100, f'{name}: nothing drawn'
    assert GOLDEN[build_artifact][name] == digest, f'{name}: drawing differs from the pre-DRAW_BOX build ({digest})'
    print(f'PASS: {name} output identical to the build before DRAW_BOX/SHOW_MSG ({lit} plane bytes set)')
