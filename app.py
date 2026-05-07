import os
from collections import defaultdict
from datetime import date, datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import Transaction, User, db

EXPENSE_CATEGORIES = [
    "Обучение",
    "Питание",
    "Транспорт",
    "Жильё",
    "Развлечения",
    "Другое",
]
INCOME_CATEGORIES = ["Обучение", "Стипендия", "Зарплата", "Подработка", "Премия", "Переводы", "Другое"]


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


with app.app_context():
    db.create_all()


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            flash("Войдите в аккаунт, чтобы продолжить.", "warning")
            return redirect(url_for("login"))
        user = db.session.get(User, user_id)
        if not user:
            # Session may reference a deleted user after DB reset/recreate.
            session.clear()
            flash("Сессия устарела. Войдите снова.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


@app.route("/")
def index():
    if get_current_user():
        return redirect(url_for("dashboard"))
    session.clear()
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Логин и пароль обязательны.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Пользователь с таким логином уже существует.", "danger")
            return redirect(url_for("register"))

        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash("Регистрация прошла успешно. Теперь войдите в систему.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            flash("Вы успешно вошли в личный кабинет.", "success")
            return redirect(url_for("dashboard"))

        flash("Неверный логин или пароль.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Вы вышли из аккаунта.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    transactions = Transaction.query.filter_by(user_id=user.id).all()

    total_income = sum(t.amount for t in transactions if t.transaction_type == "income")
    total_expense = sum(t.amount for t in transactions if t.transaction_type == "expense")
    balance = total_income - total_expense

    today = date.today()
    month_transactions = [
        t
        for t in transactions
        if t.transaction_date.year == today.year and t.transaction_date.month == today.month
    ]
    month_income = sum(t.amount for t in month_transactions if t.transaction_type == "income")
    month_expense = sum(t.amount for t in month_transactions if t.transaction_type == "expense")

    return render_template(
        "dashboard.html",
        balance=balance,
        total_income=total_income,
        total_expense=total_expense,
        month_income=month_income,
        month_expense=month_expense,
    )


@app.route("/transactions", methods=["GET", "POST"])
@login_required
def transactions():
    user = get_current_user()

    if request.method == "POST":
        amount_raw = request.form.get("amount", "").strip()
        transaction_type = request.form.get("transaction_type", "").strip()
        category = request.form.get("category", "").strip()
        comment = request.form.get("comment", "").strip() or None
        date_raw = request.form.get("transaction_date", "").strip()

        if transaction_type not in {"income", "expense"}:
            flash("Некорректный тип транзакции.", "danger")
            return redirect(url_for("transactions"))

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Сумма должна быть положительным числом.", "danger")
            return redirect(url_for("transactions"))

        try:
            transaction_date = (
                datetime.strptime(date_raw, "%Y-%m-%d").date() if date_raw else date.today()
            )
        except ValueError:
            flash("Некорректная дата.", "danger")
            return redirect(url_for("transactions"))

        if not category:
            flash("Укажите категорию.", "danger")
            return redirect(url_for("transactions"))

        transaction = Transaction(
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            comment=comment,
            transaction_date=transaction_date,
            user_id=user.id,
        )
        db.session.add(transaction)
        db.session.commit()
        flash("Транзакция успешно добавлена.", "success")
        return redirect(url_for("transactions"))

    all_transactions = (
        Transaction.query.filter_by(user_id=user.id)
        .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        .all()
    )

    existing_income_categories = sorted(
        {t.category for t in all_transactions if t.transaction_type == "income"}
    )
    existing_expense_categories = sorted(
        {t.category for t in all_transactions if t.transaction_type == "expense"}
    )
    income_categories_for_select = sorted(set(INCOME_CATEGORIES + existing_income_categories))
    expense_categories_for_select = sorted(set(EXPENSE_CATEGORIES + existing_expense_categories))
    preselected_type = request.args.get("type", "expense")
    if preselected_type not in {"income", "expense"}:
        preselected_type = "expense"

    return render_template(
        "transactions.html",
        transactions=all_transactions,
        today=date.today().isoformat(),
        expense_categories=expense_categories_for_select,
        income_categories=income_categories_for_select,
        preselected_type=preselected_type,
    )


@app.route("/transactions/delete/<int:transaction_id>", methods=["POST"])
@login_required
def delete_transaction(transaction_id):
    user = get_current_user()
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user.id).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    flash("Транзакция удалена.", "info")
    return redirect(url_for("transactions"))


@app.route("/analytics")
@login_required
def analytics():
    user = get_current_user()
    user_transactions = Transaction.query.filter_by(user_id=user.id).all()
    today = date.today()

    current_month_expenses = [
        t
        for t in user_transactions
        if t.transaction_type == "expense"
        and t.transaction_date.year == today.year
        and t.transaction_date.month == today.month
    ]
    expense_by_category = defaultdict(float)
    for expense in current_month_expenses:
        expense_by_category[expense.category] += expense.amount

    month_summary = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for transaction in user_transactions:
        key = transaction.transaction_date.strftime("%Y-%m")
        month_summary[key][transaction.transaction_type] += transaction.amount

    sorted_months = sorted(month_summary.keys())
    month_labels = sorted_months
    income_values = [round(month_summary[m]["income"], 2) for m in sorted_months]
    expense_values = [round(month_summary[m]["expense"], 2) for m in sorted_months]

    total_income = sum(t.amount for t in user_transactions if t.transaction_type == "income")
    total_expense = sum(t.amount for t in user_transactions if t.transaction_type == "expense")
    total_balance = total_income - total_expense

    month_income = sum(
        t.amount
        for t in user_transactions
        if t.transaction_type == "income"
        and t.transaction_date.year == today.year
        and t.transaction_date.month == today.month
    )
    month_expense = sum(
        t.amount
        for t in user_transactions
        if t.transaction_type == "expense"
        and t.transaction_date.year == today.year
        and t.transaction_date.month == today.month
    )

    return render_template(
        "analytics.html",
        expense_labels=list(expense_by_category.keys()),
        expense_values=[round(v, 2) for v in expense_by_category.values()],
        month_labels=month_labels,
        income_values=income_values,
        expense_month_values=expense_values,
        month_income=month_income,
        month_expense=month_expense,
        total_income=total_income,
        total_expense=total_expense,
        total_balance=total_balance,
    )


@app.route("/profile")
@login_required
def profile():
    user = get_current_user()
    transactions_count = Transaction.query.filter_by(user_id=user.id).count()
    return render_template("profile.html", user=user, transactions_count=transactions_count)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(debug=True, port=port)
