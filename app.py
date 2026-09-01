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

# --- หน้าหลัก (Index) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # รับค่าบันทึกรายการใหม่จากฟอร์ม
        pass
    
    current_admin = session.get('user', 'Admin')
    total_investment = 0.0
    total_returned = 0.0
    total_profit = 0.0
    all_customers = []
    sales_list = ['เซลล์ 1', 'เซลล์ 2']
    customer_phone_map = {}
    transactions = []
    search_query = request.args.get('search', '')

    return render_template(
        'index.html',
        current_admin=current_admin,
        total_investment=total_investment,
        total_returned=total_returned,
        total_profit=total_profit,
        all_customers=all_customers,
        sales_list=sales_list,
        customer_phone_map=customer_phone_map,
        transactions=transactions,
        search_query=search_query
    )

# --- ระบบเข้าสู่ระบบ / ออกจากระบบ ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form.get('username')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# --- หน้าสมาชิกภายใต้เซลล์ ---
@app.route('/sales_members')
def sales_members():
    current_admin = session.get('user', 'Admin')
    sales_data = [] # ดึงข้อมูลสมาชิกแยกตามเซลล์จากฐานข้อมูล
    return render_template(
        'sales_members.html',
        current_admin=current_admin,
        sales_data=sales_data
    )

# --- หน้ารายชื่อสมาชิกทั้งหมด ---
@app.route('/all_members')
def all_members():
    current_admin = session.get('user', 'Admin')
    members_list = [] # ดึงรายชื่อสมาชิกทั้งหมด
    return render_template(
        'all_members.html',
        current_admin=current_admin,
        members_list=members_list
    )

# --- หน้าสรุปลูกค้า ---
@app.route('/customer_summary')
def customer_summary():
    current_admin = session.get('user', 'Admin')
    customer_summaries = [] # สรุปข้อมูลลูกค้ารายบุคคล
    return render_template(
        'customer_summary.html',
        current_admin=current_admin,
        customer_summaries=customer_summaries
    )

# --- หน้าสรุปยอดประจำเดือน ---
@app.route('/monthly_summary_page')
def monthly_summary_page():
    current_admin = session.get('user', 'Admin')
    monthly_data = [] # สรุปยอดรายเดือน
    return render_template(
        'monthly_summary.html',
        current_admin=current_admin,
        monthly_data=monthly_data
    )

# --- ฟังก์ชันจัดการยอดชำระ ---
@app.route('/update_payment/<int:tx_id>', methods=['POST'])
def update_payment(tx_id):
    payment_type = request.form.get('payment_type')
    pay_amount = request.form.get('pay_amount')
    # โค้ดอัปเดตยอดชำระลงฐานข้อมูล
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True, port=5000)