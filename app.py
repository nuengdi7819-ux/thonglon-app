from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import traceback

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///thonglon.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

VALID_USERS = {
    'nueng': '909090',
    'nice': '022540'
}

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    sales_name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    principal = db.Column(db.Float, nullable=False)      
    daily_interest = db.Column(db.Float, nullable=False)
    paid_interest = db.Column(db.Float, default=0.0)     
    status = db.Column(db.String(20), default='ปกติ')

with app.app_context():
    db.create_all()

# เลย์เอาต์หลักพร้อมแถบเมนูด้านข้าง
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - ทองล้น</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Prompt', sans-serif; background-color: #f8f9fa; }
        .sidebar { width: 260px; min-height: 100vh; background: #fff; border-right: 1px solid #dee2e6; position: fixed; }
        .main-content { margin-left: 260px; padding: 30px; }
        .nav-link { color: #333; font-weight: 500; padding: 10px 20px; border-radius: 6px; margin-bottom: 5px; }
        .nav-link:hover, .nav-link.active { background-color: #ffc107; color: #000; }
    </style>
</head>
<body>
    <div class="sidebar p-3 d-flex flex-column">
        <h4 class="text-warning fw-bold mb-4 px-2">🪙 ทองล้น.com</h4>
        <ul class="nav nav-pills flex-column mb-auto">
            <li class="nav-item"><a href="/" class="nav-link {% if page == 'dashboard' %}active{% endif %}">📊 Dashboard</a></li>
            <li><a href="/members" class="nav-link {% if page == 'members' %}active{% endif %}">👥 1. สมาชิกทั้งหมด</a></li>
            <li><a href="/sales_members" class="nav-link {% if page == 'sales' %}active{% endif %}">📋 2. สมาชิกภายใต้เซลล์</a></li>
            <li><a href="/customer_summary" class="nav-link {% if page == 'customer' %}active{% endif %}">📂 3. สรุป고객 / ลูกค้า</a></li>
            <li><a href="/monthly_summary" class="nav-link {% if page == 'monthly' %}active{% endif %}">📅 4. สรุปยอดรายเดือน</a></li>
        </ul>
        <hr>
        <a href="/logout" class="btn btn-outline-danger w-100">ออกจากระบบ</a>
    </div>
    <div class="main-content">
        <h2 class="mb-4 text-dark fw-bold">{% block header %}{% endblock %}</h2>
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    html = BASE_LAYOUT.replace('{% block header %}Dashboard{% endblock %}', 'Dashboard ภาพรวมระบบ')
    html = html.replace('{% block content %}{% endblock %}', '''
        <div class="row">
            <div class="col-md-12">
                <div class="card p-4 shadow-sm">
                    <h4>ยินดีต้อนรับเข้าสู่ระบบบริหารจัดการ ทองล้น</h4>
                    <p class="text-muted">เลือกเมนูด้านซ้ายเพื่อจัดการข้อมูลสมาชิก ยอดลงทุน และสรุปยอดประจำเดือนได้ทันทีครับ</p>
                </div>
            </div>
        </div>
    ''')
    return render_template_string(html, title="Dashboard", page="dashboard")

@app.route('/members')
def members():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    txs = Transaction.query.all()
    rows = "".join([f"<tr><td>{t.customer_name}</td><td>{t.phone or '-'}</td><td>{t.sales_name}</td><td>{t.principal:,.2f}</td><td>{t.status}</td></tr>" for t in txs])
    
    html = BASE_LAYOUT.replace('{% block header %}1. สมาชิกทั้งหมด{% endblock %}', 'รายชื่อสมาชิกทั้งหมด')
    html = html.replace('{% block content %}{% endblock %}', f'''
        <div class="card p-4 shadow-sm">
            <table class="table table-striped">
                <thead><tr><th>ชื่อลูกค้า</th><th>เบอร์โทร</th><th>เซลล์ผู้ดูแล</th><th>เงินต้น</th><th>สถานะ</th></tr></thead>
                <tbody>{rows if rows else "<tr><td colspan='5' class='text-center text-muted'>ยังไม่มีข้อมูลสมาชิก</td></tr>"}</tbody>
            </table>
        </div>
    ''')
    return render_template_string(html, title="สมาชิกทั้งหมด", page="members")

@app.route('/sales_members')
def sales_members():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    html = BASE_LAYOUT.replace('{% block header %}2. สมาชิกภายใต้เซลล์{% endblock %}', 'สมาชิกแยกตามรายชื่อเซลล์')
    html = html.replace('{% block content %}{% endblock %}', '''
        <div class="card p-4 shadow-sm">
            <p class="text-muted">แสดงข้อมูลสมาชิกแยกตามความรับผิดชอบของเซลล์แต่ละท่าน</p>
        </div>
    ''')
    return render_template_string(html, title="สมาชิกภายใต้เซลล์", page="sales")

@app.route('/customer_summary')
def customer_summary():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    html = BASE_LAYOUT.replace('{% block header %}3. สรุปข้อมูลลูกค้า{% endblock %}', 'สรุปข้อมูลลูกค้าและรายการ')
    html = html.replace('{% block content %}{% endblock %}', '''
        <div class="card p-4 shadow-sm">
            <p class="text-muted">หน้ารายละเอียดสรุปข้อมูลลูกค้า</p>
        </div>
    ''')
    return render_template_string(html, title="สรุปข้อมูลลูกค้า", page="customer")

@app.route('/monthly_summary')
def monthly_summary():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    html = BASE_LAYOUT.replace('{% block header %}4. สรุปยอดผลประกอบการรายเดือน{% endblock %}', 'สรุปยอดรายเดือน')
    html = html.replace('{% block content %}{% endblock %}', '''
        <div class="card p-4 shadow-sm">
            <table class="table table-bordered">
                <thead class="table-dark"><tr><th>ประจำเดือน (Year-Month)</th><th>จำนวนรายการ</th><th>ทุนที่ใช้เดือนนี้ (บาท)</th><th>กำไรเดือนนี้ (บาท)</th><th>ยอดรอเก็บรวม (บาท)</th></tr></thead>
                <tbody><tr><td colspan="5" class="text-center text-muted">ยังไม่มีข้อมูลสรุปยอดรายเดือน</td></tr></tbody>
            </table>
        </div>
    ''')
    return render_template_string(html, title="สรุปยอดรายเดือน", page="monthly")

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username in VALID_USERS and VALID_USERS[username] == password:
            session['admin'] = username
            return redirect(url_for('index'))
        else:
            error = 'ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง!'
            
    login_html = """
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <title>เข้าสู่ระบบ - ทองล้น</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap" rel="stylesheet">
        <style>body { font-family: 'Prompt', sans-serif; background-color: #f8f9fa; }</style>
    </head>
    <body class="d-flex align-items-center justify-content-center vh-100">
        <div class="card p-4 shadow" style="width: 380px;">
            <h3 class="text-center mb-4 text-warning fw-bold">🪙 ทองล้น</h3>
            {% if error %}<div class="alert alert-danger py-2 text-center">{{ error }}</div>{% endif %}
            <form method="POST">
                <div class="mb-3"><label class="form-label">ชื่อผู้ใช้งาน:</label><input type="text" name="username" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">รหัสผ่าน:</label><input type="password" name="password" class="form-control" required></div>
                <button type="submit" class="btn btn-warning w-100 fw-bold">เข้าสู่ระบบ</button>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(login_html, error=error)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)