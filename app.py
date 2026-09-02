from flask import Flask, render_template_string, request, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from collections import defaultdict
import os
import io
import csv
import math

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'thonglon.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_thonglon_2026'
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
    last_payment_date = db.Column(db.Date, nullable=True)
    original_principal = db.Column(db.Float, nullable=False, default=0.0)
    principal = db.Column(db.Float, nullable=False)                      
    daily_interest = db.Column(db.Float, nullable=False)
    paid_interest = db.Column(db.Float, default=0.0)     
    status = db.Column(db.String(20), default='ปกติ')
    installment_amount = db.Column(db.Float, default=0.0)

with app.app_context():
    db.create_all()

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{{ title }} - ทองล้น</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Prompt', sans-serif; background-color: #fcf6f0; }
        .sidebar { width: 260px; min-height: 100vh; background: #2c0b0e; border-right: 2px solid #d4af37; position: fixed; top: 0; left: 0; z-index: 1050; transition: transform 0.3s ease-in-out; overflow-y: auto; color: #f8f9fa; }
        .main-content { margin-left: 260px; padding: 25px; transition: margin 0.3s ease-in-out; }
        .nav-link { color: #f1d3b2; font-weight: 500; padding: 10px 15px; border-radius: 6px; margin-bottom: 4px; font-size: 0.95rem; white-space: nowrap; }
        .nav-link:hover, .nav-link.active { background-color: #d4af37; color: #2c0b0e; font-weight: 600; }
        .sub-menu { padding-left: 25px; font-size: 0.9rem; color: #dfb182; }

        .mobile-header { display: none; background: #2c0b0e; border-bottom: 2px solid #d4af37; color: #fff; padding: 12px 15px; position: sticky; top: 0; z-index: 1040; }
        .sidebar-backdrop { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.5); z-index: 1045; }

        .btn-warning { background-color: #d4af37; border-color: #d4af37; color: #2c0b0e; font-weight: 600; }
        .btn-warning:hover { background-color: #b38f27; border-color: #b38f27; color: #fff; }

        @media (max-width: 992px) {
            .sidebar { transform: translateX(-100%); }
            .sidebar.show { transform: translateX(0); }
            .main-content { margin-left: 0; padding: 15px; }
            .mobile-header { display: flex; justify-content: space-between; align-items: center; }
            .sidebar-backdrop.show { display: block; }
        }
    </style>
</head>
<body>
    <div class="mobile-header shadow-sm">
        <div class="d-flex align-items-center gap-2">
            <button class="btn btn-outline-warning btn-sm" onclick="toggleSidebar()">☰ เมนู</button>
            <h5 class="text-warning fw-bold mb-0">🔱 ทองล้น.com</h5>
        </div>
        <div class="d-flex align-items-center gap-2">
            <span class="badge bg-warning text-dark">{{ session.get('admin') }}</span>
            <a href="/logout" class="btn btn-outline-danger btn-sm">ออก</a>
        </div>
    </div>

    <div class="sidebar-backdrop" id="sidebarBackdrop" onclick="toggleSidebar()"></div>

    <div class="sidebar p-3 d-flex flex-column shadow" id="sidebarMenu">
        <div class="d-flex justify-content-between align-items-center mb-2">
            <h4 class="text-warning fw-bold d-none d-lg-block">🔱 ทองล้น.com</h4>
            <h5 class="text-warning fw-bold d-lg-none">🔱 เมนูหลัก</h5>
            <button class="btn-close btn-close-white d-lg-none" onclick="toggleSidebar()"></button>
        </div>
        <div class="mb-3 px-2 d-none d-lg-block text-warning small border-bottom border-secondary pb-2">ผู้ใช้งาน: <b>{{ session.get('admin') }}</b></div>
        <ul class="nav nav-pills flex-column mb-auto">
            <li class="nav-item"><a href="/" class="nav-link {% if page == 'dashboard' %}active{% endif %}" onclick="toggleSidebar()">📊 Dashboard</a></li>
            <li><a href="/members" class="nav-link {% if page == 'members' %}active{% endif %}" onclick="toggleSidebar()">👥 1. สมาชิกทั้งหมด</a></li>
            <li><a href="/sales_members" class="nav-link {% if page == 'sales' %}active{% endif %}" onclick="toggleSidebar()">📋 2. สมาชิกภายใต้เซลล์</a></li>
            <li><a href="/customer_summary" class="nav-link {% if page == 'customer' %}active{% endif %}" onclick="toggleSidebar()">📂 3. สรุปลูกค้า</a></li>
            <li><a href="/customer_emergency" class="nav-link sub-menu {% if page == 'emergency' %}active{% endif %}" onclick="toggleSidebar()">🔸 3.1 เงินฉุกเฉิน</a></li>
            <li><a href="/customer_gold" class="nav-link sub-menu {% if page == 'gold' %}active{% endif %}" onclick="toggleSidebar()">🔸 3.2 ผ่อนทอง</a></li>
            <li><a href="/customer_debt" class="nav-link sub-menu {% if page == 'debt' %}active{% endif %}" onclick="toggleSidebar()">🔸 3.3 ยอดค้างเก่า</a></li>
            <li><a href="/monthly_summary" class="nav-link sub-menu {% if page == 'monthly' %}active{% endif %}" onclick="toggleSidebar()">📅 4. สรุปยอดรายเดือน</a></li>
        </ul>
        <hr class="border-secondary">
        <div class="d-flex flex-column gap-2">
            <a href="/export_data" class="btn btn-outline-warning btn-sm w-100">📥 สำรองข้อมูล (Backup)</a>
            <a href="/logout" class="btn btn-outline-danger w-100 d-none d-lg-block">ออกจากระบบ</a>
        </div>
    </div>
    
    <div class="main-content">
        <h2 class="mb-4 text-danger fw-bold fs-4">{% block header %}{% endblock %}</h2>
        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
    function toggleSidebar() {
        const sidebar = document.getElementById('sidebarMenu');
        const backdrop = document.getElementById('sidebarBackdrop');
        sidebar.classList.toggle('show');
        backdrop.classList.toggle('show');
    }

    function togglePayInput(id) {
        let selectElem = document.getElementById('payType' + id);
        let divElem = document.getElementById('amountDiv' + id);
        if (selectElem && divElem) {
            if (selectElem.value === 'full') {
                divElem.style.display = 'none';
            } else {
                divElem.style.display = 'block';
            }
        }
    }

    function handleTypeChange() {
        let typeVal = document.getElementById('txTypeSelect').value;
        let instDiv = document.getElementById('installmentDiv');
        if (typeVal === 'ยอดค้างเก่า') {
            instDiv.style.display = 'block';
        } else {
            instDiv.style.display = 'none';
        }
    }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'admin' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        try:
            p_val = float(request.form.get('principal', 0))
            custom_start_date = request.form.get('start_date')
            parsed_date = datetime.strptime(custom_start_date, '%Y-%m-%d').date() if custom_start_date else datetime.utcnow().date()
            current_sales = session.get('admin', 'unknown')
            d_interest = float(request.form.get('daily_interest', 0))
            tx_type = request.form.get('type')
            
            inst_amt = 0.0
            if tx_type == 'ยอดค้างเก่า':
                inst_amt = float(request.form.get('installment_amount', 0))

            new_tx = Transaction(
                type=tx_type,
                customer_name=request.form.get('customer_name'),
                phone=request.form.get('phone'),
                sales_name=current_sales,
                start_date=parsed_date,
                original_principal=p_val,
                principal=p_val,
                daily_interest=d_interest,
                installment_amount=inst_amt
            )
            db.session.add(new_tx)
            db.session.commit()
        except Exception as e:
            print("Error adding transaction:", e)
        return redirect(url_for('index'))

    search_query = request.args.get('search', '').strip()
    if search_query:
        transactions = Transaction.query.filter(
            (Transaction.customer_name.contains(search_query)) | 
            (Transaction.phone.contains(search_query))
        ).all()
    else:
        transactions = Transaction.query.all()

    today = datetime.now().date()
    for tx in transactions:
        days = (today - tx.start_date).days
        if days < 1:
            days = 1
        tx.days_passed = f"{days} วัน"
        acc = (tx.daily_interest * days) - tx.paid_interest
        tx.accumulated_interest = acc if acc > 0 else 0.0
        tx.total_paid = (tx.original_principal - tx.principal) + tx.paid_interest

    all_txs = Transaction.query.all()
    total_new_investment = sum(tx.original_principal for tx in all_txs if tx.type != 'ยอดค้างเก่า')
    total_debt_principal = sum(tx.principal for tx in all_txs if tx.type == 'ยอดค้างเก่า')
    total_new_principal = sum(tx.principal for tx in all_txs if tx.type != 'ยอดค้างเก่า')
    total_profit = sum(tx.paid_interest for tx in all_txs)

    rows = ""
    for tx in transactions:
        badge_color = 'bg-success'
        if tx.status == 'ตัดยอดบางส่วน':
            badge_color = 'bg-info text-dark'
        elif tx.status == 'คืนแล้ว':
            badge_color = 'bg-secondary'

        start_date_str = tx.start_date.strftime('%d/%m/%Y') if tx.start_date else '-'
        last_pay_str = tx.last_payment_date.strftime('%d/%m/%Y') if tx.last_payment_date else '-'

        display_daily_interest = f"{tx.daily_interest:,.2f}"
        display_days = tx.days_passed
        display_acc_interest = f"{tx.accumulated_interest:,.2f}"
        display_total_paid = f"{tx.total_paid:,.2f}"
        
        modal_body_content = f"""
                        <p class="text-muted mb-1">เงินต้นคงเหลือ: <b>{tx.principal:,.2f} บาท</b></p>
                        <p class="text-muted mb-3">ดอกเบี้ยสะสม: <b class="text-danger">{tx.accumulated_interest:,.2f} บาท</b></p>
                        <div class="mb-3">
                            <label class="form-label">เลือกประเภทการชำระ</label>
                            <select name="payment_type" class="form-select" id="payType{tx.id}" onchange="togglePayInput({tx.id})" required>
                                <option value="partial">จ่ายบางส่วน (ตัดดอกเบี้ย / ตัดต้น)</option>
                                <option value="full">คืนครบทั้งหมด (ปิดบัญชี)</option>
                            </select>
                        </div>
                        <div class="mb-3" id="amountDiv{tx.id}">
                            <label class="form-label">จำนวนเงินที่รับชำระจริง (บาท)</label>
                            <input type="number" step="any" name="pay_amount" class="form-control" placeholder="กรอกจำนวนเงิน">
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-danger">ส่วนลด (ถ้ามี / บาท)</label>
                            <input type="number" step="any" name="discount_amount" class="form-control" value="0" placeholder="กรอกส่วนลด">
                        </div>
        """

        rows += f"""
        <tr>
            <td>{tx.customer_name}</td>
            <td>{tx.phone or '-'}</td>
            <td><span class="badge bg-secondary">{tx.type}</span></td>
            <td>{start_date_str}</td>
            <td>{last_pay_str}</td>
            <td>{tx.original_principal:,.2f}</td>
            <td>{tx.principal:,.2f}</td>
            <td><strong class="text-primary">{display_total_paid}</strong></td>
            <td>{display_daily_interest}</td>
            <td>{display_days}</td>
            <td>{display_acc_interest}</td>
            <td><span class="badge {badge_color}">{tx.status}</span></td>
            <td>
                <div class="d-flex flex-column gap-2" style="width: 90px;">
                    <button type="button" class="btn btn-sm btn-warning w-100" data-bs-toggle="modal" data-bs-target="#payModal{tx.id}">จัดการยอด</button>
                    <a href="/delete_tx/{tx.id}" class="btn btn-sm btn-danger w-100" onclick="return confirm('ยืนยันการลบ?')">ลบ</a>
                </div>
            </td>
        </tr>

        <!-- Modal จัดการยอดชำระ -->
        <div class="modal fade" id="payModal{tx.id}" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <form action="/update_payment/{tx.id}" method="POST">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title">จัดการยอด: {tx.customer_name}</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            {modal_body_content}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">ยกเลิก</button>
                            <button type="submit" class="btn btn-warning">บันทึกการชำระ</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        """

    content = f"""
    <div class="row mb-4">
        <div class="col-md-3 mb-3">
            <div class="card p-3 shadow-sm text-white" style="background: linear-gradient(135deg, #004d99, #3399ff);">
                <h5>🔱 เงินลงทุนใหม่</h5>
                <h3>{total_new_investment:,.2f} บาท</h3>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card p-3 shadow-sm text-white" style="background: linear-gradient(135deg, #d97706, #f59e0b);">
                <h5>📂 ยอดค้างเก่าคงเหลือ</h5>
                <h3>{total_debt_principal:,.2f} บาท</h3>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card p-3 shadow-sm text-white" style="background: linear-gradient(135deg, #b30000, #ff4d4d);">
                <h5>💼 เงินต้นคงค้าง</h5>
                <h3>{total_new_principal:,.2f} บาท</h3>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card p-3 shadow-sm text-white" style="background: linear-gradient(135deg, #006622, #00b33c);">
                <h5>💰 กำไรสะสมทั้งหมด</h5>
                <h3>{total_profit:,.2f} บาท</h3>
            </div>
        </div>
    </div>

    <div class="card p-4 shadow-sm mb-4 border-warning">
        <h4 class="mb-3 fs-5 text-danger fw-bold">➕ เพิ่มรายการใหม่ (ผู้ดูแล: <span class="text-dark">{session.get('admin')}</span>)</h4>
        <form method="POST" class="row g-3">
            <div class="col-md-3">
                <label class="form-label">ประเภทรายการ</label>
                <select name="type" class="form-select" id="txTypeSelect" onchange="handleTypeChange()" required>
                    <option value="เงินฉุกเฉิน">เงินฉุกเฉิน (ลูกค้าใหม่)</option>
                    <option value="ผ่อนทอง">ผ่อนทอง (ลูกค้าใหม่)</option>
                    <option value="ยอดค้างเก่า">ยอดค้างเก่า (ลูกค้าเก่า)</option>
                </select>
            </div>
            <div class="col-md-3">
                <label class="form-label">ชื่อลูกค้า</label>
                <input type="text" name="customer_name" class="form-control" required>
            </div>
            <div class="col-md-3">
                <label class="form-label">เบอร์โทร</label>
                <input type="text" name="phone" class="form-control">
            </div>
            <div class="col-md-3">
                <label class="form-label">วันที่กู้/วันที่เริ่ม (ย้อนหลังได้)</label>
                <input type="date" name="start_date" class="form-control" value="{datetime.now().strftime('%Y-%m-%d')}" required>
            </div>
            <div class="col-md-4">
                <label class="form-label">ยอดเงินต้น/ยอดค้างทั้งหมด (บาท)</label>
                <input type="number" step="any" name="principal" class="form-control" required>
            </div>
            <div class="col-md-4" id="installmentDiv" style="display: none;">
                <label class="form-label text-danger fw-bold">ยอดชำระต่องวด (บาท)</label>
                <input type="number" step="any" name="installment_amount" class="form-control" value="0" placeholder="เช่น 150">
            </div>
            <div class="col-md-4">
                <label class="form-label">ดอกเบี้ย/วัน (บาท)</label>
                <input type="number" step="any" name="daily_interest" class="form-control" value="0" required>
            </div>
            <div class="col-md-4 d-flex align-items-end">
                <button type="submit" class="btn btn-success w-100 fw-bold">บันทึกข้อมูล</button>
            </div>
        </form>
    </div>

    <div class="card p-4 shadow-sm border-warning">
        <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
            <h4 class="mb-0 fs-5 text-danger fw-bold">📋 รายการทั้งหมด</h4>
            <form method="GET" class="d-flex">
                <input type="text" name="search" class="form-control form-control-sm me-2" placeholder="ค้นหาชื่อ หรือเบอร์โทร..." value="{search_query}">
                <button type="submit" class="btn btn-sm btn-outline-danger">ค้นหา</button>
            </form>
        </div>
        <div class="table-responsive">
            <table class="table table-striped align-middle text-nowrap">
                <thead class="table-dark">
                    <tr>
                        <th>ชื่อลูกค้า</th>
                        <th>เบอร์โทร</th>
                        <th>ประเภท</th>
                        <th>วันที่กู้</th>
                        <th>ชำระล่าสุด</th>
                        <th>เงินลงทุน</th>
                        <th>ต้นคงค้าง</th>
                        <th>ยอดที่ชำระมาแล้ว</th>
                        <th>ดอกเบี้ย/วัน</th>
                        <th>เวลาผ่านไป</th>
                        <th>ดอกเบี้ยสะสม</th>
                        <th>สถานะ</th>
                        <th>จัดการ</th>
                    </tr>
                </thead>
                <tbody>
                    {rows if rows else "<tr><td colspan='13' class='text-center text-muted'>ยังไม่มีข้อมูลรายการ</td></tr>"}
                </tbody>
            </table>
        </div>
    </div>
    """

    html = BASE_LAYOUT.replace('{% block header %}Dashboard{% endblock %}', '🔱 Dashboard บริหารจัดการระบบ')
    html = html.replace('{% block content %}{% endblock %}', content)
    return render_template_string(html, title="Dashboard", page="dashboard")

@app.route('/export_data')
def export_data():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Type', 'CustomerName', 'Phone', 'SalesName', 'StartDate', 'OriginalPrincipal', 'Principal', 'DailyInterest', 'PaidInterest', 'Status', 'InstallmentAmount'])
    
    txs = Transaction.query.all()
    for t in txs:
        cw.writerow([t.id, t.type, t.customer_name, t.phone, t.sales_name, t.start_date, t.original_principal, t.principal, t.daily_interest, t.paid_interest, t.status, t.installment_amount])
    
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8-sig'))
    output.seek(0)
    
    filename = f"thonglon_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name=filename)

@app.route('/update_payment/<int:tx_id>', methods=['POST'])
def update_payment(tx_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
        
    tx = Transaction.query.get_or_404(tx_id)
    payment_type = request.form.get('payment_type')
    today = datetime.now().date()
    discount_amt = float(request.form.get('discount_amount', 0))
    
    days = (today - tx.start_date).days
    if days < 1:
        days = 1
        
    total_acc_interest = (tx.daily_interest * days) - tx.paid_interest
    if total_acc_interest < 0:
        total_acc_interest = 0.0

    if payment_type == 'full':
        pay_amount = total_acc_interest
        discount_amt = 0.0
        tx.paid_interest += pay_amount
        tx.principal = 0.0
        tx.status = 'คืนแล้ว'
    else:
        pay_amount = float(request.form.get('pay_amount', 0))
        total_reduction = pay_amount + discount_amt
        
        if pay_amount >= total_acc_interest:
            interest_paid = total_acc_interest
            remainder = total_reduction - total_acc_interest
            tx.paid_interest += interest_paid
            if remainder > 0:
                tx.principal -= remainder
                if tx.principal < 0:
                    tx.principal = 0.0
        else:
            tx.paid_interest += pay_amount
            if discount_amt > 0:
                tx.principal -= discount_amt
                if tx.principal < 0:
                    tx.principal = 0.0
            
        if tx.principal <= 0:
            tx.status = 'คืนแล้ว'
            tx.principal = 0.0
        else:
            tx.status = 'ตัดยอดบางส่วน'

    tx.last_payment_date = today
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_tx/<int:tx_id>')
def delete_tx(tx_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    tx = Transaction.query.get_or_404(tx_id)
    db.session.delete(tx)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/members')
def members():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    txs = Transaction.query.all()
    rows = ""
    for t in txs:
        total_paid = (t.original_principal - t.principal) + t.paid_interest
        rows += f"""
        <tr>
            <td>{t.customer_name}</td>
            <td>{t.phone or '-'}</td>
            <td><span class="badge bg-danger">{t.sales_name}</span></td>
            <td><span class="badge bg-secondary">{t.type}</span></td>
            <td>{t.start_date.strftime('%d/%m/%Y') if t.start_date else '-'}</td>
            <td>{t.original_principal:,.2f}</td>
            <td>{t.principal:,.2f}</td>
            <td><strong>{total_paid:,.2f}</strong></td>
            <td>{t.status}</td>
        </tr>
        """
    
    content = f"""
    <div class="card p-4 shadow-sm border-warning">
        <h4 class="mb-3 fs-5 text-danger fw-bold">👥 รายชื่อสมาชิกทั้งหมด</h4>
        <div class="table-responsive">
            <table class="table table-striped text-nowrap align-middle">
                <thead class="table-dark">
                    <tr><th>ชื่อลูกค้า</th><th>เบอร์โทร</th><th>เซลล์ผู้ดูแล</th><th>ประเภท</th><th>วันที่กู้</th><th>เงินลงทุน</th><th>ต้นคงค้าง</th><th>ยอดที่ชำระมาแล้ว</th><th>สถานะ</th></tr>
                </thead>
                <tbody>{rows if rows else "<tr><td colspan='9' class='text-center text-muted'>ยังไม่มีข้อมูลสมาชิก</td></tr>"}</tbody>
            </table>
        </div>
    </div>
    """
    html = BASE_LAYOUT.replace('{% block header %}1. สมาชิกทั้งหมด{% endblock %}', 'สมาชิกทั้งหมด').replace('{% block content %}{% endblock %}', content)
    return render_template_string(html, title="สมาชิกทั้งหมด", page="members")

@app.route('/sales_members')
def sales_members():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    all_txs = Transaction.query.all()
    sales_data = {}
    for tx in all_txs:
        if tx.sales_name not in sales_data:
            sales_data[tx.sales_name] = []
        sales_data[tx.sales_name].append(tx)

    sales_content = ""
    for sales, txs in sales_data.items():
        sub_rows = ""
        for t in txs:
            total_paid = (t.original_principal - t.principal) + t.paid_interest
            sub_rows += f"""
            <tr>
                <td>{t.customer_name}</td>
                <td>{t.phone or '-'}</td>
                <td><span class="badge bg-secondary">{t.type}</span></td>
                <td>{t.start_date.strftime('%d/%m/%Y') if t.start_date else '-'}</td>
                <td>{t.original_principal:,.2f}</td>
                <td>{t.principal:,.2f}</td>
                <td><strong>{total_paid:,.2f}</strong></td>
                <td>{t.status}</td>
            </tr>
            """
        sales_content += f"""
        <div class="card mb-4 shadow-sm border-warning">
            <div class="card-header bg-danger text-white"><h5 class="mb-0 fs-6">🔱 เซลล์ผู้ดูแล: {sales}</h5></div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped text-nowrap align-middle">
                        <thead><tr><th>ชื่อลูกค้า</th><th>เบอร์โทร</th><th>ประเภท</th><th>วันที่กู้</th><th>เงินลงทุน</th><th>ต้นคงค้าง</th><th>ยอดที่ชำระมาแล้ว</th><th>สถานะ</th></tr></thead>
                        <tbody>{sub_rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
        """

    content = sales_content if sales_content else '<div class="card p-4 shadow-sm"><p class="text-muted text-center">ยังไม่มีข้อมูลสมาชิกภายใต้เซลล์</p></div>'
    html = BASE_LAYOUT.replace('{% block header %}2. สมาชิกภายใต้เซลล์{% endblock %}', 'สมาชิกแยกตามเซลล์').replace('{% block content %}{% endblock %}', content)
    return render_template_string(html, title="สมาชิกภายใต้เซลล์", page="sales")

@app.route('/customer_summary')
def customer_summary():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    txs = Transaction.query.all()
    customer_rows = ""
    for t in txs:
        start_str = t.start_date.strftime('%d/%m/%Y') if t.start_date else '-'
        total_paid = (t.original_principal - t.principal) + t.paid_interest
        customer_rows += f"""
        <tr>
            <td>{t.customer_name}</td>
            <td>{t.phone or '-'}</td>
            <td><span class="badge bg-danger">{t.sales_name}</span></td>
            <td>{t.type}</td>
            <td>{start_str}</td>
            <td>{t.original_principal:,.2f}</td>
            <td>{t.principal:,.2f}</td>
            <td><strong>{total_paid:,.2f}</strong></td>
            <td>{t.paid_interest:,.2f}</td>
            <td><span class="badge {'bg-success' if t.status=='ปกติ' else ('bg-info text-dark' if t.status=='ตัดยอดบางส่วน' else 'bg-secondary')}">{t.status}</span></td>
        </tr>
        """

    content = f"""
    <div class="card p-4 shadow-sm border-warning">
        <h4 class="mb-3 fs-5 text-danger fw-bold">📂 สรุปข้อมูลลูกค้าทั้งหมด</h4>
        <div class="table-responsive">
            <table class="table table-striped align-middle text-nowrap">
                <thead class="table-dark">
                    <tr>
                        <th>ชื่อลูกค้า</th>
                        <th>เบอร์โทร</th>
                        <th>เซลล์ผู้ดูแล</th>
                        <th>ประเภท</th>
                        <th>วันที่กู้</th>
                        <th>เงินลงทุน</th>
                        <th>ต้นคงค้าง</th>
                        <th>ยอดที่ชำระมาแล้ว</th>
                        <th>กำไรสะสม</th>
                        <th>สถานะ</th>
                    </tr>
                </thead>
                <tbody>
                    {customer_rows if customer_rows else "<tr><td colspan='10' class='text-center text-muted'>ยังไม่มีข้อมูลสรุปลูกค้า</td></tr>"}
                </tbody>
            </table>
        </div>
    </div>
    """
    html = BASE_LAYOUT.replace('{% block header %}3. สรุปลูกค้า{% endblock %}', 'สรุปลูกค้า').replace('{% block content %}{% endblock %}', content)
    return render_template_string(html, title="สรุปลูกค้า", page="customer")

@app.route('/customer_emergency')
def customer_emergency():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    txs = Transaction.query.filter_by(type='เงินฉุกเฉิน').all()
    customer_rows = ""
    for t in txs:
        start_str = t.start_date.strftime('%d/%m/%Y') if t.start_date else '-'
        total_paid = (t.original_principal - t.principal) + t.paid_interest
        customer_rows += f"""
        <tr>
            <td>{t.customer_name}</td>
            <td>{t.phone or '-'}</td>
            <td><span class="badge bg-danger">{t.sales_name}</span></td>
            <td>{start_str}</td>
            <td>{t.original_principal:,.2f}</td>
            <td>{t.principal:,.2f}</td>
            <td><strong>{total_paid:,.2f}</strong></td>
            <td>{t.paid_interest:,.2f}</td>
            <td><span class="badge {'bg-success' if t.status=='ปกติ' else ('bg-info text-dark' if t.status=='ตัดยอดบางส่วน' else 'bg-secondary')}">{t.status}</span></td>
        </tr>
        """

    content = f"""
    <div class="card p-4 shadow-sm border-warning">
        <h4 class="mb-3 fs-5 text-danger fw-bold">🔸 สรุปข้อมูลลูกค้า: เงินฉุกเฉิน (ลูกค้าใหม่)</h4>
        <div class="table-responsive">
            <table class="table table-striped align-middle text-nowrap">
                <thead class="table-dark">
                    <tr>
                        <th>ชื่อลูกค้า</th>
                        <th>เบอร์โทร</th>
                        <th>เซลล์ผู้ดูแล</th>
                        <th>วันที่กู้</th>
                        <th>เงินลงทุน</th>
                        <th>ต้นคงค้าง</th>
                        <th>ยอดที่ชำระมาแล้ว</th>
                        <th>กำไรสะสม</th>
                        <th>สถานะ</th>
                    </tr>
                </thead>
                <tbody>
                    {customer_rows if customer_rows else "<tr><td colspan='9' class='text-center text-muted'>ยังไม่มีข้อมูลเงินฉุกเฉิน</td></tr>"}
                </tbody>
            </table>
        </div>
    </div>
    """
    html = BASE_LAYOUT.replace('{% block header %}3.1 เงินฉุกเฉิน{% endblock %}', 'เงินฉุกเฉิน').replace('{% block content %}{% endblock %}', content)
    return render_template_string(html, title="เงินฉุกเฉิน", page="emergency")

@app.route('/customer_gold')
def customer_gold():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    txs = Transaction.query.filter_by(type='ผ่อนทอง').all()
    customer_rows = ""
    for t in txs:
        start_str = t.start_date.strftime('%d/%m/%Y') if t.start_date else '-'
        total_paid = (t.original_principal - t.principal) + t.paid_interest
        customer_rows += f"""
        <tr>
            <td>{t.customer_name}</td>
            <td>{t.phone or '-'}</td>
            <td><span class="badge bg-danger">{t.sales_name}</span></td>
            <td>{start_str}</td>
            <td>{t.original_principal:,.2f}</td>
            <td>{t.principal:,.2f}</td>
            <td><strong>{total_paid:,.2f}</strong></td>
            <td>{t.paid_interest:,.2f}</td>
            <td><span class="badge {'bg-success' if t.status=='ปกติ' else ('bg-info text-dark' if t.status=='ตัดยอดบางส่วน' else 'bg-secondary')}">{t.status}</span></td>
        </tr>
        """

    content = f"""
    <div class="card p-4 shadow-sm border-warning">
        <h4 class="mb-3 fs-5 text-danger fw-bold">🔸 สรุปข้อมูลลูกค้า: ผ่อนทอง (ลูกค้าใหม่)</h4>
        <div class="table-responsive">
            <table class="table table-striped align-middle text-nowrap">
                <thead class="table-dark">
                    <tr>
                        <th>ชื่อลูกค้า</th>
                        <th>เบอร์โทร</th>
                        <th>เซลล์ผู้ดูแล</th>
                        <th>วันที่กู้</th>
                        <th>เงินลงทุน</th>
                        <th>ต้นคงค้าง</th>
                        <th>ยอดที่ชำระมาแล้ว</th>
                        <th>กำไรสะสม</th>
                        <th>สถานะ</th>
                    </tr>
                </thead>
                <tbody>
                    {customer_rows if customer_rows else "<tr><td colspan='9' class='text-center text-muted'>ยังไม่มีข้อมูลผ่อนทอง</td></tr>"}
                </tbody>
            </table>
        </div>
    </div>
    """
    html = BASE_LAYOUT.replace('{% block header %}3.2 ผ่อนทอง{% endblock %}', 'ผ่อนทอง').replace('{% block content %}{% endblock %}', content)
    return render_template_string(html, title="ผ่อนทอง", page="gold")

@app.route('/customer_debt')
def customer_debt():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    txs = Transaction.query.filter_by(type='ยอดค้างเก่า').all()
    customer_rows = ""
    for t in txs:
        start_str = t.start_date.strftime('%d/%m/%Y') if t.start_date else '-'
        total_paid = t.original_principal - t.principal
        
        total_installments = 0
        remaining_installments = 0
        if t.installment_amount and t.installment_amount > 0:
            total_installments = math.ceil(t.original_principal / t.installment_amount)
            remaining_installments = math.ceil(t.principal / t.installment_amount)
            installment_info = f"{remaining_installments} / {total_installments} งวด"
        else:
            installment_info = "-"

        customer_rows += f"""
        <tr>
            <td>{t.customer_name}</td>
            <td>{t.phone or '-'}</td>
            <td><span class="badge bg-danger">{t.sales_name}</span></td>
            <td>{start_str}</td>
            <td>{t.original_principal:,.2f}</td>
            <td>{t.principal:,.2f}</td>
            <td><strong>{total_paid:,.2f}</strong></td>
            <td class="text-danger fw-bold">{installment_info}</td>
            <td>{t.paid_interest:,.2f}</td>
            <td><span class="badge {'bg-success' if t.status=='ปกติ' else ('bg-info text-dark' if t.status=='ตัดยอดบางส่วน' else 'bg-secondary')}">{t.status}</span></td>
        </tr>
        """

    content = f"""
    <div class="card p-4 shadow-sm border-warning">
        <h4 class="mb-3 fs-5 text-danger fw-bold">🔸 สรุปข้อมูลลูกค้า: ยอดค้างเก่า (ลูกค้าเก่า - แบ่งจ่ายเป็นงวด)</h4>
        <div class="table-responsive">
            <table class="table table-striped align-middle text-nowrap">
                <thead class="table-dark">
                    <tr>
                        <th>ชื่อลูกค้า</th>
                        <th>เบอร์โทร</th>
                        <th>เซลล์ผู้ดูแล</th>
                        <th>วันที่เริ่ม</th>
                        <th>ยอดค้างตั้งต้น</th>
                        <th>ยอดค้างคงเหลือ</th>
                        <th>เก็บเงินได้แล้ว</th>
                        <th>งวดคงเหลือ / ทั้งหมด</th>
                        <th>ยอดเก็บสะสมเข้ากำไร</th>
                        <th>สถานะ</th>
                    </tr>
                </thead>
                <tbody>
                    {customer_rows if customer_rows else "<tr><td colspan='10' class='text-center text-muted'>ยังไม่มีข้อมูลยอดค้างเก่า</td></tr>"}
                </tbody>
            </table>
        </div>
    </div>
    """
    html = BASE_LAYOUT.replace('{% block header %}3.3 ยอดค้างเก่า{% endblock %}', 'ยอดค้างเก่า').replace('{% block content %}{% endblock %}', content)
    return render_template_string(html, title="ยอดค้างเก่า", page="debt")

@app.route('/monthly_summary')
def monthly_summary():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    all_txs = Transaction.query.all()
    monthly_data = defaultdict(lambda: {'count': 0, 'new_investment': 0.0, 'debt_start': 0.0, 'profit': 0.0, 'new_paid': 0.0, 'debt_paid': 0.0})
    
    for tx in all_txs:
        if tx.start_date:
            ym = tx.start_date.strftime('%Y-%m')
            monthly_data[ym]['count'] += 1
            collected_amount = (tx.original_principal - tx.principal) + tx.paid_interest

            if tx.type == 'ยอดค้างเก่า':
                monthly_data[ym]['debt_start'] += tx.original_principal
                monthly_data[ym]['debt_paid'] += collected_amount
            else:
                monthly_data[ym]['new_investment'] += tx.original_principal
                monthly_data[ym]['new_paid'] += collected_amount

            monthly_data[ym]['profit'] += tx.paid_interest

    sorted_months = sorted(monthly_data.keys(), reverse=True)
    
    monthly_rows = ""
    for i, ym in enumerate(sorted_months):
        d = monthly_data[ym]
        total_collected = d['new_paid'] + d['debt_paid']
        
        diff_str = "-"
        if i + 1 < len(sorted_months):
            prev_ym = sorted_months[i + 1]
            prev_d = monthly_data[prev_ym]
            prev_total = prev_d['new_paid'] + prev_d['debt_paid']
            diff = total_collected - prev_total
            if prev_total > 0:
                pct = (diff / prev_total) * 100
                if diff >= 0:
                    diff_str = f'<span class="text-success">▲ +{diff:,.2f} (+{pct:.1f}%)</span>'
                else:
                    diff_str = f'<span class="text-danger">▼ {diff:,.2f} ({pct:.1f}%)</span>'
            else:
                diff_str = f'<span class="text-success">▲ +{diff:,.2f}</span>'

        monthly_rows += f"""
        <tr>
            <td><b>{ym}</b></td>
            <td>{d['count']} รายการ</td>
            <td class="text-primary">{d['new_investment']:,.2f}</td>
            <td class="text-success">{d['new_paid']:,.2f}</td>
            <td class="text-danger">{d['debt_start']:,.2f}</td>
            <td class="text-success">{d['debt_paid']:,.2f}</td>
            <td class="fw-bold">{total_collected:,.2f}</td>
            <td>{diff_str}</td>
            <td class="text-warning text-dark fw-bold">{d['profit']:,.2f}</td>
        </tr>
        """

    content = f"""
    <div class="card p-4 shadow-sm border-warning mb-4">
        <h4 class="mb-3 fs-5 text-danger fw-bold">📊 สรุปยอดผลประกอบการรายเดือน (เปรียบเทียบเชิงลึก)</h4>
        <div class="table-responsive">
            <table class="table table-bordered text-nowrap align-middle">
                <thead class="table-dark">
                    <tr>
                        <th>ประจำเดือน</th>
                        <th>รายการ</th>
                        <th>ทุนลูกค้าใหม่</th>
                        <th>เก็บลูกค้าใหม่ได้</th>
                        <th>ยอดค้างเก่าตั้งต้น</th>
                        <th>เก็บยอดค้างเก่าได้</th>
                        <th>รวมยอดเก็บได้ทั้งหมด</th>
                        <th>เปรียบเทียบ vs เดือนก่อน</th>
                        <th>กำไรสะสมรวม</th>
                    </tr>
                </thead>
                <tbody>
                    {monthly_rows if monthly_rows else "<tr><td colspan='9' class='text-center text-muted'>ยังไม่มีข้อมูลสรุปยอดรายเดือน</td></tr>"}
                </tbody>
            </table>
        </div>
    </div>
    """
    html = BASE_LAYOUT.replace('{% block header %}4. สรุปยอดผลประกอบการรายเดือน{% endblock %}', 'สรุปยอดรายเดือน').replace('{% block content %}{% endblock %}', content)
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
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>เข้าสู่ระบบ - ทองล้น</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Prompt', sans-serif; background: linear-gradient(135deg, #2c0b0e, #1a0507); color: #fff; }
            .card { background-color: #fff; color: #333; border: 2px solid #d4af37; }
        </style>
    </head>
    <body class="d-flex align-items-center justify-content-center vh-100 p-3">
        <div class="card p-4 shadow-lg w-100" style="max-width: 380px;">
            <h3 class="text-center mb-1 text-danger fw-bold">🔱 ทองล้น</h3>
            <p class="text-center text-muted small mb-4">ระบบบริหารจัดการการเงิน</p>
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
