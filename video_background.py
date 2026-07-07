# video_background.py – base64 method (worked before, safe with compressed video)
import streamlit as st
import os
import base64

def set_video_background():
    video_path = "static/background.mp4"
    if not os.path.exists(video_path):
        return

    # Base64 encode the video
    with open(video_path, "rb") as f:
        video_data = f.read()
        b64 = base64.b64encode(video_data).decode("utf-8")
    video_url = f"data:video/mp4;base64,{b64}"

    st.markdown(f"""
    <style>
        .stApp {{
            background: transparent !important;
        }}
        #bgVideo {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            object-fit: cover;
            z-index: -1000;
            pointer-events: none;
        }}
    </style>
    <video autoplay muted loop playsinline id="bgVideo">
        <source src="{video_url}" type="video/mp4">
    </video>
    """, unsafe_allow_html=True)