import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import pydeck as pdk
import os

# ─── 1. 隔离所有长中文常量 ───
PAGE_TITLE = "数字博物馆"
SYS_TITLE = "📯 明信片管理系统"
SEARCH_TIPS = "🔍 搜索..."
BACK_TAPE = "📬 邮戳面(脱敏)"
FRONT_TITLE = "🌟 正面图案"
PANEL_TITLE = "🖼️ 公众陈列馆"
ADMIN_PANEL = "📥 批量入库后台"
ADMIN_TITLE = "🛠️ 资产流核对控制台"
CROP_TITLE = "🎯 隐私区域纠偏"

# ─── 2. 系统核心初始化 ───
st.set_page_config(
    page_title=PAGE_TITLE, 
    layout="wide"
)
st.title(SYS_TITLE)

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
            "ai_reason": "完美品相",
            "notes": "无", 
            "crop_box": None
        }
    ]
if 'current_edit_id' not in st.session_state: 
    st.session_state.current_edit_id = None

# ─── 3. 马赛克算法 ───
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

# ─── 4. 多功能导航 ───
tab_names = [
    "🏛️ 数字化陈列展厅", 
    "⚙️ 批量新片入库后台", 
    "🗺️ 邮戳足迹轨迹地图"
]
tabs = st.tabs(tab_names)

# ==================== 页签 1：数字化陈列展厅 ====================
with tabs[0]:
    st.header(PANEL_TITLE)
    search = st.text_input(SEARCH_TIPS)
    
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
                
                # 💡 彻底切碎，防止截断
                sub_tabs_list = [FRONT_TITLE, BACK_TAPE]
                t1, t2 = st.tabs(sub_tabs_list)
                
                with t1: 
                    st.image(
                        card.get('front_url'), 
                        use_column_width=True
                    )
                with t2:
                    if not card.get('is_file', False):
                        st.image(
                            card.get('back_url'), 
                            use_column_width=True
                        )
                    else:
                        b_obj = card.get('back_url')
                        b_box = card.get('crop_box')
                        p_back = apply_mosaic_tape(b_obj, b_box)
                        st.image(
                            p_back, 
                            use_column_width=True
                        )
                # 💡 拆解长打印短句，每一行都极短
                c_from = card.get('loc_from', '-')
                c_to = card.get('loc_to', '-')
                c_rate = card.get('rating', 5)
                st.write(f"路线: {c_from} -> {c_to}")
                st.write(f"评分: {'⭐' * c_rate} ({c_rate}分)")
                st.markdown("---")

# ==================== 页签 2：批量新片入库后台 ====================
with tabs[1]:
    st.header(ADMIN_PANEL)
    uploaded_files = st.file_uploader(
        "批上传", 
        accept_multiple_files=True, 
        type=["jpg","png","jpeg"]
    )
    
    if uploaded_files:
        fronts, backs = {}, {}
        for f in uploaded_files:
            name, ext = os.path.splitext(f.name)
            if "正面" in name or "_F" in name or "-正面" in name:
                k = name.replace("正面","").replace("_F","").replace("-","")
                fronts[k] = f
            elif "反面" in name or "背面" in name or "_B" in name or "-反面" in name or "-背面" in name:
                k = name.replace("反面","").replace("背面","").replace("_B","").replace("-","")
                backs[k] = f
                
        matched_keys = set(
