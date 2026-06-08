import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import pydeck as pdk
import os

# ─── 1. CORE CONFIG (ALL ENGLISH TO AVOID GITHUB TRUNCATION BUG) ───
st.set_page_config(page_title="Museum", layout="wide")
st.title("📯 Maximum Cards Management System (V1.1)")

if 'db' not in st.session_state:
    st.session_state.db = [
        {
            "id": "Demo_001", 
            "title": "Zodiac - Rat 2026", 
            "status": "Archived",
            "front_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035293_iOS.jpg",
            "back_url": "https://pub-c5e31b5cdafb419a96447ae3d707c737.r2.dev/20260403_143035328_iOS.jpg",
            "is_file": False,
            "date_from": "2026-03-20", "date_to": "2026-03-25",
            "loc_from": "Guizhou", "loc_to": "Guangzhou",
            "from_lon": 106.96, "from_lat": 27.06, 
            "to_lon": 113.26, "to_lat": 23.13,
            "rating": 5, 
            "ai_reason": "Perfect Condition. Clean postmark, no folds.", 
            "notes": "None", "crop_box": None
        }
    ]
if 'current_edit_id' not in st.session_state: 
    st.session_state.current_edit_id = None

# ─── 2. MOSAIC ALGORITHM ───
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

# ─── 3. NAVIGATION TABS ───
tabs = st.tabs(["🏛️ Gallery", "⚙️ Admin Dashboard", "🗺️ Map Footprints"])

# ==================== TAB 1: GALLERY ====================
with tabs[0]:
    st.header("🖼️ Public Exhibition")
    search = st.text_input("🔍 Search Keyword...")
    display_cards = []
    for c in st.session_state.db:
        t_str = c.get('title', '')
        l_str = c.get('loc_from', '')
        if not search or search.lower() in t_str.lower() or search.lower() in l_str.lower():
            display_cards.append(c)
    if display_cards:
        cols = st.columns(3)
        for idx, card in enumerate(display_cards):
            with cols[idx % 3]:
                st.subheader(card.get('title', 'Untitled'))
                t1, t2 = st.tabs(["🌟 Front Pattern", "📬 Postmark (Protected)"])
                with t1: 
                    st.image(card.get('front_url'), use_column_width=True)
                with t2:
                    if not card.get('is_file', False):
                        st.image(card.get('back_url'), use_column_width=True)
                    else:
                        b_obj = card.get('back_url')
                        b_box = card.get('crop_box')
                        p_back = apply_mosaic_tape(b_obj, b_box)
                        st.image(p_back, use_column_width=True)
                st.write(f"Route: {card.get('loc_from')} -> {card.get('loc_to')}")
                st.write(f"AI Condition Rating: {'⭐' * card.get('rating', 5)}")
                st.markdown("---")

# ==================== TAB 2: ADMIN BACKEND ====================
with tabs[1]:
    st.header("📥 Batch Upload & Data Verify")
    uploaded_files = st.file_uploader("Upload", accept_multiple_files=True, type=["jpg","png","jpeg"])
    if uploaded_files:
        fronts, backs = {}, {}
        for f in uploaded_files:
            name, ext = os.path.splitext(f.name)
            # Short English Matching Rules to prevent cut error
            is_f = "front" in name.lower() or "_f" in name.lower()
            is_b = "back" in name.lower() or "behind" in name.lower() or "背面" in name or "反面" in name
            if is_f:
                clean_k = name.lower().replace("front","").replace("_f","").replace("-","").strip()
                fronts[clean_k] = f
            elif is_b:
                clean_k = name.lower().replace("back","").replace("behind","").replace("_b","").replace("-","").replace("背面","").replace("反面","").strip()
                backs[clean_k] = f
        f_keys = set(fronts.keys())
        b_keys = set(backs.keys())
        matched_keys = f_keys.intersection(b_keys)
        st.write(f"Successfully Matched: {len(matched_keys)} groups")
        for key in matched_keys:
            exists = any(d.get('id') == key for d in st.session_state.db)
            if not exists:
                st.success(f"Linked: {key}")
                img_front = Image.open(fronts[key]).convert("RGB")
                img_back = Image.open(backs[key]).convert("RGB")
                st.session_state.db.append({
                    "id": key, "title": f"Card Series - {key}", "status": "AI Auto-Rated",
                    "front_url": img_front, "back_url": img_back, "is_file": True,
                    "date_from": "2026-03-20", "date_to": "2026-03-25",
                    "loc_from": "Guizhou", "loc_to": "Guangzhou",
                    "from_lon": 106.96, "from_lat": 27.06, "to_lon": 113.26, "to_lat": 23.13,
                    "rating": 4, "ai_reason": "Good condition, slight edge wear.", "notes": "", "crop_box": None
                })
    st.markdown("---")
    st.subheader("🛠️ Management Panel")
    for idx, card in enumerate(st.session_state.db):
        c_id = card.get('id', 'Unknown')
        expander_title = f"[{c_id}] {card.get('title')} | Status: {card.get('status')}"
        with st.expander(expander_title):
            c_info, c_ai, c_action = st.columns([3, 3, 2])
            with c_info:
                st.write(f"Route: {card.get('loc_from')} -> {card.get('loc_to')}")
                current_rate = int(card.get('rating', 5))
                new_rating = st.slider("Manual Fix Score", 1, 5, current_rate, key=f"r_{c_id}")
                if new_rating != current_rate:
                    card['rating'] = new_rating
                    card['status'] = "Verified"
            with c_ai:
                st.warning(f"🤖 AI Reason: {card.get('ai_reason', 'None')}")
                card['notes'] = st.text_area("Notes", value=card.get('notes', ''), key=f"n_{c_id}")
            with c_action:
                if
