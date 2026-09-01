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

# --- รวม Route ทั้งหมดให้ตรงกับหน้าเมนู HTML ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # รับค่าและตรวจสอบล็อกอิน
        pass
    return render_template('login.html')

@app.route('/sales_members') # รองรับทั้งแบบขีดล่างและขีดกลาง
@app.route('/sales-members')
def sales_members():
    return render_template('sales_members.html')

@app.route('/all_members')
@app.route('/all-members')
def all_members():
    return render_template('all_members.html')

@app.route('/customer_summary')
@app.route('/customer-summary')
def customer_summary():
    return render_template('customer_summary.html')

@app.route('/monthly_summary_page')
@app.route('/monthly-summary')
def monthly_summary():
    return render_template('monthly_summary.html')

if __name__ == "__main__":
    app.run(debug=True, port=5000)