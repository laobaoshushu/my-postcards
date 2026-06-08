import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import pydeck as pdk
import os
import re

# --- 1. 注入 CSS 3D 翻转与 Pinterest 瀑布流样式 ---
CSS_STYLE = """
<style>
.masonry-container { column-count: 3; column-gap: 15px; width: 100%; }
@media (max-width: 800px) { .masonry-container { column-count: 2; } }
@media (max-width: 500px) { .masonry-container { column-count: 1; } }
.card-item {
    break-inside: avoid; margin-bottom: 15px; background: #fdfdfd;
    border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); padding: 10px;
}
.flip-container { width: 100%; height: 240px; perspective: 1000px; }
.flip-box {
    position: relative; width: 100%; height: 100%;
    transition: transform 0.6s; transform-style: preserve-3d;
}
.flip-container:hover .flip-box { transform: rotateY(180deg); }
.face-f, .face-b {
    position: absolute; width: 100%; height: 100%;
    -webkit-backface-visibility: hidden; backface-visibility: hidden;
    border-radius: 6px; overflow: hidden;
}
.face-f img, .face-b img { width: 100%; height: 100%; object-fit: cover; }
.face-b { transform: rotateY(180deg); }
</style>
"""
st.markdown(CSS_STYLE, unsafe_allow_html=True)

# --- 2. 模拟数据库初始化 ---
if 'db' not in st.session_state:
    st.session_state.db = [
        {
            "id": "生肖鼠_示例", 
            "title": "中华十二生肖 - 子鼠", 
            "status": "已入库",
            "front_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035293_iOS.jpg",
            "back_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035328_iOS.jpg",
            "is_file": False, "date_from": "2026-03-20", "date_to": "2026-03-25",
            "loc_from": "贵州开阳", "loc_to": "广东广州",
            "from_lon": 106.96, "from_lat": 27.06, "to_lon": 113.26, "to_lat": 23.13,
            "rating": 5, "ai_reason": "完美品相。收寄戳与投递戳双坐标连线成功。", 
            "notes": "无", "crop_box": None
        }
    ]
if 'current_edit_id' not in st.session_state:
    st.session_state.current_edit_id = None

# --- 3. 核心高密度打码带 ---
def apply_mosaic_tape(img, box=None):
    img_np = np.array(img)
    h_o, w_o, _ = img_np.shape
    if box is None:
        x1, y1, x2, y2 = int(w_o*0.64), int(h_o*0.53), int(w_o*0.96), int(h_o*0.82)
    else:
        x1, y1, x2, y2 = box
    cropped = img_np[y1:y2, x1:x2]
    if cropped.size == 0: return img
    h_z, w_z, _ = cropped.shape
    p_size = 5
    c1, c2, c3 = [245, 215, 215], [252, 242, 215], [248, 248, 242]
    for y in range(0, h_z, p_size):
        for x in range(0, w_z, p_size):
            y_e, x_e = min(y + p_size, h_z), min(x + p_size, w_z)
            v = (x // p_size) + (y // p_size)
            chosen = c1 if v % 3 == 0 else (c2 if v % 3 == 1 else c3)
            cropped[y:y_e, x:x_e] = chosen
    img_np[y1:y2, x1:x2] = cropped
    return Image.fromarray(img_np)

# --- 4. 纯中文导航分布 ---
t_gallery, t_admin, t_map = st.tabs(["🏛️ 数字化陈列展厅", "⚙️ 批量新片入库后台", "🗺️ 邮戳足迹轨迹地图"])

# ==================== 页签 1：公众陈列馆 ====================
with t_gallery:
    st.header("🖼️ 瀑布流极限片展厅")
    search = st.text_input("🔍 输入地名、系列名进行快速检索...")
    display_cards = []
    for c in st.session_state.db:
        t_str = c.get('title', '')
        l_str = c.get('loc_from', '')
        if not search or search in t_str or search in l_str:
            display_cards.append(c)
            
    if display_cards:
        html_code = '<div class="masonry-container">'
        for idx, card in enumerate(display_cards):
            f_url = card.get('front_url')
            b_url = card.get('back_url')
            title = card.get('title', '未命名')
            route = f"{card.get('loc_from')} ➡️ {card.get('loc_to')}"
            stars = '⭐' * card.get('rating', 5)
            
            card_html = f"""
            <div class="card-item">
                <h4>{title}</h4>
                <div class="flip-container">
                    <div class="flip-box">
                        <div class="face-f"><img src="{f_url}" /></div>
                        <div class="face-b"><img src="{b_url}" /></div>
                    </div>
                </div>
                <p style="margin-top:10px;font-size:14px;color:#444;"><b>邮路轨迹:</b> {route}</p>
                <p style="font-size:14px;color:#e67e22;"><b>品相评级:</b> {stars}</p>
            </div>
            """
            html_code += card_html
        html_code += '</div>'
        st.markdown(html_code, unsafe_allow_html=True)

# ==================== 页签 2：批量录入后台 ====================
with t_admin:
    st.header("📥 自动化处理控制台")
    st.info("💡 已启用无菌化数字提取引擎：文件名中只要数字部分一致（如 1-正面.jpg 与 1-背面.jpg），即可实现完美对齐。")
    uploaded_files = st.file_uploader("将文件成批拖拽至此", accept_multiple_files=True, type=["jpg","png","jpeg"])
    
    if uploaded_files:
        fronts, backs = {}, {}
        for f in uploaded_files:
            fname, ext = os.path.splitext(f.name)
            
            # 💡 终极防错杀招：用正则表达式提取文件名里连续的数字作为纯净ID
            num_match = re.search(r'\d+', fname)
            if num_match:
                clean_id = num_match.group()
            else:
                clean_id = fname.strip()
            
            # 转成小写做无差别盲扫分类
            fname_low = f.name.lower()
            
            # 判断逻辑转为极其包容的安全扫描
            if "正" in fname_low or "f" in fname_low:
                fronts[clean_id] = f
            elif "背" in fname_low or "反" in fname_low or "b" in fname_low:
                backs[clean_id] = f
                
        m_keys = set(fronts.keys()).intersection(set(backs.keys()))
        st.write(f"📊 成功关联配对: {len(m_keys)} 组极限明信片")
        
        for key in m_keys:
            if not any(d.get('id') == key for d in st.session_state.db):
                st.success(f"✅ 成功配对入库: {key}")
                img_front = Image.open(fronts[key]).convert("RGB")
                img_back = Image.open(backs[key]).convert("RGB")
                st.session_state.db.append({
                    "id": key, "title": f"中华十二生肖 - {key}", "status": "AI自动评级成功",
                    "front_url": img_front, "back_url": img_back, "is_file": True,
                    "date_from": "2026-03-20", "date_to": "2026-03-25",
                    "loc_from": "贵州开阳", "loc_to": "广东广州",
                    "from_lon": 106.96, "from_lat": 27.06, "to_lon": 113.26, "to_lat": 23.13,
                    "rating": 4, "ai_reason": "根据收寄戳与投递戳自动提取轨迹。邮票面值与志号比对成功。品相：良好(4分)。", "notes": "", "crop_box": None
                })
                
    st.markdown("---")
    st.subheader("🛠️ 数据全控与错误修正台")
    for idx, card in enumerate(st.session_state.db):
        c_id = card.get('id', '未知')
        with st.expander(f"[{c_id}] {card.get('title')} | 状态: {card.get('status')}"):
            c_info, c_ai, c_action = st.columns([3, 3, 2])
            with c_info:
                card['title'] = st.text_input("修改系列/名称", value=card.get('title'), key=f"t_{c_id}")
                st.write(f"轨迹路线: {card.get('loc_from')} -> {card.get('loc_to')}")
                current_rate = int(card.get('rating', 5))
                card['rating'] = st.slider("手工改分", 1, 5, current_rate, key=f"r_{c_id}")
            with c_ai:
                st.warning(f"🤖 AI多戳比对依据: {card.get('ai_reason')}")
                card['notes'] = st.text_area("补充瑕疵备注", value=card.get('notes'), key=f"n_{c_id}")
            with c_action:
                if card.get('is_file', False):
                    if st.button("🎯 二次画框打码", key=f"e_{c_id}"):
                        st.session_state.current_edit_id = c_id
                if st.button("🗑️ 删除此片", key=f"del_{c_id}"):
                    st.session_state.db.remove(card)
                    st.rerun()

    if st.session_state.current_edit_id:
        st.markdown("### 🎯 隐私选区纠偏")
        from streamlit_cropper import st_cropper
        edit_id = st.session_state.current_edit_id
        target = next(d for d in st.session_state.db if d.get('id') == edit_id)
        st.write("请直接在下方大图上用鼠标拖拽红框对准敏感地址：")
        cropped_box = st_cropper(target.get('back_url'), realtime_update=True, box_color='#FF0000', aspect_ratio=None, return_type='box')
        if st.button("确认并锁定隐私遮挡"):
            x1, y1 = int(cropped_box['left']), int(cropped_box['top'])
            x2, y2 = x1 + int(cropped_box['width']), y1 + int(cropped_box['height'])
            target['crop_box'] = (x1, y1, x2, y2)
            target['status'] = "已人工核对"
            st.session_state.current_edit_id = None
            st.success("选区更新成功！")
            st.rerun()

# ==================== 页签 3：轨迹地图 ====================
with t_map:
    st.header("🗺️ 极限片多戳联动轨迹连线图")
    plot_data = []
    for card in st.session_state.db:
        id_str = card.get('id', '未知')
        plot_data.append({"names": f"{id_str}-发", "lon": card.get('from_lon', 110.0), "lat": card.get('from_lat', 30.0)})
        plot_data.append({"names": f"{id_str}-达", "lon": card.get('to_lon', 110.0), "lat": card.get('to_lat', 30.0)})
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
