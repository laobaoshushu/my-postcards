import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import pydeck as pdk
import os

st.set_page_config(page_title="数字博物馆", layout="wide")
st.title("📯 极限明信片自动化管理系统 (V1.1)")

# ─── 初始化模拟数据库 ───
if 'db' not in st.session_state:
    st.session_state.db = [
        {
            "id": "生肖鼠_示例", 
            "title": "中华十二生肖 - 子鼠", 
            "status": "已入库",
            "front_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035293_iOS.jpg",
            "back_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035328_iOS.jpg",
            "is_file": False,
            "date_from": "2026-03-20", 
            "date_to": "2026-03-25",
            "loc_from": "贵州开阳", 
            "loc_to": "广东广州",
            "from_lon": 106.96, 
            "from_lat": 27.06, 
            "to_lon": 113.26, 
            "to_lat": 23.13,
            "rating": 5, 
            "ai_reason": "完美品相。画面完整，无折痕、污渍、掉齿，油墨清晰规整。",
            "notes": "无", 
            "crop_box": None
        }
    ]
if 'current_edit_id' not in st.session_state: 
    st.session_state.current_edit_id = None

# ─── 核心马赛克算法 ───
def apply_mosaic_tape(img, box=None):
    img_np = np.array(img)
    h_orig, w_orig, _ = img_np.shape
    if box is None:
        x1 = int(w_orig * 0.64)
        y1 = int(h_orig * 0.53)
        x2 = int(w_orig * 0.96)
        y2 = int(h_orig * 0.82)
    else:
        x1, y1, x2, y2 = box
    cropped = img_np[y1:y2, x1:x2]
    if cropped.size == 0: 
        return img
    h_z, w_z, _ = cropped.shape
    p_size = 5
    c1, c2, c3 = [245, 215, 215], [252, 242, 215], [248, 248, 242]
    for y in range(0, h_z, p_size):
        for x in range(0, w_z, p_size):
            y_e = min(y + p_size, h_z)
            x_e = min(x + p_size, w_z)
            val = (x // p_size) + (y // p_size)
            chosen = c1 if val % 3 == 0 else (c2 if val % 3 == 1 else c3)
            cropped[y:y_e, x:x_e] = chosen
    img_np[y1:y2, x1:x2] = cropped
    return Image.fromarray(img_np)

# ─── 拆解标签页定义，防止长行截断 ───
tab_names = ["🏛️ 数字化陈列展厅", "⚙️ 批量新片入库后台", "🗺️ 邮戳足迹轨迹地图"]
tabs = st.tabs(tab_names)

# ==================== 页签 1：陈列展厅 ====================
with tabs[0]:
    st.header("🖼️ 极限片公众陈列馆")
    search = st.text_input("🔍 搜索系列、地名、路线...")
    
    display_cards = []
    for c in st.session_state.db:
        t_str = c.get('title', '')
        l_str = c.get('loc_from', '')
        if not search or search in t_str or search in l_str:
            display_cards.append(c)
            
    if display_cards:
        cols = st.columns(3)
        for idx, card in enumerate(display_cards):
            with cols[idx % 3]:
                st.subheader(card.get('title', '未命名'))
                
                # 💡 拆解 st.tabs 这一行，彻底防范 SyntaxError
                sub_tabs = ["🌟 正面图案", "📬 邮戳面(脱敏)"]
                t1, t2 = st.
