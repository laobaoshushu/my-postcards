import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import pydeck as pdk
import os

st.set_page_config(page_title="数字博物馆", layout="wide")
st.title("📯 极限明信片自动化管理系统")

# ─── 初始化模拟数据库 ───
if 'db' not in st.session_state:
    st.session_state.db = [
        {
            "id": "生肖鼠_示例", 
            "title": "中华十二生肖 - 子鼠", 
            "status": "已入库",
            "front_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035293_iOS.jpg",
            "back_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035328_iOS.jpg",
            "is_file_object": False,
            "date_from": "2026-03-20", 
            "date_to": "2026-03-25",
            "loc_from": "贵州开阳", 
            "loc_to": "广东广州",
            "from_lon": 106.96, 
            "from_lat": 27.06, 
            "to_lon": 113.26, 
            "to_lat": 23.13,
            "rating": 5, 
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
    st.header("🖼️ 极限片陈列馆")
    search = st.text_input("🔍 搜索系列、地名、路线...")
    
    display_cards = []
    for c in st.session_state.db:
        if not search or search in c['title'] or search in c['loc_from']:
            display_cards.append(c)
            
    if display_cards:
        cols = st.columns(3)
        for idx, card in enumerate(display_cards):
            with cols[idx % 3]:
                st.subheader(card['title'])
                t1, t2 = st.tabs(["🌟 正面图案", "📬 邮戳面(脱敏)"])
                with t1: 
                    st.image(card['front_url'], use_column_width=True)
                with t2:
                    if not card['is_file_object']:
                        st.image(card['back_url'], use_column_width=True)
                    else:
                        p_back = apply_mosaic_tape(card['back_url'], card['crop_box'])
                        st.image(p_back, use_column_width=True)
                st.write(f"路线: {card['loc_from']} -> {card['loc_to']}")
                st.write(f"评分: {'⭐' * card['rating']}")
                st.markdown("---")

# ==================== 页签 2：批量录入后台 ====================
with tabs[1]:
    st.header("📥 批量自动化处理台")
    uploaded_files = st.file_uploader("批上传", accept_multiple_files=True, type=["jpg","png","jpeg"])
    
    if uploaded_files:
        fronts, backs = {}, {}
        for f in uploaded_files:
            name, ext = os.path.splitext(f.name)
            # 💡 核心优化：兼容“正面/F”，以及“反面/背面/B”的命名方式
            if "正面" in name or "_F" in name or "-正面" in name:
                k = name.replace("正面","").replace("_F","").replace("-","")
                fronts[k] = f
            elif "反面" in name or "背面" in name or "_B" in name or "-反面" in name or "-背面" in name:
                k = name.replace("反面","").replace("背面","").replace("_B","").replace("-","")
                backs[k] = f
                
        matched_keys = set(fronts.keys()) & set(backs.keys())
        st.write(f"成功配对: {len(matched_keys)} 组明信片")
        
        for key in matched_keys:
            exists = any(d['id'] == key for d in st.session_state.db)
            if not exists:
                st.info(f"✅ 成功录入组: {key}")
                img_front = Image.open(fronts[key]).convert("RGB")
                img_back = Image.open(backs[key]).convert("RGB")
                
                st.session_state.db.append({
                    "id": key, 
                    "title": f"中华十二生肖 - {key}", 
                    "status": "AI已自动打码",
                    "front_url": img_front, 
                    "back_url": img_back, 
                    "is_file_object": True,
                    "date_from": "2026-03-20", 
                    "date_to": "2026-03-25",
                    "loc_from": "贵州开阳", 
                    "loc_to": "广东广州",
                    "from_lon": 106.96, 
                    "from_lat": 27.06, 
                    "to_lon": 113.26, 
                    "to_lat": 23.13,
                    "rating": 4, 
                    "crop_box": None
                })
                
    st.markdown("---")
    st.subheader("🛠️ 管理库与手动二次修正")
    
    for idx, card in enumerate(st.session_state.db):
        col_name, col_status, col_btn = st.columns([4, 2, 2])
        with col_name: 
            st.write(f"[{card['id']}]")
        with col_status: 
            st.write(f"状态: `{card['status']}`")
        with col_btn:
            if card['is_file_object']:
                if st.button("手动修正", key=f"edit_{card['id']}"):
                    st.session_state.current_edit_id = card['id']
            else:
                st.button("示例数据不可改", disabled=True, key=f"edit_dis_{card['id']}")
                
    if st.session_state.current_edit_id:
        st.markdown("### 🎯 手动修正模式")
        from streamlit_cropper import st_cropper
        
        c_id = st.session_state.current_edit_id
        target = next(d for d in st.session_state.db if d['id'] == c_id)
        st.write("请在下方图片上拖拽红框对准地址：")
        
        cropped_box = st_cropper(
            target['back_url'], 
            realtime_update=True, 
            box_color='#FF0000', 
            aspect_ratio=None, 
            return_type='box'
        )
        
        if st.button("保存遮挡选区"):
            x1 = int(cropped_box['left'])
            y1 = int(cropped_box['top'])
            x2 = x1 + int(cropped_box['width'])
            y2 = y1 + int(cropped_box['height'])
            target['crop_box'] = (x1, y1, x2, y2)
            target['status'] = "已完成人工核对"
            st.session_state.current_edit_id = None
            st.success("更新成功！")
            st.rerun()

# ==================== 页签 3：轨迹地图 ====================
with tabs[2]:
    st.header("🗺️ 极限片邮路足迹馆")
    plot_data = []
    for card in st.session_state.db:
        id_str = card['id']
        f_lon = card['from_lon']
        f_lat = card['from_lat']
        t_lon = card['to_lon']
        t_lat = card['to_lat']
        
        plot_data.append({"names": f"{id_str}-寄出", "lon": f_lon, "lat": f_lat})
        plot_data.append({"names": f"{id_str}-寄达", "lon": t_lon, "lat": t_lat})
    
    df = pd.DataFrame(plot_data)
    if not df.empty:
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=pdk.ViewState(latitude=30.0, longitude=108.0, zoom=4, pitch=30),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer', 
                    data=df, 
                    get_position='[lon, lat]', 
                    get_color='[230, 30, 30, 160]', 
                    get_radius=50000
                ),
                pdk.Layer(
                    'ArcLayer', 
                    data=pd.DataFrame(st.session_state.db), 
                    get_source_position='[from_lon, from_lat]', 
                    get_target_position='[to_lon, to_lat]', 
                    get_source_color='[230, 30, 30]', 
                    get_target_color='[250, 200, 0]', 
                    stroke_width=3
                )
            ]
        ))
