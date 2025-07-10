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
