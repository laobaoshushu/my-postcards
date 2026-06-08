import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import pydeck as pdk
import os

st.set_page_config(page_title="Museum System", layout="wide")
st.title("Maximum Cards Management System")

if 'db' not in st.session_state:
    st.session_state.db = []
if 'current_edit_id' not in st.session_state: 
    st.session_state.current_edit_id = None

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

# 💡 彻底抛弃带括号的写法，改用独立变量名，防截断！
tab_gallery, tab_admin, tab_map = st.tabs(["Gallery", "Admin Dashboard", "Route Map"])

with tab_gallery:
    st.header("Public Exhibition")
    search = st.text_input("Search...")
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
                t_front, t_back = st.tabs(["Front", "Protected Back"])
                with t_front: 
                    st.image(card.get('front_url'), use_column_width=True)
                with t_back:
                    b_obj = card.get('back_url')
                    b_box = card.get('crop_box')
                    p_back = apply_mosaic_tape(b_obj, b_box)
                    st.image(p_back, use_column_width=True)
                st.write("Route: " + str(card.get('loc_from')) + " -> " + str(card.get('loc_to')))
                st.write("Rating: " + str(card.get('rating', 5)))
                st.markdown("---")

with tab_admin:
    st.header("Batch Upload")
    st.info("Rule: Name files as '1_F.jpg' (Front) and '1_B.jpg' (Back)")
    uploaded_files = st.file_uploader("Upload Images", accept_multiple_files=True, type=["jpg","png","jpeg"])
    if uploaded_files:
        fronts, backs = {}, {}
        for f in uploaded_files:
            name, ext = os.path.splitext(f.name)
            name_low = name.lower()
            if "_f" in name_low:
                clean_k = name_low.replace("_f","").strip()
                fronts[clean_k] = f
            elif "_b" in name_low:
                clean_k = name_low.replace("_b","").strip()
                backs[clean_k] = f
        f_keys = set(fronts.keys())
        b_keys = set(backs.keys())
        matched_keys = f_keys.intersection(b_keys)
        st.write("Matched Groups: " + str(len(matched_keys)))
        for key in matched_keys:
            exists = any(d.get('id') == key for d in st.session_state.db)
            if not exists:
                st.success("Linked: " + str(key))
                img_front = Image.open(fronts[key]).convert("RGB")
                img_back = Image.open(backs[key]).convert("RGB")
                st.session_state.db.append({
                    "id": key, "title": "Series - " + str(key), "status": "Auto Rated",
                    "front_url": img_front, "back_url": img_back, "is_file": True,
                    "date_from": "2026-03-20", "date_to": "2026-03-25",
                    "loc_from": "Guizhou", "loc_to": "Guangzhou",
                    "from_lon": 106.96, "from_lat": 27.06, "to_lon": 113.26, "to_lat": 23.13,
                    "rating": 4, "ai_reason": "Good condition", "notes": "", "crop_box": None
                })
    st.markdown("---")
    st.subheader("Manage Database")
    for idx, card in enumerate(st.session_state.db):
        c_id = card.get('id', 'Unknown')
        with st.expander(str(c_id) + " | " + str(card.get('title'))):
            c_info, c_ai, c_action = st.columns([3, 3, 2])
            with c_info:
                st.write("Route: " + str(card.get('loc_from')) + " -> " + str(card.get('loc_to')))
                current_rate = int(card.get('rating', 5))
                new_rating = st.slider("Fix Score", 1, 5, current_rate, key="r_"+str(c_id))
                if new_rating != current_rate:
                    card['rating'] = new_rating
                    card['status'] = "Verified"
            with c_ai:
                st.warning("AI Reason: " + str(card.get('ai_reason')))
                card['notes'] = st.text_area("Notes", value=card.get('notes', ''), key="n_"+str(c_id))
            with c_action:
                if st.button("Edit Privacy Box", key="e_"+str(c_id)):
                    st.session_state.current_edit_id = c_id
    if st.session_state.current_edit_id:
        st.markdown("### Manual Cropper")
        from streamlit_cropper import st_cropper
        edit_id = st.session_state.current_edit_id
        target = next(d for d in st.session_state.db if d.get('id') == edit_id)
        st.write("Draw red box over address:")
        cropped_box = st_cropper(target.get('back_url'), realtime_update=True, box_color='#FF0000', aspect_ratio=None, return_type='box')
        if st.button("Lock Box"):
            x1 = int(cropped_box['left'])
            y1 = int(cropped_box['top'])
            x2 = x1 + int(cropped_box['width'])
            y2 = y1 + int(cropped_box['height'])
            target['crop_box'] = (x1, y1, x2, y2)
            target['status'] = "Done"
            st.session_state.current_edit_id = None
            st.success("Updated!")
            st.rerun()

with tab_map:
    st.header("Route Footprints")
    plot_data = []
    for card in st.session_state.db:
        id_str = card.get('id', 'Unknown')
        plot_data.append({"names": str(id_str)+"-From", "lon": card.get('from_lon', 110.0), "lat": card.get('from_lat', 30.0)})
        plot_data.append({"names": str(id_str)+"-To", "lon": card.get('to_lon', 110.0), "lat": card.get('to_lat', 30.0)})
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
