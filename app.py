import streamlit as st
import numpy as np
from PIL import Image
# 引入鼠标框选核心插件
from streamlit_cropper import st_cropper

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
    st.sidebar.success("图片上传成功！")
    
    # 读取原始图片
    original_img = Image.open(uploaded_back).convert("RGB")
    
    # ─── 鼠标直接画框交互界面 ───
    st.sidebar.subheader("🎯 鼠标框选地址区域")
    st.sidebar.info("请在右侧的大图上，直接用鼠标拖拽、调整选框，对准你要遮挡的地址文字。")
    
    # 在页面主主体区域（或者侧边栏，这里放在侧边栏展示框选器）
    # 允许自由矩形框选（realtime_update=True 实时更新，box_color 设定选框颜色为显眼的红色）
    cropped_image_info = st_cropper(
        original_img, 
        realtime_update=True, 
        box_color='#FF0000', 
        aspect_ratio=None,
        return_type='box'
    )
    
    # 获取鼠标框选的精准像素坐标
    # 插件返回的格式是比例字典: {'x': 0.x, 'y': 0.y, 'w': 0.w, 'h': 0.h}
    w_orig, h_orig = original_img.size
    x1 = int(cropped_image_info['left'])
    y1 = int(cropped_image_info['top'])
    x2 = x1 + int(cropped_image_info['width'])
    y2 = y1 + int(cropped_image_info['height'])
    
    # 安全容错，确保选框有面积
    if (x2 - x1) > 5 and (y2 - y1) > 5:
        img_np = np.array(original_img)
        cropped_zone = img_np[y1:y2, x1:x2]
        h_zone, w_zone, _ = cropped_zone.shape
        
        # 填充高密度浅色系编织马赛克效果
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
                
        # 将生成的精美涂改带贴回鼠标框选的区域
        img_np[y1:y2, x1:x2] = cropped_zone
        final_processed_img = Image.fromarray(img_np)
    else:
        final_processed_img = original_img
    
    # 展示最终脱敏效果预览
    st.sidebar.image(final_processed_img, caption="最终遮挡效果预览", use_column_width=True)
    
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
            "back_url": final_processed_img, 
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
