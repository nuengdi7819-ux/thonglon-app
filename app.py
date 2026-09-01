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
import os

database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
  database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    database_url
    or "postgresql://postgres:thonglon789..@db.rzgtdsobqpnbbtvuuyp.supabase.co:5432/postgres"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Transaction(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  type = db.Column(db.String(50), nullable=False)
  customer_name = db.Column(db.String(100), nullable=False)
  phone = db.Column(db.String(20), default="-")
  principal = db.Column(db.Float, nullable=False)
  original_principal = db.Column(db.Float, nullable=False)
  daily_interest = db.Column(db.Float, default=0.0)
  discount = db.Column(db.Float, default=0.0)  # ดอกเบี้ยที่จ่ายแล้ว
  sales_name = db.Column(db.String(50), default="-")
  start_date = db.Column(db.Date, nullable=False, default=date.today)
  status = db.Column(db.String(20), default="ปกติ")


class WalletLog(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  action_type = db.Column(db.String(20), nullable=False)
  amount = db.Column(db.Float, nullable=False)
  note = db.Column(db.String(200), nullable=True)
  log_date = db.Column(db.Date, nullable=False, default=date.today)


with app.app_context():
  db.create_all()

USERS_DB = {
    "nice": {"password": "888", "display_name": "คุณไนซ์"},
    "nueng": {"password": "999", "display_name": "คุณหนึ่ง"},
}


@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    username = request.form.get("username").strip().lower()
    password = request.form.get("password").strip()
    if username in USERS_DB and USERS_DB[username]["password"] == password:
      session["user"] = USERS_DB[username]["display_name"]
      return redirect(url_for("index"))
    else:
      flash("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง!", "danger")
  return render_template("login.html")


@app.route("/logout")
def logout():
  session.clear()
  return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
def index():
  if "user" not in session:
    return redirect(url_for("login"))

  if request.method == "POST":
    action = request.form.get("form_action")
    if action in ["deposit", "withdraw"]:
      amount = float(request.form.get("amount") or 0)
      note = request.form.get("note", "")
      if amount > 0:
        db.session.add(
            WalletLog(action_type=action, amount=amount, note=note)
        )
        db.session.commit()
      return redirect(url_for("index"))

    t_type = request.form.get("type")
    name = request.form.get("customer_name")
    phone = request.form.get("phone") or "-"
    principal = float(request.form.get("principal") or 0)
    daily_interest = float(request.form.get("daily_interest") or 0)
    discount = float(request.form.get("discount") or 0)
    sales_name = request.form.get("sales_name") or "-"

    db.session.add(
        Transaction(
            type=t_type,
            customer_name=name,
            phone=phone,
            principal=principal,
            original_principal=principal,
            daily_interest=daily_interest,
            discount=discount,
            sales_name=sales_name,
            start_date=date.today(),
            status="ปกติ",
        )
    )
    db.session.commit()
    return redirect(url_for("index"))

  search_query = request.args.get("search", "").strip()
  query = Transaction.query
  if search_query:
    query = query.filter(
        (Transaction.customer_name.like(f"%{search_query}%"))
        | (Transaction.phone.like(f"%{search_query}%"))
    )

  transactions = query.all()
  today = date.today()

  total_investment = 0      # เงินต้นคงเหลือในระบบ
  total_returned = 0        # เงินต้นที่ลูกค้าคืนมาแล้ว
  total_profit = 0          # กำไรสุทธิทั้งหมด
  display_data = []

  for tx in transactions:
    # คำนวณเงินต้นที่คืนมาแล้วของรายการนี้
    returned_principal = tx.original_principal - tx.principal
    total_returned += returned_principal

    if tx.status != "คืนแล้ว":
      days_passed = max((today - tx.start_date).days + 1, 1)
      total_interest_raw = days_passed * tx.daily_interest
      accumulated_interest = max(total_interest_raw - tx.discount, 0)
      
      total_investment += tx.principal
      total_profit += tx.discount + accumulated_interest
    else:
      days_passed = 0
      total_interest_raw = 0
      accumulated_interest = 0
      total_profit += tx.discount

    display_data.append({
        "id": tx.id,
        "type": tx.type,
        "customer_name": tx.customer_name,
        "phone": tx.phone,
        "principal": tx.principal,
        "original_principal": tx.original_principal,
        "daily_interest": tx.daily_interest,
        "paid_interest": tx.discount,
        "days_passed": days_passed,
        "accumulated_interest": accumulated_interest,
        "start_date": tx.start_date.strftime("%d/%m/%Y"),
        "status": tx.status,
    })

  sales_list = [u["display_name"] for u in USERS_DB.values()]
  all_customers = [
      c[0] for c in db.session.query(Transaction.customer_name).distinct().all() if c[0]
  ]

  customer_phone_map = {}
  for tx in Transaction.query.all():
    if tx.customer_name and tx.phone and tx.phone != "-":
      customer_phone_map[tx.customer_name] = tx.phone

  return render_template(
      "index.html",
      transactions=display_data,
      total_investment=total_investment,
      total_returned=total_returned,
      total_profit=total_profit,
      current_admin=session.get("user"),
      search_query=search_query,
      sales_list=sales_list,
      all_customers=all_customers,
      customer_phone_map=customer_phone_map,
  )


@app.route("/update_payment/<int:tx_id>", methods=["POST"])
def update_payment(tx_id):
  if "user" not in session:
    return redirect(url_for("login"))

  tx = Transaction.query.get_or_404(tx_id)
  payment_type = request.form.get("payment_type")
  pay_amount = float(request.form.get("pay_amount") or 0)

  today = date.today()
  days_passed = max((today - tx.start_date).days + 1, 1)
  total_interest_raw = days_passed * tx.daily_interest
  current_interest = max(total_interest_raw - tx.discount, 0)

  if payment_type == "full":
    tx.status = "คืนแล้ว"
    tx.principal = 0
  elif payment_type == "partial":
    if pay_amount > 0:
      remaining_money = pay_amount - current_interest
      if remaining_money >= 0:
        tx.principal -= remaining_money
        tx.discount += current_interest
      else:
        tx.discount += pay_amount

      if tx.principal <= 0:
        tx.principal = 0
        tx.status = "คืนแล้ว"
      else:
        tx.status = "ตัดยอดบางส่วน"

  db.session.commit()
  return redirect(request.referrer or url_for("index"))


@app.route("/all_members")
def all_members():
  if "user" not in session:
    return redirect(url_for("login"))
  transactions = Transaction.query.all()
  return render_template("all_members.html", transactions=transactions)


@app.route("/sales_members")
def sales_members():
  if "user" not in session:
    return redirect(url_for("login"))
  transactions = Transaction.query.all()
  sales_groups = {}
  for tx in transactions:
    s_name = tx.sales_name if tx.sales_name else "ไม่ระบุเซลส์"
    if s_name not in sales_groups:
      sales_groups[s_name] = []
    sales_groups[s_name].append(tx)
  return render_template("sales_members.html", sales_groups=sales_groups)


@app.route("/customer_summary")
def customer_summary():
  if "user" not in session:
    return redirect(url_for("login"))
  cash_loans = Transaction.query.filter_by(type="ปล่อยกู้เงินสด").all()
  gold_loans = Transaction.query.filter_by(type="ผ่อนทองคำ").all()
  return render_template(
      "customer_summary.html", cash_loans=cash_loans, gold_loans=gold_loans
  )


@app.route("/monthly_summary_page")
def monthly_summary_page():
  if "user" not in session:
    return redirect(url_for("login"))
  transactions = Transaction.query.all()
  monthly_summary = {}
  today = date.today()

  for tx in transactions:
    month_key = tx.start_date.strftime("%Y-%m")
    if month_key not in monthly_summary:
      monthly_summary[month_key] = {
          "investment": 0,
          "returned": 0,
          "profit": 0,
          "pending": 0,
          "count": 0,
      }

    returned_p = tx.original_principal - tx.principal
    monthly_summary[month_key]["returned"] += returned_p

    if tx.status != "คืนแล้ว":
      days_passed = max((today - tx.start_date).days + 1, 1)
      total_interest_raw = days_passed * tx.daily_interest
      profit = max(total_interest_raw - tx.discount, 0)
      pending = tx.principal + profit
      monthly_summary[month_key]["investment"] += tx.principal
      monthly_summary[month_key]["profit"] += tx.discount + profit
      monthly_summary[month_key]["pending"] += pending
    else:
      monthly_summary[month_key]["profit"] += tx.discount

    monthly_summary[month_key]["count"] += 1

  sorted_monthly = sorted(
      [{"month": k, **v} for k, v in monthly_summary.items()],
      key=lambda x: x["month"],
      reverse=True,
  )
  return render_template(
      "monthly_summary.html", monthly_summary=sorted_monthly
  )


if __name__ == "__main__":
  app.run(debug=True, port=5000)