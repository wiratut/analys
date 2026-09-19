# Analyst Studio

เว็บแอป Data Analyst ที่เขียน frontend และ backend ด้วย Python / Reflex:
**Upload → Profile → Clean → Dashboard → Export** พร้อม Gemini insight แบบ optional

## เริ่มใช้งาน

ใช้ Python 3.11+ (ทดสอบด้วย 3.12) และ Node.js 20+ สำหรับ frontend ที่ Reflex สร้างให้
ไม่มี JavaScript ที่เขียนเองในโปรเจกต์

```bash
cd /home/asuka/Desktop/analys
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
reflex init
reflex run
```

เปิด **http://localhost:3000** (backend ใช้ port 8000) แล้วกด **Try sample dataset**
หรืออัปโหลด CSV หากในเครื่องนี้มี `.venv` และ `.web` ที่ติดตั้งแล้ว ใช้เพียง:

```bash
source .venv/bin/activate
REFLEX_DIR="$PWD/.reflex" REFLEX_USE_NPM=true reflex run
```

หน้า Upload ตั้ง Encoding และตัวคั่นเป็น Auto ได้: ตรวจ UTF-8, UTF-16/UTF-32
ที่มี BOM และ fallback ภาษาไทย Windows-874/TIS-620; รองรับ comma, semicolon,
Tab, pipe และบรรทัด `sep=;` ของ Excel หากภาษาเพี้ยนให้เลือก encoding เอง
(รวม Windows-1252 และ UTF-16 LE/BE ที่ไม่มี BOM) แล้วอัปโหลดใหม่
การเดา encoding ไม่แน่นอนเสมอไป จึงแสดง encoding/ตัวคั่นที่ใช้หลังนำเข้า
หากจำนวนช่องผิดหรือเครื่องหมายคำพูดไม่ครบ ระบบระบุบรรทัดจริงในไฟล์
และไม่ข้ามแถวที่ผิดทิ้ง หากอัปโหลดไม่สำเร็จ ข้อมูลเดิมใน session ยังอยู่

บน Debian/Ubuntu ถ้าไม่มี venv หรือ libraries ของ WeasyPrint:

```bash
sudo apt install python3-venv libpango-1.0-0 libpangoft2-1.0-0 fonts-noto-core
```

ฟอนต์ Noto Sans Thai ช่วยให้ชื่อคอลัมน์ภาษาไทยและ insight ใน PDF อ่านได้ครบ
การติดตั้ง frontend ครั้งแรกต้องใช้อินเทอร์เน็ต Reflex จะจัดการ React/Tailwind ให้เอง
ตั้ง `REFLEX_USE_NPM=true` เพื่อใช้ npm ที่มีอยู่แทนการติดตั้ง Bun
โปรเจกต์ตั้งค่า backend ให้ใช้ Uvicorn และปิดการตรวจเวอร์ชันออนไลน์ตอนเริ่มระบบ
โดยเก็บข้อมูล session ในหน่วยความจำของ backend เพียง process เดียว

## Gemini (ไม่จำเป็นต่อฟีเจอร์อื่น)

คัดลอก `.env.example` เป็น `.env` แล้ว **ใส่ key ด้วยตัวเอง**:

```bash
cp .env.example .env
```

`.env.example` มีเพียง `GEMINI_API_KEY=your_api_key_here` ไม่ได้บรรจุ key จริง
`.env` อยู่ใน `.gitignore` และไม่มี input ให้บันทึก key บน browser

ชื่อโมเดลตั้งผ่าน environment variable `GEMINI_MODEL` ได้ ค่าเริ่มต้นคือ
`gemini-2.5-flash-lite` เนื่องจาก Gemini 2.0 Flash/Flash-Lite ยุติบริการแล้ว
ตรวจโมเดลและ free-tier quota ที่บัญชีของคุณใช้งานได้ก่อนเปิด AI:
[Google model lifecycle](https://ai.google.dev/gemini-api/docs/deprecations),
[Google API pricing](https://ai.google.dev/gemini-api/docs/pricing)

กด **Generate insights** เพื่อส่งเฉพาะ summary statistics, correlations, trend
และชื่อ top categories ไป Google ไม่ส่ง row preview ผลลัพธ์เป็นข้อความภาษาไทย
ที่ติดป้าย AI แยกจากสถิติจริง พร้อม timeout และข้อความ fallback เมื่อไม่มี key,
โมเดลไม่พร้อม, rate limit หรือ API ล่ม ไม่มีการเรียก AI อัตโนมัติขณะ upload
การเปลี่ยนข้อมูลหรือตัวกรองที่ Apply จะล้าง insight เดิมเพื่อไม่ใช้สรุปที่ล้าสมัย

## วิธีทดลอง workflow

1. กด **Try sample dataset**: ข้อมูลยอดขาย 128 แถว 8 คอลัมน์ มี null,
   duplicates, ข้อความมีช่องว่าง, วันที่หลายรูปแบบ และ revenue outlier
2. หน้า **Profile** แสดง preview 30 แถว, schema, missing %, unique, mean,
   median, min, max, sample std, duplicate rows และ IQR outlier count
3. หน้า **Clean** เลือก action, method และ column แล้ว **Preview changes**
   เปรียบเทียบ before/after ก่อนกด **Apply changes**
4. ทดลอง trim customer/region, fill revenue ด้วย median, ลบ duplicate,
   parse order_date โดย Value=`mixed`, และ cap outlier
5. ใช้ **Undo** คืนข้อมูลและชนิดคอลัมน์ของ step ล่าสุด
6. ไป **Dashboard** เพื่อสร้างกราฟทุกคอลัมน์, เลือก category/date แล้ว Apply filters
   หรือเลือก X/Y ใน custom chart builder
7. ไป **Export** เพื่อดาวน์โหลด CSV, Excel หรือ PDF

### Cleaning actions

| กลุ่ม | วิธีที่รองรับ |
|---|---|
| Missing values | Drop rows, mean, median, mode, custom value, forward-fill |
| Duplicates | ทั้งแถวหรือคอลัมน์ที่เลือก; keep first/last หรือ remove all |
| Convert type | String, number, date; reject ค่าที่แปลงไม่ได้ |
| String cleaning | Trim, lowercase, uppercase, remove special characters, regex replace |
| Dates | Parse/standardize datetime UTC; extract year/month/day |
| Outliers | IQR × 1.5: cap, remove, flag |
| Columns | Rename, drop, reorder, split, merge |
| Filter rows | `==`, `!=`, `>`, `>=`, `<`, `<=`, contains, is missing, not missing |

เลือกหลายคอลัมน์โดยคลิก chip ตามลำดับ ใช้กับ duplicate key, reorder และ merge
Rename/merge ใช้ Value เป็นชื่อใหม่; split ใช้ Value เป็น literal delimiter;
regex replace ใช้ Value เป็น pattern และ Replacement เป็นข้อความแทน
Forward-fill อาจเหลือ null ที่ต้นคอลัมน์ตามนิยามของวิธีนี้

### Dashboard และขอบเขต export

- Numeric → histogram, categorical → top 15 bar chart, date → daily row-count line
- Date auto-detection ใช้รูปแบบวันที่และสัดส่วนค่าที่ parse ได้ ≥90% ในตัวอย่าง 500 ค่า
  ไม่เปลี่ยน dtype ของ source data; แถววันที่ parse ไม่ได้จะไม่ถูกนับในกราฟวันที่
- Numeric ≥2 columns → Pearson correlation (ไม่ใช่การทดสอบนัยสำคัญทางสถิติ)
- Custom bar/line รวม Y ด้วย sum แยกตาม X; scatter จำกัด 5,000 non-null rows
- Dashboard filters ใช้กับ KPI, charts, AI summary และ PDF หลัง Apply เท่านั้น
- CSV/Excel ส่งออก **clean dataset ทั้งหมด** ไม่ใช้ dashboard filters
- PDF มี summary stats, กราฟหลักสูงสุด 8 กราฟ (รวม custom/correlation เมื่อมี),
  pipeline, filter context และ AI insight ที่สร้างสำเร็จ
- PDF ใช้ Matplotlib วาดจาก chart data ชุดเดียวกับ Plotly แล้วประกอบด้วย WeasyPrint
  จึงไม่ต้องติดตั้ง Chrome/Kaleido สำหรับ export
- Excel เก็บข้อความขึ้นต้น `=` เป็นข้อความ; CSV คงค่าต้นฉบับสำหรับ round-trip

## โครงสร้าง

```text
analys/
├── rxconfig.py
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── analyst_studio/
│   ├── analyst_studio.py       # Reflex application
│   ├── state.py                # Session dataframe, preview, history, events
│   ├── components/             # Shared table, fields, cards, shell
│   ├── pages/                  # Upload / Profile / Clean / Dashboard / Export
│   ├── services/
│   │   ├── data.py             # CSV validation, DuckDB profile, filters
│   │   ├── cleaning.py         # Pure cleaning operations
│   │   ├── analytics.py        # Shared chart data, Plotly, AI summary
│   │   ├── insights.py         # Gemini with timeout/fallback
│   │   └── export.py           # CSV, Excel, PDF in memory
│   └── data/sample_sales.csv
├── tests/
└── docs/superpowers/            # Design and implementation notes
```

## Session และขนาดข้อมูล

DataFrame, undo snapshots และ pending preview เป็น backend-only Reflex State vars
(`_df`, `_snapshots`, `_pending_df`) ใช้ memory state manager ไม่มี database,
ไม่มีการเขียนไฟล์ upload/export ลงดิสก์ ไม่มี Cookie/LocalStorage/SessionStorage
สำหรับเก็บข้อมูล dataset หรือ pipeline ของแอป Reflex ใช้ session token ของ framework
เพื่อผูกการเชื่อมต่อ browser กับ state; ปิด browser แล้ว state อาจยังอยู่ใน RAM
จน timeout/restart ไม่ควรถือว่าข้อมูลจะถูกลบจาก RAM ทันทีที่ปิดแท็บ

ใช้ backend **หนึ่ง process/worker** เท่านั้น Session ไม่คงอยู่หลัง server restart
อัปโหลดไฟล์ใหม่จะแทนที่ session ปัจจุบันและล้าง history/insight
ข้อจำกัด: CSV 25 MiB, 200,000 rows, 150 columns; data+undo memory budget 512 MiB
แอปตั้งใจให้ใช้กับไฟล์ที่วิเคราะห์ใน RAM ได้ ไม่ใช่ distributed data platform

## ทดสอบ

```bash
pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall -q analyst_studio rxconfig.py
```

Tests ตรวจ CSV validation, cleaning, data types, input nonmutation, undo/session
isolation, filters, charts, CSV/Excel round-trip, PDF text/images และ AI fallback
การเรียก Gemini จริงต้องตั้ง key เอง และไม่ได้จำเป็นต่อชุดทดสอบ
