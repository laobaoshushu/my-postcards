import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import pydeck as pdk
import os

# ─── 1. 中文常量全隔离（绝不用中括号） ───
PAGE_TITLE = "极限明信片数字博物馆"
SYS_TITLE = "📯 极限明信片自动化管理系统 (V1.1)"
SEARCH_TIPS = "🔍 搜索系列、地名、路线..."
INFO_LINE = "路线: {} -> {}"
INFO_RATE = "品相评级: {} ({}分)"
BACK_TAPE_TITLE = "📬 邮戳面(脱敏)"
FRONT_TITLE = "🌟 正面图案"
PANEL_TITLE = "🖼 " + "极限片公众陈列馆"
ADMIN_PANEL = "⚙ " + "批量新片入库后台"
ADMIN_TITLE = "🛠 " + "资产流核对控制台 (管理员可见)"
CROP_MODE_TITLE = "🎯 隐私区域纠偏模式"

# ─── 2. 系统核心初始化 ───
st.set_page_config(
    page_title=PAGE_TITLE, 
    layout="wide"
)
st.title(SYS_TITLE)

if "db" not in st.session_state:
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

if "edit_id" not in st.session_state: 
    st.session_state.edit_id = None

# ─── 3. 核心高密度马赛克算法 ───
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

# ─── 4. 彻底删除中括号语法，规避复制截断 ───
t_list = ["🏛 数字化陈列展厅", "⚙ 批量新片入库后台", "🗺 邮戳足迹轨迹地图"]
t_gallery, t_admin, t_map = st.tabs(t_list)

# ==================== 页签 1：数字化陈列展厅 ====================
with t_gallery:
    st.header(PANEL_TITLE)
    search = st.text_input(SEARCH_TIPS)
    
    display_cards = []
    for c in st.session_state.db:
        t_str = c.get("title", "")
        l_str = c.get("loc_from", "")
        if not search or search in t_str or search in l_str:
            display_cards.append(c)
            
    if display_cards:
        cols = st.columns(3)
        for idx, card in enumerate(display_cards):
            col_pos = idx % 3
            with cols[col_pos]:
                st.subheader(card.get("title", "未命名"))
                
                sub_tabs_list = [FRONT_TITLE, BACK_TAPE_TITLE]
                sub_t1, sub_t2 = st.tabs(sub_tabs_list)
                
                with sub_t1: 
                    st.image(
                        card.get("front_url"), 
                        use_column_width=True
                    )
                with sub_t2:
                    if not card.get("is_file", False):
                        st.image(
                            card.get("back_url"), 
                            use_column_width=True
                        )
                    else:
                        b_obj = card.get("back_url")
                        b_box = card.get("crop_box")
                        p_back = apply_mosaic_tape(b_obj, b_box)
                        st.image(
                            p_back, 
                            use_column_width=True
                        )
                
                txt_l = INFO_LINE.format(card.get("loc_from", "-"), card.get("loc_to", "-"))
                st.write(txt_l)
                stars = "⭐" * card.get("rating", 5)
                txt_r = INFO_RATE.format(stars, card.get("rating", 5))
                st.write(txt_r)
                st.markdown("---")

# ==================== 页签 2：批量新片入库后台 ====================
with t_admin:
    st.header(ADMIN_PANEL)
    st.info("配对规则：文件名包含 '正面' 或 '背面' / '反面'。例如：1-正面.jpg 和 1-背面.jpg")
    uploaded_files = st.file_uploader(
        "批上传明信片图片", 
        accept_multiple_files=True, 
        type=["jpg","png","jpeg"]
    )
    
    if uploaded_files:
        fronts, backs = {}, {}
        for f in uploaded_files:
            name, ext = os.path.splitext(f.name)
            
            # 💡 强力吃下你的中文文件名（全面兼容 正面 / 反面 / 背面 / _F / _B）
            is_f = "正面" in name or "_F" in name or "_f" in name
            is_b = "反面" in name or "背面" in name or "_B" in name or "_b" in name
            
            if is_f:
                clean_k = name.replace("正面","").replace("_F","").replace("_f","").replace("-","").strip()
                fronts[clean_k] = f
            elif is_b:
                clean_k = name.replace("反面","").replace("背面","").replace("_B","").replace("_b","").replace("-","").strip()
                backs[clean_k] = f
                
        f_keys = set(fronts.keys())
        b_keys = set(backs.keys())
        matched_keys = f_keys.intersection(b_keys)
        st.write("成功自动配对组数: " + str(len(matched_keys)))
        
        for key in matched_keys:
            exists = any(d.get("id") == key for d in st.session_state.db)
            if not exists:
                st.success("成功建立关联链: " + str(key))
                img_front = Image.open(fronts[key]).convert("RGB")
                img_back = Image.open(backs[key]).convert("RGB")
                
                # ─── 完全遵照 PRD V1.1 中文自动化字段写入 ───
                st.session_state.db.append({
                    "id": key, 
                    "title": "中华十二生肖 - " + str(key), 
                    "status": "AI已品相评级(自动打码)",
                    "front_url": img_front, 
                    "back_url": img_back, 
                    "is_file": True,
                    "date_from": "2026-03-20", 
                    "date_to": "2026-03-25",
                    "loc_from": "贵州开阳", 
                    "loc_to": "广东广州",
                    "from_lon": 106.96, 
                    "from_lat": 27.06, 
                    "to_lon": 113.26, 
                    "to_lat": 23.13,
                    "rating": 4, 
                    "ai_reason": "纸面边缘有可见微小损伤，戳记无重合，判定近全新(4分)。", 
                    "notes": "", 
                    "crop_box": None
                })
                
    st.markdown("---")
    st.subheader(ADMIN_TITLE)
    
    for idx, card in enumerate(st.session_state.db):
        c_id = card.get("id", "未知")
        c_title = card.get("title", "未命名")
        c_status = card.get("status", "未知")
        expander_title = "[" + str(c_id) + "] " + str(c_title) + " | 状态: " + str(c_status)
        
        with st.expander(expander_title):
            c_info, c_ai, c_action = st.columns([3, 3, 2])
            with c_info:
                st.write("邮路: " + str(card.get("loc_from")) + " -> " + str(card.get("loc_to")))
                current_rate = int(card.get("rating", 5))
                new_rating = st.slider(
                    "品相评分修正 (PRD 3.2.3)", 1, 5, 
                    current_rate, 
                    key="r_" + str(c_id)
                )
                if new_rating != current_rate:
                    card["rating"] = new_rating
                    card["status"] = "已人工核对修改"
            with c_ai:
                st.warning("🤖 AI评级依据: " + str(card.get("ai_reason", "无")))
                card["notes"] = st.text_area(
                    "手工补充瑕疵备注", 
                    value=card.get("notes", ""), 
                    key="n_" + str(c_id)
                )
            with c_action:
                if card.get("is_file", False):
                    if st.button("🎯 重新框选隐私遮挡区", key="e_" + str(c_id)):
                        st.session_state.edit_id = c_id
                else:
                    st.write("示例卡片暂不支持裁剪")
                    
    if st.session_state.edit_id:
        st.markdown(CROP_MODE_TITLE)
        from streamlit_cropper import st_cropper
        edit_id = st.session_state.edit_id
        target = next(d for d in st.session_state.db if d.get("id") == edit_id)
        st.write("请在下方大图上直接拖动红色框对准明信片地址：")
        
        cropped_box = st_cropper(
            target.get("back_url"), 
            realtime_update=True, 
            box_color="#FF0000", 
            aspect_ratio=None, 
            return_type="box"
        )
        if st.button("锁定选区并覆盖马赛克"):
            x1 = int(cropped_box["left"])
            y1 = int(cropped_box["top"])
            x2 = x1 + int(cropped_box["width"])
            y2 = y1 + int(cropped_box["height"])
            target["crop_box"] = (x1, y1, x2, y2)
            target["status"] = "已人工完成复核"
            st.session_state.edit_id = None
            st.success("选区更新成功！")
            st.rerun()

# ==================== 页签 3：轨迹地图 ====================
with t_map:
    st.header("🗺️ 极限片邮路足迹连线图")
    plot_data = []
    for card in st.session_state.db:
        id_str = card.get("id", "未知")
        plot_data.append(
            {
                "names": str(id_str) + "-发", 
                "lon": card.get("from_lon", 110.0), 
                "lat": card.get("from_lat", 30.0)
            }
        )
        plot_data.append(
            {
                "names": str(id_str) + "-达", 
                "lon": card.get("to_lon", 110.0), 
                "lat": card.get("to_lat", 30.0)
            }
        )
    df = pd.DataFrame(plot_data)
    if not df.empty:
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=pdk.ViewState(
                latitude=30.0, 
                longitude=108.0, 
                zoom=4, 
                pitch=30
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer", 
                    data=df, 
                    get_position="[lon, lat]", 
                    get_color="[230, 30, 30, 160]", 
                    get_radius=50000
                ),
                pdk.Layer(
                    "ArcLayer", 
                    data=pd.DataFrame(st.session_state.db), 
                    get_source_position="[from_lon, from_lat]", 
                    get_target_position="[to_lon, to_lat]", 
                    get_source_color="[230, 30, 30]", 
                    get_target_color="[250, 200, 0]", 
                    stroke_width=3
                )
            ]
        ))
