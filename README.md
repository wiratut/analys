# Analyst Studio

เว็บแอป Data Analyst ที่เขียน frontend และ backend ด้วย Python / Reflex:
**Upload → Profile → Clean → Dashboard → Export** พร้อม Gemini insight แบบ optional

## Deploy บน Render

1. Push โปรเจกต์นี้ขึ้น GitHub
2. ใน Render เลือก **New → Blueprint** แล้วเชื่อม repository
3. ตรวจว่า plan เป็น **Free** แล้วกด Apply
4. ตั้ง `GEMINI_API_KEY` หากต้องการใช้ Gemini insights

ไฟล์ `Dockerfile` รัน frontend และ backend ของ Reflex ใน Web Service เดียวกัน
บนพอร์ตที่ Render กำหนด ส่วน `render.yaml` ตั้ง health check ไว้ที่ `/_health`.
บริการ Free อาจพักเมื่อไม่มีผู้ใช้ และ session ในหน่วยความจำจะหายเมื่อ service
restart หรือพักเครื่อง
