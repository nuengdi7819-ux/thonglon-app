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

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:thonglon789@db.rzgtdsobqpnbbtvuyp.supabase.co:5432/postgres"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
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

@app.route('/sales_members')
def sales_members():
    current_admin = session.get('user', 'Admin')
    sales_data = []
    return render_template(
        'sales_members.html',
        current_admin=current_admin,
        sales_data=sales_data
    )

@app.route('/all_members')
def all_members():
    current_admin = session.get('user', 'Admin')
    members_list = []
    return render_template(
        'all_members.html',
        current_admin=current_admin,
        members_list=members_list
    )

@app.route('/customer_summary')
def customer_summary():
    current_admin = session.get('user', 'Admin')
    customer_summaries = []
    return render_template(
        'customer_summary.html',
        current_admin=current_admin,
        customer_summaries=customer_summaries
    )

@app.route('/monthly_summary_page')
def monthly_summary_page():
    current_admin = session.get('user', 'Admin')
    monthly_data = []
    return render_template(
        'monthly_summary.html',
        current_admin=current_admin,
        monthly_data=monthly_data
    )

@app.route('/update_payment/<int:tx_id>', methods=['POST'])
def update_payment(tx_id):
    payment_type = request.form.get('payment_type')
    pay_amount = request.form.get('pay_amount')
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True, port=5000)