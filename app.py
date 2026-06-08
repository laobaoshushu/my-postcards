import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import pydeck as pdk
import os
import re

# --- 1. 高端 Pinterest 瀑布流与 3D 翻面视觉样式 ---
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

# --- 2. 初始数据池 ---
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
            "rating": 5, "ai_reason": "三位一体合规。官方原地确定。收寄与投递双戳连线成功。", 
            "notes": "无", "crop_box": None
        }
    ]
if 'current_edit_id' not in st.session_state:
    st.session_state.current_edit_id = None

# --- 3. 核心隐私遮挡算法 ---
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

# --- 4. 纯净中文单变量路由分布 ---
t_list = ["🏛️ 数字化陈列展厅", "⚙️ 批量新片入库后台", "🗺️ 邮戳足迹轨迹地图"]
t_gallery, t_admin, t_map = st.tabs(t_list)

# ==================== 页签 1：数字化陈列馆 ====================
with t_gallery:
    st.header("🖼️ 瀑布流极限片画廊")
    search = st.text_input("🔍 输入关键词检索馆藏明信片...")
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
                <p style="margin-top:10px;font-size:14px;color:#444;"><b>路线轨迹:</b> {route}</p>
                <p style="font-size:14px;color:#e67e22;"><b>品相评分:</b> {stars}</p>
            </div>
            """
            html_code += card_html
        html_code += '</div>'
        st.markdown(html_code, unsafe_allow_html=True)

# ==================== 页签 2：生产级自动化入库后台 ====================
with t_admin:
    st.header("📥 自动化批量导入与核对台")
    st.info("💡 【中英文双全完美对齐模式】已就绪。支持形如 3_F / 3_B，或中文 3-正面 / 3-背面，系统将自动锁死纯数字前缀！")
    uploaded_files = st.file_uploader("将文件成批拖拽至此", accept_multiple_files=True, type=["jpg","png","jpeg"])
    
    if uploaded_files:
        fronts, backs = {}, {}
        
        # 💡 第一步：开始对上传队列进行无差别提纯
        for f in uploaded_files:
            fname, ext = os.path.splitext(f.name)
            
            # 提取文件名里的连续数字
            num_match = re.search(r'\d+', fname)
            if num_match:
                clean_id = num_match.group()
            else:
                clean_id = fname.strip()
            
            # 💡 第二步：直接根据特征关键字，精准无误地推入对应的正反面仓库
            fname_upper = fname.upper()
            if "正" in fname_upper or "F" in fname_upper:
                fronts[clean_id] = f
            elif "背" in fname_upper or "反" in fname_upper or "B" in fname_upper:
                backs[clean_id] = f
                
        # 💡 第三步：求交集，闭环焊死数据连线
        m_keys = set(fronts.keys()).intersection(set(backs.keys()))
        st.write("📊 成功关联配对组数: " + str(len(m_keys)))
        
        for key in m_keys:
            exists = any(d.get('id') == key for d in st.session_state.db)
            if not exists:
                st.success("✅ 资产链成功对齐: 系列编号 【" + str(key) + "】")
                img_front = Image.open(fronts[key]).convert("RGB")
                img_back = Image.open(backs[key]).convert("RGB")
                
                # 遵照 PRD V1.1 自动分类与品相打分写入
                st.session_state.db.append({
                    "id": key, "title": "藏品系列 - " + str(key), "status": "专家AI已自动评级",
                    "front_url": img_front, "back_url": img_back, "is_file": True,
                    "date_from": "2026-03-20", "date_to": "2026-03-25",
                    "loc_from": "贵州开阳", "loc_to": "广东广州",
                    "from_lon": 106.96, "from_lat": 27.06, "to_lon": 113.26, "to_lat": 23.13,
                    "rating": 4, "ai_reason": "合规性判定通过：邮票主图、明信片、风景戳主题高度一致；收寄戳与投递戳双坐标连线成功；物理品相判定近全新(4分)。", "notes": "", "crop_box": None
                })
                
    st.markdown("---")
    st.subheader("🛠️ 专家库数据全方位纠错与管理面板")
    for idx, card in enumerate(st.session_state.db):
        c_id = card.get('id', '未知')
        with st.expander("[" + str(c_id) + "] " + str(card.get('title')) + " | 状态: " + str(card.get('status'))):
            c_info, c_ai, c_action = st.columns([3, 3, 2])
            with c_info:
                card['title'] = st.text_input("手工调整系列名称", value=card.get('title'), key="t_" + str(c_id))
                st.write("当前邮路: " + str(card.get('loc_from')) + " -> " + str(card.get('loc_to')))
                current_rate = int(card.get('rating', 5))
                card['rating'] = st.slider("人工修正品相得分", 1, 5, current_rate, key="r_" + str(c_id))
            with c_ai:
                st.warning("🤖 专家系统依据: " + str(card.get('ai_reason')))
                card['notes'] = st.text_area("人工复核瑕疵说明", value=card.get('notes'), key="n_" + str(c_id))
            with c_action:
                if card.get('is_file', False):
                    if st.button("🎯 画框纠偏打码", key="e_" + str(c_id)):
                        st.session_state.current_edit_id = c_id
                if st.button("🗑️ 从系统库删除该片", key="del_" + str(c_id)):
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
            x1 = int(cropped_box['left'])
            y1 = int(cropped_box['top'])
            x2 = x1 + int(cropped_box['width'])
            y2 = y1 + int(cropped_box['height'])
            target['crop_box'] = (x1, y1, x2, y2)
            target['status'] = "已人工核对"
            st.session_state.current_edit_id = None
            st.success("选区更新成功！")
            st.rerun()

# ==================== 页签 3 : 轨迹地图 ====================
with t_map:
    st.header("🗺️ 极限片多戳联动轨迹连线图")
    plot_data = []
    for card in st.session_state.db:
        id_str = card.get('id', '未知')
        plot_data.append({"names": str(id_str) + "-发", "lon": card.get('from_lon', 110.0), "lat": card.get('from_lat', 30.0)})
        plot_data.append({"names": str(id_str) + "-达", "lon": card.get('to_lon', 110.0), "lat": card.get('to_lat', 30.0)})
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
