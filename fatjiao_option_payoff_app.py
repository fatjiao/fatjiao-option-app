import streamlit as st
import numpy as np
import plotly.graph_objs as go

st.set_page_config(page_title="FATJIAO Option Payoff Assistant", layout="wide")
st.title("📈 FATJIAO Option Payoff Assistant")

PREDEFINED_STRATEGIES = {
    "None": {"legs": [], "description": "", "example": ""},
    "Covered Call (备兑看涨)": {
        "legs": [{'type': 'call', 'position': 'short', 'strike': 105.0, 'premium': 3.0, 'contracts': 1}],
        "description": "你已经有一份股票，同时卖出一个看涨期权，别人给你钱让你在股票涨到一定价格时以那个价格卖给他。这样先拿钱，但股票涨太多时赚的有限。",
        "example": "比如你有股票，价格100元，卖出执行价105元的看涨期权，别人给你3元权利金。如果股票涨到110元，你最多只能105元卖出股票，赚3元权利金，涨得多就不多赚了。"
    },
    # 你可以在这里添加其他策略
}

if 'legs' not in st.session_state:
    st.session_state.legs = []
if 'strategy_description' not in st.session_state:
    st.session_state.strategy_description = ""
if 'strategy_example' not in st.session_state:
    st.session_state.strategy_example = ""

st.sidebar.header("策略模板选择")
selected_strategy = st.sidebar.selectbox("选择策略模板", list(PREDEFINED_STRATEGIES.keys()))
if st.sidebar.button("加载策略"):
    st.session_state.legs = PREDEFINED_STRATEGIES[selected_strategy]["legs"].copy()
    st.session_state.strategy_description = PREDEFINED_STRATEGIES[selected_strategy]["description"]
    st.session_state.strategy_example = PREDEFINED_STRATEGIES[selected_strategy]["example"]
    st.success(f"已加载策略模板：{selected_strategy}")

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

if st.session_state.strategy_description or st.session_state.strategy_example:
    st.markdown("### 策略说明")
    if st.session_state.strategy_description:
        st.info(st.session_state.strategy_description)
    if st.session_state.strategy_example:
        st.markdown("**示例：**")
        st.info(st.session_state.strategy_example)

st.subheader("当前组合")
if st.session_state.legs:
    header_cols = st.columns([1, 1, 2, 2, 1, 1])
    headers = ["类型", "方向", "执行价", "权利金", "合约", "操作"]
    for col, header in zip(header_cols, headers):
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

current_price = st.number_input("当前标的价格（可选）", min_value=0.0, step=0.01, format="%.2f", key="current_price_input")

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

    zero_crossings = []
    for i in range(1, len(prices)):
        if payoff[i - 1] * payoff[i] < 0:
            x0, x1 = prices[i - 1], prices[i]
            y0, y1 = payoff[i - 1], payoff[i]
            zero = x0 - y0 * (x1 - x0) / (y1 - y0)
            zero_crossings.append(zero)

    fig = go.Figure()
    pos_x = [x for x, y in zip(prices, payoff) if y >= 0]
    pos_y = [y for y in payoff if y >= 0]
    neg_x = [x for x, y in zip(prices, payoff) if y < 0]
    neg_y = [y for y in payoff if y < 0]

    fig.add_trace(go.Scatter(x=prices, y=payoff, mode='lines', name='Payoff', line=dict(color='black')))
    fig.add_trace(go.Scatter(x=pos_x, y=pos_y, mode='lines', name='盈利', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=neg_x, y=neg_y, mode='lines', name='亏损', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=[prices[0], prices[-1]], y=[0, 0], mode='lines', name='零收益线', line=dict(color='white', dash='dash')))

    for zero in zero_crossings:
        fig.add_trace(go.Scatter(
            x=[zero], y=[0], mode='markers+text', name='盈亏平衡点',
            text=[f'{zero:.2f}'], textposition='top center',
            marker=dict(color='blue', size=12)))

    if current_price > 0:
        payoff_at_current = np.interp(current_price, prices, payoff)
        fig.add_trace(go.Scatter(
            x=[current_price, current_price], y=[min(payoff), max(payoff)],
            mode='lines', name='当前价格', line=dict(color='yellow', dash='dot')))
        fig.add_trace(go.Scatter(
            x=[current_price], y=[payoff_at_current],
            mode='markers+text', name='当前价格点',
            text=[f'{current_price:.2f}'], textposition='bottom right',
            marker=dict(color='yellow', size=14, symbol='star')))

    fig.update_layout(
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='white'),
        legend=dict(bgcolor='rgba(0,0,0,0.3)'),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="标的价格",
        yaxis_title="盈亏",
        height=500,
    )

    st.plotly_chart(fig, use_container_width=True)
