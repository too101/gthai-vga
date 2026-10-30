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

# Digest of (planes) recorded from the build before DRAW_BOX was introduced.
GOLDEN = {
    'GTHAI': {'PANEL': '037cecc986804430', 'CANT_UNLOAD': 'c1e15e6d2c352413',
              'OK_TO_UNLOAD': '74a2137945f2a0d6', 'CANT_UNLOAD_SKIP3': '07baa0734df26422',
              'OK_SKIP2': '003665d43bf06148', 'OK_SKIP3': 'b78411db034413d0'},
    'GTHAI386': {'PANEL': 'c80013f2593a81ed', 'CANT_UNLOAD': 'c1e15e6d2c352413',
                 'OK_TO_UNLOAD': '74a2137945f2a0d6', 'CANT_UNLOAD_SKIP3': '07baa0734df26422',
                 'OK_SKIP2': '003665d43bf06148', 'OK_SKIP3': 'b78411db034413d0'},
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
