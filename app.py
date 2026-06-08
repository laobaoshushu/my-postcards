import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import pydeck as pdk
from geopy.geocoders import Nominatim
from streamlit_cropper import st_cropper
import os

# 初始化基础配置
st.set_page_config(page_title="我的极限明信片数字博物馆", layout="wide")
st.title("📯 极限明信片自动化管理与陈列系统")

# ─── 数据库持久化模拟 (实际落地可一键绑定云端 Google Sheets) ───
if 'db' not in st.session_state:
    st.session_state.db = [
        {
            "id": "001", "title": "中华十二生肖 - 子鼠", "status": "已入库",
            "front_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035293_iOS.jpg",
            "back_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035328_iOS.jpg",
            "date_from": "2026-03-20", "date_to": "2026-03-25",
            "loc_from": "贵州开阳", "loc_to": "广东广州",
            "from_lon": 106.96, "from_lat": 27.06, "to_lon": 113.26, "to_lat": 23.13,
            "rating": 5, "crop_box": None
        }
    ]
if 'current_edit_id' not in st.session_state: st.session_state.current_edit_id = None

# ─── 核心工具函数：生成马赛克 ───
def apply_mosaic_tape(img, box):
    img_np = np.array(img)
    x1, y1, x2, y2 = box
    cropped = img_np[y1:y2, x1:x2]
    if cropped.size == 0: return img
    h_z, w_z, _ = cropped.shape
    p_size = 5
    c1, c2, c3 = [245, 215, 215], [252, 242, 215], [248, 248, 242]
    for y in range(0, h_z, p_size):
        for x in range(0, w_z, p_size):
            y_e, x_e = min(y + p_size, h_z), min(x + p_size, w_z)
            chosen = c1 if ((x//p_size)+(y//p_size))%3==0 else (c2 if ((x//p_size)+(y//p_size))%3==1 else c3)
            cropped[y:y_e, x:x_e] = chosen
    img_np[y1:y2, x1:x2] = cropped
    return Image.fromarray(img_np)

# ─── 创建系统功能页签 ───
tabs = st.tabs(["🏛️ 数字化陈列展厅", "⚙️ 批量新片入库后台", "🗺️ 邮戳足迹轨迹地图"])

# ==================== 页签 1：陈列展厅 ====================
with tabs[0]:
    st.header("🖼️ 极限片陈列馆")
    search = st.text_input("🔍 搜索系列或地名...")
    cols = st.columns(3)
    
    for idx, card in enumerate(st.session_state.db):
        if search and search not in card['title'] and search not in card['loc_from']: continue
        with cols[idx % 3]:
            st.subheader(f"[{card['id']}] {card['title']}")
            t1, t2 = st.tabs(["🌟 正面图案", "📬 邮戳面(脱敏)"])
            with t1: st.image(card['front_url'], use_column_width=True)
            with t2:
                # 如果有手动修改的框，用手动的；否则用自动生成的保底框
                box = card['crop_box'] if card['crop_box'] else (int(Image.open(uploaded_back if 'uploaded_back' in locals() else Image.new('RGB',(1000,600))).size[0]*0.64), int(Image.open(uploaded_back if 'uploaded_back' in locals() else Image.new('RGB',(1000,600))).size[1]*0.53), int(Image.open(uploaded_back if 'uploaded_back' in locals() else Image.new('RGB',(1000,600))).size[0]*0.96), int(Image.open(uploaded_back if 'uploaded_back' in locals() else Image.new('RGB',(1000,600))).size[1]*0.82))
                if isinstance(card['back_url'], str):
                    st.image(card['back_url'], use_column_width=True) # 演示外链
                else:
                    st.image(apply_mosaic_tape(card['back_url'], box), use_column_width=True)
            st.markdown(f"**路线**：{card['loc_from']} ➡️ {card['loc_to']} | **评级**：{'⭐'*card['rating']}")

# ==================== 页签 2：批量录入后台 ====================
with tabs[1]:
    st.header("📥 批量自动化处理台")
    uploaded_files = st.file_uploader("将明信片图片成批拖拽到此处上传", accept_multiple_files=True, type=["jpg","png","jpeg"])
    
    if uploaded_files:
        st.subheader("📦 文件自动对齐与AI预处理进度")
        # 自动对齐逻辑解析
        fronts, backs = {}, {}
        for f in uploaded_files:
            name, ext = os.path.splitext(f.name)
            if "正面" in name or "_F" in name:
                fronts[name.replace("正面","").replace("_F","")] = f
            elif "反面" in name or "_B" in name:
                backs[name.replace("反面","").replace("_B","")] = f
                
        st.write(f"成功识别到：正面 {len(fronts)} 张，反面 {len(backs)} 张。正在自动匹配...")
        
        # 找出成功配对的组
        matched_keys = set(fronts.keys()) & set(backs.keys())
        for key in matched_keys:
            st.info(f"✅ 成功配对明信片组：【{key}】")
            # 此处在录入时自动调用AI模型与自动遮挡
            if not any(d['id'] == key for d in st.session_state.db):
                # 模拟AI自动读取并自动生成基础遮挡
                st.session_state.db.append({
                    "id": key, "title": f"AI识别：{key}", "status": "待核对",
                    "front_url": fronts[key], "back_url": Image.open(backs[key]).convert("RGB"),
                    "date_from": "2026-03-20", "date_to": "2026-03-25",
                    "loc_from": "贵州开阳", "loc_to": "广东广州",
                    "from_lon": 106.96, "from_lat": 27.06, "to_lon": 113.26, "to_lat": 23.13,
                    "rating": 4, "crop_box": None
                })
                
    st.markdown("---")
    st.subheader("🛠️ 后台数据流核对与手动修正")
    
    # 列表管理展示
    for idx, card in enumerate(st.session_state.db):
        col_name, col_status, col_btn = st.columns([4, 2, 2])
        with col_name: st.write(f"**ID: {card['id']}** - {card['title']} (路线: {card['loc_from']}->{card['loc_to']})")
        with col_status: st.write(f"状态: `{card['status']}`")
        with col_btn:
            if st.button("手动修正遮挡", key=f"edit_{card['id']}"):
                st.session_state.current_edit_id = card['id']
                
    # 弹出式鼠标手动框选修正区
    if st.session_state.current_edit_id:
        st.markdown("### 🎯 手动修正模式")
        target = next(d for d in st.session_state.db if d['id'] == st.session_state.current_edit_id)
        st.write(f"正在手动为 【{target['title']}】 重新绘制高精地址选区：")
        
        if isinstance(target['back_url'], str):
            st.warning("演示预载图片不支持网页端再裁剪，请上传新图片测试鼠标画框。")
        else:
            cropped_box = st_cropper(target['back_url'], realtime_update=True, box_color='#FF0000', aspect_ratio=None, return_type='box')
            x1, y1 = int(cropped_box['left']), int(cropped_box['top'])
            x2, y2 = x1 + int(cropped_box['width']), y1 + int(cropped_box['height'])
            
            if st.button("保存手动遮挡选区"):
                target['crop_box'] = (x1, y1, x2, y2)
                target['status'] = "已人工核对"
                st.session_state.current_edit_id = None
                st.success("选区保存成功！")
                st.rerun()

# ==================== 页签 3：轨迹地图 ====================
with tabs[2]:
    st.header("🗺️ 极限片邮路足迹馆")
    
    # 整合经纬度生成连线地图
    plot_data = []
    for card in st.session_state.db:
        plot_data.append({"names": f"{card['id']}-寄出", "lon": card['from_lon'], "lat": card['from_lat']})
        plot_data.append({"names": f"{card['id']}-寄达", "lon": card['to_lon'], "lat": card['to_lat']})
    
    df = pd.DataFrame(plot_data)
    
    if not df.empty:
        # 调用高级 3D 地图引擎展示路径
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=pdk.ViewState(latitude=25.0, longitude=110.0, zoom=4, pitch=30),
            layers=[
                pdk.Layer('ScatterplotLayer', data=df, get_position='[lon, lat]', get_color='[230, 30, 30, 160]', get_radius=40000, pickable=True),
                pdk.Layer('ArcLayer', data=pd.DataFrame(st.session_state.db), get_source_position='[from_lon, from_lat]', get_target_position='[to_lon, to_lat]', get_source_color='[230, 30, 30]', get_target_color='[250, 200, 0]', stroke_width=3)
            ]
        ))
