from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///thonglon.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

# กำหนดรายชื่อผู้ใช้งานและรหัสผ่านที่ถูกต้อง
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

@app.route('/')
def index():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
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
        tx.days_passed = days
        
        acc = (tx.daily_interest * days) - tx.paid_interest
        tx.accumulated_interest = acc if acc > 0 else 0.0

    all_txs = Transaction.query.all()
    total_investment = sum(tx.principal for tx in all_txs if tx.status != 'คืนแล้ว')
    total_profit = sum(tx.paid_interest for tx in all_txs)
    total_returned = sum(tx.paid_interest for tx in all_txs)

    customers = db.session.query(Transaction.customer_name, Transaction.phone).distinct().all()
    all_customers = [c[0] for c in customers]
    customer_phone_map = {c[0]: c[1] for c in customers if c[1]}
    sales_list = ["เซลล์ A", "เซลล์ B", "เซลล์ C"]

    return render_template('index.html', 
                           transactions=transactions,
                           total_investment=total_investment,
                           total_returned=total_returned,
                           total_profit=total_profit,
                           all_customers=all_customers,
                           customer_phone_map=customer_phone_map,
                           sales_list=sales_list,
                           search_query=search_query,
                           current_admin=session.get('admin'))

@app.route('/update_payment/<int:tx_id>', methods=['POST'])
def update_payment(tx_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
        
    tx = Transaction.query.get_or_404(tx_id)
    payment_type = request.form.get('payment_type')
    
    today = datetime.now().date()
    days = (today - tx.start_date).days
    if days < 1:
        days = 1
        
    total_acc_interest = (tx.daily_interest * days) - tx.paid_interest
    if total_acc_interest < 0:
        total_acc_interest = 0.0

    if payment_type == 'full':
        tx.paid_interest += total_acc_interest
        tx.principal = 0.0
        tx.status = 'คืนแล้ว'
    else:
        pay_amount = float(request.form.get('pay_amount', 0))
        if pay_amount >= total_acc_interest:
            remainder = pay_amount - total_acc_interest
            tx.paid_interest += total_acc_interest
            if remainder > 0:
                tx.principal -= remainder
                if tx.principal < 0:
                    tx.principal = 0.0
        else:
            tx.paid_interest += pay_amount
            
        if tx.principal <= 0:
            tx.status = 'คืนแล้ว'
            tx.principal = 0.0
        else:
            tx.status = 'ตัดยอดบางส่วน'

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
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)