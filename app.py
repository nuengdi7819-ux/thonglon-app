from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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

@app.route('/')
def index():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', current_admin=session.get('admin'))

@app.route('/members')
def members():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('members.html')

@app.route('/sales_members')
def sales_members():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('sales_members.html')

@app.route('/customer_summary')
def customer_summary():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('customer_summary.html')

@app.route('/monthly_summary')
def monthly_summary():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('monthly_summary.html')

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
    app.run(debug=True)