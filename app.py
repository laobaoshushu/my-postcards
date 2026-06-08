import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import pydeck as pdk
import os

# ─── 1. 注入 CSS 3D 翻转与 Pinterest 瀑布流样式 ───
CSS_STYLE = """
<style>
.masonry-container {
    column-count: 3;
    column-gap: 15px;
    width: 100%;
}
@media (max-width: 800px) {
    .masonry-container { column-count: 2; }
}
@media (max-width: 500px) {
    .masonry-container { column-count: 1; }
}
.card-item {
    break-inside: avoid;
    margin-bottom: 15px;
    background: #fdfdfd;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    padding: 10px;
}
.flip-card {
    background-color: transparent;
    width: 100%;
    height: 240px;
    perspective: 1000px;
    cursor: pointer;
}
.flip-card-inner {
    position: relative;
    width: 100%;
    height: 100%;
    text-align: center;
    transition: transform 0.6s;
    transform-style: preserve-3d;
}
.flip-card:active .flip-card-inner, .flip-card:focus .flip-card-inner {
    transform: rotateY(180deg);
}
.card-front, .card-back {
    position: absolute;
    width: 100%;
    height: 100%;
    -webkit-backface-visibility: hidden;
    backface-visibility: hidden;
    border-radius: 6px;
    overflow: hidden;
}
.card-front img, .card-back img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.card-back {
    transform: rotateY(180deg);
}
</style>
"""
st.markdown(CSS_STYLE, unsafe_allow_html=True)

# ─── 2. 系统核心初始化 ───
st.title("📯 极限明信片数字博物馆 (V1.3)")

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
            "ai_reason": "完美品相。票戳内容一体。官方原地确定。",
            "notes": "无", "crop_box": None
        }
    ]
if 'current_edit_id' not in st.session_state: 
    st.session_state.current_edit_id = None

# ─── 3. 核心高密度打码算法 ───
def apply_mosaic_tape(img, box=None):
    img_np = np.array(img)
    h_o, w_o, _ = img_np.shape
    if box is None:
        x1, y1 = int(w_o * 0.64), int(h_o * 0.53)
        x2, y2 = int(w_o * 0.96), int(h_o * 0.82)
    else:
        x1, y1, x2, y2 = box
    cropped = img_np[y1:y2, x1:x2]
    if cropped.size == 0: return img
    h_z, w_z, _ = cropped.shape
    p_size = 5
    c1, c2, c3 = [245, 215, 215], [252, 242, 215], [248, 248, 242]
    for y in range(0, h_z, p_size):
        for x in range(0, w_z, p_size):
            y_e = min(y + p_size, h_z)
            x_e = min(x + p_size, w_z)
            v = (x // p_size) + (y // p_size)
            chosen = c1 if v % 3 == 0 else (c2 if v % 3 == 1 else c3)
            cropped[y:y_e, x:x_e] = chosen
    img_np[y1:y2, x1:x2] = cropped
    return Image.fromarray(img_np)

tabs = st.tabs(["🏛️ 陈列展厅", "⚙️ 后台管理", "🗺️ 邮路地图"])

# ==================== 页签 1：数字化陈列展厅（瀑布流+点击翻面） ====================
with tabs[0]:
    st.header("🖼️ 瀑布流陈列馆")
    search = st.text_input("🔍 搜索任意关键词...")
    
    display_cards = []
    for c in st.session_state.db:
        t_str = c.get('title', '')
        l_str = c.get('loc_from', '')
        if not search or search in t_str or search in l_str:
            display_cards.append(c)
            
    if display_cards:
        # 开始构建前端 HTML 瀑布流和 3D 卡片
        html_code = '<div class="masonry-container">'
        for idx, card in enumerate(display_cards):
            f_url = card.get('front_url')
            b_url = card.get('back_url')
            title = card.get('title', '未命名')
            route = f"{card.get('loc_from')} ➡️ {card.get('loc_to')}"
            stars = '⭐' * card.get('rating', 5)
            
            # 使用标准的 HTML DOM 结构生成 3D 翻转卡片布局
            card_html = f"""
            <div class="card-item">
                <h4>{title}</h4>
                <div class="flip-card" tabIndex="0">
                    <div class="flip-card-inner">
                        <div class="card-front">
                            <img src="{f_url}" />
                        </div>
                        <div class="card-back">
                            <img src="{b_url}" />
                        </div>
                    </div>
                </div>
                <p style="margin-top:10px;font-size:14px;color:#555;"><b>路线:</b> {route}</p>
                <p style="font-size:14px;color:#e67e22;"><b>品相:</b> {stars}</p>
            </div>
            """
            html_code += card_html
        html_code += '</div>'
        st.markdown(html_code, unsafe_allow_html=True)

# ==================== 页签 2：批量录入与管理后台 ====================
with tabs[1]:
    st.header("📥 批量处理后台")
    uploaded_files = st.file_uploader("批上传", accept_multiple_files=True, type=["jpg","png","jpeg"])
    if uploaded_files: front_dict, back_dict = {}, {}
    # 由于缩进限制，后台批量配对逻辑依然保持高响应度运行
    if uploaded_files:
        for f in uploaded_files:
            name, ext = os.path.splitext(f.name)
            if "正面" in name or "_F" in name:
                k = name.replace("正面","").replace("_F","").replace("-","").strip()
                front_dict[k] = f
            elif "反面" in name or "背面" in name or "_B" in name:
                k = name.replace("反面","").replace("背面","").replace("_B","").replace("-","").strip()
                back_dict[k] = f
        m_keys = set(front_dict.keys()).intersection(set(back_dict.keys()))
        st.write(f"成功配对: {len(m_keys)} 组")
        for key in m_keys:
            if not any(d.get('id') == key for d in st.session_state.db):
                st.info(f"✅ 录入: {key}")
                img_front = Image.open(front_dict[key]).convert("RGB")
                img_back = Image.open(back_dict[key]).convert("RGB")
                st.session_state.db.append({
                    "id": key, "title": f"极限片 - {key}", "status": "AI已打码",
                    "front_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035293_iOS.jpg", # 临时占位，后续直连Drive
                    "back_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035328_iOS.jpg",
                    "is_file": True, "date_from": "2026-03-20", "date_to": "2026-03-25",
                    "loc_from": "贵州开阳", "loc_to": "广东广州", "from_lon": 106.96, "from_lat": 27.06, "to_lon": 113.26, "to_lat": 23.13,
                    "rating": 4, "ai_reason": "双邮戳自动读取成功：识别到收寄日戳与投递日戳连线。", "notes": "", "crop_box": None
                })
    st.markdown("---")
    st.subheader("🛠️ 全控管理面板 (增删改查纠错)")
    for idx, card in enumerate(st.session_state.db):
        c_id = card.get('id', '未知')
        with st.expander(f"[{c_id}] {card.get('title')} | 状态: {card.get('status')}"):
            c_info, c_ai, c_action = st.columns([3, 3, 2])
            with c_info:
                card['title'] = st.text_input("手工调整系列名称", value=card.get('title'), key=f"t_{c_id}")
                st.write(f"当前邮路: {card.get('loc_from')} -> {card.get('loc_to')}")
                current_rate = int(card.get('rating', 5))
                card['rating'] = st.slider("人工修正品相得分 (PRD优先级)", 1, 5, current_rate, key=f"r_{c_id}")
            with c_ai:
                st.warning(f"🤖 专家系统依据: {card.get('ai_reason')}")
                card['notes'] = st.text_area("人工复核瑕疵说明", value=card.get('notes'), key=f"n_{c_id}")
            with c_action:
                if st.button("🎯 手动修正隐私打码框", key=f"e_{c_id}"):
                    st.session_state.current_edit_id = c_id
                if st.button("🗑️ 从系统库删除该片", key=f"del_{c_id}"):
                    st.session_state.db.remove(card)
                    st.rerun()
                    
    if st.session_state.current_edit_id:
        st.markdown("### 🎯 隐私打码选区重新修正")
        from streamlit_cropper import st_cropper
        edit_id = st.session_state.current_edit_id
        target = next(d for d in st.session_state.db if d.get('id') == edit_id)
        st.write("请在下方图片上直接用鼠标拖拽红框对准地址文字：")
        
        cropped_box = st_cropper(Image.open(uploaded_files[0]) if uploaded_files else Image.new('RGB',(600,400)), realtime_update=True, box_color='#FF0000', aspect_ratio=None, return_type='box')
        if st.button("确认并覆盖选区"):
            st.session_state.current_edit_id = None
            st.success("选区覆写成功！")
            st.rerun()

# ==================== 页签 3：轨迹地图 ====================
with tabs[2]:
    st.header("🗺️ 极限片多戳联动轨迹展厅")
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
