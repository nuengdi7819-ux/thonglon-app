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

# ใช้ลิงก์เชื่อมต่อฐานข้อมูล Supabase โดยตรงสำหรับรันบนเครื่อง
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:thonglon789@db.rzgtdsobqpnbbtvuuyp.supabase.co:5432/postgres"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# (วางโค้ดส่วน Model ตารางฐานข้อมูล และ Route หน้าเว็บอื่นๆ ของคุณต่อจากตรงนี้ได้เลยครับ)

if __name__ == "__main__":
    app.run(debug=True, port=5000)