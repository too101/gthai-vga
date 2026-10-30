# ผลทดสอบความเร็ว GTHAI / GTHAI386

ทดสอบรุ่น 3.30 ด้วย DOSBox-X 2026.10.01 เมื่อ 21 ตุลาคม 2026 โดยใช้ CPU จำลอง 386 เหมือนกันทั้งสองรุ่น, core `normal`, `cycles=fixed 10000` และเครื่อง `svga_s3` ค่า cycles นี้ไม่ใช่ความถี่ MHz ของเครื่องจริง

| งาน | จำนวนครั้งต่อรอบ | GTHAI (tick) | GTHAI386 (tick) | เวลาลดลง |
|---|---:|---:|---:|---:|
| คัดลอกฟอนต์ 19 แถว | 1,500,000 | 79 | 63 | 20.3% |
| ผสมพยัญชนะ + สระบน + วรรณยุกต์ | 750,000 | 108 | 83 | 23.1% |
| วาดอักษรอังกฤษ | 600,000 | 121 | 118 | 2.5% |
| ผสมและวาดอักษรไทย | 300,000 | 131 | 119 | 9.2% |

แต่ละงานทดสอบ 2 รอบ ได้จำนวน tick เท่ากันทั้งสองรอบ ตารางแสดงเวลาที่ลดลง `(เวลารุ่นปกติ − เวลารุ่น 386) / เวลารุ่นปกติ` ไม่ใช่อัตราเพิ่ม FPS

## รุ่นที่เปรียบเทียบ

- `output/GTHAI.COM`: ชุดคำสั่ง 8086 คัดลอกและผสมฟอนต์ด้วย WORD
- `output/GTHAI386.COM`: ชุดคำสั่ง 386 ใช้ DWORD ในส่วนฟอนต์และเลื่อนบิตหลายตำแหน่งในขั้นเตรียมสี โดยรักษา register ส่วนบน

ทั้งสองรุ่นยังใช้ VGA write mode 3 และเขียนภาพแบบไบต์เหมือนกัน ทดสอบทั้งคู่บน CPU จำลอง 386 เพื่อแยกผลของโค้ดจากความแตกต่างของ CPU

## วิธีทดสอบ

ใช้ `tools/benchmark_dosbox.py` สร้างโปรแกรมทดสอบจาก source เดียวกับรุ่นใช้งาน เปลี่ยนจุดเริ่มต้นให้เรียกรูทีนโดยตรงและเพิ่มตัวจับเวลา ไม่ติดตั้ง TSR และไม่แทนที่โปรแกรมที่ติดตั้งอยู่ เปิด DOSBox-X ใหม่แยกสำหรับแต่ละรุ่น โค้ดเดิมหลังคำสั่งกระโดดแรกจนจบ executable ตรวจแล้วตรงกับ release ทุกไบต์

จับเวลาด้วย BIOS tick (ประมาณ 54.925 มิลลิวินาทีต่อ tick) โดยเริ่มหลัง tick เปลี่ยน รวมค่าใช้จ่ายของลูป เตรียมพารามิเตอร์ และ interrupt ซึ่งใช้แบบเดียวกันทั้งสองรุ่น งานวาดเขียน VGA จริงในตัวจำลองซ้ำที่ตำแหน่งเดิม ใช้รูทีน `L62B3H` สำหรับอังกฤษ และ `DO_MSG` สำหรับไทย ส่วนงานผสมฟอนต์เรียก `COPY_GLYPH19` และ `OR_GLYPH_ROWS`

```powershell
python tools/benchmark_dosbox.py --assembler C:\tools\jwasm.exe --dosbox C:\DOSBox-X\dosbox-x.exe --scale 3 --repetitions 2
```

สคริปต์ใช้ Python บน Windows และไม่ต้องติดตั้ง dependency เพิ่ม ผลใหม่อยู่ที่ `work/benchmark/results.json` ผลรอบนี้เก็บไว้ที่ [dosbox-386-10000.json](benchmarks/dosbox-386-10000.json)

## การตีความ

รุ่น 386 ลดเวลาในส่วนคัดลอกและผสมฟอนต์ได้ชัดเจนในตัวจำลองนี้ ส่วนการวาดรวมได้ประโยชน์น้อยกว่า เพราะยังมีงานเตรียมและเขียน VGA ที่ใช้เส้นทางร่วมกัน ผลนี้เป็น microbenchmark ไม่รวมการสแกนหน้าจอทั้งหมด การตรวจกรอบ หรือการทำงานของโปรแกรม DOS อื่น จึงไม่ใช่อัตราเร่งของทั้งโปรแกรม

ความละเอียดของเวลาอยู่ที่หนึ่ง BIOS tick ผลอังกฤษต่างกันเพียง 3 tick จึงเป็นผลขนาดเล็ก ผลบน CPU และการ์ด VGA จริงอาจต่างจากนี้ ยังไม่ได้วัดบนเครื่องจริง

## English summary

On the same emulated 386 in DOSBox-X, GTHAI386 reduced elapsed time by 20.3% for glyph copying, 23.1% for Thai glyph composition, 2.5% for ASCII drawing, and 9.2% for composed Thai drawing. Both repetitions returned identical tick counts. These tests call individual routines and repeatedly draw to one screen cell; they do not measure whole-application performance or physical VGA hardware.

## รุ่น 3.31 — ใช้สถานะ VGA ร่วมและตรวจจอด้วย CMPSD

ทดสอบ 22 ตุลาคม 2026 ใน DOSBox-X ด้วย CPU จำลอง 386, core normal, fixed 10000 cycles เหมือนกันทุกตัว เทียบ source ก่อนแก้จาก commit `731512f` กับรุ่น 3.31 ทดสอบ 2 รอบ ผลดิบอยู่ที่ [dosbox-screen-3.31.json](benchmarks/dosbox-screen-3.31.json)

| โปรแกรม / งาน | จำนวนครั้งต่อรอบ | ก่อนแก้ (tick) | หลังแก้ (tick) | เวลาลดลง |
|---|---:|---:|---:|---:|
| GTHAI ตรวจจอเดิม | 5,000 | 24, 23 | 24, 23 | ไม่เปลี่ยน |
| GTHAI วาดใหม่ทั้งจอ | 500 | 244, 244 | 229, 229 | 6.1% |
| GTHAI386 ตรวจจอเดิม | 5,000 | 24, 23 | 12, 12 | 48.9% จากค่ามัธยฐาน |
| GTHAI386 วาดใหม่ทั้งจอ | 500 | 239, 239 | 224, 224 | 6.3% |

กรณีนี้เรียก `UPDATE_SCREEN_THAI_25` จริง เตรียมจอ 80×25 เป็นอักษร A สี 07h และซ่อน cursor กรณีตรวจจอเดิมใช้ข้อมูลตรงกับ buffer สำรอง กรณีวาดใหม่ล้าง buffer สำรองทั้ง 4,000 ไบต์ก่อนทุกครั้ง ซึ่งรวมเวลาล้างนี้ไว้ด้วย ปิดการตรวจกรอบสำหรับงานวัดนี้ (`CURRENT_MODE=0`) ผลจึงไม่ใช่การวัดโปรแกรม DOS ทั้งตัวหรือข้อความไทยที่ผสมหลายชั้น

ทั้งสองรุ่นลด OUT จาก 7 ครั้งต่อตัว เป็น 5 ครั้งสำหรับตัวแรก, 4 ครั้งสำหรับตัวต่อไป และคืนสถานะ 2 ครั้งเมื่อจบชุด จึงลดเวลาในงานวาดได้แม้ใช้คำสั่ง 8086 ส่วน CMPSD ช่วยงานตรวจจอของรุ่น 386 โดยเฉพาะ

ทุกตัวอักษรยังโหลด latch สีพื้นใหม่ เพราะการอ่าน B800 ระหว่างประมวลผลข้อความเปลี่ยน latch ได้ เมื่อวาดช่องว่าง/cursor หรือออกจากการอัปเดตจะคืนสถานะ VGA ส่วนการวาดเดี่ยวและ dialog ใช้เส้นทางที่คืนสถานะทุกครั้ง การปรับนี้ใช้กับโหมดไทย 25 บรรทัด

### เรียกทดสอบซ้ำ

```powershell
python tools/benchmark_dosbox.py --assembler C:\tools\jwasm.exe --dosbox C:\DOSBox-X\dosbox-x.exe --profile screen --repetitions 2 --work-dir work/benchmark-screen
```

ใช้ `--target GTHAI` หรือ `--target GTHAI386` เพื่อเลือกตัวเดียว และ `--source` เพื่อระบุไฟล์ ASM ก่อนแก้ สคริปต์ยังอ่าน GTHAI.INC และฟอนต์จากโครงการปัจจุบัน จึงต้องใช้ไฟล์ประกอบที่ตรงกับรุ่นที่ต้องการวัด สำหรับผลชุดนี้ include เปลี่ยนเฉพาะหมายเลขรุ่นจาก baseline โดยคำสั่งช่วยและฟอนต์ยังเหมือนเดิม

### English summary for 3.31

Both builds now share VGA register state during consecutive glyph rendering in Thai 25-line screen updates. On the same emulated 386, full-screen ASCII redraw time fell by 6.1% for GTHAI and 6.3% for GTHAI386 versus their respective previous builds. The 386 build also uses CMPSD and reduced unchanged-screen checking time by 48.9% using median BIOS ticks. These results exclude frame detection and are not physical-hardware measurements.

## Profile `scenarios` — สถานการณ์ใช้งานจริง (ยังไม่มีผลวัด)

ใช้เรียก `UPDATE_SCREEN_THAI_25` และ `SCRL_UP1` ของไดรเวอร์จริงกับหน้าจอที่สร้างแบบกำหนดผลได้จาก `tools/bench_scenarios.py` แต่ละกรณีโหลดหน้าจอของตัวเองก่อนจับเวลา ผลเป็น BIOS tick ในตัวจำลองเช่นเดียวกับ profile อื่น

| กรณี | งานต่อรอบ | จำนวนรอบ (×scale) |
|---|---|---:|
| `nc_full` | วาดใหม่ทั้งจอแบบ Norton Commander (กรอบคู่ แรเงา แถบ F-key) | 300 |
| `thai_full` | วาดใหม่ทั้งจอข้อความไทยผสมสระ/วรรณยุกต์/ตัวเลข | 300 |
| `blank_full` | วาดใหม่ทั้งจอช่องว่าง | 500 |
| `edit_cell` | หน้าจอแบบ editor สลับอักษรหนึ่งช่องแล้วอัปเดต | 5,000 |
| `cursor_move` | ขยับ cursor สลับสองตำแหน่งแล้วอัปเดต | 5,000 |
| `scroll_line` | `SCRL_UP1` เลื่อนจอหนึ่งบรรทัด | 200 |

```powershell
python tools/benchmark_dosbox.py --assembler C:\tools\jwasm.exe --dosbox C:\DOSBox-X\dosbox-x.exe --profile scenarios --repetitions 3 --work-dir work/benchmark-scenarios
```

- ใช้ `--source` ชี้ไปที่ ASM รุ่นเก่าและแยก `--work-dir` เพื่อเทียบรุ่น และใช้ `--scale` ปรับจำนวนรอบให้ได้อย่างน้อยหลายสิบ tick (จำนวนรอบเกิน 50,000 ต้องหาร 50,000 ลงตัว)
- `tests/verify_benchmark_scenarios.py` ตรวจใน Unicorn ว่าแต่ละกรณีทำงานตามที่ตั้งใจ (เข้าเส้นทางตรวจกรอบ/ผสมสระ, แก้ไม่เกินหนึ่งแถว, cursor ไม่แตะข้อความ, latch scroll ครบ) แต่ไม่ได้วัดเวลา
- จำนวนรอบเป็นค่าเริ่มต้นที่ยังไม่ได้ปรับกับ DOSBox-X ถ้ากรณีใดได้ 0 tick สคริปต์จะหยุดด้วย assertion ให้เพิ่ม `--scale`
- `nc_full` รอบแรกอาจยกเลิกการวาดเพื่อสแกนกรอบก่อน (พฤติกรรมของไดรเวอร์) ซึ่งเฉลี่ยหายไปเมื่อรอบมาก

### ผลวัด profile `scenarios` (รุ่น 3.32)

วัด 30 ตุลาคม 2026 ใน DOSBox-X, CPU จำลอง 386, fixed 10000 cycles, 3 รอบ ได้ค่าเท่ากันทุกรอบ ผลดิบอยู่ที่ [dosbox-scenarios-3.32.json](benchmarks/dosbox-scenarios-3.32.json)

| กรณี | GTHAI (ticks) | GTHAI386 (ticks) | เปลี่ยนแปลง |
|---|---:|---:|---:|
| nc_full (300 รอบ) | 141 | 138 | -2.1% |
| thai_full (300 รอบ) | 141 | 138 | -2.1% |
| blank_full (500 รอบ) | 235 | 230 | -2.1% |
| edit_cell (5,000 รอบ) | 24 | 12 | -50.0% |
| cursor_move (5,000 รอบ) | 26 | 14 | -46.2% |
| scroll_line (200 รอบ) | 18 | 18 | 0.0% |

ข้อสังเกต: วาดใหม่ทั้งจอใช้เวลาเท่ากันไม่ว่าเนื้อหาอะไร (ต้นทุนอยู่ที่การเขียนทีละไบต์) การแก้ทีละช่องและการขยับ cursor เสียเวลาไปกับการสแกนเทียบหน้าจอเป็นหลักซึ่งรุ่น 386 ลดลงครึ่งหนึ่ง และการเลื่อนจอเท่ากันทั้งสองรุ่น ผลนี้มาจากตัวจำลอง ไม่ได้วัดต้นทุนบัส VGA จริงหรือเครื่อง 8086 จริง
