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

## รุ่น 3.31 — ผล screen benchmark เดิม (ถอนการอ้างอิง)

**ตรวจพบข้อผิดพลาดในตัววัดเมื่อ 29 ตุลาคม 2026:** screen profile ตั้ง BIOS mode 12h แต่ไม่ได้เปิด Graphics Controller register 6 เป็น 01h แบบไดรเวอร์ ทำให้ B800 ไม่อยู่ใน memory mapping ที่ต้องการ จึงไม่ยืนยันว่าข้อมูลที่อ่านมาวาดเป็นอักษร A ตามที่อธิบายไว้ ตัวเลขและไฟล์ดิบด้านล่างเก็บไว้เพื่อประวัติ **ไม่ใช้ยืนยันเปอร์เซ็นต์การเร่งของงานหน้าจอที่ระบุ** รุ่น 3.33 ใช้ตัววัดที่แก้ mapping และตรวจข้อมูลอ่านกลับแล้ว

ข้อผิดพลาดนี้ไม่เกี่ยวกับ glyph profile รุ่น 3.30 ที่เรียกรูทีนกับฟอนต์และ A000 โดยตรง


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

### English correction for 3.31

The original screen-profile percentages are withdrawn: the harness did not enable the driver's B800 VGA memory mapping, so it did not verify the stated ASCII workload. Raw historical data remains above for provenance. Use the corrected 3.33 measurements below. The separate 3.30 glyph profile is unaffected.

## รุ่น 3.33 — ช่องว่างเป็นชุด เทียบ baseline 3.32

ทดสอบ 29 ตุลาคม 2026 ใน DOSBox-X 2026.10.01, CPU จำลอง 386, core normal, fixed 10000 cycles ทุกกรณี ใช้ตัววัดที่แก้ GC06=01h แล้ว และอ่าน B800 กลับเพื่อตรวจว่าเตรียมข้อมูลได้จริง

แต่ละกรณีวาดใหม่ทั้งจอ 80×25 จำนวน 200 ครั้งต่อรอบ ทดสอบ 2 รอบได้ tick เท่ากันทั้งสองรอบทุกกรณี รวมเวลาล้าง VID_SAVE ก่อนวาดแต่ละครั้ง ปิดการตรวจกรอบและซ่อน cursor เช่นเดียวกันทั้งก่อนและหลัง

| งาน | GTHAI ก่อน → หลัง (เวลาลดลง) | GTHAI386 ก่อน → หลัง (เวลาลดลง) |
|---|---|---|
| blank_long | 66 → 30 (54.5%) | 64 → 30 (53.1%) |
| blank_mixed | 69 → 40 (42.0%) | 67 → 40 (40.3%) |
| blank_alternating | 66 → 66 (0.0%) | 64 → 64 (0.0%) |
| ascii_control | 97 → 97 (0.0%) | 94 → 94 (0.0%) |

- blank_long: ช่องว่างทั้งจอ สีพื้นเดียวกัน
- blank_mixed: อักษร A หนึ่งตัว ตามด้วยช่องว่าง 15 ช่อง สีเดียวกัน
- blank_alternating: ช่องว่างทั้งจอ สลับสีพื้นทุกช่อง ใช้ทางเดิมโดยอัตโนมัติ
- ascii_control: อักษร A เต็มจอ เป็นกรณีควบคุมที่ไม่ใช้เส้นทางช่องว่าง

ตัวเลขเป็น BIOS tick และเปอร์เซ็นต์เวลาที่ลดลง ไม่ใช่ FPS และไม่ใช่ผลบน CPU/การ์ด VGA จริง ข้อมูลดิบและ hash ของ source อยู่ใน [dosbox-blanks-3.33.json](benchmarks/dosbox-blanks-3.33.json)

### เรียกซ้ำ

```powershell
python tools/benchmark_dosbox.py --assembler C:\tools\jwasm.exe --dosbox C:\DOSBox-X\dosbox-x.exe --profile blanks --repetitions 2 --work-dir work/benchmark-blanks
```

เทียบกับ ASM รุ่นก่อนโดยใช้ --source และแยก --work-dir; baseline ที่ใช้ในครั้งนี้เป็น GTHAI.ASM จาก commit ก่อนแก้ โดยยังใช้ include ปัจจุบันซึ่งเปลี่ยนเฉพาะหมายเลขรุ่นในส่วนที่เกี่ยวข้อง คำสั่งของ baseline ไม่ได้รับการปรับ batch ช่องว่าง

### ข้อแลกเปลี่ยน

ไม่เปลี่ยนกฎนับช่องว่างสำหรับชดเชยสระ การแยกสีทำในขั้นวาดเท่านั้น ใช้การเขียนแบบไบต์ทั้ง 19 แถวและรักษาการวนข้าม 64 KB; foreground ต่างกันไม่ต้องแยกชุด ถ้าสองช่องแรกมีสีพื้นต่างกันจะใช้ลูปเดิมทั้งช่วง เป็นการเลือกแบบอนุรักษ์นิยม จึงอาจพลาดประโยชน์ของช่วงสีเดียวกันที่ตามมาภายหลัง

รักษา PUSHF/CLI/POPF แต่ขอบเขตปิด interrupt ของชุดยาวอาจครอบ 80×19 byte stores แทนหนึ่งตัวอักษร ยังไม่ได้วัด interrupt latency บนเครื่องจริง

### English summary for 3.33

With the corrected B800 mapping and verified workload data, long uniform blank-screen redraws took 54.5% less time in GTHAI and 53.1% less in GTHAI386 versus 3.32. The A-plus-spaces workload improved by 42.0% and 40.3%, respectively. Alternating backgrounds and ASCII-only controls had unchanged BIOS tick counts. Results are emulator measurements, not hardware timings.

## รุ่น 3.34 — พักแถวใน RAM เทียบ baseline 3.33

ทดสอบ 29 ตุลาคม 2026, DOSBox-X/core normal/CPU 386/fixed 10000 cycles ใช้ B800 mapping และตรวจ readback เช่นเดียวกับ 3.33 วาดใหม่ 200 ครั้งต่อกรณี ทดสอบ 2 รอบได้ค่า tick ตรงกันทุกกรณี ไม่รวมการตรวจกรอบและซ่อน cursor

| งาน | GTHAI ก่อน → หลัง (tick / เวลา) | GTHAI386 ก่อน → หลัง (tick / เวลา) |
|---|---|---|
| row_ascii_same | 97 → 80 (ลด 17.5%) | 94 → 80 (ลด 14.9%) |
| row_ascii_foreground | 97 → 87 (ลด 10.3%) | 94 → 87 (ลด 7.4%) |
| row_ascii_background | 97 → 98 (เพิ่ม 1.0%) | 94 → 96 (เพิ่ม 2.1%) |
| row_thai | 103 → 98 (ลด 4.9%) | 98 → 93 (ลด 5.1%) |

- row_ascii_same: A เต็มจอ สี 07h
- row_ascii_foreground: A เต็มจอ สีอักษรวน 0–15 แต่สีพื้นเดิม
- row_ascii_background: A เต็มจอ สีพื้นสลับทุกช่อง เลือก direct path
- row_thai: วน ก + สระอิ + ไม้เอก + A สี 07h; ไม่ใช่ตัวแทนภาษาไทยทุกบริบท โดยเฉพาะรหัสที่ต้องกลับไปตรวจกรอบจริง

ทดสอบ profile ช่องว่างเดิมเพื่อดูต้นทุนที่เพิ่มจาก 3.33:

| งาน | GTHAI ก่อน → หลัง (tick / เวลา) | GTHAI386 ก่อน → หลัง (tick / เวลา) |
|---|---|---|
| blank_long | 30 → 30 (ลด 0.0%) | 30 → 30 (ลด 0.0%) |
| blank_mixed | 40 → 41 (เพิ่ม 2.5%) | 40 → 41 (เพิ่ม 2.5%) |
| blank_alternating | 66 → 67 (เพิ่ม 1.5%) | 64 → 65 (เพิ่ม 1.6%) |
| ascii_control | 97 → 80 (ลด 17.5%) | 94 → 80 (ลด 14.9%) |

ค่าที่เพิ่มเพียง 1–2 tick อยู่ใกล้ความละเอียด BIOS timer แต่ไม่ถือว่าพิสูจน์ว่าไม่มีต้นทุน ผลนี้แสดงข้อแลกเปลี่ยนของเงื่อนไขเลือกรูทีนและสถานะเพิ่ม ข้อมูลทั้งหมดเป็นผลในตัวจำลอง ไม่ใช่การ์ด VGA จริง

### วิธีและขอบเขตการป้องกัน interrupt

พักเพียงแถวที่เปลี่ยน ขนาด 160 ไบต์ พร้อมคำก่อน/หลังเป็น guard และคง offset SI เดิมด้วย segment alias กรณีสองช่องแรกเป็นช่องว่างหรือสีพื้นต่างกันใช้ทางตรง เงื่อนไขนี้อาจพลาดแถวที่มีข้อความหนาแน่นหลังช่องว่างนำหน้า แต่ลดต้นทุนในกรณีช่องว่างมาก

การไม่มี B800 read ระหว่าง glyph ไม่รับประกันว่า latch จะรอดจาก ISR อื่น จึงใช้ critical section กลุ่มไม่เกิน 8 glyph เท่านั้น และล้าง latch cache ก่อนคืน IF ไม่ปิด interrupt ครอบทั้งแถว กรณีช่องว่างยังใช้ critical section ของ blank run ตาม 3.33

classifiers ที่ต้องอ่านบริบทจริงจะจบ critical group และอ่าน B800 ตามเดิม; ไม่อ้างว่าเส้นทางภาษาไทย/กรอบทั้งหมดเลิกอ่าน B800 แล้ว การอ่านจอและตำแหน่ง cursor หลังจบแถวยังทำตามเดิม

ในแบบจำลอง VGA จอ A สีเดียวเต็ม 80×25 ใช้ GC OUT 1,003 ครั้ง แทนประมาณ 8,003 ครั้งของ batch 3.33 (ลดประมาณ 87.5%) แต่จำนวน OUT ที่ลดลงไม่เท่ากับเปอร์เซ็นต์เวลาที่ลดลง เนื่องจากมีงานสำเนาและจัดการสถานะเพิ่ม

```powershell
python tools/benchmark_dosbox.py --assembler C:\tools\jwasm.exe --dosbox C:\DOSBox-X\dosbox-x.exe --profile rows --repetitions 2 --work-dir work/benchmark-rows
```

ผลดิบพร้อม hash อยู่ใน [dosbox-rows-3.34.json](benchmarks/dosbox-rows-3.34.json) baseline 3.33 เป็น snapshot จากการทำข้อ 1 ก่อนหน้าที่ยังไม่ได้ commit; ใช้ include ปัจจุบันซึ่งเปลี่ยนข้อความเลขรุ่น แต่ไม่เปลี่ยนคำสั่งของ baseline

### English summary for 3.34

Eligible changed rows are staged in RAM. Latch reuse is limited to interrupt-masked groups of at most eight glyphs; the cache is invalidated before interrupts are restored, including when frame context must be read from B800. Compared with 3.33, uniform ASCII redraw time fell by 17.5% in GTHAI and 14.9% in GTHAI386. The tested Thai composition pattern improved by about 5%. Some alternating-background or sparse-text cases took 1–2 extra BIOS ticks. These are emulator results with a conservative row-selection heuristic.

## 3.35 — อัปเดตเฉพาะช่องที่ภาพเปลี่ยน

เทียบกับ snapshot 3.34 บน DOSBox-X, normal core, CPU 386, fixed 10,000 cycles เหมือนกันทั้งสองรุ่น วัด 2,000 updates ต่อกรณี ทำซ้ำ 2 รอบ ได้ค่าแต่ละรอบเท่ากัน หน่วยเป็น BIOS tick (ประมาณ 54.925 ms); ค่าน้อยกว่าเร็วกว่า

| กรณี | GTHAI 3.34 → 3.35 | GTHAI386 3.34 → 3.35 |
|---|---:|---:|
| เปลี่ยนอักษรอังกฤษหนึ่งช่อง | 41 → 32 | 37 → 28 |
| เปลี่ยนสีตัวอักษรหนึ่งช่อง | 41 → 32 | 37 → 28 |
| เปลี่ยนสระในข้อความไทยตัวอย่าง | 48 → 43 | 42 → 38 |
| เปลี่ยน 16 ช่อง ต้องวาดเต็มแถว | 41 → 44 | 37 → 40 |
| สลับช่องว่าง/อักษรในแถวเริ่มด้วยช่องว่าง | 22 → 22 | 17 → 18 |

อักษรอังกฤษเร็วขึ้น 22.0% / 24.3% และไทยตัวอย่าง 10.4% / 9.5% ตามลำดับ เป็นการแก้ซ้ำในแถวเดิม การวาดเริ่มต้นอยู่นอกช่วงจับเวลา แต่รวมการสร้างข้อมูลเปรียบเทียบครั้งแรก แถวไทยเก็บ descriptor 6 ไบต์ต่อช่อง รวม 480 ไบต์สำหรับแถวล่าสุด เมื่อสลับแถวหรือข้อมูลหมดอายุ ต้องจัดวางแถวเดิมเพิ่มหนึ่งรอบ จึงไม่ควรนำตัวเลขนี้ไปอ้างว่าเร็วขึ้นเท่ากันทุกหน้าจอ

เส้นทางวาดเต็มแถวมีต้นทุนตรวจเงื่อนไขเพิ่ม กรณีเปลี่ยน 16 ช่องช้าลงประมาณ 7.3% / 8.1% ในการทดสอบนี้ เป้าหมายของรุ่นนี้คือการแก้ข้อความจำนวนน้อย ไม่ใช่เร่งทุกกรณี

Regression เปลี่ยนอักษรอังกฤษหนึ่งช่องตรวจพบการเขียน VGA 20 ไบต์ เทียบกับ 1,530 ไบต์ของการวาดเต็มแถว และภาพทั้งสี่ plane ตรงกัน ตรวจกรณีผสมสระ วรรณยุกต์ การชดเชย 0/1/2/7 ช่อง สี การเปลี่ยนตัวเลือก กรอบ แรเงา และหน้าต่างแทรกระหว่างวาดด้วย

ผลดิบและ hash: [dosbox-partial-3.35.json](benchmarks/dosbox-partial-3.35.json) เป็นผลจำลอง ยังไม่มีผลวัดบนการ์ด VGA จริง

### English summary for 3.35

Eligible sparse edits redraw only changed output cells. Repeated single-cell edits in one row improved ASCII update time by 22–24% and the tested Thai pattern by about 10%. A 480-byte exact rendering-descriptor cache covers one complex row; cold or switched rows require extra layout work. Dense changes retain full-row rendering and incurred 7–8% overhead in this test. These are emulator measurements, not hardware results.

ทดสอบวาดใหม่ทั้งจอ 200 ครั้งต่อกรณี เพิ่มเติม (2 รอบ ค่าแต่ละรอบเท่ากัน):

| รูปแบบแถว | GTHAI 3.34 → 3.35 | GTHAI386 3.34 → 3.35 |
|---|---:|---:|
| อังกฤษสีเดียว | 80 → 85 | 80 → 84 |
| อังกฤษสลับสีตัวอักษร | 87 → 92 | 87 → 91 |
| อังกฤษสลับสีพื้น | 98 → 103 | 96 → 101 |
| ไทยผสมสระ–วรรณยุกต์ | 98 → 103 | 93 → 98 |

การวาดใหม่ทั้งจอจึงช้าลงประมาณ 4.6–6.3% จากงานตรวจเงื่อนไขเพิ่มเติม ผลดิบรวมอยู่ในไฟล์ 3.35 ข้างต้น

## 3.36 — ลด DIV ในการตรวจกรอบและแรเงา

แทนการหาร 160 สามจุดด้วยตารางต้นแถวขนาด 250 ไบต์ เทสต์จับคู่ครบ 4,000 byte offsets และชุดตรวจกรอบ/แรเงาเดิม ทั้งสองรุ่นยังใช้เกณฑ์ตรวจเดิม

ตัววัด `--profile frames` เรียก L4B7FH ที่ช่องกลางจอ 200,000 ครั้งต่อกรณี บนหน้า B0h หรือ B3h ทั้งจอ เปิด B800 mapping และตรวจข้อมูลที่เติมก่อนวัด CPU จำลอง 386, normal core, 10,000 cycles, 2 รอบ ได้ค่าซ้ำเท่ากัน หน่วย BIOS tick:

| กรณี | GTHAI 3.35 → 3.36 | GTHAI386 3.35 → 3.36 |
|---|---:|---:|
| ตรวจ shade B0h | 16 → 17 | 16 → 16 |
| ตรวจเส้นตั้ง B3h | 20 → 21 | 20 → 20 |

ผลนี้ยังไม่แสดงความเร็วเพิ่มบน 386 จำลอง: รุ่น 8086 ช้าลง 6.25% / 5% ในสองกรณี ส่วนรุ่น 386 เท่าเดิม ความละเอียดของ tick ไม่สามารถแยกความต่างเล็กกว่านี้ได้ ไม่ใช่ benchmark ของการวาดหน้าจอทั้งหมด และไม่ได้จับเวลา MARK_SHADE_HORIZONTAL โดยตรง

เป้าหมายคือเลี่ยงการหารที่แพงบน 8086 จริง แต่ยังไม่มีผลวัดเครื่อง 8086 ยืนยัน จึงไม่อ้างเปอร์เซ็นต์ความเร็วเพิ่มบนเครื่องจริง ผลดิบ: [dosbox-frames-3.36.json](benchmarks/dosbox-frames-3.36.json)

Version 3.36 replaces three divisions in frame/shading row-boundary checks with a 250-byte table. Exhaustive row mapping and rendering regressions pass. The emulated 386 microbenchmark showed no gain for GTHAI386 and a 5–6.25% slowdown for the 8086 build. Real 8086 performance remains unmeasured.

## 3.37 — MOVSD สำหรับแถวข้อความใน GTHAI386

เปลี่ยนสองจุดจาก 80 WORD เป็น 40 DWORD: สำเนา B800 ไป ROW_TEXT_BUFFER และสำรองแถวไป VID_SAVE ใช้ SI/DI/CX 16 บิตและไม่เปลี่ยนครึ่งบนของรีจิสเตอร์ GTHAI รุ่น 8086 คง MOVSW เดิม

ผล `--profile rows --target GTHAI386`, DOSBox-X normal/386/fixed 10,000 cycles, วาดใหม่ทั้งจอ 200 ครั้งต่อกรณี, 2 รอบได้ค่าเท่ากัน หน่วย BIOS tick:

| กรณี | 3.36 → 3.37 | เวลาลดลง |
|---|---:|---:|
| อังกฤษสีเดียว | 84 → 83 | 1.19% |
| อังกฤษสลับสีตัวอักษร | 91 → 90 | 1.10% |
| อังกฤษสลับสีพื้น | 101 → 100 | 0.99% |
| ไทยผสมสระ–วรรณยุกต์ | 98 → 97 | 1.02% |

เป็นผลต่างเพียงหนึ่ง tick ต่อชุดทดสอบ จึงควรสรุปเป็นประมาณ 1% ในงานที่ทดสอบ ไม่อ้างความเร็วบนเครื่องจริงหรือทุกสถานการณ์ ผลดิบและ hash: [dosbox-movsd-3.37.json](benchmarks/dosbox-movsd-3.37.json)

The 386 build now uses REP MOVSD for two 160-byte row copies, retaining 16-bit addressing/counts and preserving upper register halves. Full-screen redraw microbenchmarks improved by approximately 1% on the emulated 386. The 8086 build retains MOVSW; VGA writes and scrolling are unchanged.

## 3.38 — Batch สถานะ VGA ในโหมดไทย 8 บรรทัด

ใช้ `--profile thai8` เรียก UPDATE_SCREEN_THAI_8 โดยตั้ง DISPMODE=1 เปรียบเทียบกับ source snapshot 3.37 บน DOSBox-X normal/386/fixed 10,000 cycles เหมือนกันทั้งสอง executable วาดใหม่ทั้งจอ 200 ครั้งต่อกรณี ทำซ้ำ 2 รอบ ได้ค่าแต่ละรอบเท่ากัน หน่วย BIOS tick:

| กรณี | GTHAI 3.37 → 3.38 | GTHAI386 3.37 → 3.38 |
|---|---:|---:|
| อังกฤษสีเดียว | 121 → 109 (9.9%) | 119 → 107 (10.1%) |
| ไทยตัวอย่าง A1/D4/E8/ASCII | 124 → 112 (9.7%) | 122 → 110 (9.8%) |

ไทยตัวอย่างนี้วาดแต่ละช่องตามโหมด 8 บรรทัด ไม่มีการผสมสระ–วรรณยุกต์อัตโนมัติ ตัววัดเปิด B800 mapping และตรวจข้อมูลก่อนจับเวลา การลดจำนวน OUT ไม่เท่ากับเปอร์เซ็นต์ความเร็วที่เพิ่มขึ้น และยังไม่มีผลวัดบนการ์ดจริง

Regression วาดอักษรอังกฤษ 2,000 ช่องพบ GC OUT ลดจาก 14,000 เป็น 8,003 ครั้ง (42.8%) ตรวจภาพทุก plane และ VID_SAVE เทียบกับการบังคับวาดทีละตัว รวมสี ช่องว่าง cursor เคลื่อน/คงที่/ซ่อน และการสลับไปกลับกับ updater โหมด 25 บรรทัด หลังออก batch flags ต้องเป็นศูนย์และ GC ต้องกลับ mode 0 โดยปิด set/reset

ผลดิบและ hash: [dosbox-thai8-3.38.json](benchmarks/dosbox-thai8-3.38.json)

Thai 8-line mode now batches VGA register state while reseeding background latches for every glyph. It retains the original non-composing layout and flushes on every exit. Full-screen redraw tests improved by approximately 10% in both builds on the emulated 386; real-hardware performance remains unmeasured.

## 3.39 — ลดต้นทุนตรวจ partial redraw

แยก preflight ที่เก็บ AX เท่านั้นออกจากการเตรียม parser ตรวจแถวที่ไม่มีภาพอ้างอิงหรือเริ่มด้วยช่องว่างก่อน และตรวจเก้าช่องแรกแบบหยุดทันทีเมื่อพบช่องเดิม ถ้าทั้งเก้าช่องต่างกันย่อมเกินขีดจำกัดแปดช่อง จึงวาดเต็มแถวได้ทันที ส่วน BX/BP/DS เก็บเฉพาะตอนสร้าง descriptor แถวผสม

เปรียบเทียบกับ source snapshot 3.38 บน DOSBox-X normal/386/fixed 10,000 cycles, 2 รอบ ค่าแต่ละรอบเท่ากัน ใช้ `--profile rows` สำหรับวาดใหม่ทั้งจอ 200 ครั้ง และ `--profile partial` สำหรับแก้แถวเดิม 2,000 ครั้ง หน่วย BIOS tick

การทดสอบ partial ทั้งห้ากรณีได้เวลาเท่าเดิมทั้งสองรุ่นภายในความละเอียด tick ได้แก่ อังกฤษ เปลี่ยนสี ไทยผสม เปลี่ยน 16 ช่องกลางแถว และแถวเริ่มด้วยช่องว่าง กรณี 16 ช่องกลางแถวยังต้องตรวจละเอียด เพราะ probe ต้นแถวไม่ครอบคลุมบริเวณนั้น

เพิ่ม regression กรณี 8 ช่องแรกเปลี่ยนต้องเข้าการตรวจละเอียด ส่วน 9/80 ช่องแรกเปลี่ยนต้องข้าม โดยภาพทุก plane ตรงกับการวาดเต็มแถว รวมชุดเดิมด้านสระ วรรณยุกต์ การสลับ cache และหน้าต่างแทรก ยังไม่มีผลวัดบนเครื่องจริง

| วาดใหม่ทั้งจอ | GTHAI 3.38 → 3.39 | GTHAI386 3.38 → 3.39 |
|---|---:|---:|
| อังกฤษสีเดียว | 85 → 84 | 83 → 82 |
| อังกฤษสลับสีตัวอักษร | 92 → 90 | 90 → 89 |
| อังกฤษสลับสีพื้น | 103 → 102 | 100 → 99 |
| ไทยผสมสระ–วรรณยุกต์ | 103 → 102 | 97 → 96 |

วาดใหม่ทั้งจอเร็วขึ้น 1.0–2.2% ในชุดนี้ ลดได้บางส่วนของต้นทุนที่เพิ่มใน 3.35 ไม่ได้คืนความเร็วทั้งหมด ส่วน partial profile ทั้งห้ากรณีเวลาเท่าเดิม: GTHAI 32/32/43/44/22 ticks และ GTHAI386 27/27/37/39/17 ticks ตามลำดับกรณีอังกฤษ/สี/ไทย/16 ช่อง/ช่องว่าง ผลดิบและ hash: [dosbox-preflight-3.39.json](benchmarks/dosbox-preflight-3.39.json)

Version 3.39 reduces partial-redraw setup overhead with an early eligibility check, a bounded nine-cell dense-change probe, and narrower register saves. Full-screen redraw tests improved by 1.0–2.2%; all five sparse/dense-edit controls retained their previous tick counts. This recovers only part of the overhead introduced in 3.35. Measurements use an emulated 386, not real hardware.

## 3.40 — โหมด 8 บรรทัดและ cache แถวผสมสี่ช่อง

เทียบ source snapshot 3.39 กับ 3.40 บน DOSBox-X normal/386/fixed 10,000 cycles ทั้งสอง executable ทำซ้ำสองรอบ ค่าแต่ละรอบเท่ากัน หน่วย BIOS tick (ประมาณ 54.925 ms)

### โหมดไทย 8 บรรทัด

`--profile thai8` วาดใหม่ทั้งจอ 200 ครั้งต่อกรณี ตั้ง DISPMODE=1 ไม่ผสมสระ–วรรณยุกต์ เปิดและตรวจ B800 mapping ก่อนวัด

| กรณี | GTHAI 3.39 → 3.40 | GTHAI386 3.39 → 3.40 |
|---|---:|---:|
| อังกฤษสีเดียว | 109 → 109 | 107 → 108 |
| ไทย A1/D4/E8/ASCII แยกช่อง | 112 → 113 | 110 → 111 |
| ช่องว่างยาว | 94 → 32 | 92 → 32 |
| A ผสมช่องว่าง 15 ช่อง | 96 → 46 | 94 → 46 |
| ช่องว่างสีพื้นสลับ | 94 → 70 | 92 → 67 |

ช่องว่างยาวเร็วขึ้น 66.0% / 65.2%, แบบผสมเร็วขึ้น 52.1% / 51.1% และแบบสีพื้นสลับเร็วขึ้น 25.5% / 27.2% ตามลำดับ แถวตัวอักษรเต็มไม่เร็วขึ้นในตัวจำลองนี้ บางกรณีเพิ่มหนึ่ง tick (ประมาณ 0.9%) แม้การเดินจอต่อเนื่องจะลด DIV จาก 2,000 เป็น 25 ครั้ง จึงไม่อ้างว่าการลด DIV หรือใช้ CMPSD ทำให้ทุกกรณีเร็วขึ้น และยังไม่มีผลบน 8086 จริง

### cache แถวผสม

`--profile cache4` ทำ 2,000 รอบ แก้สระ D4/D8 หนึ่งช่องและอัปเดตทันทีทีละแถว รอบหนึ่งมี 4 updates สำหรับกรณีสี่แถว หรือ 2 updates สำหรับกรณีชนช่อง cache รวมการสร้าง cache ครั้งแรก แต่ไม่รวมวาดจอเริ่มต้น ห้ามเปรียบเทียบเวลาข้ามสองกรณีโดยไม่คิดจำนวน updates

| กรณี | GTHAI 3.39 → 3.40 | GTHAI386 3.39 → 3.40 |
|---|---:|---:|
| สลับแถว 3/12/21/22 คนละช่อง cache | 244 → 174 | 220 → 150 |
| สลับแถว 3/7 ชนช่อง cache | 122 → 122 | 110 → 111 |

สี่แถวคนละช่องเร็วขึ้น 28.7% / 31.8% เมื่อชนช่องไม่ได้ประโยชน์ และรุ่น 386 เพิ่มหนึ่ง tick ในชุดนี้ cache เป็น direct-mapped โดยใช้เลขแถว modulo four ไม่ใช่ LRU และไม่ได้รับประกันว่าแถวใด ๆ สี่แถวจะอยู่พร้อมกันได้ ข้อมูลภาพเพิ่ม 1,440 ไบต์ และข้อมูลกำกับเพิ่ม 21 ไบต์

### กรณีควบคุม partial redraw

เทียบกับผล final 3.39 (`--profile partial`, 2,000 updates ต่อกรณี): อังกฤษ/สี/ไทยแถวเดียว/ช่องว่างได้เวลาเท่าเดิมทั้งสองรุ่น ส่วน 16 ช่องกลางแถว GTHAI เท่าเดิมที่ 44 ticks และ GTHAI386 เพิ่มจาก 39 เป็น 40 ticks (2.6%) จึงมีต้นทุนเพิ่มเล็กน้อยนอกกรณี cache hit หลายแถว

Regression ตรวจตำแหน่งโหมด 8 บรรทัดครบ 2,000 ช่อง การวาดช่องว่างเทียบทีละช่องและทุก plane ขอบแถวและสี การเทียบ WORD คี่ทุกตำแหน่ง และการคง/ชน/ยกเลิก cache สี่ช่อง พร้อมชุดเดิมของ popup และการสลับโหมด ทั้งสอง executable ผ่าน

ผลดิบและ hash: [dosbox-multirow-3.40.json](benchmarks/dosbox-multirow-3.40.json) เป็นการทดสอบตัวจำลอง ไม่ใช่ผลบนการ์ด VGA จริง

Version 3.40 caches Thai-8 row coordinates, uses CMPSD for longer 386 comparison tails with an immediate-word fast path, groups row-bounded spaces, and expands composed-row descriptors to four direct-mapped cache slots. Long blank redraws improved by about 65–66%, and alternating edits across four non-colliding Thai rows by 29–32%. Dense character redraws showed no gain and some one-tick regressions. Colliding cache rows still rebuild; cache data grows by 1,461 bytes. Hardware timings remain unmeasured.

## 3.41 — ผสมภาพเมื่อเปลี่ยน, วาดเต็มแถวเฉพาะทาง และ LRU

เทียบ source snapshot 3.40 กับ 3.41 ใน DOSBox-X normal/386/fixed 10,000 cycles ทั้งสอง executable ทำซ้ำ 2 รอบ ทุกค่าซ้ำเท่ากัน หน่วย BIOS tick

### วาดใหม่ทั้งจอ

`--profile rows` วาดใหม่ทั้งจอ 200 ครั้งต่อกรณี ทาง RENDER_FULL_ROW สร้างจาก parser เดียวกันแต่ตัดเงื่อนไข descriptor และ deferred composition ออก ตัวตรวจ generator --check ป้องกันกฎจัดวางสองทางไม่ตรงกัน

| กรณี | GTHAI 3.40 → 3.41 | GTHAI386 3.40 → 3.41 |
|---|---:|---:|
| อังกฤษสีเดียว | 84 → 81 | 82 → 80 |
| อังกฤษสลับสีตัวอักษร | 91 → 88 | 89 → 87 |
| อังกฤษสลับสีพื้น | 102 → 99 | 99 → 97 |
| ไทยผสมสระ–วรรณยุกต์ | 102 → 99 | 96 → 93 |

เร็วขึ้นประมาณ 2.0–3.6% ในชุดนี้ เป็นผลรวมของการเปลี่ยนรุ่น ไม่ได้แยกจับเวลาเฉพาะแต่ละคำสั่ง

### แก้ข้อความทีละช่อง

`--profile partial` 2,000 updates ต่อกรณี เทียบกับผล final 3.40:

| กรณี | GTHAI 3.40 → 3.41 | GTHAI386 3.40 → 3.41 |
|---|---:|---:|
| อักษรอังกฤษ | 32 → 32 | 27 → 27 |
| สีตัวอักษร | 32 → 32 | 27 → 27 |
| สระในแถวไทย | 43 → 39 | 37 → 35 |
| เปลี่ยน 16 ช่องกลางแถว | 44 → 43 | 40 → 38 |
| แถวเริ่มด้วยช่องว่าง | 22 → 22 | 17 → 17 |

ไทยตัวอย่างเร็วขึ้น 9.3% / 5.4% ทาง partial สร้าง descriptor ก่อน ไม่ผสม bitmap จนกว่าจะพบว่าภาพเปลี่ยน เทสต์ยืนยันภาพเดิมมี COPY_GLYPH19/OR_GLYPH_ROWS เป็นศูนย์ ส่วน glyph ที่เปลี่ยนผสมและเขียน VGA ในช่วงป้องกัน interrupt เดียวกัน จากนั้นปล่อย group ก่อนคืน FLAGS

### LRU และ API query

`--profile cache4` 2,000 รอบ กรณี four มี 4 updates ต่อรอบ กรณี collision มี 2 และ query มี 1 รวมการสร้าง cache แรก แต่ไม่รวมการวาดจอเริ่มต้น

| กรณี | GTHAI 3.40 → 3.41 | GTHAI386 3.40 → 3.41 |
|---|---:|---:|
| สลับแถว 3/12/21/22 | 174 → 158 | 150 → 139 |
| สลับแถว 3/7 ที่เคยชน direct mapping | 122 → 79 | 111 → 70 |
| เรียก API 80h อ่านรุ่นก่อนแก้สระแต่ละครั้ง | 50 → 39 | 44 → 35 |

แถวที่เคยชน cache เร็วขึ้น 35.2% / 36.9% และ query ทุก update เร็วขึ้น 22.0% / 20.5% กรณี query เป็น workload เฉพาะโปรแกรมที่เรียก API บ่อย ไม่ใช่การพิมพ์ปกติ ผลเกิดจากทั้ง deferred composition และการรักษา cache ไม่ใช่เปอร์เซ็นต์ของ LRU เพียงอย่างเดียว

cache ยังมี 4 ช่อง แต่เป็น fully associative LRU เก็บสี่แถวใด ๆ ได้ เมื่อเพิ่มแถวที่ห้าแทนแถวที่ไม่ได้ใช้นานที่สุด เพิ่ม rank/hit metadata รวม 5 ไบต์ โค้ดเต็มไฟล์เพิ่มจาก 3.40 จำนวน 653 ไบต์ (GTHAI) / 636 ไบต์ (GTHAI386) ขนาด release 34,172 / 34,201 ไบต์

Regression ทั้งสองรุ่นผ่าน รวม glyph ผสมทุกชนิดใน classification table 15 glyphs, สระ/วรรณยุกต์/สี/translation, popup แทรก, LRU promotion/eviction, API query/save-options ไม่ยกเลิก cache และ setters ยกเลิกครบทุกช่อง การบันทึกไฟล์ของ API 82h ถูก stub เฉพาะในเทสต์ cache เพื่อไม่เขียนไฟล์จริง

ผลดิบและ hash: [dosbox-deferred-lru-3.41.json](benchmarks/dosbox-deferred-lru-3.41.json) ใช้ตัวจำลอง ยังไม่มีผลวัดเครื่องจริง

Version 3.41 defers composed bitmaps until a cell's exact descriptor changes, specializes full-row rendering from the shared parser, retains caches across API queries/save-options, and uses four fully associative LRU slots. Full redraws improved by 2.0–3.6%, single-row Thai edits by 5–9%, and edits alternating between formerly colliding rows by 35–37%. Frequent API-query workloads improved by 20–22%. These are combined-version emulator results; individual optimizations were not timed separately. LRU adds five metadata bytes, while total COM size grows by 653/636 bytes.
