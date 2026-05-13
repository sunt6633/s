/* ═══════════════════════════════════════════
   小龙模拟盘 - Frontend JS
   ═══════════════════════════════════════════ */

let selectedStock = null;
let currentTradePage = 1;

// ── Tab switching ──
function switchTab(tab) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + tab).classList.add('active');
    document.querySelector(`.nav-btn[data-tab="${tab}"]`).classList.add('active');

    if (tab === 'dashboard') loadDashboard();
    if (tab === 'history') loadTrades(1);
}

// ── Toast ──
function showToast(msg, type = 'info') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'toast ' + type;
    t.style.display = 'block';
    setTimeout(() => { t.style.display = 'none'; }, 3000);
}

// ── Format currency ──
function fmtCNY(v) {
    return '¥' + Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtPct(v) {
    return (v >= 0 ? '+' : '') + v.toFixed(2) + '%';
}

function pnlClass(v) {
    return v > 0 ? 'pnl-up' : v < 0 ? 'pnl-down' : '';
}

// ── Dashboard ──
async function loadDashboard() {
    try {
        const res = await fetch('/api/dashboard');
        const d = await res.json();

        document.getElementById('total-assets').textContent = fmtCNY(d.total_assets);
        document.getElementById('cash-balance').textContent = fmtCNY(d.cash);
        document.getElementById('market-value').textContent = fmtCNY(d.total_market_value);

        const pnlEl = document.getElementById('total-pnl');
        pnlEl.textContent = fmtCNY(d.total_pnl) + ' (' + fmtPct(d.total_pnl_pct) + ')';
        const card = document.getElementById('pnl-card');
        card.className = 'stat-card ' + (d.total_pnl > 0 ? 'positive' : d.total_pnl < 0 ? 'negative' : '');

        // Holdings
        const tbody = document.getElementById('holdings-body');
        if (d.holdings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="empty-row">暂无持仓，去交易页面买入股票吧</td></tr>';
        } else {
            tbody.innerHTML = d.holdings.map(h => `
                <tr>
                    <td><span class="code-badge">${h.stock_code}</span></td>
                    <td><strong>${h.stock_name}</strong></td>
                    <td>${h.quantity}</td>
                    <td>${fmtCNY(h.avg_cost)}</td>
                    <td>${fmtCNY(h.current_price)}</td>
                    <td>${fmtCNY(h.market_value)}</td>
                    <td class="${pnlClass(h.pnl)}">${fmtCNY(h.pnl)}</td>
                    <td class="${pnlClass(h.pnl_pct)}">${fmtPct(h.pnl_pct)}</td>
                    <td>
                        <button class="btn btn-sell btn-small" onclick="quickSell('${h.stock_code}','${h.stock_name}',${h.current_price},${h.quantity})">
                            卖出
                        </button>
                    </td>
                </tr>
            `).join('');
        }

        // Update server time
        document.getElementById('server-time').textContent = d.server_time;
        const statusEl = document.getElementById('trading-status');
        if (d.trading_hours) {
            statusEl.textContent = '交易中';
            statusEl.className = 'status-badge open';
        } else {
            statusEl.textContent = '已收盘';
            statusEl.className = 'status-badge closed';
        }
    } catch (e) {
        console.error('Dashboard load error:', e);
    }
}

function quickSell(code, name, price, qty) {
    switchTab('trade');
    selectStock({ code, name, price });
    document.getElementById('trade-price').value = price;
    document.getElementById('trade-quantity').value = qty;
    document.getElementById('trade-quantity').max = qty;
    updatePreview();
}

// ── Stock search ──
let searchTimer = null;
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('stock-search');
    input.addEventListener('input', () => {
        clearTimeout(searchTimer);
        const q = input.value.trim();
        if (q.length < 1) {
            document.getElementById('search-results').style.display = 'none';
            return;
        }
        searchTimer = setTimeout(() => searchStock(q), 300);
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#stock-search') && !e.target.closest('#search-results')) {
            document.getElementById('search-results').style.display = 'none';
        }
    });

    // Auto-update preview on input change
    ['trade-price', 'trade-quantity'].forEach(id => {
        document.getElementById(id).addEventListener('input', updatePreview);
    });

    // Start dashboard
    loadDashboard();
    setInterval(loadDashboard, 30000); // Refresh every 30s
});

async function searchStock(q) {
    try {
        const res = await fetch('/api/search?q=' + encodeURIComponent(q));
        const results = await res.json();
        const dd = document.getElementById('search-results');
        if (results.length === 0) {
            dd.innerHTML = '<div class="search-item" style="color:var(--text3)">未找到匹配股票</div>';
            dd.style.display = 'block';
            return;
        }
        dd.innerHTML = results.map(r => `
            <div class="search-item" onclick='selectStock(${JSON.stringify(r)})'>
                <span>
                    <span class="stock-name">${r.name}</span>
                    <span class="code-badge">${r.code}</span>
                </span>
                <span class="stock-price" style="color:${r.change_pct >= 0 ? 'var(--red)' : 'var(--green)'}">
                    ${Number(r.price).toFixed(2)} ${r.change_pct >= 0 ? '+' : ''}${r.change_pct}%
                </span>
            </div>
        `).join('');
        dd.style.display = 'block';
    } catch (e) {
        console.error('Search error:', e);
    }
}

function selectStock(stock) {
    selectedStock = stock;
    document.getElementById('stock-search').value = '';
    document.getElementById('search-results').style.display = 'none';
    document.getElementById('selected-stock').style.display = 'flex';
    document.getElementById('selected-name').textContent = stock.name;
    document.getElementById('selected-code').textContent = stock.code;
    document.getElementById('trade-price').value = stock.price || '';
    updatePreview();
}

function updatePreview() {
    const price = parseFloat(document.getElementById('trade-price').value) || 0;
    const qty = parseInt(document.getElementById('trade-quantity').value) || 0;
    const preview = document.getElementById('trade-preview');
    const activeTab = document.querySelector('.nav-btn.active').dataset.tab;

    if (price <= 0 || qty <= 0) {
        preview.style.display = 'none';
        return;
    }

    const amount = price * qty;
    const commission = Math.max(amount * 0.00025, 5);
    const taxRow = document.getElementById('preview-tax-row');

    if (activeTab === 'trade') {
        // Determine direction based on which button is focused? Show buy by default
        taxRow.style.display = 'none';
        const total = amount + commission;
        document.getElementById('preview-amount').textContent = fmtCNY(amount);
        document.getElementById('preview-commission').textContent = fmtCNY(commission);
        document.getElementById('preview-total').textContent = fmtCNY(total);
    }

    preview.style.display = 'block';
}

// ── Trade execution ──
async function executeTrade(direction) {
    if (!selectedStock) {
        showToast('请先搜索并选择一只股票', 'error');
        return;
    }

    const price = parseFloat(document.getElementById('trade-price').value);
    const quantity = parseInt(document.getElementById('trade-quantity').value);

    if (!price || price <= 0) { showToast('请输入有效价格', 'error'); return; }
    if (!quantity || quantity < 100 || quantity % 100 !== 0) {
        showToast('数量必须为100的整数倍', 'error');
        return;
    }

    const msgEl = document.getElementById('trade-message');

    try {
        const res = await fetch('/api/' + direction, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                stock_code: selectedStock.code,
                stock_name: selectedStock.name,
                price: price,
                quantity: quantity,
            })
        });
        const data = await res.json();

        if (data.success) {
            showToast(data.message, 'success');
            msgEl.textContent = '✅ ' + data.message;
            msgEl.className = 'trade-message success';
            msgEl.style.display = 'block';
            loadDashboard();
            setTimeout(() => { msgEl.style.display = 'none'; }, 5000);
        } else {
            showToast(data.error || '交易失败', 'error');
            msgEl.textContent = '❌ ' + (data.error || '交易失败');
            msgEl.className = 'trade-message error';
            msgEl.style.display = 'block';
        }
    } catch (e) {
        showToast('网络错误', 'error');
    }
}

// ── Stock Picker ──
async function runPicker() {
    const loading = document.getElementById('picker-loading');
    const results = document.getElementById('picker-results');
    loading.style.display = 'block';
    results.innerHTML = '';

    try {
        const res = await fetch('/api/picker');
        const data = await res.json();
        loading.style.display = 'none';

        if (data.error) {
            results.innerHTML = `<p class="empty-hint" style="color:var(--red)">${data.error}</p>`;
            return;
        }

        if (!data.picks || data.picks.length === 0) {
            results.innerHTML = `<p class="empty-hint">本轮筛选了 ${data.total_screened || 0} 只股票，暂未发现符合条件的标的</p>`;
            return;
        }

        results.innerHTML = `
            <p style="color:var(--text2);font-size:13px;margin-bottom:16px;">
                筛选 ${data.total_screened} 只 · 发现 ${data.picks.length} 只符合条件 · ${data.updated_at}
            </p>
            ${data.picks.map(p => `
                <div class="pick-card">
                    <div class="pick-info">
                        <span class="pick-name">${p.name}</span>
                        <span class="pick-code">${p.code}</span>
                        <span class="${p.change_pct >= 0 ? 'pnl-up' : 'pnl-down'}" style="margin-left:8px;">
                            ${p.change_pct >= 0 ? '+' : ''}${p.change_pct}%
                        </span>
                        <div class="pick-reason">💡 ${p.reason}</div>
                    </div>
                    <div class="pick-stats">
                        <div class="pick-stat">
                            <div class="label">价格</div>
                            <div class="value">${fmtCNY(p.price)}</div>
                        </div>
                        <div class="pick-stat">
                            <div class="label">RSI</div>
                            <div class="value">${p.rsi}</div>
                        </div>
                        <div class="pick-stat">
                            <div class="label">量比</div>
                            <div class="value">${p.vol_ratio}x</div>
                        </div>
                        <button class="btn btn-buy btn-small" onclick="pickBuy('${p.code}','${p.name}',${p.price})">买入</button>
                    </div>
                </div>
            `).join('')}
        `;
    } catch (e) {
        loading.style.display = 'none';
        results.innerHTML = '<p class="empty-hint" style="color:var(--red)">筛选出错，请稍后重试</p>';
    }
}

function pickBuy(code, name, price) {
    switchTab('trade');
    selectStock({ code, name, price });
}

// ── Trade History ──
async function loadTrades(page) {
    currentTradePage = page || 1;
    try {
        const res = await fetch(`/api/trades?page=${currentTradePage}&per_page=20`);
        const data = await res.json();
        const tbody = document.getElementById('trades-body');

        if (data.trades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="empty-row">暂无交易记录</td></tr>';
            return;
        }

        tbody.innerHTML = data.trades.map(t => `
            <tr>
                <td style="font-size:12px;color:var(--text2)">${t.trade_time}</td>
                <td><span style="color:${t.direction === 'buy' ? 'var(--red)' : 'var(--green)'};font-weight:600;">
                    ${t.direction === 'buy' ? '买入' : '卖出'}
                </span></td>
                <td><span class="code-badge">${t.stock_code}</span></td>
                <td><strong>${t.stock_name}</strong></td>
                <td>${fmtCNY(t.price)}</td>
                <td>${t.quantity}</td>
                <td>${fmtCNY(t.commission)}</td>
                <td>${t.stamp_tax > 0 ? fmtCNY(t.stamp_tax) : '--'}</td>
                <td>${fmtCNY(t.total_cost)}</td>
            </tr>
        `).join('');

        // Pagination
        const pg = document.getElementById('trades-pagination');
        if (data.pages <= 1) { pg.innerHTML = ''; return; }
        let btns = '';
        for (let i = 1; i <= data.pages; i++) {
            btns += `<button class="${i === currentTradePage ? 'active' : ''}" onclick="loadTrades(${i})">${i}</button>`;
        }
        pg.innerHTML = btns;
    } catch (e) {
        console.error('Load trades error:', e);
    }
}
