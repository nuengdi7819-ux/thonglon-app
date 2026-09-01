from datetime import date, datetime
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

# เชื่อมต่อฐานข้อมูล Supabase PostgreSQL (อัปเดตลิงก์พอร์ตและการเชื่อมต่อให้สมบูรณ์)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:thonglon789@db.rzgtdsobqpnbbtvuyp.supabase.co:5432/postgres"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --- โมเดลตารางข้อมูลธุรกรรม ---
class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    principal = db.Column(db.Float, nullable=False, default=0.0)
    daily_interest = db.Column(db.Float, nullable=False, default=0.0)
    discount = db.Column(db.Float, nullable=False, default=0.0)
    sales_name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    paid_interest = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(50), nullable=False, default='ปกติ') # 'ปกติ', 'ตัดยอดบางส่วน', 'คืนแล้ว'

    def to_dict(self):
        today = date.today()
        start = self.start_date if isinstance(self.start_date, date) else datetime.strptime(str(self.start_date), '%Y-%m-%d').date()
        days_passed = max(0, (today - start).days)
        
        # คำนวณดอกเบี้ยสุทธิค้างชำระ
        gross_interest = days_passed * self.daily_interest
        accumulated_interest = max(0.0, gross_interest - self.paid_interest - self.discount)
        
        return {
            'id': self.id,
            'type': self.type,
            'customer_name': self.customer_name,
            'phone': self.phone or '-',
            'sales_name': self.sales_name,
            'start_date': start.strftime('%Y-%m-%d'),
            'principal': self.principal,
            'daily_interest': self.daily_interest,
            'discount': self.discount,
            'paid_interest': self.paid_interest,
            'days_passed': days_passed,
            'accumulated_interest': accumulated_interest,
            'status': self.status
        }

# สร้างตารางในฐานข้อมูลอัตโนมัติหากยังไม่มี
with app.app_context():
    db.create_all()

# --- ฟังก์ชันช่วยเตรียมข้อมูลครบถ้วนสำหรับ HTML ทุกหน้า ---
def get_dashboard_context(search_query=''):
    query = Transaction.query
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            (Transaction.customer_name.ilike(search_pattern)) | 
            (Transaction.phone.ilike(search_pattern))
        )
    
    all_tx_models = query.order_by(Transaction.id.desc()).all()
    transactions = [tx.to_dict() for tx in all_tx_models]
    
    # คำนวณยอดสรุปภาพรวม 3 กล่อง
    all_db_txs = Transaction.query.all()
    total_investment = sum(tx.principal for tx in all_db_txs if tx.status != 'คืนแล้ว')
    total_returned = sum(tx.principal for tx in all_db_txs if tx.status == 'คืนแล้ว')
    total_profit = sum(tx.paid_interest for tx in all_db_txs)
    
    # รายชื่อลูกค้า และ แผนที่เบอร์โทรศัพท์สำหรับ JS Auto-fill
    all_customers = list(set(tx.customer_name for tx in all_db_txs if tx.customer_name))
    customer_phone_map = {}
    for tx in all_db_txs:
        if tx.customer_name and tx.phone:
            customer_phone_map[tx.customer_name] = tx.phone

    # รายชื่อเซลส์ผู้ดูแล
    preset_sales = ['เซลล์ 1', 'เซลล์ 2', 'เซลล์ 3']
    db_sales = list(set(tx.sales_name for tx in all_db_txs if tx.sales_name))
    sales_list = list(set(preset_sales + db_sales))

    return {
        'current_admin': session.get('user', 'nice'),
        'total_investment': total_investment,
        'total_returned': total_returned,
        'total_profit': total_profit,
        'all_customers': all_customers,
        'sales_list': sales_list,
        'customer_phone_map': customer_phone_map,
        'transactions': transactions,
        'search_query': search_query
    }

# --- ROUTES ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        tx_type = request.form.get('type')
        customer_name = request.form.get('customer_name')
        phone = request.form.get('phone')
        principal = float(request.form.get('principal', 0) or 0)
        daily_interest = float(request.form.get('daily_interest', 0) or 0)
        discount = float(request.form.get('discount', 0) or 0)
        sales_name = request.form.get('sales_name')

        new_tx = Transaction(
            type=tx_type,
            customer_name=customer_name,
            phone=phone,
            principal=principal,
            daily_interest=daily_interest,
            discount=discount,
            sales_name=sales_name,
            start_date=date.today(),
            paid_interest=0.0,
            status='ปกติ'
        )
        db.session.add(new_tx)
        db.session.commit()
        return redirect(url_for('index'))

    search_query = request.args.get('search', '')
    context = get_dashboard_context(search_query)
    return render_template('index.html', **context)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        session['user'] = username if username else 'nice'
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/sales_members')
def sales_members():
    search_query = request.args.get('search', '')
    context = get_dashboard_context(search_query)
    return render_template('sales_members.html', **context)

@app.route('/all_members')
def all_members():
    search_query = request.args.get('search', '')
    context = get_dashboard_context(search_query)
    return render_template('all_members.html', **context)

@app.route('/customer_summary')
def customer_summary():
    search_query = request.args.get('search', '')
    context = get_dashboard_context(search_query)
    return render_template('customer_summary.html', **context)

@app.route('/monthly_summary_page')
def monthly_summary_page():
    search_query = request.args.get('search', '')
    context = get_dashboard_context(search_query)
    return render_template('monthly_summary.html', **context)

@app.route('/update_payment/<int:tx_id>', methods=['POST'])
def update_payment(tx_id):
    tx = Transaction.query.get_or_404(tx_id)
    payment_type = request.form.get('payment_type')
    pay_amount = float(request.form.get('pay_amount', 0) or 0)

    if payment_type == 'full':
        tx.status = 'คืนแล้ว'
    elif payment_type == 'partial':
        tx.paid_interest += pay_amount
        tx.status = 'ตัดยอดบางส่วน'
    
    db.session.commit()
    return redirect(request.referrer or url_for('index'))

if __name__ == "__main__":
    app.run(debug=True, port=5000)