"""Database models for the stock simulation platform."""
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Account(db.Model):
    """User trading account."""
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default='模拟账户')
    cash = db.Column(db.Float, nullable=False, default=10000.0)
    initial_capital = db.Column(db.Float, nullable=False, default=10000.0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    trades = db.relationship('Trade', backref='account', lazy=True)
    holdings = db.relationship('Holding', backref='account', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'cash': round(self.cash, 2),
            'initial_capital': self.initial_capital,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Holding(db.Model):
    """Current stock holdings."""
    __tablename__ = 'holdings'

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    stock_code = db.Column(db.String(10), nullable=False)
    stock_name = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    avg_cost = db.Column(db.Float, nullable=False, default=0.0)
    buy_date = db.Column(db.Date, nullable=False, default=date.today)

    __table_args__ = (
        db.UniqueConstraint('account_id', 'stock_code', name='uq_account_stock'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'quantity': self.quantity,
            'avg_cost': round(self.avg_cost, 4),
            'buy_date': self.buy_date.isoformat() if self.buy_date else None,
        }


class Trade(db.Model):
    """Transaction history."""
    __tablename__ = 'trades'

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    stock_code = db.Column(db.String(10), nullable=False)
    stock_name = db.Column(db.String(50), nullable=False)
    direction = db.Column(db.String(4), nullable=False)  # 'buy' or 'sell'
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    commission = db.Column(db.Float, nullable=False, default=0.0)
    stamp_tax = db.Column(db.Float, nullable=False, default=0.0)
    total_cost = db.Column(db.Float, nullable=False, default=0.0)
    trade_time = db.Column(db.DateTime, default=datetime.now)
    is_valid = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'direction': self.direction,
            'price': round(self.price, 2),
            'quantity': self.quantity,
            'commission': round(self.commission, 2),
            'stamp_tax': round(self.stamp_tax, 2),
            'total_cost': round(self.total_cost, 2),
            'trade_time': self.trade_time.strftime('%Y-%m-%d %H:%M:%S') if self.trade_time else None,
            'is_valid': self.is_valid,
        }
