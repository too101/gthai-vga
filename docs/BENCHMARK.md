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
