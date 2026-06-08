import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import pydeck as pdk
import os

st.set_page_config(page_title="数字博物馆", layout="wide")
st.title("📯 极限明信片自动化管理系统 (V1.1)")

# ─── 数据库初始化 (采用标准的字典结构，防止任何键值缺失) ───
if 'db' not in st.session_state:
    st.session_state.db = [
        {
            "id": "生肖鼠_示例", 
            "title": "中华十二生肖 - 子鼠", 
            "status": "已入库",
            "front_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035293_iOS.jpg",
            "back_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035328_iOS.jpg",
            "is_file": False,
            "date_from": "2026-03-20", "date_to": "2026-03-25",
            "loc_from": "贵州开阳", "loc_to": "广东广州",
            "from_lon": 106.96, "from_lat": 27.06, "to_lon": 113.26, "to_lat": 23.13,
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
    c1 = [245, 215, 215]
    c2 = [252, 242, 215]
    c3 = [248, 248, 242]
    for y in range(0, h_z, p_size):
        for x in range(0, w_z, p_size):
            y_e = min(y + p_size, h_z)
            x_e = min(x + p_size, w_z)
            val = (x // p_size) + (y // p_size)
            if val % 3 == 0:
                chosen = c1
            elif val % 3 == 1:
                chosen = c2
            else:
                chosen = c3
            cropped[y:y_e, x:x_e] = chosen
    img_np[y1:y2, x1:x2] = cropped
    return Image.fromarray(img_np)

# ─── 页面导航 ───
tabs = st.tabs(["🏛️ 数字化陈列展厅", "⚙️ 批量新片入库后台", "🗺️ 邮戳足迹轨迹地图"])

# ==================== 页签 1：陈列展厅 ====================
with tabs[0]:
    st.header("🖼️ 极限片公众陈列馆")
    search = st.text_input("🔍 搜索系列、地名、路线...")
    
    # 采用更稳健的循环过滤，防止在读取中崩溃
    display_cards = []
    for c in st.session_state.db:
        # 使用 .get() 函数防守，如果键不存在则默认返回空或错误，绝不崩溃
        title_str = c.get('title', '')
        loc_str = c.get('loc_from', '')
        if not search or search in title_str or search in loc_str:
            display_cards.append(c)
            
    if display_cards:
        cols = st.columns(3)
        for
