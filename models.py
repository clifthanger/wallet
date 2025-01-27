from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Tabel Sub Kategori
class SubCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # Nama sub kategori (unik)
    type = db.Column(db.String(10), nullable=False)  # Tipe: 'income' atau 'expense'

    def __repr__(self):
        return f'<SubCategory {self.name}>'

# Tabel Transaksi
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)  # 'income' atau 'expense'
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(10), nullable=False)  # Format: YYYY-MM-DD
    description = db.Column(db.String(200), nullable=True)
    sub_category_id = db.Column(db.Integer, db.ForeignKey('sub_category.id'), nullable=True)  # Relasi ke Sub Kategori
    sub_category = db.relationship('SubCategory', backref='transactions')  # Relasi

    def __repr__(self):
        return f'<Transaction {self.id}>'