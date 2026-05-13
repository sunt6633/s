---
name: stock-simulator
description: A-share stock simulation trading platform. Use when user asks about stock trading simulation, portfolio management, virtual stock trading, or wants to practice trading without real money. Provides daily stock picking, simulated buy/sell, position tracking, P&L monitoring, and trade history.
---

# Stock Simulator

A-share stock simulation trading platform with AI-powered stock picking.

## Features

- **Daily Stock Picker**: Screens CSI 300 stocks using MA crossover, volume surge, and RSI indicators
- **Simulated Trading**: Buy/sell with commission and stamp tax calculation
- **Portfolio Tracking**: Real-time position monitoring with P&L
- **Trade History**: Complete transaction log with pagination

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Server

```bash
cd scripts
python app.py
```

Server runs at `http://localhost:5000`.

### 3. Access the Dashboard

Open browser to `http://localhost:5000` for the web UI, or use API endpoints:

- `GET /api/dashboard` - Account summary and holdings
- `GET /api/picker` - Get stock picks
- `POST /api/buy` - Buy stocks
- `POST /api/sell` - Sell stocks
- `GET /api/trades` - Trade history
- `GET /api/search?q=xxx` - Search stocks

## Trading Rules

- Initial capital: ¥10,000
- Minimum lot: 100 shares (1手)
- Commission: 0.025% (minimum ¥5)
- Stamp tax: 0.05% (sell only)
- T+1 rule: Cannot sell on the same day as purchase

## Stock Picker Strategy

The picker screens CSI 300 stocks using:
1. **MA Crossover**: MA5 crosses above MA20
2. **Volume Surge**: Today's volume > 1.5x 20-day average
3. **RSI Filter**: RSI between 30-70

## External Access

To access from outside the local network, use cloudflared tunnel:

```bash
cloudflared tunnel --url http://localhost:5000
```

This generates a temporary public URL.

## Cron Integration

Set up daily stock picking at market open (9:30 AM):

```bash
openclaw cron add --name "stock-pick" --cron "30 9 * * 1-5" --tz "Asia/Shanghai" --message "Run stock picker and notify user" --announce
```
