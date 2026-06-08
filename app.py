import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import pydeck as pdk
import os

# 设置页面基本信息
st.set_page_config(page_title="我的极限明信片数字博物馆", layout="wide")
st.title("📯 极限明信片自动化管理与陈列系统")

# ─── 数据库持久化模拟 (初始包含一张示例明信片) ───
if 'db' not in st.session_state:
    st.session_state.db = [
        {
            "id": "生肖鼠_示例", "title": "中华十二生肖 - 子鼠", "status": "已入库",
            "front_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035293_iOS.jpg",
            "back_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035328_iOS.jpg",
            "is_file_object": False,
            "date_from": "2026-03-20", "date_to": "2026-03-25",
            "loc_from": "贵州开阳", "loc_to": "广东广州",
            "from_lon": 106.96, "from_lat": 27.06, "to_lon": 113.26, "to_lat": 23.13,
            "rating": 5, "crop_box": None
        }
    ]
if 'current_edit_id' not in st.session_state: st.session_state.current_edit_id = None

# ─── 核心工具函数：生成浅色编织马赛克涂改带 ───
def apply_mosaic_tape(img, box=None):
    img_np = np.array(img)
    h_orig, w_orig, _ = img_np.shape
    
    # 如果没有指定手动框，采用标准的右下角安全保底区域
    if box is None:
        x1, y1, x2, y2 = int(w_orig * 0.64), int(h_orig * 0.53), int(w_orig * 0.96), int(h_orig * 0.82)
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
            chosen = c1 if ((x//p_size)+(y//p_size))%3==0 else (c2 if ((x//p_size)+(y//p_size))%3==1 else c3)
            cropped[y:y_e, x:x_e] = chosen
            
    img_np[y1:y2, x1:x2] = cropped
    return Image.fromarray(img_np)

# ─── 创建系统功能页签 ───
tabs = st.tabs(["🏛️ 数字化陈列展厅", "⚙️ 批量新片入库后台", "🗺️ 邮戳足迹轨迹地图"])

# ==================== 页签 1：陈列展厅 ====================
with tabs[0]:
    st.header("🖼️ 极限片陈列馆")
    search = st.text_input("🔍 搜索系列、地名、路线...")
    
    # 过滤搜索数据
    display_cards = [c for c in st.session_state.db if not search or (search in c['title'] or search in c['loc_from'])]
    
    if display_cards:
        cols = st.columns(3)
        for idx, card in enumerate(display_cards):
            with cols[idx % 3]:
                st.subheader(f"{card['title']}")
                t1, t2 = st.tabs(["🌟 正面图案", "📬 邮戳面(脱敏)"])
                with t1: 
                    st.image(card['front_url'], use_column_width=True)
                with t2:
                    if not card['is_file_object']:
                        st.image(card['back_url'], use_column_width=True)
                    else:
                        processed_back = apply_mosaic_tape(card['back_url'], card['crop_box'])
                        st.image(processed_back, use_column_width=True)
                        
                st.markdown(f"**路线**：{card['loc_from']} ➡️ {card['loc_to']} | **系统评级**：{'⭐'*card['rating']}")
                st.markdown("---")
    else:
        st.write("暂无匹配的明信片。")

# ==================== 页签 2：批量录入后台 ====================
with tabs[1]:
    st.header("📥 批量自动化处理台")
    uploaded_files = st.file_uploader("将明信片图片成批拖拽到此处上传", accept_multiple_files=True, type=["jpg","png","jpeg"])
    
    if uploaded_files:
        st.subheader("📦 文件自动对齐与AI预处理进度")
        fronts, backs = {}, {}
        for f in uploaded_files:
            name, ext = os.path.splitext(f.name)
            if "正面" in name or "_F" in name:
                fronts[name.replace("正面","").replace("_F","")] = f
            elif "反面" in name or "_B" in name:
                backs[name.replace("反面","").replace("_B","")] = f
                
        # 找出成功配对的组
        matched_keys = set(fronts.keys()) & set(backs.keys())
        st.write(f"成功识别到：正面 {len(fronts)} 张，反面 {len(backs)} 张。成功自动配对：{len(matched_keys)} 组。")
        
        for key in matched_keys:
            if not any(d['id'] == key for d in st.session_state.db):
                st.info(f"✅ 新增自动配对组：【{key}】（AI已自动完成首次
