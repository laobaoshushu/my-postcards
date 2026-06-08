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

tabs = st.tabs(["Gallery", "Admin Dashboard", "Route Map"])

with tabs[0]:
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
                t1, t2 = st.tabs(["Front", "Protected Back"])
                with t1: 
                    st.image(card.get('front_url'), use_column_width=True)
                with t2:
                    b_obj = card.get('back_url')
                    b_box = card.get('crop_box')
                    p_back = apply_mosaic_tape(b_obj, b_box)
                    st.image(p_back, use_column_width=True)
                st.write("Route: " + str(card.get('loc_from')) + " -> " + str(card.get('loc_to')))
                st.write("Rating: " + str(card.get('rating', 5)))
                st.markdown("---")

with tabs
