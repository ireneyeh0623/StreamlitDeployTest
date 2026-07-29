import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# ==============================================================================
# 1. 系統環境配置
# ==============================================================================

st.set_page_config(page_title="改良版 SAR 趨勢追蹤系統 (K線版)", layout="wide")

if "is_dark" not in st.session_state:
    st.session_state.is_dark = False

# ==============================================================================
# 2. 視覺設計 Tokens（與 LohasFiveLineChart_1.py 共用同一套 Design Handoff 規格）
# ==============================================================================

LIGHT_TOKENS = {
    "bg": "#f3f2f2",
    "surface_alt": "#f8f7f6",
    "text": "#201f1d",
    "text_muted": "rgba(32,31,29,0.55)",
    "divider": "rgba(32,31,29,0.16)",
    "accent": "#b68235",
    "grid_line": "rgba(32,31,29,0.08)",
    "shadow": "0 3px 10px rgba(45,43,43,0.14)",
    "candle": {"up": "#8b1e1e", "down": "#1f5c3d"},
}
DARK_TOKENS = {
    "bg": "#17140f",
    "surface_alt": "#1c1912",
    "text": "#f3ede2",
    "text_muted": "rgba(243,237,226,0.6)",
    "divider": "rgba(243,237,226,0.16)",
    "accent": "#c99a4e",
    "grid_line": "rgba(243,237,226,0.12)",
    "shadow": "0 12px 32px rgba(0,0,0,0.5)",
    "candle": {"up": "#d0342c", "down": "#2f9d68"},
}

is_dark = st.session_state.is_dark
tok = DARK_TOKENS if is_dark else LIGHT_TOKENS
chart_template = "plotly_dark" if is_dark else "plotly_white"

# ==============================================================================
# 3. 全域樣式（字型／配色／按鈕／輸入框／側邊欄版面）
# ==============================================================================

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600&family=Lora:wght@400;600&display=swap');

    html, body, [class*="css"] {{ font-family: 'Lora', serif; }}
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Cormorant Garamond', serif !important;
        font-weight: 600 !important;
    }}

    .stApp, [data-testid="stAppViewContainer"] {{
        background-color: {tok['bg']} !important;
        color: {tok['text']} !important;
    }}
    [data-testid="stHeader"] {{ background-color: transparent !important; }}

    /* 側邊欄版面 */
    [data-testid="stSidebar"] {{
        background-color: {tok['bg']} !important;
        border-right: 1px solid {tok['divider']};
        min-width: 300px !important;
        max-width: 300px !important;
    }}
    [data-testid="stSidebarUserContent"] {{ padding: 40px 28px !important; }}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: 18px; }}
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{
        font-size: 12px !important;
        color: {tok['text_muted']} !important;
        font-family: 'Lora', serif !important;
    }}
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {{
        color: {tok['text']};
    }}

    /* 輸入框：邊框只畫在最外層容器，內層元素一律去邊框/去底色，避免雙層邊框與底色不一致 */
    [data-testid="stSidebar"] div[data-baseweb="input"] {{
        border: 1px solid {tok['divider']} !important;
        border-radius: 4px !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }}
    [data-testid="stSidebar"] div[data-baseweb="input"] * {{
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
    }}
    [data-testid="stSidebar"] div[data-baseweb="input"] input {{
        color: {tok['text']} !important;
    }}

    /* 數字輸入框(+/-按鈕)：步進按鈕改為描邊風格，與整體設計語彙一致 */
    [data-testid="stSidebar"] [data-testid="stNumberInputStepUp"],
    [data-testid="stSidebar"] [data-testid="stNumberInputStepDown"] {{
        border-color: {tok['divider']} !important;
        background-color: transparent !important;
        color: {tok['text']} !important;
        opacity: 1 !important;
    }}
    [data-testid="stSidebar"] [data-testid="stNumberInputStepUp"] svg,
    [data-testid="stSidebar"] [data-testid="stNumberInputStepDown"] svg {{
        fill: {tok['text']} !important;
        stroke: {tok['text']} !important;
        opacity: 1 !important;
    }}
    [data-testid="stSidebar"] [data-testid="stNumberInputStepUp"]:hover,
    [data-testid="stSidebar"] [data-testid="stNumberInputStepDown"]:hover {{
        border-color: {tok['accent']} !important;
        color: {tok['accent']} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stNumberInputStepUp"]:hover svg,
    [data-testid="stSidebar"] [data-testid="stNumberInputStepDown"]:hover svg {{
        fill: {tok['accent']} !important;
        stroke: {tok['accent']} !important;
    }}

    /* 瀏覽器自動填入(autofill)會強制套用自己的底色，一般CSS蓋不掉，需用此專門技巧解除 */
    [data-testid="stSidebar"] input:-webkit-autofill,
    [data-testid="stSidebar"] input:-webkit-autofill:hover,
    [data-testid="stSidebar"] input:-webkit-autofill:focus,
    [data-testid="stSidebar"] input:-webkit-autofill:active {{
        -webkit-box-shadow: 0 0 0 1000px transparent inset !important;
        -webkit-text-fill-color: {tok['text']} !important;
        caret-color: {tok['text']};
        transition: background-color 9999s ease-in-out 0s;
    }}

    /* 按鈕：設計系統一律採 outline 樣式，不使用實心填色 */
    div.stButton > button {{
        width: 100%;
        background-color: transparent !important;
        border-radius: 4px !important;
        font-family: 'Cormorant Garamond', serif !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        box-shadow: none !important;
    }}
    div.stButton > button[kind="secondary"] {{
        color: {tok['text']} !important;
        border: 1px solid {tok['divider']} !important;
    }}
    div.stButton > button[kind="secondary"]:hover {{
        border-color: {tok['accent']} !important;
        color: {tok['accent']} !important;
    }}
    div.stButton > button[kind="primary"] {{
        color: {tok['accent']} !important;
        border: 1px solid {tok['accent']} !important;
    }}
    div.stButton > button[kind="primary"]:hover {{
        background-color: color-mix(in srgb, {tok['accent']} 12%, transparent) !important;
    }}

    /* 圖表卡片容器（st.container(border=True)） */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        border: 1px solid {tok['divider']} !important;
        border-radius: 7px !important;
        background-color: {tok['surface_alt']} !important;
        box-shadow: {tok['shadow']};
    }}
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 4. 側邊欄：使用者參數輸入區
# ==============================================================================

st.sidebar.markdown(
    f"<div style='font-size:12px;letter-spacing:.08em;text-transform:uppercase;"
    f"color:{tok['text_muted']};margin-bottom:-6px;'>查詢設定</div>",
    unsafe_allow_html=True,
)

# 股票與日期輸入
stock_id = st.sidebar.text_input("股票代號(如2330或AAPL)", "2330")
start_date = st.sidebar.date_input("起始日期(YYYY/MM/DD)", datetime(2025, 10, 1))
end_date = st.sidebar.date_input("結束日期(YYYY/MM/DD)", datetime.now())

st.sidebar.markdown(
    f"<hr style='border:none;border-top:1px solid {tok['divider']};margin:4px 0;'>",
    unsafe_allow_html=True,
)

# SAR 核心參數：AF (加速因子) —— 以 +/- 按鈕(number_input)取代滑桿
af_start = st.sidebar.number_input(
    "AF 起始值", min_value=0.01, max_value=0.10, value=0.02, step=0.01, format="%.2f"
)
af_max = st.sidebar.number_input(
    "AF 極限值", min_value=0.10, max_value=0.50, value=0.20, step=0.01, format="%.2f"
)

st.sidebar.markdown(
    f"<hr style='border:none;border-top:1px solid {tok['divider']};margin:4px 0;'>",
    unsafe_allow_html=True,
)

# 收盤價容許度 (避免因盤中影線誤觸導致頻繁轉向)(收盤價確認機制參數) —— 以 +/- 按鈕(number_input)取代滑桿
tolerance_pct = st.sidebar.number_input(
    "誤差容忍值%(預設1%)", min_value=0.0, max_value=5.0, value=1.0, step=0.5, format="%.1f"
)
up_tol = 1 - tolerance_pct / 100    # e.g. 1% → 0.99
down_tol = 1 + tolerance_pct / 100  # e.g. 1% → 1.01

st.sidebar.markdown(
    f"<hr style='border:none;border-top:1px solid {tok['divider']};margin:4px 0;'>",
    unsafe_allow_html=True,
)

# 視覺主題切換：以按鈕切換整頁亮/深色（對應網頁背景）
theme_label = "切換為深色" if not is_dark else "切換為亮色"
theme_icon = ":material/dark_mode:" if not is_dark else ":material/light_mode:"
theme_clicked = st.sidebar.button(theme_label, icon=theme_icon, type="secondary", use_container_width=True)

# 開始計算觸發按鈕
analyze_btn = st.sidebar.button("開始計算", type="primary", use_container_width=True)

if theme_clicked:
    st.session_state.is_dark = not st.session_state.is_dark
    st.rerun()

# ==============================================================================
# 5. 主程式執行邏輯
# ==============================================================================

st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;">
      <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="{tok['accent']}" stroke-width="1.6">
        <path d="M3 17l5-6 4 3 6-9"/><path d="M14 5h5v5"/>
      </svg>
      <h1 style="margin:0;font-size:36px;">改良版 SAR 趨勢追蹤系統 (K線版)</h1>
    </div>
    """, unsafe_allow_html=True)

if not analyze_btn:
    st.markdown(
        f"<div style='color:{tok['text_muted']};font-size:15px;margin-top:12px;'>"
        f"請點開左上角選單 [ >> ] 在左側面板設定參數後，按「開始計算」即可產出圖表</div>",
        unsafe_allow_html=True,
    )
else:
    # 依序嘗試：原始輸入 → 加 .TW → 加 .TWO
    candidates = [stock_id, f"{stock_id}.TW", f"{stock_id}.TWO"]
    data = pd.DataFrame()
    search_id = stock_id
    for candidate in candidates:
        data = yf.download(candidate, start=start_date, end=end_date, auto_adjust=True, progress=False)
        if not data.empty:
            search_id = candidate
            break

    # 顯示股票代碼
    st.markdown(
        f"<div style='margin-top:4px;font-family:\"Cormorant Garamond\",serif;"
        f"font-size:19px;color:{tok['text_muted']};'>{search_id}</div>",
        unsafe_allow_html=True,
    )

    if not data.empty:
        # [修正1] yfinance 0.2.x+ 新版本回傳 MultiIndex 欄位，須在 reset_index() 之前先扁平化
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # [修正2] yfinance 不同版本日期索引名稱不一致：
        #   舊版 → 'Date'，新版 → 'Datetime'
        #   強制統一命名為 'Date'，確保 reset_index() 後欄位名稱固定
        data.index.name = 'Date'

        df = data.copy().reset_index()

        # 格式化日期(用於 X 軸顯示)：移除 X 軸非交易日空隙的關鍵，先將日期轉為字串
        # 這樣會顯示成：Nov 02 2022
        df['Date_Str'] = df['Date'].dt.strftime('%b %d %Y')

        # 展平數據確保計算穩定
        df['Close_1D'] = df['Close'].values.flatten()
        df['High_1D'] = df['High'].values.flatten()
        df['Low_1D'] = df['Low'].values.flatten()
        df['Open_1D'] = df['Open'].values.flatten()

        # --- 請刪除這一段 ---
        # psar = df.ta.psar(high='High_1D', low='Low_1D', close='Close_1D',
        #                   af0=af_start, af=af_start, max_af=af_max)

        # if psar is not None:
        #     df['SAR_Long'] = psar.iloc[:, 0]
        #     df['SAR_Short'] = psar.iloc[:, 1]
        # else:
        #     df['SAR_Long'] = np.nan
        #     df['SAR_Short'] = np.nan

        # --- [取代為此段] 改良版 SAR 核心計算法 ---
        df['SAR'] = np.nan
        df['Trend'] = 0  # 趨勢標記：1 為多頭, -1 為空頭

        # 初始趨勢判斷：若第一天收紅則初步看多
        initial_trend = 1 if df['Close_1D'].iloc[0] > df['Open_1D'].iloc[0] else -1
        curr_trend = initial_trend
        curr_af = af_start
        # 初始 SAR 位在低點(多)或高點(空)
        curr_sar = df['Low_1D'].iloc[0] if initial_trend == 1 else df['High_1D'].iloc[0]
        # EP (極值點)：多頭為最高價，空頭為最低價
        ep = df['High_1D'].iloc[0] if initial_trend == 1 else df['Low_1D'].iloc[0]

        for i in range(len(df)):
            c_high, c_low, c_close = df['High_1D'].iloc[i], df['Low_1D'].iloc[i], df['Close_1D'].iloc[i]
            df.iat[i, df.columns.get_loc('SAR')] = curr_sar
            df.iat[i, df.columns.get_loc('Trend')] = curr_trend

            next_trend, next_af = curr_trend, curr_af

            # --- 多頭趨勢判斷 ---
            if curr_trend == 1: # 上升趨勢(創新高)
                if c_high > ep:
                    ep = c_high
                    next_af = min(curr_af + af_start, af_max) # 增加加速因子

                if c_low <= curr_sar: # 觸碰點位(盤中跌破 SAR)
                    # [改良邏輯] 若收盤價仍高於 SAR*容許比例，則不轉向，僅重置 AF 並調整 SAR 位置
                    if c_close > curr_sar * up_tol:
                        next_af, ep = af_start, c_high
                        next_sar = c_low # 重置為當日低點
                    else: # 未能守住，標準反轉(真正收破：轉向為空頭)
                        next_trend, next_af, next_sar, ep = -1, af_start, ep, c_low
                else: # 正常上升(沒觸碰)
                    next_sar = curr_sar + curr_af * (ep - curr_sar)
                    # 確保 SAR 不會高於前兩日低點
                    if i > 0: next_sar = min(next_sar, c_low, df['Low_1D'].iloc[i-1])

            # --- 空頭趨勢判斷 ---
            else: # 下降趨勢(創新低)
                if c_low < ep:
                    ep = c_low
                    next_af = min(curr_af + af_start, af_max)

                if c_high >= curr_sar: # 觸碰點位(盤中突破 SAR)
                    # [改良邏輯] 若收盤價仍低於 SAR*容許比例，不轉向
                    if c_close < curr_sar * down_tol:
                        next_af, ep = af_start, c_low
                        next_sar = c_high # 重置為當日高點
                    else: # 未能守住，標準反轉(真正收過：轉向為多頭)
                        next_trend, next_af, next_sar, ep = 1, af_start, ep, c_high
                else: # 正常下降(沒觸碰)
                    next_sar = curr_sar + curr_af * (ep - curr_sar)
                    # 確保 SAR 不會低於前兩日高點
                    if i > 0: next_sar = max(next_sar, c_high, df['High_1D'].iloc[i-1])

            curr_sar, curr_trend, curr_af = next_sar, next_trend, next_af

        # 將 SAR 分拆為多空兩欄，方便 Plotly 著色（紅點與綠點）
        df['SAR_Long'] = df.apply(lambda x: x['SAR'] if x['Trend'] == 1 else np.nan, axis=1)
        df['SAR_Short'] = df.apply(lambda x: x['SAR'] if x['Trend'] == -1 else np.nan, axis=1)


        # ==============================================================================
        # 6. 繪圖與互動優化
        # ==============================================================================
        fig = go.Figure()

        # 使用 Date_Str (字串日期) 當 X 軸，避開假日空隙
        fig.add_trace(go.Candlestick(
            x=df['Date_Str'], open=df['Open_1D'], high=df['High_1D'], low=df['Low_1D'], close=df['Close_1D'],
            name='K線', increasing_line_color=tok['candle']['up'], decreasing_line_color=tok['candle']['down']
        ))

        # 多頭支撐點 (紅色)
        fig.add_trace(go.Scatter(
            x=df['Date_Str'], y=df['SAR_Long'], name='多頭支撐', mode='markers',
            marker=dict(size=4, color=tok['candle']['up'], symbol='circle')
        ))

        # 空頭壓力點 (綠色)
        fig.add_trace(go.Scatter(
            x=df['Date_Str'], y=df['SAR_Short'], name='空頭壓力', mode='markers',
            marker=dict(size=4, color=tok['candle']['down'], symbol='circle')
        ))

        # 新增 rangebreaks 或將 xaxis 類型改為 category 以消除缺口
        fig.update_layout(
            height=700,
            template=chart_template,
            xaxis_rangeslider_visible=False, # 隱藏滑動條讓圖表乾淨
            hovermode='x unified',
            font=dict(color=tok['text'], family='Lora, serif'),
            # 關鍵修正：將 xaxis 類型設為 category，配合 Date_Str 使用以忽略非交易日
            xaxis=dict(
                type='category',
                color=tok['text'],
                tickfont=dict(color=tok['text']),
                gridcolor=tok['grid_line'],
                nticks=8  # 限制顯示的座標標籤數量，避免字體重疊
            ),
            yaxis=dict(color=tok['text'], tickfont=dict(color=tok['text']), gridcolor=tok['grid_line']),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(color=tok['text_muted'], family='Lora, serif')
            ),
            paper_bgcolor=tok['surface_alt'],
            plot_bgcolor=tok['surface_alt']
        )

        with st.container(border=True):
            st.plotly_chart(fig, use_container_width=True)

        # ==============================================================================
        # 7. 數據摘要指標
        # ==============================================================================
        st.markdown("<h4 style='margin:28px 0 16px;'>最新狀態</h4>", unsafe_allow_html=True)
        valid_df = df.dropna(subset=['Close_1D'])

        if not valid_df.empty:
            last_price = valid_df['Close_1D'].iloc[-1]

            is_long = not pd.isna(df['SAR_Long'].iloc[-1])
            trend_text = "看漲 (多頭)" if is_long else "看跌 (空頭)"
            sar_val = df['SAR_Long'].iloc[-1] if is_long else df['SAR_Short'].iloc[-1]
            sar_label = "SAR 支撐位置" if is_long else "SAR 壓力位置"

            def _stat_card(label, value):
                return f"""
                <div style="border:1px solid {tok['divider']};border-radius:4px;padding:20px 22px;">
                  <div style="font-size:12px;color:{tok['text_muted']};margin-bottom:8px;">{label}</div>
                  <div style="font-family:'Cormorant Garamond',serif;font-size:28px;color:{tok['text']};font-variant-numeric:tabular-nums;">{value}</div>
                </div>
                """

            col1, col2, col3 = st.columns(3)
            col1.markdown(_stat_card("目前趨勢", trend_text), unsafe_allow_html=True)
            col2.markdown(_stat_card("收盤價", f"{last_price:.2f}"), unsafe_allow_html=True)
            col3.markdown(_stat_card(sar_label, f"{sar_val:.2f}"), unsafe_allow_html=True)

    else:
        st.error(f"找不到股票資料（已嘗試：{', '.join(candidates)}），請檢查代號或日期。")

# 1.收盤價容許區間：
#     在上升趨勢中，判斷條件改為 c_close > curr_sar * 0.99。即使盤中低價穿過 SAR，只要收盤沒跌破 SAR 的 99%，趨勢就不會反轉，而是重置計算。
#     在下降趨勢中，則為 c_close < curr_sar * 1.01。
# 2.重置機制：
#     當觸發改良邏輯時，程式碼會執行 next_af = af_start（重置加速因子）以及 next_sar = c_low (或 c_high)，這能讓 SAR 點位更緊貼當日的影線。
# 3.繪圖銜接：
#     最後兩行將計算出的 SAR 根據 Trend 拆分回 SAR_Long 與 SAR_Short，這樣您後續的 Plotly 繪圖程式碼（紅點與綠點）完全不需要更動即可直接使用。
