"""小龙模拟盘 - A-Share Stock Simulation Trading Platform."""
import os
from datetime import datetime, date, timedelta
from flask import Flask, render_template, jsonify, request
from models import db, Account, Holding, Trade
from sqlalchemy import func
import traceback

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock_sim.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# ── Trading constants ──
INITIAL_CAPITAL = 10000.0
COMMISSION_RATE = 0.00025   # 0.025%
MIN_COMMISSION = 5.0
STAMP_TAX_RATE = 0.0005     # 0.05%, sell only
MIN_LOT = 100               # 1手 = 100股


def get_account():
    acc = Account.query.first()
    if not acc:
        acc = Account(name='小龙模拟盘', cash=INITIAL_CAPITAL, initial_capital=INITIAL_CAPITAL)
        db.session.add(acc)
        db.session.commit()
    return acc


def calc_commission(amount):
    return max(amount * COMMISSION_RATE, MIN_COMMISSION)


def calc_stamp_tax(amount):
    return amount * STAMP_TAX_RATE


def is_trading_hours():
    now = datetime.now()
    weekday = now.weekday()
    if weekday >= 5:
        return False
    t = now.time()
    morning = (t >= datetime.strptime('09:30', '%H:%M').time() and
               t <= datetime.strptime('11:30', '%H:%M').time())
    afternoon = (t >= datetime.strptime('13:00', '%H:%M').time() and
                 t <= datetime.strptime('15:00', '%H:%M').time())
    return morning or afternoon


def get_price_info(stock_code):
    """Get realtime or last-known price for a stock."""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == stock_code]
        if len(row) > 0:
            r = row.iloc[0]
            return {
                'price': float(r.get('最新价', 0)),
                'name': str(r.get('名称', '')),
                'change_pct': float(r.get('涨跌幅', 0)),
                'prev_close': float(r.get('昨收', 0)),
                'open': float(r.get('今开', 0)),
                'high': float(r.get('最高', 0)),
                'low': float(r.get('最低', 0)),
            }
    except Exception:
        pass
    return None


# ── Pages ──
@app.route('/')
def index():
    return render_template('index.html')


# ── API: Dashboard ──
@app.route('/api/dashboard')
def api_dashboard():
    acc = get_account()
    holdings = Holding.query.filter_by(account_id=acc.id).filter(Holding.quantity > 0).all()
    total_market_value = 0.0
    holdings_data = []
    for h in holdings:
        info = get_price_info(h.stock_code)
        current_price = info['price'] if info else h.avg_cost
        name = info['name'] if info else h.stock_name
        mv = current_price * h.quantity
        pnl = (current_price - h.avg_cost) * h.quantity
        pnl_pct = ((current_price - h.avg_cost) / h.avg_cost * 100) if h.avg_cost > 0 else 0
        total_market_value += mv
        holdings_data.append({
            'stock_code': h.stock_code,
            'stock_name': name,
            'quantity': h.quantity,
            'avg_cost': round(h.avg_cost, 4),
            'current_price': round(current_price, 2),
            'market_value': round(mv, 2),
            'pnl': round(pnl, 2),
            'pnl_pct': round(pnl_pct, 2),
            'buy_date': h.buy_date.isoformat() if h.buy_date else None,
        })

    total_assets = acc.cash + total_market_value
    total_pnl = total_assets - acc.initial_capital
    total_pnl_pct = (total_pnl / acc.initial_capital * 100) if acc.initial_capital > 0 else 0

    today_trades = Trade.query.filter(
        Trade.account_id == acc.id,
        Trade.trade_time >= date.today().isoformat()
    ).all()

    today_pnl = 0.0
    for t in today_trades:
        if t.direction == 'sell':
            today_pnl += t.total_cost

    return jsonify({
        'cash': round(acc.cash, 2),
        'total_market_value': round(total_market_value, 2),
        'total_assets': round(total_assets, 2),
        'total_pnl': round(total_pnl, 2),
        'total_pnl_pct': round(total_pnl_pct, 2),
        'initial_capital': acc.initial_capital,
        'holdings': holdings_data,
        'holding_count': len(holdings_data),
        'today_trade_count': len(today_trades),
        'trading_hours': is_trading_hours(),
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })


# ── API: Stock lookup ──
@app.route('/api/stock/<code>')
def api_stock_info(code):
    info = get_price_info(code)
    if info:
        return jsonify(info)
    return jsonify({'error': '未找到该股票'}), 404


# ── API: Buy ──
@app.route('/api/buy', methods=['POST'])
def api_buy():
    data = request.json
    stock_code = data.get('stock_code', '').strip()
    stock_name = data.get('stock_name', '').strip()
    price = float(data.get('price', 0))
    quantity = int(data.get('quantity', 0))

    if not stock_code or not stock_name:
        return jsonify({'error': '请输入股票代码和名称'}), 400
    if quantity <= 0 or quantity % MIN_LOT != 0:
        return jsonify({'error': f'买入数量必须为{MIN_LOT}的整数倍（至少{MIN_LOT}股）'}), 400
    if price <= 0:
        return jsonify({'error': '价格必须大于0'}), 400

    acc = get_account()
    amount = price * quantity
    commission = calc_commission(amount)
    total = amount + commission

    if total > acc.cash:
        return jsonify({'error': f'资金不足，需要 ¥{total:.2f}，可用 ¥{acc.cash:.2f}'}), 400

    # Deduct cash
    acc.cash -= total

    # Update or create holding
    holding = Holding.query.filter_by(account_id=acc.id, stock_code=stock_code).first()
    if holding:
        new_qty = holding.quantity + quantity
        holding.avg_cost = (holding.avg_cost * holding.quantity + amount) / new_qty
        holding.quantity = new_qty
        holding.stock_name = stock_name
    else:
        holding = Holding(
            account_id=acc.id, stock_code=stock_code, stock_name=stock_name,
            quantity=quantity, avg_cost=price, buy_date=date.today()
        )
        db.session.add(holding)

    # Record trade
    trade = Trade(
        account_id=acc.id, stock_code=stock_code, stock_name=stock_name,
        direction='buy', price=price, quantity=quantity,
        commission=commission, stamp_tax=0, total_cost=total,
        trade_time=datetime.now()
    )
    db.session.add(trade)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'买入 {stock_name}({stock_code}) {quantity}股 @ ¥{price:.2f}',
        'trade': trade.to_dict(),
    })


# ── API: Sell ──
@app.route('/api/sell', methods=['POST'])
def api_sell():
    data = request.json
    stock_code = data.get('stock_code', '').strip()
    stock_name = data.get('stock_name', '').strip()
    price = float(data.get('price', 0))
    quantity = int(data.get('quantity', 0))

    if not stock_code:
        return jsonify({'error': '请输入股票代码'}), 400
    if quantity <= 0 or quantity % MIN_LOT != 0:
        return jsonify({'error': f'卖出数量必须为{MIN_LOT}的整数倍（至少{MIN_LOT}股）'}), 400
    if price <= 0:
        return jsonify({'error': '价格必须大于0'}), 400

    acc = get_account()
    holding = Holding.query.filter_by(account_id=acc.id, stock_code=stock_code).first()

    if not holding or holding.quantity < quantity:
        avail = holding.quantity if holding else 0
        return jsonify({'error': f'持仓不足，可卖 {avail} 股'}), 400

    # T+1 check
    today = date.today()
    if holding.buy_date >= today:
        return jsonify({'error': 'T+1限制：当日买入的股票不能当日卖出'}), 400

    amount = price * quantity
    commission = calc_commission(amount)
    stamp_tax = calc_stamp_tax(amount)
    proceeds = amount - commission - stamp_tax

    acc.cash += proceeds
    holding.quantity -= quantity
    if holding.quantity == 0:
        db.session.delete(holding)

    trade = Trade(
        account_id=acc.id, stock_code=stock_code, stock_name=stock_name or holding.stock_name,
        direction='sell', price=price, quantity=quantity,
        commission=commission, stamp_tax=stamp_tax, total_cost=proceeds,
        trade_time=datetime.now()
    )
    db.session.add(trade)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'卖出 {stock_name or holding.stock_name}({stock_code}) {quantity}股 @ ¥{price:.2f}',
        'trade': trade.to_dict(),
    })


# ── API: Trades ──
@app.route('/api/trades')
def api_trades():
    acc = get_account()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    trades = Trade.query.filter_by(account_id=acc.id)\
        .order_by(Trade.trade_time.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'trades': [t.to_dict() for t in trades.items],
        'total': trades.total,
        'pages': trades.pages,
        'current_page': trades.page,
    })


# ── API: Stock Picker ──
@app.route('/api/picker')
def api_picker():
    try:
        from stock_picker import screen_stocks
        result = screen_stocks(max_results=10)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'picks': [], 'error': str(e), 'total_screened': 0})


# ── API: Search stock ──
@app.route('/api/search')
def api_search_stock():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        mask = df['代码'].str.contains(query) | df['名称'].str.contains(query)
        results = df[mask].head(20)
        return jsonify([{
            'code': str(r['代码']),
            'name': str(r['名称']),
            'price': float(r.get('最新价', 0)),
            'change_pct': float(r.get('涨跌幅', 0)),
        } for _, r in results.iterrows()])
    except Exception as e:
        return jsonify([])


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
