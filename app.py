import streamlit as st
import cv2
import numpy as np
from PIL import Image

# 设置页面基本信息
st.set_page_config(page_title="我的极限明信片数字馆", layout="wide")
st.title("📯 极限明信片数字化管理系统")
st.write("零本地环境，全云端驱动的明信片收藏馆")

# 模拟数据库
if 'cards' not in st.session_state:
    st.session_state.cards = [
        {
            "id": 1,
            "title": "中华十二生肖 - 子鼠",
            "front_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035293_iOS.jpg",
            "back_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035328_iOS.jpg",
            "date_from": "2026-03-20",
            "date_to": "2026-03-25",
            "loc_from": "贵州开阳鼠场",
            "loc_to": "广东广州赤岗",
            "rating": 5,
            "scenery_stamp": "无"
        }
    ]

# ----------------- 侧边栏：管理与录入 -----------------
st.sidebar.header("📥 新片入库（后台）")
uploaded_front = st.sidebar.file_uploader("上传明信片正面 (Pattern)", type=["jpg", "png", "jpeg"])
uploaded_back = st.sidebar.file_uploader("上传明信片反面 (Postmark)", type=["jpg", "png", "jpeg"])

if uploaded_front and uploaded_back:
    st.sidebar.success("图片上传成功！正在绘制浅色生肖像素遮挡...")
    
    # ─── 浅色系生肖鼠像素画算法 ───
    back_img = Image.open(uploaded_back).convert("RGB")
    width, height = back_img.size
    
    # 1. 定位地址文字区域
    crop_box = (int(width * 0.62), int(height * 0.52), int(width * 0.98), int(height * 0.82))
    cropped_zone = back_img.crop(crop_box)
    
    img_array = np.array(cropped_zone)
    h_zone, w_zone, _ = img_array.shape
    
    # 2. 定义一个 12x16 的生肖鼠像素矩阵（1代表图案，0代表背景）
    RAT_PATTERN = [
        [0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0],
        [0,0,0,0,1,1,1,1,1,1,1,0,0,0,0,0],
        [0,0,0,1,1,1,0,0,1,1,1,1,0,0,0,0],
        [0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
        [0,1,1,1,0,0,1,1,1,0,1,1,1,1,0,0],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,1],
        [1,1,1,1,0,0,0,0,1,1,1,1,0,0,0,1],
        [0,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0],
        [0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0],
        [0,0,0,1,1,1,1,1,1,0,0,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0],
    ]
    
    # 3. 设定浅色系配色
    COLOR_BG = [250, 245, 235]       # 极浅的米白纸张底色
    COLOR_RAT_1 = [245, 180, 180]    # 柔和浅粉红
    COLOR_RAT_2 = [250, 225, 160]    # 柔和浅米黄
    
    rows = len(RAT_PATTERN)
    cols_count = len(RAT_PATTERN[0])
    pixel_h = h_zone // rows
    pixel_w = w_zone // cols_count
    
    # 4. 遍历矩阵绘制像素画（严格核对缩进）
    for r in range(rows):
        for c in range(cols_count):
            y_start = r * pixel_h
            y_end = min((r + 1) * pixel_h, h_zone)
            x_start = c * pixel_w
            x_end = min((c + 1) * pixel_w, w_zone)
            
            if RAT_PATTERN[r][c] == 1:
                chosen_color = COLOR_RAT_1 if (r + c) % 2 == 0 else COLOR_RAT_2
            else:
                chosen_color = COLOR_BG
                
            img_array[y_start:y_end, x_start:x_end] = chosen_color
            
    # 5. 把像素画拼回原图
    mosaic_zone = Image.fromarray(img_array)
    back_img.paste(mosaic_zone, crop_box)
    # ─── 算法结束 ───
    
    st.sidebar.image(back_img, caption="艺术像素画隐私脱敏预览", use_column_width=True)
    
    # 录入表单
    st.sidebar.subheader("信息核对")
    title = st.sidebar.text_input("系列/名称", value="中华十二生肖 - 未命名")
    loc_from = st.sidebar.text_input("寄发地", value="AI识别中...")
    date_from = st.sidebar.date_input("寄发时间")
    rating = st.sidebar.slider("给极限片评级", 1, 5, 5)
    
    if st.sidebar.button("确认入库"):
        st.session_state.cards.append({
            "id": len(st.session_state.cards) + 1,
            "title": title,
            "front_url": uploaded_front,
            "back_url": back_img, 
            "date_from": str(date_from),
            "date_to": "-",
            "loc_from": loc_from,
            "loc_to": "-",
            "rating": rating,
            "scenery_stamp": "未知"
        })
        st.rerun()

# ----------------- 主界面：陈列馆展示 -----------------
st.header("🖼️ 我的明信片陈列展厅")

# 筛选器
search_query = st.text_input("🔍 搜索系列、地名或时间...")

# 展现明信片列表
cols = st.columns(3)

for idx, card in enumerate(st.session_state.cards):
    if search_query and search_query not in card['title'] and search_query not in card['loc_from']:
        continue
        
    with cols[idx % 3]:
        st.subheader(card['title'])
        
        tab1, tab2 = st.tabs(["🌟 正面图案", "📬 邮戳反面 (已脱敏)"])
        with tab1:
            st.image(card['front_url'], use_column_width=True)
        with tab2:
            st.image(card['back_url'], use_column_width=True)
            
        st.markdown(f"""
        * **寄发路线**：{card['loc_from']} ➡️ {card['loc_to']}
        * **寄发日期**：{card['date_from']}
        * **风景戳**：{card['scenery_stamp']}
        * **系统评级**：{'⭐' * card['rating']}
        """)
        st.markdown("---")
