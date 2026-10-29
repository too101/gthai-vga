"""Execute custom INT10 dispatch: queries retain caches; mutations invalidate."""
exec((__import__('pathlib').Path(__file__).parent/'verify_vga.py').read_text().split('\nm=Machine()')[0])
q=Machine();entry=0xed00;rel=(symbols['CSTM_VID']-(entry+5))&65535
q.u.mem_write(0x10000+entry,b'\x9c\x0e\xe8'+rel.to_bytes(2,'little')+b'\xc3')
symbols['API_CACHE_TEST']=entry
# Skip DOS file I/O, retaining actual dispatcher selection for AH=82h.
q.u.mem_write(0x1ee00,b'\xc3')
def skip_file(u,address,size,_):u.reg_write(UC_X86_REG_IP,0xee00)
q.u.hook_add(UC_HOOK_CODE,skip_file,begin=0x10000+symbols['STORE_OPTIONS'],end=0x10000+symbols['STORE_OPTIONS'])
for ah in (0x80,0x82,0x86,0x87,0x88,0x89,0x8a,0x8b,0x95):
 q.word('DISPLAY_EPOCH',123)
 q.u.mem_write(0x10000+symbols['ROW_CACHED_ID'],bytes([3,7,11,15]))
 q.u.mem_write(0x10000+symbols['ROW_IMAGE_VALID'],bytes([1])*25)
 q.call('API_CACHE_TEST',ax=ah<<8,bx=0,ds=0x1000)
 assert int.from_bytes(q.u.mem_read(0x10000+symbols['DISPLAY_EPOCH'],2),'little')==123,ah
 assert q.u.mem_read(0x10000+symbols['ROW_CACHED_ID'],4)==bytes([3,7,11,15]),ah
 assert q.u.mem_read(0x10000+symbols['ROW_IMAGE_VALID'],25)==bytes([1])*25,ah
for ah in (0x81,0x83):
 q.word('DISPLAY_EPOCH',123)
 q.call('API_CACHE_TEST',ax=ah<<8,bx=0,ds=0x1000)
 assert int.from_bytes(q.u.mem_read(0x10000+symbols['DISPLAY_EPOCH'],2),'little')==124,ah
 assert q.u.mem_read(0x10000+symbols['ROW_CACHED_ID'],4)==bytes([255])*4,ah
 assert q.u.mem_read(0x10000+symbols['ROW_IMAGE_VALID'],25)==bytes(25),ah
print('PASS: custom API queries/save-options retain cache; config/colour setters invalidate all slots')
