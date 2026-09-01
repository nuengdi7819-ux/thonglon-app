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

# --- โค้ดส่วน Route หน้าเว็บทั้งหมด ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # โค้ดตรวจสอบข้อมูลผู้ใช้จากฟอร์มและฐานข้อมูล Supabase
        pass
    return render_template('login.html')

@app.route('/sales-members')
def sales_members():
    # หน้าจัดการหรือแสดงข้อมูลสมาชิกฝั่งยอดขาย
    return render_template('sales_members.html')

@app.route('/all-members')
def all_members():
    # หน้าแสดงรายชื่อสมาชิกทั้งหมด
    return render_template('all_members.html')

@app.route('/customer-summary')
def customer_summary():
    # หน้าสรุปข้อมูลลูกค้า
    return render_template('customer_summary.html')

@app.route('/monthly-summary')
def monthly_summary():
    # หน้าสรุปยอดประจำเดือน
    return render_template('monthly_summary.html')

# (สามารถเพิ่ม Route อื่นๆ ต่อจากตรงนี้ได้เลยครับ)

if __name__ == "__main__":
    app.run(debug=True, port=5000)