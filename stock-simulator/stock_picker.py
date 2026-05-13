"""Stock picker: screen A-share stocks based on technical indicators using akshare."""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import traceback


def calc_rsi(series, period=14):
    """Calculate RSI."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def get_hs300_stocks():
    """Get CSI 300 component stocks."""
    try:
        df = ak.index_stock_cons_csindex(symbol="000300")
        stocks = []
        for _, row in df.iterrows():
            code = str(row.get('成分券代码', row.get('证券代码', ''))).strip()
            name = str(row.get('成分券名称', row.get('证券名称', ''))).strip()
            if code and name:
                stocks.append({'code': code, 'name': name})
        return stocks
    except Exception:
        pass

    try:
        df = ak.stock_hs300_component_cninfo()
        stocks = []
        for _, row in df.iterrows():
            code = str(row.iloc[1]).strip() if len(row) > 1 else ''
            name = str(row.iloc[2]).strip() if len(row) > 2 else ''
            if code and name:
                stocks.append({'code': code, 'name': name})
        if stocks:
            return stocks
    except Exception:
        pass

    try:
        df = ak.index_stock_cons(symbol="000300")
        stocks = []
        for _, row in df.iterrows():
            code = str(row.iloc[0]).strip()
            name = str(row.iloc[1]).strip() if len(row) > 1 else ''
            if code and name:
                stocks.append({'code': code, 'name': name})
        if stocks:
            return stocks
    except Exception:
        pass

    return []


def get_stock_history(code, days=60):
    """Get daily history for a stock."""
    try:
        end = datetime.now().strftime('%Y%m%d')
        start = (datetime.now() - timedelta(days=days + 40)).strftime('%Y%m%d')
        df = ak.stock_zh_a_hist(symbol=code, period="daily",
                                start_date=start, end_date=end, adjust="qfq")
        if df is not None and len(df) > 0:
            df.columns = [c.strip() for c in df.columns]
            return df
    except Exception:
        pass
    return None


def get_realtime_price(code):
    """Get realtime price for a stock."""
    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == code]
        if len(row) > 0:
            r = row.iloc[0]
            return {
                'price': float(r.get('最新价', 0)),
                'change_pct': float(r.get('涨跌幅', 0)),
                'volume': float(r.get('成交量', 0)),
                'amount': float(r.get('成交额', 0)),
                'open': float(r.get('今开', 0)),
                'high': float(r.get('最高', 0)),
                'low': float(r.get('最低', 0)),
                'prev_close': float(r.get('昨收', 0)),
                'name': str(r.get('名称', '')),
            }
    except Exception:
        pass
    return None


def analyze_stock(code, name):
    """Analyze a single stock and return signal info if criteria met."""
    df = get_stock_history(code, days=60)
    if df is None or len(df) < 30:
        return None

    try:
        close = df['收盘'].astype(float)
        volume = df['成交量'].astype(float)
    except Exception:
        return None

    if close.isna().all() or volume.isna().all():
        return None

    # MA
    ma5 = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()

    if len(ma5.dropna()) < 2 or len(ma20.dropna()) < 2:
        return None

    ma5_now = ma5.iloc[-1]
    ma5_prev = ma5.iloc[-2]
    ma20_now = ma20.iloc[-1]
    ma20_prev = ma20.iloc[-2]

    # MA crossover: 5-day crosses above 20-day
    ma_cross = (ma5_prev <= ma20_prev) and (ma5_now > ma20_now)
    if not ma_cross:
        return None

    # Volume surge
    vol_avg20 = volume.rolling(20).mean().iloc[-1]
    vol_today = volume.iloc[-1]
    if pd.isna(vol_avg20) or vol_avg20 == 0:
        return None
    vol_ratio = vol_today / vol_avg20
    if vol_ratio < 1.5:
        return None

    # RSI
    rsi = calc_rsi(close, 14)
    rsi_now = rsi.iloc[-1]
    if pd.isna(rsi_now) or rsi_now < 30 or rsi_now > 70:
        return None

    price = float(close.iloc[-1])
    pct_change = float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100)

    return {
        'code': code,
        'name': name,
        'price': round(price, 2),
        'change_pct': round(pct_change, 2),
        'ma5': round(float(ma5_now), 2),
        'ma20': round(float(ma20_now), 2),
        'rsi': round(float(rsi_now), 2),
        'vol_ratio': round(float(vol_ratio), 2),
        'reason': f"MA5({round(float(ma5_now),2)})上穿MA20({round(float(ma20_now),2)}); 成交量放大{round(float(vol_ratio),1)}倍; RSI={round(float(rsi_now),1)}",
    }


def screen_stocks(max_results=10):
    """Screen CSI 300 stocks and return top picks."""
    stocks = get_hs300_stocks()
    if not stocks:
        return {'picks': [], 'error': '无法获取沪深300成分股数据', 'total_screened': 0}

    picks = []
    screened = 0
    errors = 0

    for s in stocks[:80]:
        screened += 1
        try:
            result = analyze_stock(s['code'], s['name'])
            if result:
                picks.append(result)
                if len(picks) >= max_results:
                    break
        except Exception as e:
            errors += 1
            if errors > 10:
                break
            continue

    return {
        'picks': sorted(picks, key=lambda x: x['vol_ratio'], reverse=True)[:max_results],
        'total_screened': screened,
        'total_picks': len(picks),
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
