import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import pydeck as pdk
import os

st.set_page_config(page_title="极限明信片数字博物馆", layout="wide")
st.title("📯 极限明信片数字化管理与陈列系统 (V1.1)")

# ─── 1. PRD 附录：核心数据结构定义 ───
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
            "rating": 5,          # PRD 3.2.3 品相评级
            "ai_reason": "完美品相。画面完整，无折痕、污渍、掉齿，油墨清晰规整。", # PRD 附录：AI评级依据
            "notes": "无",        # PRD 附录：瑕疵备注
            "crop_box": None
        }
    ]
if 'current_edit_id' not in st.session_state: 
    st.session_state.current_edit_id = None

# ─── 2. 核心马赛克涂改带算法 ───
def apply_mosaic_tape(img, box=None):
    img_np = np.array(img)
    h_o, w_o, _ = img_np.shape
    if box is None:
        x1, y1, x2, y2 = int(w_o * 0.64), int(h_o * 0.53), int(w_o * 0.96), int(h_o * 0.82)
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
            y_e, x_e = min(y + p_size, h_z), min(x + p_size, w_z)
            val = (x // p_size) + (y // p_size)
            chosen = c1 if val % 3 == 0 else (c2 if val % 3 == 1 else c3)
            cropped[y:y_e, x:x_e] = chosen
    img_np[y1:y2, x1:x2] = cropped
    return Image.fromarray(img_np)

# ─── 3. 系统控制台也签页 ───
tabs = st.tabs(["🏛️ 数字化陈列展厅", "⚙️ 批量新片入库后台", "🗺️ 邮戳足迹轨迹地图"])

# ==================== 页签 1：陈列展厅（前端展示） ====================
with tabs[0]:
    st.header("🖼️ 极限片公众陈列馆")
    search = st.text_input("🔍 搜索系列、地名、路线...")
    
    display_cards = [c for c in st.session_state.db if not search or search in c['title'] or search in c['loc_from']]
    
    if display_cards:
        cols = st.columns(3)
        for idx, card in enumerate(display_cards):
            with cols[idx % 3]:
                st.subheader(card['title'])
                t1, t2 = st.tabs(["🌟 正面图案", "📬 邮戳面(脱敏)"])
                with t1: 
                    st.image(card['front_url'], use_column_width=True)
                with t2:
                    if not card['is_file']:
                        st.image(card['back_url'], use_column_width=True)
                    else:
                        p_back = apply_mosaic_tape(card['back_url'], card['crop_box'])
                        st.image(p_back, use_column_width=True)
                st.write(f"路线: {card['loc_from']} -> {card['loc_to']}")
                st.write(f"品相评级: {'⭐' * card['rating']} ({card['rating']}分)") # 线上仅展示分数
                st.markdown("---")

# ==================== 页签 2：批量录入与管理（后台） ====================
with tabs[1]:
    st.header("📥 批量处理与后台数据核对")
    
    # PRD 3.2.3.5 批量上传组件
    uploaded_files = st.file_uploader("拖拽批量上传图片", accept_multiple_files=True, type=["jpg","png","jpeg"])
    
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
                
        matched_keys = set(fronts.keys()) & set(backs.keys())
        st.write(f"成功配对: {len(matched_keys)} 组明信片")
        
        for key in matched_keys:
            if not any(d['id'] == key for d in st.session_state.db):
                st.info(f"✅ 自动入库: {key}")
                img_front = Image.open(fronts[key]).convert("RGB")
                img_back = Image.open(backs[key]).convert("RGB")
                
                # ─── PRD 3.2.3.4: 模拟触发AI自动品相检测与信息提取 ───
                st.session_state.db.append({
                    "id": key, 
                    "title": f"中华十二生肖 - {key}", 
                    "status": "AI已自动评级打码",
                    "front_url": img_front, "back_url": img_back, "is_file": True,
                    "date_from": "2026-03-20", "date_to": "2026-03-25",
                    "loc_from": "贵州开阳", "loc_to": "广东广州",
                    "from_lon": 106.96, "from_lat": 27.06, "to_lon": 113.26, "to_lat": 23.13,
                    "rating": 4, # AI基于规则自动给出的初始评分
                    "ai_reason": "纸面边缘有可见轻微磨损，无破损硬折。判定为良好品相(4分)。", # PRD 3.2.3.4.2 AI判定摘要
                    "notes": "", 
                    "crop_box": None
                })
                
    st.markdown("---")
    st.subheader("🛠️ 资产流核对控制台 (管理员可见)")
    
    for idx, card in enumerate(st.session_state.db):
        expander_title = f"[{card['id']}] {card['title']} | 状态: {card['status']}"
        with st.expander(expander_title):
            c_info, c_ai, c_action = st.columns([3, 3, 2])
            with c_info:
                st.markdown(f"路线: -> {card['loc_to']}")
                st.markdown(f"收发时间: / {card['date_to']}")
                # 管理员可在此手动修正评级 (PRD 3.2.3.4.3)
                new_rating = st.slider("品相评分修正", 1, 5, int(card['rating']), key=f"rate_v_{card['id']}")
                if new_rating != card['rating']:
                    card['rating'] = new_rating
                    card['status'] = "已人工核对修改"
            with c_ai:
                st.warning(f"🤖 AI评级依据:") # 仅后台可见
                # 管理员补充瑕疵说明 (PRD 3.2.3.4.4)
                card['notes'] = st.text_area("✍️ 补充人工瑕疵备注", value=card['notes'], key=f"note_v_{card['id']}")
            with c_action:
                if card['is_file']:
                    if st.button("🎯 二次手动修剪隐私选区", key=f"edit_{card['id']}"):
                        st.session_state.current_edit_id = card['id']
                else:
                    st.write("预载示例不支持网页端修剪")
                    
    # 手动修正遮挡弹窗
    if st.session_state.current_edit_id:
        st.markdown("### 🎯 隐私区域纠偏模式")
        from streamlit_cropper import st_cropper
        target = next(d for d in st.session_state.db if d['id'] == st.session_state.current_edit_id)
        
        cropped_box = st_cropper(target['back_url'], realtime_update=True, box_color='#FF0000', aspect_ratio=None, return_type='box')
        if st.button("确认并锁定隐私遮挡"):
            x1, y1 = int(cropped_box['left']), int(cropped_box['top'])
            x2, y2 = x1 + int(cropped_box['width']), y1 + int(cropped_box['height'])
            target['crop_box'] = (x1, y1, x2, y2)
            target['status'] = "已完成复核"
            st.session_state.current_edit_id = None
            st.success("遮挡范围已更新！")
            st.rerun()

# ==================== 页签 3：轨迹地图 ====================
with tabs[2]:
    st.header("🗺️ 极限片邮路足迹馆")
    plot_data = []
    for card in st.session_state.db:
        plot_data.append({"names": f"{card['id']}-发", "lon": card['from_lon'], "lat": card['from_lat']})
        plot_data.append({"names": f"{card['id']}-达", "lon": card['to_lon'], "lat": card['to_lat']})
    
    df = pd.DataFrame(plot_data)
    if not df.empty:
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=pdk.ViewState(latitude=30.0, longitude=108.0, zoom=4, pitch=30),
            layers=[
                pdk.Layer('ScatterplotLayer', data=df, get_position='[lon, lat]', get_color='[230, 30, 30, 160]', get_radius=50000),
                pdk.Layer('ArcLayer', data=pd.DataFrame(st.session_state.db), get_source_position='[from_lon, from_lat]', get_target_position='[to_lon, to_lat]', get_source_color='[230, 30, 30]', get_target_color='[250, 200, 0]', stroke_width=3)
            ]
        ))
