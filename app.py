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
    st.sidebar.success("图片上传成功！正在智能识别地址标签...")
    
    # 读取原始图片
    original_img = Image.open(uploaded_back).convert("RGB")
    img_np = np.array(original_img)
    h_orig, w_orig, _ = img_np.shape
    
    # ─── 智能名址贴轮廓识别算法 ───
    # 1. 默认保底区域（万一AI识别失败，采用这个紧凑区域保底）
    x1, y1, x2, y2 = int(w_orig * 0.64), int(h_orig * 0.53), int(w_orig * 0.96), int(h_orig * 0.82)
    
    try:
        # 转为 OpenCV 的 BGR 格式进行图像处理
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        
        # 针对右下角名址贴进行二值化：把白色的名址标签纸凸显出来
        _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
        
        # 寻找图像中的所有闭合轮廓
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_box = None
        max_area = 0
        
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # 过滤条件：地址贴应该在右下角，且面积大小要适中
            if x > w_orig * 0.5 and y > h_orig * 0.4:
                area = w * h
                # 寻找右下角面积最大的那个白色矩形块
                if area > max_area and w > w_orig * 0.2 and h > h_orig * 0.1:
                    max_area = area
                    best_box = (x, y, x + w, y + h)
        
        if best_box:
            # 成功识别到白色地址标签，内缩2像素使马赛克边缘更贴合，不溢出白条
            x1, y1, x2, y2 = best_box
            x1, y1, x2, y2 = x1 + 2, y1 + 2, x2 - 2, y2 - 2
    except Exception as e:
        pass # 如果识别出错，自动降级使用默认保底区域
        
    # 2. 精准裁剪识别出来的地址块
    cropped_zone = img_np[y1:y2, x1:x2]
    h_zone, w_zone, _ = cropped_zone.shape
    
    # 3. 生成极高密度的微型浅色像素点（5x5像素，彻底糊掉文字）
    pixel_size = 5
    COLOR_1 = [245, 215, 215]  # 浅樱花粉
    COLOR_2 = [252, 242, 215]  # 浅香草黄
    COLOR_3 = [248, 248, 242]  # 极浅米白
    
    for y in range(0, h_zone, pixel_size):
        for x in range(0, w_zone, pixel_size):
            y_end = min(y + pixel_size, h_zone)
            x_end = min(x + pixel_size, w_zone)
            
            grid_x = x // pixel_size
            grid_y = y // pixel_size
            
            if (grid_x + grid_y) % 3 == 0:
                chosen_color = COLOR_1
            elif (grid_x + grid_y) % 3 == 1:
                chosen_color = COLOR_2
            else:
                chosen_color = COLOR_3
                
            cropped_zone[y:y_end, x:x_end] = chosen_color
            
    # 4. 把处理好的高密度像素涂改带贴回原图
    img_np[y1:y2, x1:x2] = cropped_zone
    back_img = Image.fromarray(img_np)
    # ─── 算法结束 ───
    
    st.sidebar.image(back_img, caption="智能动态遮挡预览", use_column_width=True)
    
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
