from datetime import date
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "thonglon_secret_key_security"

# ใช้ลิงก์เชื่อมต่อฐานข้อมูล Supabase สำหรับรันระบบ
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:thonglon789@db.rzgtdsobqpnbbtvuyp.supabase.co:5432/postgres"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --- โค้ดส่วน Route หน้าเว็บ ---

@app.route('/')
def index():
    # ส่งไปที่หน้า index.html (หากมีไฟล์เทมเพลตอยู่ในโฟลเดอร์ templates)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # โค้ดจัดการการเข้าสู่ระบบ
    if request.method == 'POST':
        # รับค่าจากฟอร์มล็อกอินตามต้องการ
        pass
    return render_template('login.html')

# (สามารถวาง Model ตารางฐานข้อมูล หรือ Route อื่นๆ เพิ่มเติมตรงนี้ได้เลยครับ)

if __name__ == "__main__":
    app.run(debug=True, port=5000)