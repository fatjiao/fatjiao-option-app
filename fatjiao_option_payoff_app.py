import streamlit as st
import numpy as np
import plotly.graph_objs as go

st.set_page_config(page_title="FATJIAO Option Payoff Assistant")

st.title("📈 FATJIAO Option Payoff Assistant")

PREDEFINED_STRATEGIES = {
    "None": [],
    "Covered Call (备兑看涨)": [
        {'type': 'call', 'position': 'short', 'strike': 105.0, 'premium': 3.0, 'contracts': 1},
    ],
    "Protective Put (防护性看跌)": [
        {'type': 'put', 'position': 'long', 'strike': 95.0, 'premium': 2.0, 'contracts': 1},
    ],
    "Bull Call Spread (牛市看涨价差)": [
        {'type': 'call', 'position': 'long', 'strike': 100.0, 'premium': 5.0, 'contracts': 1},
        {'type': 'call', 'position': 'short', 'strike': 110.0, 'premium': 2.0, 'contracts': 1},
    ],
    "Bear Put Spread (熊市看跌价差)": [
        {'type': 'put', 'position': 'long', 'strike': 110.0, 'premium': 6.0, 'contracts': 1},
        {'type': 'put', 'position': 'short', 'strike': 100.0, 'premium': 3.0, 'contracts': 1},
    ],
    "Iron Condor (铁鹰)": [
        {'type': 'put', 'position': 'long', 'strike': 90.0, 'premium': 1.0, 'contracts': 1},
        {'type': 'put', 'position': 'short', 'strike': 95.0, 'premium': 2.0, 'contracts': 1},
        {'type': 'call', 'position': 'short', 'strike': 105.0, 'premium': 2.0, 'contracts': 1},
        {'type': 'call', 'position': 'long', 'strike': 110.0, 'premium': 1.0, 'contracts': 1},
    ],
}

if 'legs' not in st.session_state:
    st.session_state.legs = []

st.sidebar.header("策略模板选择")
selected_strategy = st.sidebar.selectbox("选择策略模板", list(PREDEFINED_STRATEGIES.keys()))
if st.sidebar.button("加载策略"):
    st.session_state.legs = PREDEFINED_STRATEGIES[selected_strategy].copy()
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
            'strike': strike,
            'premium': premium,
            'contracts': contracts
        })

current_price = st.number_input("当前标的价格（可选）", min_value=0.0, step=0.01, format="%.2f")

st.subheader("当前组合")
if st.session_state.legs:
    for i, leg in enumerate(st.session_state.legs):
        with st.expander(f"期权腿 {i+1} - 类型:{leg['type']}，方向:{leg['position']}，执行价:{leg['strike']:.2f}"):
            leg['type'] = st.selectbox("类型", ['call', 'put'], index=0 if leg['type']=='call' else 1, key=f"type_{i}")
            leg['position'] = st.selectbox("方向", ['long', 'short'], index=0 if leg['position']=='long' else 1, key=f"pos_{i}")
            leg['strike'] = st.number_input("执行价", value=float(leg['strike']), step=1.0, format="%.2f", key=f"strike_{i}")
            leg['premium'] = st.number_input("权利金", value=float(leg['premium']), step=0.1, format="%.2f", key=f"premium_{i}")
            leg['contracts'] = st.number_input("合约数", value=int(leg['contracts']), step=1, format="%d", key=f"contracts_{i}")
            if st.button("❌ 删除该腿", key=f"delete_{i}"):
                st.session_state.legs.pop(i)
                st.experimental_rerun()
    if st.button("🧹 清空全部"):
        st.session_state.legs = []
        st.experimental_rerun()
else:
    st.info("当前没有任何腿，请先添加或加载策略模板。")

if st.session_state.legs:
    st.subheader("📊 到期收益图")

    prices = np.linspace(
        0.5 * min(float(leg['strike']) for leg in st.session_state.legs),
        1.5 * max(float(leg['strike']) for leg in st.session_state.legs), 500
    )

    def option_leg_payoff(s, strike, premium, otype, pos, contracts):
        intrinsic = np.maximum(s - strike, 0) if otype == 'call' else np.maximum(strike - s, 0)
        return (intrinsic - premium if pos == 'long' else premium - intrinsic) * contracts

    def total_payoff(s, legs):
        total = np.zeros_like(s)
        for leg in legs:
            total += option_leg_payoff(s, float(leg['strike']), float(leg['premium']), leg['type'], leg['position'], int(leg['contracts']))
        return total

    payoff = total_payoff(prices, st.session_state.legs)

    fig = go.Figure()

    # 0盈亏线，白色虚线
    fig.add_trace(go.Scatter(
        x=[prices[0], prices[-1]], y=[0, 0],
        mode='lines', line=dict(color='white', dash='dash'),
        showlegend=False
    ))

    # 利用断点分段，绘制绿色和红色分段线条
    # 先找到分段区间（盈亏符号变化处）
    signs = np.sign(payoff)
    segment_indices = [0]
    for i in range(1, len(signs)):
        if signs[i] != signs[i-1]:
            segment_indices.append(i)
    segment_indices.append(len(payoff))

    # 分段绘制不同颜色
    for start, end in zip(segment_indices[:-1], segment_indices[1:]):
        segment_x = prices[start:end]
        segment_y = payoff[start:end]
        color = 'green' if segment_y[0] >= 0 else 'red'
        fig.add_trace(go.Scatter(
            x=segment_x, y=segment_y,
            mode='lines',
            line=dict(color=color, width=3),
            showlegend=False
        ))

    # 标记当前标的价格
    if current_price > 0:
        payoff_at_current = total_payoff(np.array([current_price]), st.session_state.legs)[0]
        fig.add_trace(go.Scatter(
            x=[current_price], y=[payoff_at_current],
            mode='markers+text',
            marker=dict(color='blue', size=12, symbol='x'),
            text=[f"当前价\n{current_price:.2f}\n盈亏 {payoff_at_current:.2f}"],
            textposition='top center',
            name='当前标的价格'
        ))

    fig.update_layout(
        title='期权策略到期盈亏图',
        xaxis_title='标的价格',
        yaxis_title='盈亏',
        hovermode='x unified',
        template='plotly_dark',
        plot_bgcolor='black',
        paper_bgcolor='black'
    )

    st.plotly_chart(fig, use_container_width=True, config={'responsive': True})
