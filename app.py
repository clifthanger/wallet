from flask import Flask, render_template, request, redirect, url_for
from models import db, Transaction, SubCategory
from datetime import datetime
import locale

# Set locale ke Indonesia
locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Buat database
with app.app_context():
    db.create_all()

# Fungsi untuk memformat angka ke format Rupiah
def format_rupiah(amount):
    """
    Format angka ke dalam format mata uang Rupiah (Rp#.##).
    Contoh: 1000 -> Rp1.000,00
    """
    return f"Rp{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Fungsi untuk mengubah format tanggal dari yyyy-mm-dd ke dd-mm-yyyy
def format_tanggal(tanggal):
    try:
        return datetime.strptime(tanggal, '%Y-%m-%d').strftime('%d-%m-%Y')
    except ValueError:
        return tanggal  # Jika format tidak valid, kembalikan tanggal asli

# Tambahkan fungsi format_rupiah ke konteks template
@app.context_processor
def utility_processor():
    return dict(format_rupiah=format_rupiah)

# Halaman utama (Read)
@app.route('/')
def index():
    # Ambil semua transaksi
    transactions = Transaction.query.all()

    # Hitung total pemasukan dan pengeluaran
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    sisa = total_income - total_expense

    # Ambil tanggal paling lama dan paling baru
    if transactions:
        tanggal_terlama = format_tanggal(min(t.date for t in transactions))
        tanggal_terbaru = format_tanggal(max(t.date for t in transactions))
    else:
        tanggal_terlama = tanggal_terbaru = "Tidak ada data"

    return render_template(
        'index.html',
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        sisa=sisa,
        tanggal_terlama=tanggal_terlama,
        tanggal_terbaru=tanggal_terbaru
    )

# Tambah transaksi (Create)
@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        type = request.form['type']
        amount = float(request.form['amount'])
        date = request.form['date']
        description = request.form['description']
        sub_category_id = request.form.get('sub_category_id')  # Ambil sub kategori

        new_transaction = Transaction(
            type=type,
            amount=amount,
            date=date,
            description=description,
            sub_category_id=sub_category_id if sub_category_id else None
        )
        db.session.add(new_transaction)
        db.session.commit()
        return redirect(url_for('index'))

    # Ambil daftar sub kategori untuk dropdown
    income_sub_categories = SubCategory.query.filter_by(type='income').all()
    expense_sub_categories = SubCategory.query.filter_by(type='expense').all()
    return render_template('add_transaction.html', income_sub_categories=income_sub_categories, expense_sub_categories=expense_sub_categories)

# Edit transaksi (Update)
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_transaction(id):
    transaction = Transaction.query.get_or_404(id)

    if request.method == 'POST':
        transaction.type = request.form['type']
        transaction.amount = float(request.form['amount'])
        transaction.date = request.form['date']
        transaction.description = request.form['description']
        transaction.sub_category_id = request.form.get('sub_category_id')  # Update sub kategori
        db.session.commit()
        return redirect(url_for('index'))

    # Ambil daftar sub kategori untuk dropdown
    income_sub_categories = SubCategory.query.filter_by(type='income').all()
    expense_sub_categories = SubCategory.query.filter_by(type='expense').all()
    return render_template('edit_transaction.html', transaction=transaction, income_sub_categories=income_sub_categories, expense_sub_categories=expense_sub_categories)

# Hapus transaksi (Delete)
@app.route('/delete/<int:id>')
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    return redirect(url_for('index'))

# Halaman pemasukan (Income)
@app.route('/income')
def income():
    # Ambil bulan saat ini sebagai default filter
    current_month = datetime.now().strftime('%Y-%m')
    transactions = Transaction.query.filter(Transaction.type == 'income', Transaction.date.like(f'{current_month}%')).all()
    total_income = sum(t.amount for t in transactions)
    return render_template('income.html', transactions=transactions, total_income=total_income, current_month=current_month)

# Halaman pengeluaran (Expense)
@app.route('/expense')
def expense():
    # Ambil bulan saat ini sebagai default filter
    current_month = datetime.now().strftime('%Y-%m')
    transactions = Transaction.query.filter(Transaction.type == 'expense', Transaction.date.like(f'{current_month}%')).all()
    total_expense = sum(t.amount for t in transactions)
    return render_template('expense.html', transactions=transactions, total_expense=total_expense, current_month=current_month)

# Filter transaksi berdasarkan custom range
@app.route('/filter_transactions', methods=['POST'])
def filter_transactions():
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    # Query transaksi berdasarkan range tanggal
    transactions = Transaction.query.filter(Transaction.date.between(start_date, end_date)).all()

    # Hitung total pemasukan dan pengeluaran
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    sisa = total_income - total_expense

    # Format tanggal
    start_date_formatted = format_tanggal(start_date)
    end_date_formatted = format_tanggal(end_date)

    return render_template(
        'index.html',
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        sisa=sisa,
        tanggal_terlama=start_date_formatted,
        tanggal_terbaru=end_date_formatted
    )

# Tambah Sub Kategori
@app.route('/add_sub_category', methods=['GET', 'POST'])
def add_sub_category():
    if request.method == 'POST':
        name = request.form['name']
        type = request.form['type']

        # Cek apakah sub kategori sudah ada
        existing_sub_category = SubCategory.query.filter_by(name=name, type=type).first()
        if existing_sub_category:
            return "Sub kategori sudah ada!", 400

        new_sub_category = SubCategory(name=name, type=type)
        db.session.add(new_sub_category)
        db.session.commit()
        return redirect(url_for('sub_categories'))

    return render_template('add_sub_category.html')

# Halaman utama sub kategori (Read)
@app.route('/sub_categories')
def sub_categories():
    sub_categories = SubCategory.query.all()
    return render_template('sub_categories.html', sub_categories=sub_categories)

# Edit sub kategori (Update)
@app.route('/edit_sub_category/<int:id>', methods=['GET', 'POST'])
def edit_sub_category(id):
    sub_category = SubCategory.query.get_or_404(id)

    if request.method == 'POST':
        sub_category.name = request.form['name']
        sub_category.type = request.form['type']
        db.session.commit()
        return redirect(url_for('sub_categories'))

    return render_template('edit_sub_category.html', sub_category=sub_category)

# Hapus sub kategori (Delete)
@app.route('/delete_sub_category/<int:id>')
def delete_sub_category(id):
    sub_category = SubCategory.query.get_or_404(id)
    db.session.delete(sub_category)
    db.session.commit()
    return redirect(url_for('sub_categories'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)