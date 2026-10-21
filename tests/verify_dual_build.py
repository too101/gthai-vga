"""Check both artifacts, 386 register safety, CPU gate and instruction counts."""
from pathlib import Path
import os
from collections import Counter
prefix=(Path(__file__).with_name('verify_vga.py')).read_text().split('\nm=Machine()')[0]
def load(name):
    old=os.environ.get('GTHAI_TARGET')
    os.environ['GTHAI_TARGET']=name
    ns={'__file__':str(Path(__file__).with_name('verify_vga.py'))}
    try: exec(compile(prefix,'verify_vga.py','exec'),ns)
    finally:
        if old is None: os.environ.pop('GTHAI_TARGET',None)
        else: os.environ['GTHAI_TARGET']=old
    return ns

for name in ('GTHAI','GTHAI386'):
    ns=load(name); sy=ns['symbols']; m=ns['Machine'](); u=m.u
    assert sy['FONT_2']-sy['FONT_1']==4864
    assert u.mem_read(0x10000+sy['WHICHPTR'],1)==b'\0'
    assert u.mem_read(0x10000+sy['DISPLAY_COLUMN_ADJUST'],1)==b'\x02'
    reg_names=('EAX','EBX','ECX','EDX','ESI','EDI','EBP')
    for helper,raised in [('COPY_GLYPH19',0),('OR_GLYPH_ROWS',0),('OR_GLYPH_ROWS',3)]:
        source=sy['FONT_2']+255*19+raised; dest=sy['GLYPH_COMPOSE']
        glyph=bytes(u.mem_read(0x10000+source,19-raised))
        initial=bytes(range(19)); u.mem_write(0x10000+dest,initial+b'\0\x5a\xa5')
        for i,reg in enumerate(reg_names): u.reg_write(ns['UC_X86_REG_'+reg],(0xa500+i)<<16)
        counter=Counter()
        def count(u,address,size,data): counter['instructions']+=1
        hook=u.hook_add(ns['UC_HOOK_CODE'],count)
        m.call(helper,bx=source,bp=dest,cx=19-raised)
        u.hook_del(hook)
        for i,reg in enumerate(reg_names): assert u.reg_read(ns['UC_X86_REG_'+reg])>>16==0xa500+i,(name,helper,reg)
        expected=glyph if helper=='COPY_GLYPH19' else bytes(a|b for a,b in zip(initial,glyph+bytes(raised)))
        assert bytes(u.mem_read(0x10000+dest,22))==expected+b'\0\x5a\xa5'
        print(f'PASS: {name} {helper} raised={raised}: {counter["instructions"]} instructions, high registers and glyph bounds intact')

ns=load('GTHAI386')
# Emulate historical FLAGS restrictions while executing the compiled guard.
def emulate_flags(u,kind):
    high=[0xf000 if kind=='8086' else 0]
    def code(u,address,size,data):
        op=bytes(u.mem_read(address,1))[0]
        if op==0x9c:
            sp=(u.reg_read(ns['UC_X86_REG_SP'])-2)&65535
            value=(u.reg_read(ns['UC_X86_REG_EFLAGS'])&0xfff)|high[0]
            u.mem_write((u.reg_read(ns['UC_X86_REG_SS'])<<4)+sp,value.to_bytes(2,'little'))
            u.reg_write(ns['UC_X86_REG_SP'],sp)
            u.reg_write(ns['UC_X86_REG_IP'],(address-0x10000+1)&65535)
        elif op==0x9d:
            sp=u.reg_read(ns['UC_X86_REG_SP'])
            value=int.from_bytes(u.mem_read((u.reg_read(ns['UC_X86_REG_SS'])<<4)+sp,2),'little')
            high[0]=0xf000 if kind=='8086' else 0 if kind=='286' else value&0x7000
            u.reg_write(ns['UC_X86_REG_SP'],(sp+2)&65535)
            u.reg_write(ns['UC_X86_REG_EFLAGS'],(value&0xfff)|2)
            u.reg_write(ns['UC_X86_REG_IP'],(address-0x10000+1)&65535)
        else:
            assert op not in (0x66,0x67,0x0f),'Post-8086 opcode executed before CPU acceptance'
    u.hook_add(ns['UC_HOOK_CODE'],code)
    return high
for kind in ('8086','286','386'):
    m=ns['Machine'](); u=m.u; high=emulate_flags(u,kind)
    m.call('CHECK_CPU_386',ax=0x1234,cx=0x5678)
    assert bool(u.reg_read(ns['UC_X86_REG_EFLAGS'])&1)==(kind=='386')
    assert u.reg_read(ns['UC_X86_REG_AX'])==0x1234 and u.reg_read(ns['UC_X86_REG_CX'])==0x5678
    assert high[0]==(0xf000 if kind=='8086' else 0)
    print(f'PASS: compiled FLAGS guard accepts/rejects {kind} correctly and restores flags/registers')
for kind in ('8086','286'):
    m=ns['Machine'](); u=m.u; emulate_flags(u,kind); exits=[]
    def interrupt(u,number,data):
        assert number==0x21,'BIOS reached before CPU rejection'
        ax=u.reg_read(ns['UC_X86_REG_AX'])
        if ax>>8==0x4c:
            exits.append(ax&255); u.emu_stop()
        else: assert ax>>8==9
    u.hook_add(ns['UC_HOOK_INTR'],interrupt)
    u.emu_start(0x10000+ns['symbols']['INIT'],0x1f000,count=10000)
    assert exits==[1]
    print(f'PASS: GTHAI386 installer rejects {kind} before any 386 opcode or BIOS setup')
# Native Unicorn FLAGS path, without historical emulation.
m=ns['Machine'](); m.call('CHECK_CPU_386')
assert m.u.reg_read(ns['UC_X86_REG_EFLAGS'])&1
print('PASS: native 386+ FLAGS guard path')
