import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw

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
    # 提取自你提供的生肖鼠剪纸轮廓简化版
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
    
    # 3. 设定浅色系配色（低饱和度、柔和的马卡龙暖色调）
    COLOR_BG = [250, 245, 235]       # 极浅的米白纸张底色（覆盖文字）
    COLOR_RAT_1 = [245, 180, 180]    # 柔和浅粉红（生肖鼠主色）
    COLOR_RAT_2 = [250, 225, 160]    # 柔和浅米黄（生肖鼠配色）
    
    # 计算每个像素格子的大小，使其刚好填满地址栏
    rows = len(RAT_PATTERN)
    cols_count = len(RAT_PATTERN[0])
    pixel_h = h_zone // rows
    pixel_w = w_zone // cols_count
    
    # 4. 遍历矩阵绘制像素画
    for r in range(rows):
        for c in range(cols_count):
            y_start = r * pixel_h
            y_end =
