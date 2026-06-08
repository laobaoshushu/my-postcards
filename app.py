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
    st.sidebar.success("图片上传成功！正在生成红黄交错马赛克...")
    
    # ─── 红黄交错方块马赛克算法 ───
    back_img = Image.open(uploaded_back).convert("RGB")
    width, height = back_img.size
    
    # 1. 定位地址文字区域
    crop_box = (int(width * 0.62), int(height * 0.52), int(width * 0.98), int(height * 0.82))
    cropped_zone = back_img.crop(crop_box)
    
    # 将裁剪区域转为 numpy 矩阵进行像素处理
    img_array = np.array(cropped_zone)
    h_zone, w_zone, _ = img_array.shape
    
    # 2. 设定马赛克颗粒大小（格子大小，数字越大格子越大）
    pixel_size = 16 
    
    # 定义标准中国红和金黄色的 RGB 颜色
    COLOR_RED = [230, 30, 30]     # 红
    COLOR_YELLOW = [255, 215, 0]  # 黄
    
    # 3. 双层循环遍历每个方块，进行红黄交错染色
    for y in range(0, h_zone, pixel_size):
        for x in range(0, w_zone, pixel_size):
            # 确定当前格子的边界
            y_end = min(y + pixel_size, h_zone)
            x_end = min(x + pixel_size, w_zone)
            
            # 根据格子在行列中的奇偶位置（X坐标+Y坐标的格子索引），决定它是红色还是黄色
            grid_x = x // pixel_size
            grid_y = y // pixel_size
            
            if (grid_x + grid_y) % 2 == 0:
                chosen_color = COLOR_RED
            else:
                chosen_color = COLOR_YELLOW
                
            # 将这个小方块区域强制填充为选定的颜色
            img_array[y:y_end, x:x_end] = chosen_color
            
    # 4. 把处理好的马赛克拼回原图
    mosaic_zone = Image.fromarray(img_array)
    back_img.paste(mosaic_zone, crop_box)
    # ─── 算法结束 ───
    
    st.sidebar.image(back_img, caption="红黄交错马赛克预览", use_column_width=True)
    
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
