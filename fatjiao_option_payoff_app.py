import streamlit as st
import numpy as np
import plotly.graph_objs as go

st.set_page_config(page_title="FATJIAO Option Payoff Assistant", layout="wide")
st.title("📈 FATJIAO Option Payoff Assistant")

# ===== 预设策略字典（含通俗说明与实例） =====
PREDEFINED_STRATEGIES = {
    "None": {
        "legs": [],
        "description": "",
        "example": ""
    },
    "Covered Call (备兑看涨)": {
        "legs": [
            {'type': 'call', 'position': 'short', 'strike': 105.0, 'premium': 3.0, 'contracts': 1},
        ],
        "description": "你已经有一份股票，同时卖出一个看涨期权，别人给你钱让你在股票涨到一定价格时以那个价格卖给他。这样先拿钱，但股票涨太多时赚的有限。",
        "example": "比如你有股票，价格100元，卖出执行价105元的看涨期权，别人给你3元权利金。如果股票涨到110元，你最多只能105元卖出股票，赚3元权利金，涨得多就不多赚了。"
    },
    "Protective Put (防护性看跌)": {
        "legs": [
            {'type': 'put', 'position': 'long', 'strike': 95.0, 'premium': 2.0, 'contracts': 1},
        ],
        "description": "你有股票，但怕跌得厉害，买个看跌期权当保险。如果股票跌了，可以按约定价卖出，减少亏损。",
        "example": "你有股票，现价100元，买执行价95元看跌期权，付2元权利金。股票跌到90元，可以按95元卖出，避免大亏。"
    },
    "Bull Call Spread (牛市看涨价差)": {
        "legs": [
            {'type': 'call', 'position': 'long', 'strike': 100.0, 'premium': 5.0, 'contracts': 1},
            {'type': 'call', 'position': 'short', 'strike': 110.0, 'premium': 2.0, 'contracts': 1},
        ],
        "description": "买一个低价看涨期权，同时卖一个高价看涨期权，花钱少但赚的钱有限，适合觉得股票会涨但涨幅不大。",
        "example": "买100元执行价看涨期权花5元，同时卖110元执行价看涨期权收2元。股票涨到105元，你赚差价，但涨到120元也只能赚到110元限额。"
    },
    "Bear Put Spread (熊市看跌价差)": {
        "legs": [
            {'type': 'put', 'position': 'long', 'strike': 110.0, 'premium': 6.0, 'contracts': 1},
            {'type': 'put', 'position': 'short', 'strike': 100.0, 'premium': 3.0, 'contracts': 1},
        ],
        "description": "买一个高价看跌期权，同时卖一个低价看跌期权，花钱少，赚的钱有限，适合觉得股票会跌但跌幅有限。",
        "example": "买110元执行价看跌期权花6元，卖100元执行价看跌期权收3元。股票跌到105元赚差价，但跌到90元最多赚100元限额。"
    },
    "Iron Condor (铁鹰)": {
        "legs": [
            {'type': 'put', 'position': 'long', 'strike': 90.0, 'premium': 1.0, 'contracts': 1},
            {'type': 'put', 'position': 'short', 'strike': 95.0, 'premium': 2.0, 'contracts': 1},
            {'type': 'call', 'position': 'short', 'strike': 105.0, 'premium': 2.0, 'contracts': 1},
            {'type': 'call', 'position': 'long', 'strike': 110.0, 'premium': 1.0, 'contracts': 1},
        ],
        "description": "同时卖出看涨和看跌期权，赌股票不会涨太多或跌太多，同时买两个保护期权限制风险。适合预期股价在区间内。",
        "example": "卖出95元看跌和105元看涨期权，收权利金，同时买90元看跌和110元看涨期权防止亏损。"
    },
    "Straddle (跨式组合)": {
        "legs": [
            {'type': 'call', 'position': 'long', 'strike': 100.0, 'premium': 4.0, 'contracts': 1},
            {'type': 'put', 'position': 'long', 'strike': 100.0, 'premium': 3.5, 'contracts': 1},
        ],
        "description": "同时买入相同行权价的看涨和看跌期权，赌股票大涨或大跌，但不知道方向。",
        "example": "买100元执行价看涨和看跌期权，股票大涨或大跌都可能赚钱。"
    },
    "Strangle (勒式组合)": {
        "legs": [
            {'type': 'call', 'position': 'long', 'strike': 105.0, 'premium': 2.0, 'contracts': 1},
            {'type': 'put', 'position': 'long', 'strike': 95.0, 'premium': 1.5, 'contracts': 1},
        ],
        "description": "买价格不同的看涨和看跌期权，赌股票价格突破一个区间，上下大幅波动。",
        "example": "买105元看涨和95元看跌期权，期待股票涨过105或跌破95。"
    },
    "Butterfly Spread (蝶式价差)": {
        "legs": [
            {'type': 'call', 'position': 'long', 'strike': 95.0, 'premium': 7.0, 'contracts': 1},
            {'type': 'call', 'position': 'short', 'strike': 100.0, 'premium': 4.0, 'contracts': 2},
            {'type': 'call', 'position': 'long', 'strike': 105.0, 'premium': 2.0, 'contracts': 1},
        ],
        "description": "买低价和高价看涨期权，卖中间两个看涨期权，赚股票价格在中间时的最大收益。",
        "example": "买95元和105元看涨期权各一份，卖100元看涨期权两份，期待股票价格接近100元。"
    },
    "Calendar Spread (日历价差)": {
        "legs": [
            {'type': 'call', 'position': 'long', 'strike': 100.0, 'premium': 3.0, 'contracts': 1},
            {'type': 'call', 'position': 'short', 'strike': 100.0, 'premium': 1.5, 'contracts': 1},
        ],
        "description": "买长期看涨期权，卖短期同价看涨期权，赚时间价值差价，适合股票价格短期波动小。",
        "example": "买3个月后到期100元看涨期权，卖1个月后到期100元看涨期权。"
    },
}

# 初始化状态
if 'legs' not in st.session_state:
    st.session_state.legs = []
if 'strategy_description' not in st.session_state:
    st.session_state.strategy_description = ""
if 'strategy_example' not in st.session_state:
    st.session_state.strategy_example = ""

# 侧边栏选择策略模板
st.sidebar.header("策略模板选择")
selected_strategy = st.sidebar.selectbox("选择策略模板", list(PREDEFINED_STRATEGIES.keys()))
if st.sidebar.button("加载策略"):
    st.session_state.legs = PREDEFINED_STRATEGIES[selected_strategy]["legs"].copy()
    st.session_state.strategy_description = PREDEFINED_STRATEGIES[selected_strategy]["description"]
    st.session_state.strategy_example = PREDEFINED_STRATEGIES[selected_strategy]["example"]
    st.success(f"已加载策略模板：{selected_strategy}")

# 侧边栏添加新腿
st.sidebar.header("添加新腿")
with st.sidebar.form("add_leg_form"):
    otype = st.selectbox("类型", ['call', 'put'])
    pos = st.selectbox("方向", ['long', 'short'])
    strike = st.number_input("执行价", value=100.0, step=1.0, format="%.2f")
    premium = st.number_input("权利金", value=5.0, step=0.1, format="%.2f")
    contracts = st.number_input("合约数", value=1, step=1, format="%d")
    add = st.form_submit_button("➕ 添加期权腿")
    if add:
        st.session_state.legs.append({
            'type': otype,
            'position': pos,
            'strike': float(strike),
            'premium': float(premium),
            'contracts': int(contracts)
        })

# 主区显示策略说明及实例（如果有）
if st.session_state.strategy_description or st.session_state.strategy_example:
    st.markdown("### 策略说明")
    if st.session_state.strategy_description:
        st.info(st.session_state.strategy_description)
    if st.session_state.strategy_example:
        st.markdown("**示例：**")
        st.info(st.session_state.strategy_example)

# 当前组合显示
st.subheader("当前组合")
if st.session_state.legs:
    cols = st.columns([1, 1, 2, 2, 1, 1])
    headers = ["类型", "方向", "执行价", "权利金", "合约", "操作"]
    for col, header in zip(cols, headers):
        col.markdown(f"**{header}**")

    for i, leg in enumerate(st.session_state.legs):
        cols = st.columns([1, 1, 2, 2, 1, 1])
        leg['type'] = cols[0].selectbox("", ['call', 'put'], index=0 if leg['type'] == 'call' else 1, key=f"type_{i}")
        leg['position'] = cols[1].selectbox("", ['long', 'short'], index=0 if leg['position'] == 'long' else 1, key=f"pos_{i}")
        leg['strike'] = float(cols[2].number_input("", value=float(leg['strike']), step=1.0, format="%.2f", key=f"strike_{i}"))
        leg['premium'] = float(cols[3].number_input("", value=float(leg['premium']), step=0.1, format="%.2f", key=f"premium_{i}"))
        leg['contracts'] = int(cols[4].number_input("", value=int(leg['contracts']), step=1, format="%d", key=f"contracts_{i}"))
        if cols[5].button("❌ 删除", key=f"delete_{i}"):
            st.session_state.legs.pop(i)
            st.experimental_rerun()

    if st.button("🧹 清空全部"):
        st.session_state.legs = []
        st.session_state.strategy_description = ""
        st.session_state.strategy_example = ""
        st.experimental_rerun()
else:
    st.info("当前没有任何腿，请先添加或加载策略模板。")

# 输入当前标的价格（可选）
current_price = st.number_input("当前标的价格（可选）", min_value=0.0, step=0.01, format="%.2f", key="current_price_input")

# 计算并绘制收益图
if st.session_state.legs:
    st.subheader("📊 到期收益图")
    prices = np.linspace(0.5 * min(leg['strike'] for leg in st.session_state.legs),
                         1.5 * max(leg['strike'] for leg in st.session_state.legs), 500)

    def option_leg_payoff(s, strike, premium, otype, pos, contracts):
        intrinsic = np.maximum(s - strike, 0) if otype == 'call' else np.maximum(strike - s, 0)
        return (intrinsic - premium if pos == 'long' else premium - intrinsic) * contracts

    def total_payoff(s, legs):
        total = np.zeros_like(s)
        for leg in legs:
            total += option_leg_payoff(s, leg['strike'], leg['premium'], leg['type'], leg['position'], leg['contracts'])
        return total

    payoff = total_payoff(prices, st.session_state.legs)

    # 计算盈亏平衡点
    zero_crossings = []
    for i in range(1, len(prices)):
        if payoff[i - 1] * payoff[i] < 0:
            x0, x1 = prices[i - 1], prices[i]
            y0, y1 = payoff[i - 1], payoff[i]
            zero = x0 - y0 * (x1 - x0) / (y1 - y0)
            zero_crossings.append(zero)

    fig = go.Figure()

    # 收益曲线（黑色线）
    fig.add_trace(go.Scatter(x=prices, y=payoff, mode='lines', name='Payoff', line=dict(color='black')))

    # 盈利区域填充（绿色半透明）
    fig.add_trace(go.Scatter(
        x=prices, y=np.maximum(payoff, 0),
        fill='tozeroy',
        mode='none',
        showlegend=True,
        name='盈利',
        fillcolor='rgba(0,255,0,0.3)'
    ))

    # 亏损区域填充（红色半透明）
    fig.add_trace(go.Scatter(
        x=prices, y=np.minimum(payoff, 0),
        fill='tozeroy',
        mode='none',
        showlegend=True,
        name='亏损',
        fillcolor='rgba(255,0,0,0.3)'
    ))

    # 零收益线（白色虚线）
    fig.add_trace(go.Scatter(x=[prices[0], prices[-1]], y=[0, 0], mode='lines', name='零收益线', line=dict(color='white', dash='dash')))

    # 标记盈亏平衡点（蓝色圆点）
    for zero in zero_crossings:
        fig.add_trace(go.Scatter(
            x=[zero], y=[0], mode='markers+text', name='盈亏平衡点',
            text=[f'{zero:.2f}'], textposition='top center',
            marker=dict(color='blue', size=12)))

    # 标记当前标的价格线及文字
    if current_price > 0:
        payoff_at_current = np.interp(current_price, prices, payoff)
        fig.add_trace(go.Scatter(
            x=[current_price, current_price], y=[min(payoff), max(payoff)],
            mode='lines', name='当前价格', line=dict(color='yellow', dash='dot')))
        fig.add_trace(go.Scatter(
            x=[current_price], y=[payoff_at_current],
            mode='markers+text', name='当前价格点',
            text=[f'{current_price:.2f}'],
            textposition='bottom center',
            marker=dict(color='yellow', size=14, symbol='star')))

    fig.update_layout(
        title='期权策略到期盈亏图',
        xaxis_title='标的价格',
        yaxis_title='盈亏',
        hovermode='x unified',
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='white'),
    )

    st.plotly_chart(fig, use_container_width=True)
