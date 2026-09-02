from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///thonglon.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    sales_name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    initial_principal = db.Column(db.Float, nullable=False, default=0.0) # เงินต้นตั้งต้น
    principal = db.Column(db.Float, nullable=False)      # เงินต้นคงเหลือปัจจุบัน
    returned_principal = db.Column(db.Float, default=0.0) # เงินต้นที่คืนมาแล้ว
    daily_interest = db.Column(db.Float, nullable=False)
    paid_interest = db.Column(db.Float, default=0.0)     # ดอกเบี้ยที่จ่ายแล้ว (กำไรสะสม)
    status = db.Column(db.String(20), default='ปกติ')    # ปกติ, ตัดยอดบางส่วน, คืนแล้ว

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
    
    # คำนวณค่าต่างๆ แสดงในตารางแต่ละรายการ
    for tx in transactions:
        days = (today - tx.start_date).days
        if days < 1:
            days = 1  # ยืมและคืนภายในวันเดียวกัน คิดอย่างน้อย 1 วัน
        tx.days_passed = days
        
        # ดอกเบี้ยทั้งหมดที่ควรจะเป็นตั้งแต่วันเริ่ม - ดอกเบี้ยที่จ่ายไปแล้ว
        acc = (tx.daily_interest * days) - tx.paid_interest
        tx.accumulated_interest = acc if acc > 0 else 0.0

    # คำนวณกล่องสรุปภาพรวมด้านบนให้ถูกต้องตามหลักการ
    all_txs = Transaction.query.all()
    total_investment = sum(tx.principal for tx in all_txs if tx.status != 'คืนแล้ว') # เงินต้นคงเหลือที่ยังปล่อยกู้
    total_returned = sum(tx.returned_principal for tx in all_txs)                  # เงินต้นที่ลูกค้าทยอยคืนมาแล้ว
    total_profit = sum(tx.paid_interest for tx in all_txs)                         # กำไรสุทธิ = ดอกเบี้ยที่ได้รับจริงทั้งหมด

    # รายชื่อลูกค้าและแผนที่เบอร์โทร
    customers = db.session.query(Transaction.customer_name, Transaction.phone).distinct().all()
    all_customers = [c[0] for c in customers]
    customer_phone_map = {c[0]: c[1] for c in customers if c[1]}
    
    sales_list = ["เซลล์ A", "เซลล์ B", "เซลล์ C"] # ปรับเปลี่ยนตามรายชื่อเซลล์จริงของคุณ

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
        # ปิดบัญชี: จ่ายดอกเบี้ยที่ค้างทั้งหมด + เงินต้นคงเหลือทั้งหมด
        tx.paid_interest += total_acc_interest
        tx.returned_principal += tx.principal
        tx.principal = 0.0
        tx.status = 'คืนแล้ว'
    else:
        pay_amount = float(request.form.get('pay_amount', 0))
        
        # นำเงินที่จ่ายมา ไปตัดดอกเบี้ยค้างชำระก่อน
        if pay_amount >= total_acc_interest:
            remainder = pay_amount - total_acc_interest
            tx.paid_interest += total_acc_interest
            
            # เงินที่เหลือจากการตัดดอกเบี้ย นำไปลดเงินต้น และสะสมยอดเงินต้นที่คืนแล้ว
            if remainder > 0:
                if remainder > tx.principal:
                    remainder = tx.principal
                tx.principal -= remainder
                tx.returned_principal += remainder
        else:
            # จ่ายมาไม่พอตัดแม้แต่ดอกเบี้ย
            tx.paid_interest += pay_amount
            
        if tx.principal <= 0.01:
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

# (เส้นทางอื่นๆ เช่น login, sales_members, customer_summary, monthly_summary คงไว้ตามเดิมของคุณ)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)