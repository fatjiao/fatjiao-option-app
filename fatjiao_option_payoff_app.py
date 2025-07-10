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
