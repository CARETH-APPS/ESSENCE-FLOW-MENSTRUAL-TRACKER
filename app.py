# ───────────────── FORCE UTF-8 ENVIRONMENT ─────────────────
import os
os.environ["PYTHONIOENCODING"] = "utf-8"

import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta, datetime
from statistics import mean, stdev
import random
import json
import matplotlib.pyplot as plt  
import base64
import calendar
import hashlib
import difflib
import string
import numpy as np
import re
import urllib.parse
import requests
import time
from insights import smart_insights_page
from video_background import set_video_background
from PIL import Image
import shutil
import mimetypes
import html

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="Essence Flow", page_icon="🌸", layout="wide", initial_sidebar_state="auto")
st.set_option('client.toolbarMode', 'minimal')

# ───────────────── BACKGROUND ─────────────────
FALLBACK_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" opacity="0.15">
  <defs><style>.body{fill:#D4A0A0;}.hair{fill:#5D4037;}.cloth{fill:#C28585;}</style></defs>
  <circle cx="100" cy="140" r="30" class="body"/><circle cx="80" cy="110" r="15" class="hair"/>
  <circle cx="120" cy="110" r="15" class="hair"/><ellipse cx="100" cy="180" rx="35" ry="50" class="cloth"/>
  <path d="M85 155 Q100 165 115 155" stroke="#4E342E" fill="none" stroke-width="3"/>
  <circle cx="300" cy="130" r="35" class="body"/><circle cx="280" cy="100" r="18" class="hair"/>
  <circle cx="320" cy="100" r="18" class="hair"/><ellipse cx="300" cy="180" rx="40" ry="55" class="cloth"/>
  <path d="M285 145 Q300 155 315 155" stroke="#4E342E" fill="none" stroke-width="3"/>
  <circle cx="520" cy="150" r="28" class="body"/><circle cx="500" cy="120" r="14" class="hair"/>
  <circle cx="540" cy="120" r="14" class="hair"/><ellipse cx="520" cy="190" rx="35" ry="45" class="cloth"/>
  <path d="M505 165 Q520 175 535 165" stroke="#4E342E" fill="none" stroke-width="3"/>
  <circle cx="60" cy="80" r="4" fill="#FFD700"/><circle cx="350" cy="60" r="5" fill="#FFD700"/>
  <circle cx="570" cy="90" r="3" fill="#FFD700"/>
</svg>"""
FALLBACK_B64 = base64.b64encode(FALLBACK_SVG.encode('utf-8')).decode('utf-8')
FALLBACK_URI = f"data:image/svg+xml;base64,{FALLBACK_B64}"

def get_image_data_uri(image_filename):
    if not st.session_state.get("use_custom_bg", True):
        return FALLBACK_URI
    base_dir = os.path.join(os.getcwd(), "backgrounds")
    file_path = os.path.join(base_dir, image_filename)
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            b64 = base64.b64encode(data).decode('utf-8')
            mime = "image/png" if file_path.lower().endswith(".png") else "image/jpeg"
            return f"data:{mime};base64,{b64}"
        except:
            pass
    return FALLBACK_URI

def set_page_background(image_file):
    use_custom = st.session_state.get("use_custom_bg", True)
    dark = st.session_state.get("night_mode", False)
    if not use_custom:
        bg_uri = FALLBACK_URI
        gradient = "linear-gradient(135deg, #2E1B2E 0%, #4A2C3E 100%)"
        blend = "soft-light"
        if dark:
            gradient = "linear-gradient(135deg, #1e1a2a 0%, #2a1e2a 100%)"
            blend = "darken"
        st.markdown(f"""
        <style>
            .stApp {{
                background: {gradient}, url('{bg_uri}') center/cover no-repeat !important;
                background-blend-mode: {blend} !important;
            }}
        </style>
        """, unsafe_allow_html=True)
        return
    bg_uri = get_image_data_uri(image_file)
    gradient = "linear-gradient(135deg, #2E1B2E 0%, #4A2C3E 100%)"
    blend = "soft-light"
    if dark:
        gradient = "linear-gradient(135deg, #1e1a2a 0%, #2a1e2a 100%)"
        blend = "darken"
    st.markdown(f"""
    <style>
        .stApp {{
            background: {gradient}, url('{bg_uri}') center/cover no-repeat !important;
            background-blend-mode: {blend} !important;
        }}
    </style>
    """, unsafe_allow_html=True)

# ───────────────── LOAD LANGUAGES ─────────────────
def load_languages():
    try:
        with open("languages.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

LANG = load_languages()

FALLBACK_TEXTS = {
    "happy_emoji": "😊 Happy",
    "neutral_emoji": "😐 Neutral",
    "sad_emoji": "😢 Sad",
    "angry_emoji": "😠 Angry",
    "tired_emoji": "😴 Tired",
    "smart_insights": "Smart Insights",
    "chat_with_careth": "Chat with Careth",
    "product_supply": "Product Supply",
    "cycle_history": "Cycle History",
    "pregnancy_info": "Pregnancy Info",
    "learn_books": "Learn & Books",
    "community": "Community",
    "online_hub": "Online Hub",
    "settings": "Settings",
    "admin_panel": "Admin Panel",
    "dashboard": "Dashboard",
    "log_period": "Log Period",
    "symptom_tracker": "Symptom Tracker",
    "calendar_planner": "Calendar & Planner",
    "wellness_insights": "Wellness Insights",
    "prod": "Product Supply",
    "set": "Settings",
    "comm_faq": "Community Stories",
    "rem_cal_tools": "Calendar & Reminders",
    "preg": "Pregnancy Assistant",
    "hist": "Cycle History",
    "sym": "Symptom Tracker",
    "log": "Log Period",
    "wellness": "Wellness Insights",
    "learn_books": "Learn & Books",
    "online_hub": "Online Hub",
    "admin_panel_title": "Admin Panel",
    "you_might_also_like": "You might also like",
    "phase_menstrual": "Menstrual",
    "phase_follicular": "Follicular",
    "phase_ovulation": "Ovulation",
    "phase_luteal": "Luteal",
    "ai_greeting_name1": "Hello",
    "ai_greeting_name2": "Nice to meet you!",
    "ai_greeting_name3": "Hey",
    "ai_greeting_name4": "It's a pleasure to meet you!",
    "ai_greeting_name5": "Hi",
    "ai_greeting_name6": "Lovely to know your name!",
    "ai_greeting_name7": "Welcome",
    "ai_greeting_name8": "Thanks for telling me your name!",
    "ai_greeting_name9": "Greetings",
    "ai_greeting_name10": "I'm Careth, your menstrual health assistant.",
    "ai_how_are_you1": "I'm doing great, thank you for asking! How can I support you today?",
    "ai_how_are_you2": "I'm wonderful, thanks! What's on your mind?",
    "ai_how_are_you3": "I'm here and ready to help! What can I do for you?",
    "ai_who_are_you1": "I'm Careth, your friendly menstrual health assistant. I'm here to answer your questions about periods, symptoms, wellness, and more.",
    "ai_who_are_you2": "I'm Careth – your AI companion for cycle tracking, symptom relief, and reproductive health education.",
    "ai_who_are_you3": "My name is Careth. I was designed to help you understand your body, manage menstrual symptoms, and make informed health decisions.",
    "ai_what_is_name1": "I'm Careth! Your personal menstrual health assistant.",
    "ai_what_is_name2": "You can call me Careth – I'm here to support you with period and wellness questions.",
    "ai_what_is_name3": "I'm Careth, your cycle companion. Ask me anything!",
    "ai_what_can_do1": "I can help you with period predictions, symptom management, product advice, wellness tips, and understanding your cycle phases.",
    "ai_what_can_do2": "You can ask me about cramps, PMS, irregular periods, fertility, contraception, nutrition, and much more. I'm here to help!",
    "ai_what_can_do3": "I can answer questions about your cycle, suggest remedies for pain, explain medical conditions, and guide you through using the Essence Flow app.",
    "ai_hello1": "Hello! How can I help you today?",
    "ai_hello2": "Hi there! What would you like to know about your cycle?",
    "ai_hello3": "Hey! I'm Careth, your menstrual health assistant. Ask me anything.",
    "ai_good_morning": "Good morning! I hope you have a peaceful day. How are you feeling?",
    "ai_good_afternoon": "Good afternoon! I'm here whenever you need me.",
    "ai_good_evening": "Good evening! Take a deep breath – I'm here to help.",
    "ai_thanks1": "You're very welcome! I'm always here for you.",
    "ai_thanks2": "Happy to help! Stay strong and healthy.",
    "ai_thanks3": "Glad I could assist! Come back anytime.",
    "ai_bye1": "Goodbye! Take care of yourself.",
    "ai_bye2": "See you next time! Wishing you a healthy cycle.",
    "ai_bye3": "Farewell! Remember, I'm always here when you need support.",
    "ai_no_intents": "I'm still learning, but I couldn't find an answer to your question. Could you rephrase?",
    "ai_low_similarity": "I'm not sure I understood. Can you ask in a different way?",
    "ai_ask_question": "Please type your question so I can help you.",
    "ai_fallback": "I'm not sure how to answer that. Try asking about periods, cramps, products, or wellness.",
    "ai_next_period": "Your next period is predicted to start around {date}.",
    "ai_need_more_periods": "I need more period data to make a prediction. Log at least two periods.",
    "ai_current_day": "You are on day {day} of your cycle. Your average cycle length is {length} days.",
    "ai_log_period_first": "Please log your last period first so I can help.",
    "ai_avg_cycle": "Your average cycle length is {length} days.",
    "ai_last_period": "Your last period started on {date}.",
    "ai_ovulation_today": "You are likely ovulating today – your most fertile day!",
    "ai_ovulation_past": "Your last ovulation was around {date}.",
    "ai_ovulation_future": "You are likely to ovulate in about {days} days (around {date}).",
    "ai_need_more_cycles": "Log more cycles to get accurate ovulation predictions.",
    "ai_ovulation_date": "Your predicted ovulation date is around {date}.",
    "ai_log_periods_for_ovulation": "I need at least two periods to predict ovulation.",
    "ai_period_duration": "Your periods usually last {days} days.",
    "ai_irregular_high": "Your cycles are quite irregular (variability {var:.1f} days). Consider tracking triggers or seeing a doctor if it bothers you.",
    "ai_irregular_normal": "Your cycles show mild variation ({var:.1f} days), which is normal.",
    "ai_not_enough_cycles": "Log more cycles to analyse irregularity.",
    "ai_periods_logged": "You have logged {count} periods so far.",
    "weekly_score_needs_improvement": "Your wellness score needs improvement. Try to drink more water, sleep better, or exercise.",
    "exercise_guides": "Exercise Guides",
    "select_topic": "Select a topic",
    "save_cycle_settings": "Save Cycle Settings",
    "period_duration_days": "Period Duration (days)",
    "icon_only_nav": "Icon only navigation",
    "save_emergency_contact": "Save Emergency Contact",
    "water_goal": "Water goal: {goal} glasses",
    "pain_level": "Pain level (0=none, 10=worst)",
    "pain": "Pain (1-10)",
    "self_care_activity": "Self-care activity (optional)"
}

def t(key):
    lang = st.session_state.get("language", "English")
    val = LANG.get(lang, {}).get(key, LANG.get("English", {}).get(key, None))
    if val is None:
        return FALLBACK_TEXTS.get(key, key)
    return val

# ───────────────── STYLING ─────────────────
st.markdown("""
<style>
    .stApp { background: #2E1B2E; }
    .card { background: rgba(40, 25, 40, 0.85); border-radius: 24px; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 8px 24px rgba(0,0,0,0.3); color: #F0E6EF; }
    .phase-badge { background: #5E3A4A; color: #F0E6EF; padding: 0.4rem 1.5rem; border-radius: 30px; font-weight: 700; }
    .alert-banner { background: rgba(60, 30, 40, 0.9); border-left: 6px solid #C28585; padding: 1rem 1.5rem; border-radius: 16px; margin: 1rem 0; color: #F0E6EF; }
    .quick-card { background: rgba(40,25,40,0.85); border-radius: 20px; padding: 1.2rem; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.3); transition: 0.2s; color: #F0E6EF; }
    .quick-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.5); }
    .circular-progress { width: 130px; height: 130px; border-radius: 50%; background: conic-gradient(#C28585 calc(var(--p)*1%), #5E3A4A 0); display: flex; align-items: center; justify-content: center; margin: 0 auto; }
    .circular-inner { width: 100px; height: 100px; border-radius: 50%; background: #3A2430; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; font-weight: 700; color: #F0E6EF; }
    .footer { text-align: center; color: #F0E6EF; margin-top: 2rem; font-size: 0.9rem; opacity: 0.7; }
    h1, h2, h3, h4, h5, h6 { color: #F0E6EF; font-weight: 700; }
    .stButton button { background: #C28585; color: white; border-radius: 20px; border: none; padding: 0.7rem 2rem; font-weight: 600; box-shadow: 0 4px 12px rgba(180,65,128,0.3); }
    .stButton button:hover { background: #D4A0A0; }
    .css-1d391kg { background: #1B131C; }
    .sidebar-header { padding: 1rem 0.5rem 0.5rem 0.5rem; text-align: center; border-bottom: 1px solid #5E3A4A; margin-bottom: 0.8rem; }
    .sidebar-header h2 { margin-bottom: 0.2rem; font-size: 1.8rem; }
    .stRadio > div { flex-direction: column; gap: 0.6rem; }
    .stRadio label { font-size: 1.2rem; font-weight: 500; color: #F0E6EF; display: flex; align-items: center; gap: 0.7rem; padding: 0.5rem 0.8rem; border-radius: 14px; transition: background 0.2s, color 0.2s; }
    .stRadio label:hover { background: rgba(194, 133, 133, 0.2); color: #EAA4BE; }
    .stDateInput label, .stSelectbox label, .stTextInput label, .stTextArea label, .stSlider label { color: #F0E6EF !important; }
    .book-reader {
        background: rgba(255, 248, 245, 0.95);
        padding: 2rem;
        border-radius: 20px;
        font-family: 'Georgia', 'Times New Roman', serif;
        font-size: 1.15rem;
        line-height: 1.8;
        color: #2E1B2E;
        max-height: 70vh;
        overflow-y: auto;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        border: 1px solid #C28585;
    }
    .dark-mode .book-reader {
        background: rgba(30, 20, 40, 0.95);
        color: #F0E6EF;
        border-color: #EAA4BE;
    }
    .book-reader h1, .book-reader h2, .book-reader h3 {
        color: #B34180;
        font-weight: 600;
    }
    .book-reader p {
        margin-bottom: 1rem;
    }
    .book-reader::-webkit-scrollbar {
        width: 8px;
    }
    .book-reader::-webkit-scrollbar-track {
        background: #E8D8E0;
        border-radius: 10px;
    }
    .book-reader::-webkit-scrollbar-thumb {
        background: #C28585;
        border-radius: 10px;
    }
    .onboarding-highlight {
        background: rgba(194,133,133,0.3);
        border-left: 4px solid #FFD700;
        padding: 0.8rem;
        border-radius: 12px;
        margin: 0.5rem 0;
    }
    .top-nav {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 8px;
        margin-bottom: 20px;
        background: rgba(30, 20, 30, 0.7);
        padding: 10px;
        border-radius: 30px;
        backdrop-filter: blur(5px);
    }
    .top-nav button {
        background: #5E3A4A;
        border: none;
        border-radius: 40px;
        padding: 8px 12px;
        color: white;
        font-size: 0.9rem;
        font-weight: 500;
        cursor: pointer;
        transition: 0.2s;
    }
    .top-nav button:hover {
        background: #C28585;
        transform: scale(1.02);
    }
    @media (max-width: 768px) {
        .top-nav button {
            font-size: 0.75rem;
            padding: 6px 8px;
        }
    }
    .focus-chat-input {
        animation: gentle-pulse 0.5s;
    }
    @keyframes gentle-pulse {
        0% { border-color: #C28585; }
        100% { border-color: inherit; }
    }
    .main-chat-expander {
        background: rgba(30, 20, 35, 0.9);
        border-radius: 20px;
        margin-bottom: 20px;
        padding: 0.5rem;
    }
    .community-post {
        background: rgba(255,255,255,0.05);
        border-radius: 20px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        border: 1px solid #5E3A4A;
        transition: 0.2s;
    }
    .community-post:hover {
        background: rgba(255,255,255,0.08);
        border-color: #C28585;
    }
    .post-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 0.5rem;
    }
    .post-username {
        font-weight: 600;
        color: #EAA4BE;
        font-size: 1.1rem;
    }
    .post-time {
        font-size: 0.8rem;
        opacity: 0.6;
        margin-left: auto;
    }
    .notification-badge {
        background: #ff4444;
        color: white;
        border-radius: 50%;
        padding: 0.1rem 0.5rem;
        font-size: 0.7rem;
        margin-left: 0.3rem;
    }
    .read-receipt {
        font-size: 0.8rem;
        margin-left: 0.3rem;
    }
    .msg-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.2rem;
    }
    .contact-card {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px;
        border-radius: 12px;
        background: rgba(255,255,255,0.05);
        margin: 4px 0;
        cursor: pointer;
        transition: 0.2s;
    }
    .contact-card:hover {
        background: rgba(255,255,255,0.12);
    }
    .scroll-arrow {
        position: fixed;
        bottom: 80px;
        right: 20px;
        background: #C28585;
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        font-size: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        cursor: pointer;
        z-index: 1000;
        transition: 0.2s;
    }
    .scroll-arrow:hover {
        background: #D4A0A0;
        transform: scale(1.1);
    }
    .unread-glow {
        box-shadow: 0 0 12px #ff4444;
        border-left: 4px solid #ff4444;
        padding-left: 8px;
    }
</style>
""", unsafe_allow_html=True)

def apply_night_mode():
    if st.session_state.get("night_mode"):
        st.markdown("""
        <style>
            .stApp { background: #1a1a2e !important; }
            .card { background: rgba(25, 25, 40, 0.9) !important; }
            .alert-banner { background: rgba(35, 30, 40, 0.95) !important; }
            .phase-badge { background: #4a3a4a !important; }
            .circular-inner { background: #2a2a3e !important; }
            .quick-card { background: rgba(25, 25, 40, 0.9) !important; }
            .css-1d391kg { background: #0f0f1a; }
            .book-reader { background: rgba(30, 25, 40, 0.95); color: #e0e0e0; border-color: #C28585; }
            .onboarding-highlight { background: rgba(100,70,100,0.4); }
            .top-nav { background: rgba(20, 20, 30, 0.8); }
            .stButton button { background: #7a5a7a; }
            .stButton button:hover { background: #9a7a9a; }
            .stRadio label { color: #e0e0e0; }
            .stDateInput label, .stSelectbox label, .stTextInput label, .stTextArea label, .stSlider label { color: #e0e0e0 !important; }
            .stMarkdown, .stMarkdown p, .stMarkdown div { color: #e0e0e0; }
            .scroll-arrow { background: #7a5a7a; }
            .scroll-arrow:hover { background: #9a7a9a; }
        </style>
        """, unsafe_allow_html=True)

# ───────────────── DATABASE ─────────────────
DB = "cycle_data.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, password TEXT, email TEXT, created_at TEXT, country TEXT DEFAULT 'GH')")
    for col, dtype in [("is_admin", "INTEGER DEFAULT 0"), ("is_teen", "INTEGER DEFAULT NULL"), 
                       ("last_username_change", "TEXT"), ("profile_pic", "TEXT")]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")
        except sqlite3.OperationalError:
            pass
    c.execute("CREATE TABLE IF NOT EXISTS cycles (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, start_date TEXT, cycle_length INTEGER, period_duration INTEGER DEFAULT 5, flow_quality TEXT, pain_level INTEGER, medication TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS symptoms (user_id INTEGER, date TEXT, cramps TEXT, mood TEXT, flow TEXT, pain INTEGER, energy INTEGER, bloating TEXT, appetite TEXT, notes TEXT, headache TEXT, skin TEXT, bleeding_intensity TEXT, anemia_symptoms TEXT, lower_back_pain TEXT, breast_tenderness TEXT, PRIMARY KEY(user_id, date))")
    c.execute("CREATE TABLE IF NOT EXISTS product_inventory (user_id INTEGER, product_type TEXT, count INTEGER, price REAL DEFAULT 0, threshold INTEGER DEFAULT 3, notes TEXT, is_reusable INTEGER DEFAULT 0, PRIMARY KEY(user_id, product_type))")
    c.execute("CREATE TABLE IF NOT EXISTS product_usage (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, period_start_date TEXT, product_type TEXT, quantity_used INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS settings (user_id INTEGER, key TEXT, value TEXT, PRIMARY KEY(user_id, key))")
    c.execute("CREATE TABLE IF NOT EXISTS daily_wellness (user_id INTEGER, date TEXT, mood_emoji TEXT, water_glasses INTEGER, sleep_hours REAL, exercise_minutes INTEGER, self_care TEXT, PRIMARY KEY(user_id, date))")
    c.execute("CREATE TABLE IF NOT EXISTS calendar_events (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, event_date TEXT, title TEXT, type TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS planner_tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, task_text TEXT, phase_suggested TEXT, completed INTEGER DEFAULT 0, user_type TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS custom_symptoms (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, symptom_name TEXT UNIQUE)")
    c.execute("CREATE TABLE IF NOT EXISTS symptom_log_custom (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, symptom_id INTEGER, severity TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS journal (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, entry TEXT, private INTEGER DEFAULT 1)")
    c.execute("CREATE TABLE IF NOT EXISTS medications (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT UNIQUE)")
    c.execute("CREATE TABLE IF NOT EXISTS medication_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, med_id INTEGER, dosage TEXT, notes TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS bbt (user_id INTEGER, date TEXT, temperature REAL, PRIMARY KEY(user_id, date))")
    c.execute("CREATE TABLE IF NOT EXISTS cervical_mucus (user_id INTEGER, date TEXT, type TEXT, PRIMARY KEY(user_id, date))")
    c.execute("CREATE TABLE IF NOT EXISTS ovulation_tests (user_id INTEGER, date TEXT, result TEXT, PRIMARY KEY(user_id, date))")
    c.execute("CREATE TABLE IF NOT EXISTS water_intake (user_id INTEGER, date TEXT, glasses INTEGER, PRIMARY KEY(user_id, date))")
    c.execute("CREATE TABLE IF NOT EXISTS exercise_log (user_id INTEGER, date TEXT, minutes INTEGER, type TEXT, PRIMARY KEY(user_id, date))")
    c.execute("CREATE TABLE IF NOT EXISTS sleep_quality (user_id INTEGER, date TEXT, hours REAL, quality INTEGER, PRIMARY KEY(user_id, date))")
    c.execute("CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, reminder_date TEXT, title TEXT, description TEXT, is_recurring INTEGER DEFAULT 0)")
    c.execute("CREATE TABLE IF NOT EXISTS partner_notes (user_id INTEGER, note TEXT, created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS product_locations (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, location_name TEXT, address TEXT, product_type TEXT, submitted_date TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS skipped_cycles (user_id INTEGER, cycle_start_date TEXT, reason TEXT, PRIMARY KEY(user_id, cycle_start_date))")
    c.execute("CREATE TABLE IF NOT EXISTS global_settings (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('whatsapp_teen_group', '')")
    c.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('whatsapp_adult_group', '')")
    
    c.execute("CREATE TABLE IF NOT EXISTS chat_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, timestamp TEXT, user_message TEXT, ai_response TEXT, flagged INTEGER DEFAULT 0)")
    c.execute("""
        CREATE TABLE IF NOT EXISTS community_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            text TEXT,
            image_path TEXT,
            timestamp TEXT,
            likes INTEGER DEFAULT 0,
            expires_at TEXT,
            deleted INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS community_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            user_id INTEGER,
            username TEXT,
            text TEXT,
            timestamp TEXT,
            deleted INTEGER DEFAULT 0
        )
    """)
    try:
        c.execute("ALTER TABLE community_replies ADD COLUMN deleted INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    c.execute("""
        CREATE TABLE IF NOT EXISTS community_likes (
            post_id INTEGER,
            user_id INTEGER,
            PRIMARY KEY (post_id, user_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            details TEXT,
            timestamp TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS private_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user INTEGER,
            to_user INTEGER,
            message TEXT,
            timestamp TEXT,
            read INTEGER DEFAULT 0,
            deleted_for_sender INTEGER DEFAULT 0
        )
    """)
    try:
        c.execute("ALTER TABLE private_messages ADD COLUMN deleted_for_sender INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    for col in ["file_path", "file_name"]:
        try:
            c.execute(f"ALTER TABLE private_messages ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass
    c.execute("""
        CREATE TABLE IF NOT EXISTS blocked_users (
            user_id INTEGER,
            blocked_user_id INTEGER,
            PRIMARY KEY (user_id, blocked_user_id)
        )
    """)
    conn.commit()
    conn.close()
    for folder in ["uploads", "uploads/profiles", "uploads/private"]:
        if not os.path.exists(folder):
            os.makedirs(folder)

def get_global_setting(key, default=""):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT value FROM global_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_global_setting(key, value):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO global_settings (key, value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()
def is_strong_password(pw):
    if len(pw) < 8: return False, t("password_too_short")
    if not re.search(r"[A-Z]", pw): return False, t("password_no_upper")
    if not re.search(r"[0-9]", pw): return False, t("password_no_digit")
    return True, ""

def register_user(name, pw, email="", country="GH"):
    strong, msg = is_strong_password(pw)
    if not strong: return msg
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (name, password, email, created_at, country) VALUES (?,?,?,?,?)",
                  (name, hash_pw(pw), email, datetime.now().isoformat(), country))
        user_id = c.lastrowid
        if name == "CARETHAICARETH12349090":
            c.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
        c.execute("INSERT INTO settings (user_id, key, value) VALUES (?,?,?)", (user_id, "cycle_len", "28"))
        c.execute("INSERT INTO settings (user_id, key, value) VALUES (?,?,?)", (user_id, "period_dur", "5"))
        c.execute("INSERT INTO settings (user_id, key, value) VALUES (?,?,?)", (user_id, "teen_mode", "False"))
        c.execute("INSERT INTO settings (user_id, key, value) VALUES (?,?,?)", (user_id, "emergency_name", ""))
        c.execute("INSERT INTO settings (user_id, key, value) VALUES (?,?,?)", (user_id, "emergency_phone", ""))
        c.execute("INSERT INTO settings (user_id, key, value) VALUES (?,?,?)", (user_id, "online_mode", "True"))
        for prod, cnt in [("pad",20),("tampon",10),("cup",1)]:
            c.execute("INSERT INTO product_inventory (user_id, product_type, count) VALUES (?,?,?)", (user_id, prod, cnt))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(name, pw):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, name, country, is_admin, last_username_change, profile_pic FROM users WHERE name=? AND password=?", (name, hash_pw(pw)))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0], row[1], row[2], row[3], row[4], row[5]
    return None, None, "GH", 0, None, None

def get_user_setting(user_id, key, default=""):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE user_id=? AND key=?", (user_id, key))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_user_setting(user_id, key, value):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (user_id, key, value) VALUES (?,?,?)", (user_id, key, value))
    conn.commit()
    conn.close()

def log_user_activity(user_id, action, details=""):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO user_activity_log (user_id, action, details, timestamp) VALUES (?,?,?,?)",
              (user_id, action, details, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ─── BLOCK/UNBLOCK HELPERS ──────────────────────────────────────────
def block_user(user_id, blocked_user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO blocked_users (user_id, blocked_user_id) VALUES (?,?)", (user_id, blocked_user_id))
    conn.commit()
    conn.close()
    log_user_activity(user_id, "blocked_user", f"Blocked user ID: {blocked_user_id}")

def unblock_user(user_id, blocked_user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM blocked_users WHERE user_id = ? AND blocked_user_id = ?", (user_id, blocked_user_id))
    conn.commit()
    conn.close()
    log_user_activity(user_id, "unblocked_user", f"Unblocked user ID: {blocked_user_id}")

def is_user_blocked(user_id, blocked_user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT 1 FROM blocked_users WHERE user_id = ? AND blocked_user_id = ?", (user_id, blocked_user_id))
    row = c.fetchone()
    conn.close()
    return row is not None

def load_cycles(user_id):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM cycles WHERE user_id=? ORDER BY start_date ASC", conn, params=[user_id])
    conn.close()
    return df

def delete_cycle(user_id, cycle_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM cycles WHERE id = ? AND user_id = ?", (cycle_id, user_id))
    c.execute("SELECT id, start_date FROM cycles WHERE user_id=? ORDER BY start_date ASC", (user_id,))
    rows = c.fetchall()
    if len(rows) >= 2:
        for i in range(len(rows) - 1):
            current_id = rows[i][0]
            current_date = date.fromisoformat(rows[i][1])
            next_date = date.fromisoformat(rows[i+1][1])
            diff = (next_date - current_date).days
            c.execute("UPDATE cycles SET cycle_length = ? WHERE id = ?", (diff, current_id))
    elif len(rows) == 1:
        c.execute("UPDATE cycles SET cycle_length = NULL WHERE id = ?", (rows[0][0],))
    conn.commit()
    conn.close()
    st.success("Period deleted and cycle lengths recalculated.")
    time.sleep(0.5)

def add_period(user_id, ds, dur, flow_q="", pain_lvl=0, med=""):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT start_date FROM cycles WHERE user_id=? AND start_date < ? ORDER BY start_date DESC LIMIT 1", (user_id, ds))
    prev = c.fetchone()
    if prev:
        pl = (date.fromisoformat(ds) - date.fromisoformat(prev[0])).days
        c.execute("UPDATE cycles SET cycle_length = ? WHERE user_id=? AND start_date = ?", (pl, user_id, prev[0]))
    c.execute("INSERT OR IGNORE INTO cycles (user_id, start_date, period_duration, flow_quality, pain_level, medication) VALUES (?,?,?,?,?,?)",
              (user_id, ds, int(dur), flow_q, int(pain_lvl), med))
    conn.commit()
    conn.close()
    st.balloons()
    time.sleep(0.5)

def skip_period(user_id, expected_start_date, reason="Not specified"):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO skipped_cycles (user_id, cycle_start_date, reason) VALUES (?,?,?)",
              (user_id, expected_start_date, reason))
    conn.commit()
    conn.close()
    st.balloons()
    time.sleep(0.5)

def is_period_skipped(user_id, start_date):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT 1 FROM skipped_cycles WHERE user_id=? AND cycle_start_date=?", (user_id, start_date))
    row = c.fetchone()
    conn.close()
    return row is not None

def get_late_period_reminder(user_id):
    p = predict(user_id)
    if p["next"] and p["last"]:
        today = date.today()
        if today > p["next"]:
            cycles = load_cycles(user_id)
            latest = cycles["start_date"].max() if not cycles.empty else None
            if not latest or date.fromisoformat(latest) < p["next"]:
                if not is_period_skipped(user_id, p["next"].isoformat()):
                    return p["next"]
    return None

def save_sym(user_id, d, cramps, mood, flow, pain, energy, bloating, appetite, notes, headache="", skin="", bleeding_intensity="Normal", anemia_symptoms="", lower_back_pain="No", breast_tenderness="No"):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO symptoms (user_id, date, cramps, mood, flow, pain, energy, bloating, appetite, notes, headache, skin, bleeding_intensity, anemia_symptoms, lower_back_pain, breast_tenderness) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (user_id, d, cramps, mood, flow, int(pain), int(energy), bloating, appetite, notes, headache, skin, bleeding_intensity, anemia_symptoms, lower_back_pain, breast_tenderness))
    conn.commit()
    conn.close()
    st.balloons()
    time.sleep(0.5)

def get_sym(user_id, d):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM symptoms WHERE user_id=? AND date=?", (user_id, d))
    r = c.fetchone()
    conn.close()
    return r

def get_products(user_id):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT product_type, count, price, threshold, notes, is_reusable FROM product_inventory WHERE user_id=?", conn, params=[user_id])
    conn.close()
    return df

def upd_product(user_id, pt, delta):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE product_inventory SET count = count + ? WHERE user_id=? AND product_type=?", (delta, user_id, pt))
    conn.commit()
    conn.close()
    st.balloons()
    time.sleep(0.5)

def update_product_price(user_id, product_type, new_price):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE product_inventory SET price = ? WHERE user_id=? AND product_type=?", (new_price, user_id, product_type))
    conn.commit()
    conn.close()
    st.success(f"Price for {product_type} updated to {new_price:.2f}")
    time.sleep(0.5)

def recent_sym(user_id, n=10):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT date, pain, energy, mood FROM symptoms WHERE user_id=? ORDER BY date DESC LIMIT ?", conn, params=[user_id, n])
    conn.close()
    return df

def load_wellness(user_id):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM daily_wellness WHERE user_id=? ORDER BY date DESC", conn, params=[user_id])
    conn.close()
    return df

def save_wellness(user_id, d, mood_emoji, water, sleep, exercise, self_care):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO daily_wellness (user_id, date, mood_emoji, water_glasses, sleep_hours, exercise_minutes, self_care) VALUES (?,?,?,?,?,?,?)",
              (user_id, d, mood_emoji, int(water), float(sleep), int(exercise), self_care))
    conn.commit()
    conn.close()

def add_calendar_event(user_id, event_date, title, etype="custom"):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO calendar_events (user_id, event_date, title, type) VALUES (?,?,?,?)", (user_id, event_date, title, etype))
    conn.commit()
    conn.close()

def load_all_calendar_events(user_id):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM calendar_events WHERE user_id=?", conn, params=[user_id])
    conn.close()
    return df

def get_planner_tasks(user_id, start_date, end_date):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT id, date, task_text, phase_suggested, completed FROM planner_tasks WHERE user_id=? AND date BETWEEN ? AND ? ORDER BY date",
                           conn, params=[user_id, start_date, end_date])
    conn.close()
    return df

def add_planner_task(user_id, task_date, task_text, phase_suggested="", user_type=""):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO planner_tasks (user_id, date, task_text, phase_suggested, user_type, completed) VALUES (?,?,?,?,?,?)",
              (user_id, task_date.isoformat(), task_text, phase_suggested, user_type, 0))
    conn.commit()
    conn.close()

def update_task_completion(user_id, task_id, completed):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE planner_tasks SET completed = ? WHERE id=? AND user_id=?", (1 if completed else 0, task_id, user_id))
    conn.commit()
    conn.close()
    st.balloons()
    time.sleep(0.5)

def add_reminder(user_id, reminder_date, title, description, is_recurring=0):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO reminders (user_id, reminder_date, title, description, is_recurring) VALUES (?,?,?,?,?)",
              (user_id, reminder_date.isoformat(), title, description, is_recurring))
    conn.commit()
    conn.close()
    st.balloons()
    time.sleep(0.5)

def get_reminders(user_id, from_date):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM reminders WHERE user_id=? AND reminder_date >= ? ORDER BY reminder_date", conn, params=[user_id, from_date.isoformat()])
    conn.close()
    return df

def get_all_reminders(user_id):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT reminder_date, title, description FROM reminders WHERE user_id=? ORDER BY reminder_date", conn, params=[user_id])
    conn.close()
    return df

def predict(user_id):
    df = load_cycles(user_id)
    cl = int(get_user_setting(user_id, "cycle_len", "28"))
    pd_ = int(get_user_setting(user_id, "period_dur", "5"))
    if df.empty:
        return {"last": None, "avg_cl": cl, "pd": pd_, "next": None, "ov": None, "fw": [], "prediction_range": (cl-2, cl+2), "confidence": "Low", "variability": 0, "cycle_count": 0}
    ls = date.fromisoformat(df["start_date"].iloc[-1])
    dur = int(df["period_duration"].iloc[-1]) if not pd.isna(df["period_duration"].iloc[-1]) else pd_
    comp = df["cycle_length"].dropna().tolist()
    comp = [int(x) for x in comp]
    avg_cl = int(round(mean(comp))) if comp else cl
    variability = stdev(comp) if len(comp) >= 2 else 0
    pn = ls + timedelta(days=avg_cl)
    ov = pn - timedelta(days=14)
    fw = [ov - timedelta(days=5), ov + timedelta(days=5)]
    if comp:
        range_low = max(1, avg_cl - int(variability))
        range_high = avg_cl + int(variability)
        confidence = "High" if variability <= 3 else "Medium" if variability <= 7 else "Low"
    else:
        range_low = cl - 2
        range_high = cl + 2
        confidence = "Low"
    return {"last": ls, "avg_cl": avg_cl, "pd": dur, "next": pn, "ov": ov, "fw": fw, "variability": variability, "cycle_count": len(df),
            "prediction_range": (range_low, range_high), "confidence": confidence}

def cd_(p):
    if not p["last"]: return None
    return max((date.today() - p["last"]).days + 1, 0)

def phase(cd, p):
    if cd is None: return "Unknown"
    dur = int(p["pd"])
    ov_day = (p["ov"] - p["last"]).days + 1 if p["ov"] else None
    if not ov_day: return "Unknown"
    discreet = st.session_state.get("discreet", False)
    teen = st.session_state.get("teen_mode", False)
    if discreet:
        if cd <= dur: return "Phase 1"
        elif cd < ov_day: return "Phase 2"
        elif cd == ov_day: return "Phase 3"
        else: return "Phase 4"
    if teen:
        if cd <= dur: return t("phase_teen_period")
        elif cd < ov_day: return t("phase_teen_growing")
        elif cd == ov_day: return t("phase_teen_ovulation")
        else: return t("phase_teen_pre")
    if cd <= dur: return t("phase_menstrual")
    elif cd < ov_day: return t("phase_follicular")
    elif cd == ov_day: return t("phase_ovulation")
    else: return t("phase_luteal")

def check_red_flags(user_id):
    flags = []
    today = date.today()
    p = predict(user_id)
    if p["last"]:
        days_since = (today - p["last"]).days
        if days_since > 45 and p["cycle_count"] >= 2:
            flags.append(t("flag_missed_period"))
    s = get_sym(user_id, today.isoformat())
    if s:
        pain_val = s[4]
        if pain_val is not None and str(pain_val) != 'None':
            try:
                if int(pain_val) >= 8:
                    flags.append(t("flag_severe_pain"))
            except:
                pass
        if len(s) > 11 and s[11] == "Flooding":
            flags.append(t("flag_flooding"))
        if len(s) > 12 and s[12]:
            flags.append(t("flag_anemia"))
        if len(s) > 9 and s[9] == "Severe":
            flags.append(t("flag_severe_headache"))
    return flags

def get_country_emergency_numbers(country_code):
    numbers = {
        "GH": {"ambulance": "193", "mental": "233 243 222 222", "reproductive": "0800 900 111"},
        "NG": {"ambulance": "112", "mental": "0800 332 2646", "reproductive": "0800 225 522"},
        "KE": {"ambulance": "999", "mental": "1190", "reproductive": "0800 720 575"},
        "ZA": {"ambulance": "10177", "mental": "0800 567 567", "reproductive": "0800 123 345"}
    }
    return numbers.get(country_code, numbers["GH"])

def sos_module(user_id):
    with st.expander(t("when_to_see_doctor"), expanded=False):
        st.markdown(t("doctor_signs"))
        user_flags = check_red_flags(user_id)
        if user_flags:
            st.warning(t("based_on_data"))
            for f in user_flags:
                st.error(f)
        country_code = st.session_state.get("user_country", "GH")
        em = get_country_emergency_numbers(country_code)
        st.info(t("emergency_numbers_info").format(amb=em['ambulance'], ment=em['mental'], repr=em['reproductive']))
    emergency_name = get_user_setting(user_id, "emergency_name", "")
    emergency_phone = get_user_setting(user_id, "emergency_phone", "")
    if emergency_name and emergency_phone:
        st.info(t("your_emergency_contact").format(name=emergency_name, phone=emergency_phone))
        st.markdown(f'<a href="tel:{emergency_phone}" target="_blank"><button style="background:#C28585; color:white; border:none; border-radius:20px; padding:0.5rem 1rem;">📱 {t("call_button")} {emergency_name}</button></a>', unsafe_allow_html=True)

def add_product_location(user_id, location_name, address, product_type):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO product_locations (user_id, location_name, address, product_type, submitted_date) VALUES (?,?,?,?,?)",
              (user_id, location_name, address, product_type, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    st.balloons()
    time.sleep(0.5)

def get_product_locations():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT location_name, address, product_type FROM product_locations ORDER BY submitted_date DESC", conn)
    conn.close()
    return df

def get_cycle_irregularity(user_id):
    cycles = load_cycles(user_id)
    if len(cycles) < 3:
        return None
    comp = cycles["cycle_length"].dropna().tolist()
    if len(comp) >= 2:
        variability = stdev(comp)
        if variability > 7:
            return t("irregular_advice").format(var=variability)
    return None

def get_region_average(country_code):
    if country_code in ["GH", "NG", "CI", "SN"]:
        return (24, 32)
    elif country_code in ["KE", "UG", "TZ", "RW"]:
        return (25, 33)
    elif country_code in ["ZA", "ZW", "ZM", "MW"]:
        return (26, 34)
    else:
        return (21, 35)

def product_tracker(user_id):
    set_page_background("products.png")
    st.title(t("prod"))
    df = get_products(user_id)
    if df.empty:
        st.info(t("no_products"))
        prods = {}
    else:
        prods = df.set_index("product_type").to_dict(orient="index")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([t("inventory_tab"), t("usage_history_tab"), t("cost_savings_tab"), t("shopping_list_tab"), t("care_tips_tab")])
    with tab1:
        st.subheader(t("your_stock"))
        with st.expander(t("add_new_product")):
            with st.form("new_product_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input(t("product_name"))
                    new_count = st.number_input(t("initial_count"), 1, 1000, 10)
                    new_price = st.number_input(t("price_per_unit_local"), 0.0, 1000.0, 0.0, step=0.5)
                with col2:
                    new_threshold = st.number_input(t("low_stock_threshold"), 1, 50, 3)
                    new_notes = st.text_area(t("notes_optional"))
                    is_reusable = st.checkbox(t("reusable_product"))
                if st.form_submit_button(t("add")):
                    conn = sqlite3.connect(DB)
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO product_inventory (user_id, product_type, count, price, threshold, notes, is_reusable) VALUES (?,?,?,?,?,?,?)",
                              (user_id, new_name, new_count, new_price, new_threshold, new_notes, 1 if is_reusable else 0))
                    conn.commit()
                    conn.close()
                    st.success(t("added_success").format(name=new_name))
                    st.rerun()
        if prods:
            for pt, info in prods.items():
                with st.container():
                    st.markdown(f"**{pt.capitalize()}**")
                    col_labels = st.columns([2, 1, 1, 1, 1])
                    col_labels[0].write(f"📦 {t('stock')}")
                    col_labels[1].write(f"➖ {t('use')}")
                    col_labels[2].write(f"➕ {t('add')}")
                    col_labels[3].write(f"💰 {t('price')} (GHS)")
                    col_labels[4].write(f"⚙️ {t('action')}")
                    
                    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                    col1.metric("", info["count"])
                    if info["count"] <= info["threshold"]:
                        col1.warning(t("low_stock_warning").format(threshold=info["threshold"]))
                    
                    use = col2.number_input("", 0, 100, 0, key=f"use_{pt}", label_visibility="collapsed")
                    add = col3.number_input("", 0, 100, 0, key=f"add_{pt}", label_visibility="collapsed")
                    edit_price = col4.number_input("", 0.0, 1000.0, info["price"], step=0.5, key=f"price_{pt}", label_visibility="collapsed")
                    if col5.button(t("update"), key=f"btn_{pt}"):
                        net = -use + add
                        if net != 0:
                            upd_product(user_id, pt, net)
                        if edit_price != info["price"]:
                            update_product_price(user_id, pt, edit_price)
                        st.rerun()
                    
                    if info["price"] > 0 or info["notes"]:
                        with st.expander(t("details")):
                            if info["price"] > 0:
                                st.caption(f"💵 {t('price')}: {info['price']:.2f}")
                            if info["notes"]:
                                st.caption(f"📝 {info['notes']}")
                            if info["is_reusable"]:
                                st.caption("♻️ " + t("reusable_note"))
                    st.divider()
    with tab2:
        st.subheader(t("product_usage_period"))
        conn = sqlite3.connect(DB)
        usage_df = pd.read_sql_query("SELECT period_start_date, product_type, quantity_used FROM product_usage WHERE user_id=? ORDER BY period_start_date DESC", conn, params=[user_id])
        conn.close()
        if not usage_df.empty:
            pivot = usage_df.pivot_table(index="period_start_date", columns="product_type", values="quantity_used", fill_value=0)
            st.dataframe(pivot, use_container_width=True)
            if len(pivot.columns) > 0:
                fig, ax = plt.subplots()
                for col in pivot.columns[:3]:
                    ax.plot(pivot.index, pivot[col], marker='o', label=col)
                ax.set_xlabel(t("period_start"))
                ax.set_ylabel(t("quantity_used"))
                ax.legend()
                st.pyplot(fig)
        else:
            st.info(t("log_usage_info"))
    with tab3:
        st.subheader(t("cost_savings"))
        if not prods:
            st.info(t("add_prices_to_see_savings"))
        else:
            disposable = df[(df["is_reusable"] == 0) & (df["price"] > 0)]
            reusable = df[(df["is_reusable"] == 1) & (df["price"] > 0)]
            if disposable.empty and reusable.empty:
                st.info(t("no_prices_entered"))
            else:
                if not disposable.empty:
                    total_disp = disposable["price"].sum() * 20
                    st.metric(t("yearly_disposable_cost"), f"GH₵ {total_disp:.2f}")
                if not reusable.empty:
                    total_reuse = reusable["price"].sum()
                    st.metric(t("one_time_reusable_investment"), f"GH₵ {total_reuse:.2f}")
                    if not disposable.empty:
                        st.success(t("savings_message").format(savings=max(0, total_disp - total_reuse)))
    with tab4:
        st.subheader(t("shopping_list"))
        low_items = []
        if prods:
            for pt, info in prods.items():
                if info["count"] <= info["threshold"]:
                    low_items.append({t("product"): pt, t("current"): info["count"], t("needed"): info["threshold"] + 5 - info["count"], t("price"): info["price"]})
        if low_items:
            df_list = pd.DataFrame(low_items)
            st.dataframe(df_list, use_container_width=True)
            total_cost = sum([item[t("needed")] * item[t("price")] for item in low_items if item[t("price")] > 0])
            st.metric(t("estimated_restock_cost"), f"GH₵ {total_cost:.2f}")
            if st.button(t("share_whatsapp")):
                msg = t("shopping_list_msg") + "\n"
                for item in low_items:
                    msg += f"- {item[t('product')]}: " + t("need") + f" {item[t('needed')]} (" + t("current_stock") + f" {item[t('current')]})\n"
                encoded = urllib.parse.quote(msg)
                st.markdown(f"[{t('click_to_send_whatsapp')}](https://wa.me/?text={encoded})")
        else:
            st.success(t("all_well_stocked"))
    with tab5:
        st.subheader(t("reusable_care"))
        st.markdown(t("reusable_care_text"))

# ───────────────── OTHER HELPERS ─────────────────
def add_bbt(user_id, date, temp):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO bbt (user_id, date, temperature) VALUES (?,?,?)", (user_id, date, temp))
    conn.commit()
    conn.close()

def add_cervical_mucus(user_id, date, mucus_type):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO cervical_mucus (user_id, date, type) VALUES (?,?,?)", (user_id, date, mucus_type))
    conn.commit()
    conn.close()

def add_ovulation_test(user_id, date, result):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO ovulation_tests (user_id, date, result) VALUES (?,?,?)", (user_id, date, result))
    conn.commit()
    conn.close()

def add_water_intake(user_id, date, glasses):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO water_intake (user_id, date, glasses) VALUES (?,?,?)", (user_id, date, glasses))
    conn.commit()
    conn.close()

def get_water_intake(user_id, start_date, end_date):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT date, glasses FROM water_intake WHERE user_id=? AND date BETWEEN ? AND ? ORDER BY date", conn, params=[user_id, start_date, end_date])
    conn.close()
    return df

def add_exercise_log(user_id, date, minutes, ex_type):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO exercise_log (user_id, date, minutes, type) VALUES (?,?,?,?)", (user_id, date, minutes, ex_type))
    conn.commit()
    conn.close()

def add_sleep_quality(user_id, date, hours, quality):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO sleep_quality (user_id, date, hours, quality) VALUES (?,?,?,?)", (user_id, date, hours, quality))
    conn.commit()
    conn.close()

def get_sleep_quality(user_id, limit=30):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT date, hours, quality FROM sleep_quality WHERE user_id=? ORDER BY date DESC LIMIT ?", conn, params=[user_id, limit])
    conn.close()
    return df

def get_ovulation_tests(user_id, limit=10):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT date, result FROM ovulation_tests WHERE user_id=? ORDER BY date DESC LIMIT ?", conn, params=[user_id, limit])
    conn.close()
    return df

def add_product_usage(user_id, period_start_date, usage_dict):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    for prod, qty in usage_dict.items():
        if qty > 0:
            c.execute("INSERT INTO product_usage (user_id, period_start_date, product_type, quantity_used) VALUES (?,?,?,?)",
                      (user_id, period_start_date, prod, qty))
    conn.commit()
    conn.close()

def record_period_usage(user_id, period_start_date):
    conn = sqlite3.connect(DB)
    products = pd.read_sql_query("SELECT product_type FROM product_inventory WHERE user_id=?", conn, params=[user_id])["product_type"].tolist()
    conn.close()
    if not products:
        return
    st.subheader(t("how_many_products_used").format(date=period_start_date))
    usage = {}
    cols = st.columns(3)
    for i, pt in enumerate(products):
        with cols[i % 3]:
            usage[pt] = st.number_input(f"{pt.capitalize()}", 0, 200, 0, key=f"usage_{pt}_{period_start_date}")
    if st.button(t("save_usage")):
        add_product_usage(user_id, period_start_date, usage)
        st.success(t("usage_saved"))
        st.rerun()

def add_partner_note(user_id, note):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO partner_notes (user_id, note, created_at) VALUES (?,?,?)", (user_id, note, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_partner_notes(user_id):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT note, created_at FROM partner_notes WHERE user_id=? ORDER BY created_at DESC", conn, params=[user_id])
    conn.close()
    return df

# ───────────────── NOTIFICATION AND SOUND ─────────────────
def get_unread_count(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM private_messages WHERE to_user = ? AND read = 0", (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def mark_all_read(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE private_messages SET read = 1 WHERE to_user = ? AND read = 0", (user_id,))
    conn.commit()
    conn.close()

def delete_message(message_id, user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT from_user, read FROM private_messages WHERE id = ?", (message_id,))
    row = c.fetchone()
    if row and row[0] == user_id and row[1] == 0:
        c.execute("DELETE FROM private_messages WHERE id = ?", (message_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

# ───────────────── AI CHAT ─────────────────
ABBREV_MAP = {"u":"you","r":"are","ur":"your","pls":"please","plz":"please","thx":"thanks"}
def expand_abbreviations(text):
    words = text.split()
    return " ".join([ABBREV_MAP.get(w, w) for w in words])

_INTENTS = None
_VECTORIZER = None
_MATRIX = None

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def load_and_fit():
    global _INTENTS, _VECTORIZER, _MATRIX
    if _INTENTS is not None:
        return
    try:
        with open("final_qa_dataset.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        _INTENTS = []
        return
    except json.JSONDecodeError:
        _INTENTS = []
        return
    if not isinstance(data, list):
        _INTENTS = []
        return
    valid = [item for item in data if "question" in item and "answer" in item]
    _INTENTS = valid
    if not _INTENTS:
        return
    questions = [clean_text(item["question"]) for item in _INTENTS]
    _VECTORIZER = TfidfVectorizer(stop_words='english')
    _MATRIX = _VECTORIZER.fit_transform(questions)

def log_chat(user_id, user_msg, ai_resp, flagged=False):
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO chat_logs (user_id, timestamp, user_message, ai_response, flagged) VALUES (?,?,?,?,?)",
                  (user_id, datetime.now().isoformat(), user_msg, ai_resp, 1 if flagged else 0))
        conn.commit()
        conn.close()
    except Exception:
        pass

def get_careth_response(user_message, user_id=None):
    msg = user_message.lower().strip()
    flagged = False
    if user_id is not None:
        p = predict(user_id)
        cd = cd_(p)
        cycle_len = p["avg_cl"] if p["avg_cl"] else int(get_user_setting(user_id, "cycle_len", "28"))
        period_dur = p["pd"] if p["pd"] else int(get_user_setting(user_id, "period_dur", "5"))
        last_period = p["last"].strftime("%d %B %Y") if p["last"] else t("not_logged_yet")
        next_period = p["next"].strftime("%d %B %Y") if p["next"] else t("unknown_log_more")
        if "my next period" in msg or "when is my next period" in msg or "next period date" in msg:
            if p["next"]:
                return t("ai_next_period").format(date=next_period), False
            else:
                return t("ai_need_more_periods"), False
        if "what day of my cycle" in msg or "cycle day" in msg or "what day am i on" in msg:
            if cd is not None:
                return t("ai_current_day").format(day=cd, length=cycle_len), False
            else:
                return t("ai_log_period_first"), False
        if "how long is my cycle" in msg or "my cycle length" in msg or "average cycle" in msg:
            return t("ai_avg_cycle").format(length=cycle_len), False
        if "last period" in msg or "when was my last period" in msg:
            return t("ai_last_period").format(date=last_period), False
        if "am i ovulating" in msg or "ovulation today" in msg or "fertile today" in msg:
            if p["ov"]:
                today = date.today()
                if today == p["ov"]:
                    return t("ai_ovulation_today"), False
                elif today > p["ov"]:
                    return t("ai_ovulation_past").format(date=p['ov'].strftime('%d %B %Y')), False
                else:
                    days_to_ov = (p["ov"] - today).days
                    return t("ai_ovulation_future").format(days=days_to_ov, date=p['ov'].strftime('%d %B %Y')), False
            else:
                return t("ai_need_more_cycles"), False
        if "when will i ovulate" in msg or "ovulation date" in msg:
            if p["ov"]:
                return t("ai_ovulation_date").format(date=p['ov'].strftime('%d %B %Y')), False
            else:
                return t("ai_log_periods_for_ovulation"), False
        if "how long does my period last" in msg or "my period duration" in msg:
            return t("ai_period_duration").format(days=period_dur), False
        if "irregular cycle" in msg or "why is my cycle irregular" in msg:
            var = p["variability"]
            if var > 7:
                return t("ai_irregular_high").format(var=var), False
            elif var > 0:
                return t("ai_irregular_normal").format(var=var), False
            else:
                return t("ai_not_enough_cycles"), False
        if "how many periods have i logged" in msg or "periods logged" in msg:
            count = p["cycle_count"]
            return t("ai_periods_logged").format(count=count), False

    name_match = re.search(r"(?:my name is|i'm|call me)\s+([A-Za-zÀ-ÿ]{2,})", msg, re.IGNORECASE)
    if name_match:
        name = name_match.group(1).capitalize()
        greetings = [
            f"{t('ai_greeting_name1')} {name}! {t('ai_greeting_name2')}",
            f"{t('ai_greeting_name3')} {name}! {t('ai_greeting_name4')}",
            f"{t('ai_greeting_name5')} {name}! {t('ai_greeting_name6')}",
            f"{t('ai_greeting_name7')} {name}! {t('ai_greeting_name8')}",
            f"{t('ai_greeting_name9')} {name}! {t('ai_greeting_name10')}"
        ]
        return random.choice(greetings), False

    msg = msg.replace("menstruation", "period")
    msg = msg.replace("menstrual", "period")
    
    how_are_you = ["how are you", "how are u", "how r u"]
    for h in how_are_you:
        if h in msg:
            return random.choice([t("ai_how_are_you1"), t("ai_how_are_you2"), t("ai_how_are_you3")]), False
    
    if "who are you" in msg or "who r u" in msg:
        return random.choice([t("ai_who_are_you1"), t("ai_who_are_you2"), t("ai_who_are_you3")]), False
    
    if "what is your name" in msg or "what's your name" in msg:
        return random.choice([t("ai_what_is_name1"), t("ai_what_is_name2"), t("ai_what_is_name3")]), False
    
    if "what can you do" in msg or "how can you help" in msg:
        return random.choice([t("ai_what_can_do1"), t("ai_what_can_do2"), t("ai_what_can_do3")]), False
    
    if msg in ["hello", "hi", "hey"] or msg.startswith("hello ") or msg.startswith("hi "):
        return random.choice([t("ai_hello1"), t("ai_hello2"), t("ai_hello3")]), False
    
    if "good morning" in msg:
        return t("ai_good_morning"), False
    if "good afternoon" in msg:
        return t("ai_good_afternoon"), False
    if "good evening" in msg:
        return t("ai_good_evening"), False
    
    if "thank" in msg or "thanks" in msg:
        return random.choice([t("ai_thanks1"), t("ai_thanks2"), t("ai_thanks3")]), False
    
    if "bye" in msg or "goodbye" in msg or "see you" in msg:
        return random.choice([t("ai_bye1"), t("ai_bye2"), t("ai_bye3")]), False
    
    load_and_fit()
    if not _INTENTS:
        return t("ai_no_intents"), True
    msg = expand_abbreviations(user_message)
    msg = msg.replace("menstruation", "period").replace("menstrual", "period")
    msg_clean = clean_text(msg)
    if not msg_clean:
        return t("ai_ask_question"), True
    user_vec = _VECTORIZER.transform([msg_clean])
    similarities = cosine_similarity(user_vec, _MATRIX).flatten()
    best_idx = np.argmax(similarities)
    best_score = similarities[best_idx]
    if best_score < 0.2:
        return t("ai_low_similarity"), True
    return _INTENTS[best_idx].get("answer", t("ai_fallback")), False

def sidebar_chat(user_id):
    st.sidebar.markdown("---")
    st.sidebar.markdown("<h4 style='color:#F0E6EF;'>💬 " + t("chat_title") + "</h4>", unsafe_allow_html=True)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for msg in st.session_state.chat_history[-6:]:
        avatar = "🌸" if msg["role"] == "assistant" else "👤"
        with st.sidebar.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])
    user_input = st.sidebar.chat_input(t("chat_input_placeholder"), key="chat_input_field")
    if user_input:
        response, flagged = get_careth_response(user_input, user_id)
        log_chat(user_id, user_input, response, flagged)
        st.session_state.chat_history.append({"role":"user","content":user_input})
        st.session_state.chat_history.append({"role":"assistant","content":response})
        st.rerun()
    if st.session_state.get("show_welcome_popup", False):
        if not st.session_state.get("welcome_added", False):
            user_name = st.session_state.get("user", "dear")
            welcome_msg = t("welcome_back").format(name=user_name)
            st.session_state.chat_history.append({"role":"assistant","content":welcome_msg})
            st.session_state.welcome_added = True
        st.markdown("""
        <script>
        setTimeout(function() {
            let input = document.querySelector('input[aria-label="Ask me anything about your cycle..."]');
            if (input) {
                input.focus();
                input.classList.add('focus-chat-input');
            }
        }, 200);
        </script>
        """, unsafe_allow_html=True)
        st.session_state.show_welcome_popup = False
        st.rerun()

def main_chat_area(user_id):
    set_video_background()
    st.markdown("### " + t("chat_title_main"))
    if "main_chat_history" not in st.session_state:
        st.session_state.main_chat_history = []
    for msg in st.session_state.main_chat_history:
        avatar = "🌸" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])
    user_input = st.chat_input(t("chat_input_placeholder_main"))
    if user_input:
        response, flagged = get_careth_response(user_input, user_id)
        log_chat(user_id, user_input, response, flagged)
        st.session_state.main_chat_history.append({"role":"user","content":user_input})
        st.session_state.main_chat_history.append({"role":"assistant","content":response})
        st.rerun()

# ───────────────── LOGIN / REGISTER ─────────────────
def login_screen():
    set_page_background("default.png")
    st.markdown(f"<h1>{t('login_title')}</h1>", unsafe_allow_html=True)
    name = st.text_input(t("name"))
    pw = st.text_input(t("password"), type="password")
    if st.button(t("login")):
        user_id, username, country, is_admin, last_change, profile_pic = login_user(name, pw)
        if user_id:
            st.session_state.user_id = user_id
            st.session_state.user = username
            st.session_state.user_country = country
            st.session_state.is_admin = is_admin
            st.session_state.last_username_change = last_change
            st.session_state.profile_pic = profile_pic or ""
            online_mode = get_user_setting(user_id, "online_mode", "True")
            st.session_state.online_mode = online_mode.lower() == "true"
            cycles = load_cycles(user_id)
            if cycles.empty:
                st.session_state.new_user = True
                st.session_state.step = "online_choice"
            else:
                st.session_state.new_user = False
                st.session_state.step = "main"
            st.rerun()
        else:
            st.error(t("invalid_credentials"))
    if st.button(t("register")):
        st.session_state.show_register = True
        st.rerun()

def register_screen():
    set_page_background("default.png")
    st.markdown(f"<h1>{t('register_title')}</h1>", unsafe_allow_html=True)
    name = st.text_input(t("name"))
    pw = st.text_input(t("password"), type="password")
    pw2 = st.text_input(t("confirm_password"), type="password")
    email = st.text_input(t("email"))
    country = st.selectbox(t("country_select"), ["GH (Ghana)", "NG (Nigeria)", "KE (Kenya)", "ZA (South Africa)", t("other")], index=0)
    country_code = country.split()[0] if "(" in country else "GH"
    if st.button(t("register")):
        if pw != pw2:
            st.error(t("passwords_do_not_match"))
        else:
            result = register_user(name, pw, email, country_code)
            if result is True:
                st.success(t("account_created"))
                st.session_state.show_register = False
                st.rerun()
            else:
                st.error(result)
    if st.button(t("back_to_login")):
        st.session_state.show_register = False
        st.rerun()

def online_choice_screen():
    set_page_background("default.png")
    st.markdown(f"<h1>{t('online_choice_title')}</h1>", unsafe_allow_html=True)
    st.markdown(t('online_choice_prompt'))
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t('go_online'), use_container_width=True):
            st.session_state.online_mode = True
            set_user_setting(st.session_state.user_id, "online_mode", "True")
            st.session_state.step = "setup_wizard"
            st.rerun()
    with col2:
        if st.button(t('stay_offline'), use_container_width=True):
            st.session_state.online_mode = False
            set_user_setting(st.session_state.user_id, "online_mode", "False")
            st.session_state.step = "setup_wizard"
            st.rerun()
    st.stop()

def setup_wizard(user_id):
    set_page_background("onboarding.png")
    st.title(t("setup_title"))
    st.markdown(t("setup_prompt"))
    with st.form("setup_form"):
        cycle_len = st.number_input(t("cycle_length_label"), min_value=20, max_value=45, value=28, help=t("cycle_length_help"))
        period_dur = st.number_input(t("period_duration_label"), min_value=2, max_value=10, value=5)
        if st.form_submit_button(t("start_tracking")):
            set_user_setting(user_id, "cycle_len", str(cycle_len))
            set_user_setting(user_id, "period_dur", str(period_dur))
            st.session_state.step = "main"
            st.success(t("all_set"))
            st.balloons()
            time.sleep(0.5)
            st.rerun()

def interactive_onboarding():
    if not st.session_state.get("show_onboarding", False):
        return
    with st.sidebar:
        st.markdown("## " + t("quick_tour"))
        step = st.session_state.get("onboarding_step", 0)
        steps = [
            (t("dashboard_onb"), t("dashboard_desc")),
            (t("log_period_onb"), t("log_period_desc")),
            (t("symptom_onb"), t("symptom_desc")),
            (t("pregnancy_onb"), t("pregnancy_desc")),
            (t("calendar_onb"), t("calendar_desc")),
            (t("wellness_onb"), t("wellness_desc")),
            (t("learn_onb"), t("learn_desc")),
            (t("community_onb"), t("community_desc")),
            (t("online_hub_onb"), t("online_hub_desc")),
            (t("settings_onb"), t("settings_desc"))
        ]
        if step < len(steps):
            title, desc = steps[step]
            st.markdown(f'<div class="onboarding-highlight">✨ <strong>{title}</strong><br>{desc}</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            if col1.button(t("next"), key="onb_next"):
                st.session_state.onboarding_step = step + 1
                if step + 1 == len(steps):
                    st.session_state.show_onboarding = False
                st.rerun()
            if col2.button(t("skip"), key="onb_skip"):
                st.session_state.show_onboarding = False
                st.rerun()
        else:
            st.session_state.show_onboarding = False
            st.rerun()

def safe_format_date(date_obj):
    try:
        return date_obj.strftime(t("date_format"))
    except UnicodeEncodeError:
        return date_obj.strftime("%Y-%m-%d")

def dashboard(user_id):
    set_page_background("dashboard.png")
    st.title("🌸 Essence Flow")
    st.caption(safe_format_date(date.today()))
    
    late_date = get_late_period_reminder(user_id)
    if late_date:
        st.warning(t("late_period_warning").format(date=late_date.strftime('%d %b %Y')))
        col1, col2 = st.columns(2)
        with col1:
            if st.button(t("log_period_now")):
                st.session_state.menu = "log_period"
                st.rerun()
        with col2:
            if st.button(t("skip_this_period")):
                skip_period(user_id, late_date.isoformat(), t("late_period_reason"))
                st.success(t("skipped_success"))
                st.rerun()
    
    with st.expander(t("when_to_see_doctor"), expanded=False):
        st.markdown(t("doctor_signs"))
        user_flags = check_red_flags(user_id)
        if user_flags:
            st.warning(t("based_on_data"))
            for f in user_flags:
                st.error(f)
        country_code = st.session_state.get("user_country", "GH")
        em = get_country_emergency_numbers(country_code)
        st.info(t("emergency_numbers_info").format(amb=em['ambulance'], ment=em['mental'], repr=em['reproductive']))
    
    emergency_name = get_user_setting(user_id, "emergency_name", "")
    emergency_phone = get_user_setting(user_id, "emergency_phone", "")
    if emergency_name and emergency_phone:
        st.info(t("your_emergency_contact").format(name=emergency_name, phone=emergency_phone))
        st.markdown(f'<a href="tel:{emergency_phone}" target="_blank"><button style="background:#C28585; color:white; border:none; border-radius:20px; padding:0.5rem 1rem;">📱 {t("call_button")} {emergency_name}</button></a>', unsafe_allow_html=True)
    
    p = predict(user_id)
    cd = cd_(p)
    ph = phase(cd, p)
    prog = min(int((cd/p["avg_cl"])*100),100) if cd and p["avg_cl"] else 0
    st.markdown(f"""
    <div class="circular-progress" style="--p:{prog};">
        <div class="circular-inner">{cd if cd else '?'}</div>
    </div>
    <p style="text-align:center;"><span class="phase-badge">{ph}</span></p>
    """, unsafe_allow_html=True)
    
    if p["next"]:
        variance = int((p['prediction_range'][1] - p['prediction_range'][0]) / 2)
        st.info(f"📅 Your next period is predicted around {p['next'].strftime('%d %b %Y')} (± {variance} days).")
    
    cols = st.columns(4)
    actions = [
        (t("log_period_button"), "log_period"),
        (t("log_symptoms_button"), "symptom_tracker"),
        (t("calendar_button"), "calendar_planner"),
        (t("planner_button"), "calendar_planner")
    ]
    for i, (label, key) in enumerate(actions):
        if cols[i].button(label):
            st.session_state.menu = key
            st.rerun()
    
    prods = get_products(user_id)
    if not prods.empty:
        low_stock = [row["product_type"] for _, row in prods[prods["count"] <= prods["threshold"]].iterrows()]
        if low_stock:
            st.warning(t("low_stock_warning_short").format(products=', '.join(low_stock)))
    
    affs = [t("affirmation1"), t("affirmation2"), t("affirmation3")]
    st.markdown(f'<div class="card">✨ {random.choice(affs)}</div>', unsafe_allow_html=True)

def log_period(user_id):
    set_page_background("log_period.png")
    st.title(t("log"))
    d = st.date_input(t("period_start_date"), max_value=date.today())
    dur = st.number_input(t("duration_days"), 1, 10, int(get_user_setting(user_id, "period_dur", "5")))
    flow = st.selectbox(t("flow_quality"), [t("light"), t("medium"), t("heavy")])
    pain = st.slider(t("pain_level"), 1, 10, 1)
    med = st.text_input(t("medication_taken"))
    
    col1, col2 = st.columns(2)
    if col1.button(t("save_period")):
        add_period(user_id, d.isoformat(), dur, flow, pain, med)
        st.success(t("period_saved"))
        record_period_usage(user_id, d.isoformat())
        st.rerun()
    
    if col2.button(t("skip_period_button")):
        if d > date.today():
            st.error(t("cannot_skip_future"))
        else:
            skip_period(user_id, d.isoformat(), t("user_skipped"))
            st.success(t("skipped_success_msg").format(date=d))
            st.rerun()
    
    st.subheader(t("last_periods"))
    cycles_df = load_cycles(user_id)
    if not cycles_df.empty:
        display_df = cycles_df.tail(5).copy()
        st.dataframe(
            display_df[["start_date", "period_duration", "flow_quality", "pain_level"]].rename(
                columns={
                    "start_date": "Start Date",
                    "period_duration": "Duration (days)",
                    "flow_quality": "Flow",
                    "pain_level": "Pain (1-10)"
                }
            ),
            use_container_width=True
        )
        st.write("**Delete a period:**")
        for idx, row in cycles_df.tail(5).iterrows():
            col_a, col_b, col_c = st.columns([3, 1, 1])
            col_a.write(f"{row['start_date']} – {row['period_duration']} days, {row['flow_quality']}, pain {row['pain_level']}/10")
            confirm = col_b.checkbox("Confirm", key=f"confirm_{row['id']}")
            if col_c.button("🗑️", key=f"del_{row['id']}"):
                if confirm:
                    delete_cycle(user_id, row['id'])
                    st.rerun()
                else:
                    st.warning("Please confirm deletion first.")
    else:
        st.info("No periods logged yet.")

def symptom_tracker(user_id):
    set_page_background("symptoms.png")
    st.title(t("sym"))
    sel = st.date_input(t("date"), value=date.today())
    with st.form("sym_form"):
        cramps = st.selectbox(t("cramps"), [t("none"), t("mild"), t("medium"), t("severe")])
        mood = st.selectbox(t("mood"), [t("neutral"), t("happy"), t("sad"), t("irritable")])
        flow = st.selectbox(t("flow"), [t("none_flow"), t("light"), t("normal"), t("heavy")])
        bleeding_intensity = st.selectbox(t("bleeding_intensity"), [t("light"), t("normal"), t("heavy"), t("flooding")])
        pain = st.slider(t("pain"), 1,10,1)
        energy = st.slider(t("energy"), 1,5,3)
        bloating = st.selectbox(t("bloating"), [t("no"), t("mild"), t("moderate"), t("severe")])
        appetite = st.selectbox(t("appetite"), [t("low"), t("normal"), t("high")])
        headache = st.selectbox(t("headache"), [t("no"), t("mild"), t("moderate"), t("severe")])
        lower_back_pain = st.selectbox(t("lower_back_pain"), [t("no"), t("mild"), t("moderate"), t("severe")])
        breast_tenderness = st.selectbox(t("breast_tenderness"), [t("no"), t("mild"), t("moderate"), t("severe")])
        anemia_symptoms = st.text_area(t("anemia_symptoms"))
        skin = st.text_input(t("skin_condition"))
        notes = st.text_area(t("notes"))
        if st.form_submit_button(t("save_sym")):
            save_sym(user_id, sel.isoformat(), cramps, mood, flow, pain, energy, bloating, appetite, notes, headache, skin, bleeding_intensity, anemia_symptoms, lower_back_pain, breast_tenderness)
            st.success(t("saved"))
            if pain >= 8:
                st.info(t("high_pain_advice"))
            if bleeding_intensity == "Flooding":
                st.info(t("flooding_advice"))
            st.rerun()
    st.subheader(t("sym_hist_title"))
    df = recent_sym(user_id, 10)
    if not df.empty:
        st.dataframe(df, use_container_width=True)

def view_history(user_id):
    set_page_background("history.png")
    st.title(t("hist"))
    cycles = load_cycles(user_id)
    if cycles.empty:
        st.info(t("no_cycles_logged"))
        return
    cycles["start_date"] = pd.to_datetime(cycles["start_date"])
    cycles = cycles.sort_values("start_date")
    cycles["cycle_number"] = range(1, len(cycles) + 1)
    st.subheader(t("cycle_length_chart"))
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(cycles["cycle_number"], cycles["cycle_length"], 'o-', color='#C28585', linewidth=2, markersize=8)
    avg_line = cycles["cycle_length"].mean()
    ax.axhline(y=avg_line, color='gray', linestyle='--', label=t("average_label").format(avg=avg_line))
    ax.set_xlabel(t("period_number"))
    ax.set_ylabel(t("cycle_length_days"))
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3)
    st.pyplot(fig)
    if len(cycles) >= 2:
        longest = cycles["cycle_length"].max()
        shortest = cycles["cycle_length"].min()
        st.info(t("cycle_range_info").format(short=shortest, long=longest))
        if longest - shortest > 10:
            st.warning(t("high_variability_warning"))
        else:
            st.success(t("regular_cycle_good"))
    st.subheader(t("detailed_cycle_list"))
    st.dataframe(cycles[["start_date", "cycle_length", "period_duration", "flow_quality", "pain_level"]].rename(
        columns={"start_date": t("start_date"), "cycle_length": t("cycle_length"), "period_duration": t("period_duration"),
                 "flow_quality": t("flow"), "pain_level": t("pain")}), use_container_width=True)
    csv = cycles.to_csv(index=False)
    st.download_button(t("download_csv"), csv, "cycle_history.csv", "text/csv")

def pregnancy_info(user_id):
    set_page_background("pregnancy.png")
    st.title(t("preg"))
    st.markdown(t("educational_only"))
    p = predict(user_id)
    if not p["last"]:
        st.warning(t("log_period_first"))
        return
    today = date.today()
    days_since = (today - p["last"]).days
    weeks = days_since // 7
    st.metric(t("days_since_last_period"), days_since)
    sex = st.radio(t("unprotected_sex_question"), (t("no"), t("unsure"), t("yes")), index=0, key="preg_sex")
    likelihood = t("low")
    if p["next"]:
        late = days_since - p["avg_cl"]
        if p["ov"] and p["ov"] <= today and sex in [t("yes"), t("unsure")]:
            likelihood = t("medium")
        if late > 7 and sex == t("yes"):
            likelihood = t("high")
        if late > 14 and sex == t("yes"):
            likelihood = t("very_high")
    if p["next"]:
        late_days = max(0, days_since - p["avg_cl"])
        if late_days > 0:
            st.warning(t("period_late_warning").format(days=late_days))
            if likelihood == t("high"):
                st.error(t("high_likelihood_pregnancy"))
            elif likelihood == t("medium"):
                st.warning(t("medium_likelihood_pregnancy"))
            else:
                st.info(t("low_likelihood_pregnancy"))
    if days_since > 28 and late_days > 7 and sex == t("yes"):
        due_date = p["last"] + timedelta(days=280)
        st.success(t("due_date_estimate").format(date=due_date.strftime('%d %B %Y')))
        if weeks <= 13:
            st.info(t("first_trimester_info"))
        elif weeks <= 27:
            st.info(t("second_trimester_info"))
        else:
            st.info(t("third_trimester_info"))
        with st.expander(t("nutrition_warning")):
            st.markdown(t("nutrition_text"))
    else:
        st.info(t("not_late_concern"))
    with st.expander(t("common_questions")):
        q = st.selectbox(t("select_question"), [t("early_signs_q"), t("when_to_test_q"), t("pregnancy_on_period_q"), t("implantation_bleeding_q")])
        answers = {
            t("early_signs_q"): t("early_signs_a"),
            t("when_to_test_q"): t("when_to_test_a"),
            t("pregnancy_on_period_q"): t("pregnancy_on_period_a"),
            t("implantation_bleeding_q"): t("implantation_bleeding_a")
        }
        st.info(answers.get(q, t("consult_doctor")))
    st.caption(t("always_consult_doctor"))

# ───────────────── LEARN & BOOKS ─────────────────
LEARN_CONTENT = {
    "What is Menstruation?": "Menstruation is the monthly shedding of the uterine lining. It's a sign of a healthy reproductive system. The average cycle is 28 days, but 21-35 days is normal. Bleeding usually lasts 3-7 days.",
    "Cycle Phases Explained": "Your cycle has four phases: Menstrual (bleeding), Follicular (egg maturing, energy rising), Ovulation (egg release, peak fertility), Luteal (post-ovulation, possible PMS). Each phase affects your energy, mood, and body.",
    "How to Manage Cramps": "Use a heating pad or hot water bottle on your lower belly. Drink ginger or chamomile tea. Take ibuprofen if needed. Gentle exercise like walking or yoga can also help. Avoid caffeine and salty foods.",
    "Common Myths Busted": "Myth: You can't get pregnant on your period. Fact: It's unlikely but possible if you have a short cycle. Myth: Period blood is dirty. Fact: It's just blood and tissue. Myth: You shouldn't bathe. Fact: Bathing is safe and helps cramps.",
    "When to See a Doctor": "See a doctor if you: soak a pad/tampon every hour for several hours, have severe pain that stops daily activities, bleed for more than 7 days, have cycles shorter than 21 days or longer than 35 days, or miss 3+ periods (not pregnant).",
    "Nutrition for Your Cycle": "During your period: eat iron-rich foods (moringa, beans, spinach, liver). During follicular phase: fresh fruits and lean protein. During ovulation: light meals and antioxidants. During luteal phase: complex carbs like yam, oats, and dark chocolate to stabilise mood.",
    "Menstrual Product Guide": "Pads: worn outside, good for beginners. Tampons: inserted, good for swimming. Menstrual cups: reusable, eco-friendly, last 12 hours. Period underwear: comfortable, can be worn alone or as backup. Choose what works for you.",
    "Exercise During Your Period": "Light exercise like walking, stretching, and walking can reduce cramps and boost mood. Listen to your body – rest if you are tired. High-intensity workouts may be better in the follicular and ovulation phases.",
    "Mental Health & PMS": "Hormonal changes can cause mood swings, irritability, and sadness. Practice self-care: journaling, talking to a friend, getting enough sleep. If severe, see a doctor – you may have PMDD which is treatable.",
    "Fertility Awareness": "Track your cycle to know when you ovulate. The fertile window is 5 days before ovulation and the day of ovulation. Use apps, BBT, or cervical mucus to identify it. Helpful for conception or natural family planning.",
    "PCOS (Polycystic Ovary Syndrome)": "PCOS affects 1 in 10 women. Symptoms: irregular periods, acne, weight gain, excess hair. Manage with diet, exercise, and sometimes medication. See a doctor for diagnosis and treatment.",
    "Endometriosis Basics": "Endometriosis causes severe period pain, heavy bleeding, and pain during sex. It can lead to infertility. See a gynaecologist if you suspect it. Treatments include pain relief, hormonal therapy, and surgery.",
    "Perimenopause Guide": "Perimenopause is the transition to menopause, usually in your 40s. Symptoms: irregular periods, hot flashes, night sweats, mood changes, vaginal dryness. Treatments are available – talk to your doctor.",
    "Menopause Overview": "Menopause is when periods stop for 12 consecutive months (average age 51). Symptoms include hot flashes, vaginal dryness, sleep problems. HRT and lifestyle changes can help. Discuss with a doctor.",
    "Period Poverty Solutions": "If you cannot afford pads or tampons, try reusable cloth pads or menstrual cups. Many NGOs provide free products. In Ghana, ask at your local CHPS compound. In Kenya, look for government distribution programs.",
    "How to Use a Menstrual Cup": "Fold the cup, insert it into the vagina, and rotate to open. It creates a seal. Empty every 12 hours, rinse with water, and reinsert. Sterilise by boiling between cycles. One cup lasts years.",
    "Tampon Safety": "Change tampons every 4-8 hours. Use the lowest absorbency needed for your flow. Never leave a tampon in for more than 8 hours to avoid Toxic Shock Syndrome (TSS). TSS is rare but serious.",
    "Reusable Cloth Pads": "You can make your own from old cotton cloth. Cut into an oval shape, layer absorbent towel in the middle, sew layers together. Attach buttons or snaps to secure around underwear. Wash in cold water, dry in sun.",
    "Periods & School/Work": "Keep an emergency kit in your bag: 2 pads, spare underwear, wet wipes, painkiller. Talk to a teacher or boss if you need to step out. By speaking up, you can help improve facilities for everyone.",
    "Sex & Your Period": "It is safe to have sex during your period. It may even relieve cramps (orgasms release endorphins). Use a condom to prevent STIs and pregnancy (yes, pregnancy is still possible!).",
    "Oral Contraceptives & Periods": "Birth control pills can regulate cycles, reduce cramps, and lighten flow. They may cause side effects like nausea or mood changes. Talk to a doctor to see if they are right for you.",
    "IUDs & Periods": "A hormonal IUD often makes periods lighter and less painful. A copper IUD may make periods heavier initially. Both are long-term contraception (3-10 years). See a doctor for insertion.",
    "Stress & Irregular Periods": "High stress can delay ovulation and cause late or missed periods. Relaxation techniques like deep breathing, exercise, and good sleep can help. If stress is chronic, consider talking to a counsellor.",
    "Travel & Your Cycle": "Time zone changes and stress of travel can affect your cycle. Pack extra supplies, use a cup (no need to change in airports), and stay hydrated. Your cycle usually returns to normal within a month.",
    "Lunar Cycle Connection": "Some women notice their period aligns with the moon (full moon or new moon). Track your cycle to see if you have a pattern. It's not scientifically proven, but it can be a fun observation.",
    "Iron Deficiency Anaemia": "Heavy periods can cause iron deficiency, leading to fatigue, pale skin, dizziness, and cold hands. Eat iron-rich foods (moringa, red meat, beans, dark greens). A doctor can test your iron levels.",
    "PMS vs PMDD": "PMS causes mild to moderate mood swings, bloating, and fatigue. PMDD (Premenstrual Dysphoric Disorder) is severe – extreme depression, anger, and hopelessness that disrupts daily life. PMDD can be treated – see a doctor.",
    "Vaginal Discharge Throughout Cycle": "Normal discharge changes: dry after period, sticky and white before ovulation, clear and stretchy (egg white) at ovulation, then thick and creamy before next period. Abnormal discharge: yellow, green, lumpy, or foul smell – see a doctor.",
    "How to Track Your Cycle with BBT": "Basal Body Temperature (BBT) is your lowest morning temperature. Take it every day before getting out of bed. After ovulation, it rises and stays high. This helps confirm ovulation and predict your next period.",
    "Cervical Mucus Method": "Cervical mucus changes during your cycle. After period: dry or sticky. Before ovulation: creamy. At ovulation: clear, stretchy like egg white – this is your fertile window. After ovulation: dry again. Track to know when you can conceive.",
    "Ovulation Test Kits": "Ovulation test strips detect the LH hormone surge that happens 24-36 hours before ovulation. They are very accurate and can help you time intercourse if trying to conceive.",
    "Pregnancy Testing: When and How": "Take a home pregnancy test after your period is late. Use first morning urine for best results. Follow the instructions exactly. If negative but period still late, test again in 3-5 days or see a doctor.",
    "Ectopic Pregnancy Symptoms": "Ectopic pregnancy occurs when the embryo implants outside the uterus (usually fallopian tube). Symptoms: sharp pelvic pain, light vaginal bleeding, shoulder pain, dizziness. This is a medical emergency – seek help immediately.",
    "Miscarriage Signs": "Signs of miscarriage include: vaginal bleeding (heavy or light), cramping or back pain, passing clots or tissue. If you are pregnant and have these symptoms, see a doctor or go to an emergency room.",
    "Postpartum Periods": "After giving birth, your first period may be heavier and more painful. It can return as early as 6 weeks (if not breastfeeding) or much later (if breastfeeding). Use pads (no tampons until your doctor says it's safe).",
    "Breastfeeding and Your Cycle": "Breastfeeding suppresses ovulation – many mothers do not get a period for months. However, you can still get pregnant (especially after 6 months). Use contraception if you do not want another pregnancy.",
    "Menstrual Migraines": "Some women get severe headaches before or during their period due to estrogen drop. Treatment: NSAIDs (ibuprofen), triptans (prescription), or continuous birth control to skip periods. Track your headaches to identify triggers.",
    "PCOS Diet Tips": "If you have PCOS, focus on low-glycemic foods (whole grains, beans, vegetables), healthy fats (avocado, nuts), and lean protein. Reduce sugar and processed foods. Losing even 5% of body weight can improve symptoms.",
    "Endometriosis Pain Relief": "In addition to medication, try heat packs, pelvic floor physiotherapy, and anti-inflammatory foods (leafy greens, fatty fish, turmeric). Some women find relief with acupuncture or TENS machines. Find what works for you.",
    "When to Start Birth Control Pills": "You can start the pill at any time. If you start within 5 days of your period, you are protected immediately. Otherwise, use condoms for 7 days. Talk to a doctor to get a prescription.",
    "Natural Family Planning Methods": "Combine BBT tracking, cervical mucus monitoring, and cycle length calculation. With perfect use, it can be up to 99% effective. It requires daily commitment and works best for regular cycles."
}

def learn_and_books(user_id):
    set_page_background("learn.png")
    st.title(t("learn_books"))
    tab1, tab2 = st.tabs([t("learn_title"), t("books")])
    with tab1:
        search = st.text_input(t("search_guides"), key="learn_search")
        filtered_content = {k:v for k,v in LEARN_CONTENT.items() if search.lower() in k.lower() or search.lower() in v.lower()}
        topics = list(filtered_content.keys()) if search else list(LEARN_CONTENT.keys())
        st.markdown("### " + t("select_topic"))
        topic = st.selectbox("", topics, key="learn_topic")
        st.info(LEARN_CONTENT[topic])
        st.markdown("---")
        st.subheader(t("you_might_also_like"))
        other_topics = [t for t in topics if t != topic]
        random.shuffle(other_topics)
        for ot in other_topics[:3]:
            st.markdown(f"- {ot}")
    with tab2:
        books_library(user_id)

def books_library(user_id):
    books_dir = os.path.join(os.getcwd(), "books")
    if not os.path.exists(books_dir):
        st.info(t("create_books_folder"))
        return
    files = [f for f in os.listdir(books_dir) if f.endswith(('.txt','.md'))]
    if not files:
        st.warning(t("no_books_found"))
        return
    search = st.text_input(t("search_books"), key="book_search")
    filtered = [f for f in files if search.lower() in f.lower()] if search else files
    if not st.session_state.get("book_opened"):
        cols = st.columns(3)
        for idx, f in enumerate(filtered):
            with cols[idx % 3]:
                if st.button(f"📖 {f}", key=f"book_{f}"):
                    st.session_state.selected_book = f
                    st.session_state.book_opened = True
                    st.rerun()
    else:
        with open(os.path.join(books_dir, st.session_state.selected_book), "r", encoding="utf-8") as f:
            content = f.read()
        st.markdown(f"<div class='book-reader'>{content}</div>", unsafe_allow_html=True)
        if st.button(t("close_book")):
            st.session_state.book_opened = False
            st.session_state.selected_book = None
            st.rerun()

# ───────────────── WELLNESS INSIGHTS ─────────────────
def wellness_insights(user_id):
    set_page_background("wellness.png")
    st.title(t("wellness"))
    tabs = st.tabs([t("daily_wellness"), t("health_tips"), t("self_care"), t("local_wisdom"), t("anemia_check"), t("exercise_guides")])
    with tabs[0]:
        today_str = str(date.today())
        existing = load_wellness(user_id)
        cur = existing[existing["date"]==today_str] if not existing.empty else pd.DataFrame()
        with st.form("wellness_form"):
            mood = st.selectbox(t("mood"), [t("happy_emoji"), t("neutral_emoji"), t("sad_emoji"), t("angry_emoji"), t("tired_emoji")])
            water = st.number_input(t("water_intake_label"), 0, 20, value=int(cur["water_glasses"].iloc[0]) if not cur.empty else 0)
            water_goal = 8
            st.progress(min(water/water_goal, 1.0))
            st.caption(t("water_goal").format(goal=water_goal))
            sleep = st.number_input(t("sleep_hours"), 0.0, 24.0, value=float(cur["sleep_hours"].iloc[0]) if not cur.empty else 7.0, step=0.5)
            exercise = st.number_input(t("exercise_minutes"), 0, 300, value=int(cur["exercise_minutes"].iloc[0]) if not cur.empty else 0)
            self_care = st.text_area(t("self_care_activity"), placeholder="e.g., meditation, reading, bath, journaling")
            if st.form_submit_button(t("save")):
                save_wellness(user_id, today_str, mood.split(" ")[0], water, sleep, exercise, self_care)
                st.success(t("saved"))
        week_ago = date.today() - timedelta(days=7)
        wellness_data = load_wellness(user_id)
        week_data = wellness_data[wellness_data["date"] >= week_ago.isoformat()]
        if not week_data.empty:
            avg_water = week_data["water_glasses"].mean()
            avg_sleep = week_data["sleep_hours"].mean()
            score = (avg_water/8)*0.5 + (avg_sleep/8)*0.5
            score = min(1, max(0, score))
            if score >= 0.8:
                st.success(t("weekly_score_great").format(score=int(score*100)))
            elif score >= 0.5:
                st.info(t("weekly_score_good").format(score=int(score*100)))
            else:
                st.warning(t("weekly_score_needs_improvement").format(score=int(score*100)))
    with tabs[1]:
        sym_df = recent_sym(user_id, 90)
        if sym_df.empty:
            st.info(t("log_more_symptoms"))
        else:
            sym_df["date"] = pd.to_datetime(sym_df["date"])
            sym_df = sym_df.sort_values("date")
            st.subheader(t("pain_energy_chart"))
            last30 = sym_df.tail(30)
            if len(last30) > 0:
                fig, ax = plt.subplots(figsize=(10,4))
                x = range(len(last30))
                ax.bar([i-0.2 for i in x], last30["pain"], width=0.4, label=t("pain_label"), color="#C28585")
                ax.bar([i+0.2 for i in x], last30["energy"], width=0.4, label=t("energy_label"), color="#90EE90")
                ax.set_xticks(x)
                ax.set_xticklabels(last30["date"].dt.strftime("%d/%m"), rotation=45, ha="right")
                ax.legend()
                st.pyplot(fig)
                avg_pain = last30["pain"].mean()
                avg_energy = last30["energy"].mean()
                st.info(t("avg_pain_energy").format(pain=avg_pain, energy=avg_energy))
                if avg_pain > 5:
                    st.warning(t("pain_high_advice"))
                else:
                    st.success(t("pain_low_good"))
            st.subheader(t("mood_distribution"))
            mood_counts = sym_df["mood"].value_counts()
            if not mood_counts.empty:
                fig2, ax2 = plt.subplots(figsize=(6,6))
                colors = {"Neutral":"gray","Happy":"gold","Sad":"lightblue","Irritable":"orange"}
                pie_colors = [colors.get(m, "gray") for m in mood_counts.index]
                ax2.pie(mood_counts.values, labels=mood_counts.index, autopct='%1.0f%%', colors=pie_colors, startangle=90)
                ax2.set_title(t("how_you_felt"))
                st.pyplot(fig2)
                top_mood = mood_counts.idxmax()
                st.info(t("most_common_mood").format(mood=top_mood, count=mood_counts.max()))
            water_df = get_water_intake(user_id, (date.today() - timedelta(days=30)).isoformat(), date.today().isoformat())
            if not water_df.empty:
                st.subheader(t("water_intake_chart"))
                fig4, ax4 = plt.subplots(figsize=(10,4))
                ax4.bar(water_df["date"], water_df["glasses"], color="#4287f5")
                ax4.axhline(y=8, color="red", linestyle="--", label=t("recommend_8_glasses"))
                ax4.set_xticklabels(water_df["date"], rotation=45, ha="right")
                ax4.legend()
                st.pyplot(fig4)
                avg_water = water_df["glasses"].mean()
                if avg_water < 7:
                    st.warning(t("water_low_advice").format(avg=avg_water))
                else:
                    st.success(t("water_good").format(avg=avg_water))
        cycles = load_cycles(user_id)
        if len(cycles) >= 3:
            st.subheader(t("cycle_length_over_time"))
            cycles["start_date"] = pd.to_datetime(cycles["start_date"])
            cycles = cycles.sort_values("start_date")
            cycles["num"] = range(1, len(cycles)+1)
            fig3, ax3 = plt.subplots(figsize=(8,4))
            ax3.plot(cycles["num"], cycles["cycle_length"], 'o-', color='purple', markersize=8)
            ax3.set_xlabel(t("cycle_number"))
            ax3.set_ylabel(t("days"))
            ax3.grid(True, linestyle='--', alpha=0.3)
            st.pyplot(fig3)
            valid_lengths = cycles["cycle_length"].dropna()
            if len(valid_lengths) >= 2:
                first = valid_lengths.iloc[0]
                last = valid_lengths.iloc[-1]
                trend = last - first
                if abs(trend) > 3:
                    st.warning(t("cycle_change_warning").format(trend=trend))
                else:
                    st.success(t("cycle_stable"))
    with tabs[2]:
        st.subheader(t("local_african_foods"))
        st.markdown(t("local_foods_text"))
        st.subheader(t("local_remedies"))
        st.markdown(t("local_remedies_text"))
    with tabs[3]:
        st.subheader(t("anemia_check"))
        st.markdown(t("anemia_disclaimer"))
        q1 = st.radio(t("extreme_tiredness"), [t("no"), t("sometimes"), t("yes")], key="an1")
        q2 = st.radio(t("pale_palms"), [t("no"), t("maybe"), t("yes")], key="an2")
        q3 = st.radio(t("dizzy_standing"), [t("no"), t("sometimes"), t("yes")], key="an3")
        q4 = st.radio(t("short_breath"), [t("no"), t("sometimes"), t("yes")], key="an4")
        q5 = st.radio(t("cold_hands"), [t("no"), t("sometimes"), t("yes")], key="an5")
        score = [q1,q2,q3,q4,q5].count(t("yes")) + 0.5 * [q1,q2,q3,q4,q5].count(t("sometimes"))
        if score >= 3:
            st.warning(t("anemia_warning"))
        else:
            st.success(t("anemia_low_risk"))
    with tabs[4]:
        st.subheader(t("exercise_video_guides"))
        st.markdown(t("video_links"))
    with tabs[5]:
        st.subheader(t("share_wellness_report"))
        sym_df = recent_sym(user_id, 30)
        if sym_df.empty:
            st.info(t("not_enough_data_report"))
        else:
            avg_pain = sym_df["pain"].mean()
            avg_energy = sym_df["energy"].mean()
            report = t("report_template").format(pain=avg_pain, energy=avg_energy, mood=sym_df['mood'].mode()[0] if not sym_df['mood'].mode().empty else 'N/A')
            st.text_area(t("copy_report"), report, height=150)
            if st.button(t("send_via_whatsapp")):
                encoded = urllib.parse.quote(report)
                st.markdown(f"[{t('click_to_send_whatsapp')}](https://wa.me/?text={encoded})")

# ───────────────── CALENDAR & PLANNER ─────────────────
def calendar_planner(user_id):
    set_page_background("calender.png")
    st.title(t("rem_cal_tools"))
    try:
        from calendar_component import render_beautiful_calendar
        cycles_df = load_cycles(user_id)
        events_df = load_all_calendar_events(user_id)
        prediction = predict(user_id)
        current_day = cd_(prediction) or 0
        today = date.today()
        start_of_month = date(today.year, today.month, 1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        tasks_df = get_planner_tasks(user_id, start_of_month.isoformat(), end_of_month.isoformat())
        reminders_df = get_all_reminders(user_id)
        render_beautiful_calendar(
            year=today.year, month=today.month,
            periods_df=cycles_df, events_df=events_df,
            prediction=prediction, current_cycle_day=current_day,
            add_event_callback=lambda d,t,typ: add_calendar_event(user_id, d, t, typ),
            log_period_callback=lambda d,dur,flow,pl,med: add_period(user_id, d, dur, flow, pl, med),
            log_symptom_callback=lambda d,cr,mo,fl,pa,en,bl,ap,no,he,sk,bi,an,lb,bt: save_sym(user_id, d, cr, mo, fl, pa, en, bl, ap, no, he, sk, bi, an, lb, bt),
            tasks_df=tasks_df,
            add_planner_task_callback=lambda dt, txt, ph, ut: add_planner_task(user_id, dt, txt, ph, ut),
            reminders_df=reminders_df
        )
    except ImportError:
        st.error(t("calendar_component_missing"))
    st.markdown("---")
    p = predict(user_id)
    cd = cd_(p)
    ph = phase(cd, p)
    st.subheader(t("cycle_planner_title").format(phase=ph))
    tips = {
        t("phase_menstrual"): {t("food"): t("menstrual_food"), t("exercise"): t("menstrual_exercise"), t("productivity"): t("menstrual_productivity"), t("self_care"): t("menstrual_self_care")},
        t("phase_follicular"): {t("food"): t("follicular_food"), t("exercise"): t("follicular_exercise"), t("productivity"): t("follicular_productivity"), t("self_care"): t("follicular_self_care")},
        t("phase_ovulation"): {t("food"): t("ovulation_food"), t("exercise"): t("ovulation_exercise"), t("productivity"): t("ovulation_productivity"), t("self_care"): t("ovulation_self_care")},
        t("phase_luteal"): {t("food"): t("luteal_food"), t("exercise"): t("luteal_exercise"), t("productivity"): t("luteal_productivity"), t("self_care"): t("luteal_self_care")}
    }
    base_ph = ph.split()[0] if " " in ph else ph
    tip = tips.get(base_ph, tips[t("phase_follicular")])
    col1, col2, col3, col4 = st.columns(4)
    col1.info(f"🍲 **{t('eat')}:** {tip[t('food')]}")
    col2.info(f"🏃‍♀️ **{t('move')}:** {tip[t('exercise')]}")
    col3.info(f"📋 **{t('do')}:** {tip[t('productivity')]}")
    col4.info(f"🧘 **{t('self_care')}:** {tip[t('self_care')]}")
    with st.expander(t("task_templates")):
        t_col1, t_col2, t_col3, t_col4 = st.columns(4)
        template_menstrual = [t("rest"), t("journal"), t("light_admin"), t("plan_next_cycle")]
        template_follicular = [t("start_project"), t("learn_new"), t("exercise"), t("socialize")]
        template_ovulation = [t("networking"), t("presentation"), t("pitch_ideas"), t("important_meeting")]
        template_luteal = [t("finish_tasks"), t("organise"), t("cleaning"), t("self_care_rest")]
        with t_col1:
            st.write(f"**{t('phase_menstrual')}**")
            for task in template_menstrual:
                if st.button(f"➕ {task}", key=f"temp_men_{task}"):
                    add_planner_task(user_id, date.today(), task, t("phase_menstrual"))
                    st.success(t("task_added_today").format(task=task))
                    st.rerun()
        with t_col2:
            st.write(f"**{t('phase_follicular')}**")
            for task in template_follicular:
                if st.button(f"➕ {task}", key=f"temp_fol_{task}"):
                    add_planner_task(user_id, date.today(), task, t("phase_follicular"))
                    st.success(t("task_added_today").format(task=task))
                    st.rerun()
        with t_col3:
            st.write(f"**{t('phase_ovulation')}**")
            for task in template_ovulation:
                if st.button(f"➕ {task}", key=f"temp_ovu_{task}"):
                    add_planner_task(user_id, date.today(), task, t("phase_ovulation"))
                    st.success(t("task_added_today").format(task=task))
                    st.rerun()
        with t_col4:
            st.write(f"**{t('phase_luteal')}**")
            for task in template_luteal:
                if st.button(f"➕ {task}", key=f"temp_lut_{task}"):
                    add_planner_task(user_id, date.today(), task, t("phase_luteal"))
                    st.success(t("task_added_today").format(task=task))
                    st.rerun()
    st.subheader(t("tasks_this_week"))
    today = date.today()
    end_week = today + timedelta(days=7)
    tasks_df = get_planner_tasks(user_id, today.isoformat(), end_week.isoformat())
    if not tasks_df.empty:
        for _, row in tasks_df.iterrows():
            col_a, col_b = st.columns([0.1, 0.9])
            completed = bool(row["completed"])
            with col_a:
                new_state = st.checkbox("", value=completed, key=f"task_{row['id']}")
                if new_state != completed:
                    update_task_completion(user_id, row["id"], new_state)
                    st.rerun()
            with col_b:
                st.write(f"**{row['date']}:** {row['task_text']} _{row['phase_suggested']}_")
    else:
        st.info(t("no_tasks_this_week"))
    with st.expander(t("add_custom_task")):
        task_text = st.text_input(t("task_description"), key="custom_task")
        phase_choice = st.selectbox(t("phase"), [t("phase_menstrual"), t("phase_follicular"), t("phase_ovulation"), t("phase_luteal"), t("any")], key="phase_choice")
        if st.button(t("add_task")):
            add_planner_task(user_id, today, task_text, phase_choice, "General")
            st.success(t("task_added"))
            st.rerun()
    st.markdown("---")
    st.subheader(t("reminders"))
    with st.expander(t("set_reminder")):
        rem_date = st.date_input(t("reminder_date"), min_value=date.today(), key="rem_date")
        rem_title = st.text_input(t("title"), key="rem_title")
        rem_desc = st.text_area(t("description"), key="rem_desc")
        is_recurring = st.checkbox(t("recurring_monthly"), key="recurring")
        if st.button(t("set_reminder_button")):
            add_reminder(user_id, rem_date, rem_title, rem_desc, 1 if is_recurring else 0)
            st.success(t("reminder_set"))
            st.rerun()
    upcoming = get_reminders(user_id, date.today())
    if not upcoming.empty:
        for _, row in upcoming.iterrows():
            st.info(f"📅 {row['reminder_date']}: {row['title']} – {row['description']}")
    st.markdown("---")
    st.subheader(t("cycle_statistics"))
    cycles = load_cycles(user_id)
    if not cycles.empty:
        last_cycle = cycles.iloc[-1]["cycle_length"] if not pd.isna(cycles.iloc[-1]["cycle_length"]) else t("na")
        avg = cycles["cycle_length"].mean() if not cycles["cycle_length"].isna().all() else t("na")
        st.write(f"**{t('last_cycle_length')}:** {last_cycle} {t('days')}")
        st.write(f"**{t('average_cycle_length')}:** {avg:.1f} {t('days')}" if isinstance(avg, float) else f"**{t('average_cycle_length')}:** {avg}")
        st.write(f"**{t('periods_logged_count')}:** {len(cycles)}")
    st.subheader(t("tools"))
    tools_cols = st.columns(5)
    if tools_cols[0].button(t("cycle_compare")):
        cycles = load_cycles(user_id)
        if len(cycles) >= 2:
            fig, ax = plt.subplots()
            ax.plot(range(len(cycles)), cycles["cycle_length"], marker='o')
            st.pyplot(fig)
        else:
            st.info(t("need_two_periods"))
    if tools_cols[1].button(t("cost_calc")):
        currency = st.selectbox(t("currency"), ["GHS","NGN","KES","ZAR"], key="cur")
        pad_cost = st.number_input(f"{t('cost_per_pad')} ({currency})", 0.0, 10.0, 1.5, step=0.5, key="pad_cost")
        pads = st.number_input(t("pads_per_period"), 10, 50, 20, key="pads")
        st.metric(t("cost_per_period"), f"{currency} {pads*pad_cost:.2f}")
    if tools_cols[2].button(t("milestones")):
        cnt = len(load_cycles(user_id))
        st.write(f"{t('periods_logged_count')}: {cnt}")
        if cnt >= 10: st.success(t("milestone_10"))
        elif cnt >= 5: st.info(t("milestone_5"))
        else: st.info(t("log_more_periods"))
    if tools_cols[3].button(t("pdf_report")):
        try:
            from fpdf import FPDF
            cycles = load_cycles(user_id).tail(5)
            if cycles.empty:
                st.warning(t("no_data_report"))
            else:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200,10,"Essence Flow Report", ln=1, align='C')
                for _, row in cycles.iterrows():
                    pdf.cell(200,10,f"{t('start')}: {row['start_date']}  {t('length')}: {row['cycle_length']}", ln=1)
                st.download_button(t("download_pdf"), pdf.output(dest='S').encode('latin-1'), "report.pdf")
        except ImportError:
            st.error(t("install_fpdf"))
    if tools_cols[4].button(t("savings_calc")):
        amount = st.number_input(t("target_savings"), 0, 10000, 100, key="amount")
        months = st.number_input(t("months"), 1, 60, 12, key="months")
        st.metric(t("save_per_month"), f"${amount/months:.2f}")

# ───────────────── COMMUNITY STORIES ─────────────────
def community_stories(user_id):
    set_page_background("community.png")
    st.title(t("comm_faq"))
    
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT name, profile_pic FROM users WHERE id = ?", (user_id,))
    user_row = c.fetchone()
    username = user_row[0] if user_row else "Unknown"
    profile_pic = user_row[1] if user_row else ""
    conn.close()
    
    is_admin = st.session_state.get("is_admin", False)
    
    with st.form("new_story_form", clear_on_submit=True):
        story_text = st.text_area(t("comm_share"), placeholder="Share your story, advice, or question...", key="story_text")
        category = st.selectbox(t("category"), [t("hope"), t("advice"), t("humor"), t("story"), t("question")], key="story_category")
        anonymous = st.checkbox(t("post_anonymously"), key="story_anonymous")
        uploaded_file = st.file_uploader("Attach an image (optional, max 7MB)", type=["jpg", "jpeg", "png", "gif", "webp"], key="story_image")
        share_wa = st.checkbox(t("share_whatsapp_group"), key="story_share_wa")
        if st.form_submit_button(t("post")):
            if not story_text.strip() and uploaded_file is None:
                st.warning("Please write something or attach an image.")
            else:
                image_path = None
                if uploaded_file is not None:
                    if uploaded_file.size > 7 * 1024 * 1024:
                        st.error("Image file too large. Maximum size is 7MB.")
                    else:
                        os.makedirs("uploads", exist_ok=True)
                        ext = uploaded_file.name.split('.')[-1]
                        filename = f"post_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000,9999)}.{ext}"
                        filepath = os.path.join("uploads", filename)
                        with open(filepath, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        image_path = filepath
                        st.success("Image uploaded successfully!")
                display_name = t("anonymous") if anonymous else username
                expires_at = (datetime.now() + timedelta(hours=48)).isoformat()
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("""
                    INSERT INTO community_posts (user_id, username, text, image_path, timestamp, expires_at)
                    VALUES (?,?,?,?,?,?)
                """, (user_id, display_name, story_text, image_path, datetime.now().isoformat(), expires_at))
                conn.commit()
                conn.close()
                st.success("Story posted!")
                log_user_activity(user_id, "posted_story", f"Story ID: {c.lastrowid}")
                if share_wa:
                    teen_link = get_global_setting("whatsapp_teen_group", "")
                    adult_link = get_global_setting("whatsapp_adult_group", "")
                    if teen_link or adult_link:
                        choice = st.radio(t("group_choice"), [t("teen"), t("adult")], key="share_wa_choice")
                        link = teen_link if choice == t("teen") else adult_link
                        if link:
                            encoded = urllib.parse.quote(f"🌸 Essence Flow {t('story_prefix')} ({category}):\n{story_text[:200]}...")
                            url = f"{link}&text={encoded}" if "?" in link else f"{link}?text={encoded}"
                            st.markdown(f"[📱 {t('send_to_whatsapp')}]({url})")
                    else:
                        st.warning(t("no_whatsapp_links"))
                st.rerun()
    
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # For non-admin, exclude posts from admin users
    if is_admin:
        query = """
            SELECT p.id, p.user_id, p.username, p.text, p.image_path, p.timestamp, p.likes, p.expires_at, p.deleted
            FROM community_posts p
            ORDER BY p.timestamp DESC
        """
        params = ()
    else:
        query = """
            SELECT p.id, p.user_id, p.username, p.text, p.image_path, p.timestamp, p.likes, p.expires_at, p.deleted
            FROM community_posts p
            JOIN users u ON p.user_id = u.id
            WHERE u.is_admin = 0 AND p.expires_at > ? AND p.deleted = 0
            ORDER BY p.timestamp DESC
        """
        params = (datetime.now().isoformat(),)
    c.execute(query, params)
    posts = c.fetchall()
    conn.close()
    
    if not posts:
        st.info("No stories yet. Be the first to post!")
    else:
        if "story_index" not in st.session_state:
            st.session_state.story_index = 0
        total = len(posts)
        idx = st.session_state.story_index
        
        col_left, col_mid, col_right = st.columns([1, 6, 1])
        with col_left:
            if st.button("◀", key="prev_story", use_container_width=True):
                if idx > 0:
                    st.session_state.story_index = idx - 1
                    st.rerun()
        with col_mid:
            st.caption(f"Story {idx+1} of {total}")
        with col_right:
            if st.button("▶", key="next_story", use_container_width=True):
                if idx < total - 1:
                    st.session_state.story_index = idx + 1
                    st.rerun()
        
        post = posts[idx]
        post_id, post_user_id, post_username, post_text, post_image, post_time, likes, expires_at, deleted = post
        
        try:
            dt = datetime.fromisoformat(post_time)
            time_str = dt.strftime("%d %b %Y, %H:%M")
        except:
            time_str = post_time
        expired = False
        try:
            if datetime.fromisoformat(expires_at) < datetime.now():
                expired = True
        except:
            pass
        
        # Get profile pic of the post author
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT profile_pic FROM users WHERE id = ?", (post_user_id,))
        pic_row = c.fetchone()
        author_pic = pic_row[0] if pic_row else ""
        conn.close()
        
        # Build post with avatar using st.markdown (properly escaped)
        escaped_username = html.escape(post_username)
        escaped_text = html.escape(post_text) if post_text else ""
        escaped_time = html.escape(time_str)
        
        # Show post with avatar
        with st.container():
            # Avatar and header
            col_avatar, col_name, col_time = st.columns([1, 4, 3])
            with col_avatar:
                if author_pic and os.path.exists(author_pic):
                    st.image(author_pic, width=40)
                else:
                    st.write("🌸")
            with col_name:
                st.markdown(f"**{escaped_username}**")
            with col_time:
                st.caption(escaped_time)
            
            # Category and metadata
            if category:
                st.markdown(f"<span style='font-size:0.7rem; background:#5E3A4A; padding:2px 8px; border-radius:10px;'>Category: {category}</span>", unsafe_allow_html=True)
            if expired and is_admin:
                st.warning("⚠️ Expired")
            if deleted and is_admin:
                st.warning("🗑️ Deleted")
            
            # Post text
            if post_text:
                st.write(escaped_text)
            
            # Post image
            if post_image and os.path.exists(post_image):
                try:
                    image = Image.open(post_image)
                    st.image(image, use_container_width=True, width=500)
                except:
                    st.warning("Image could not be loaded.")
            
            # Like, Reply, Share, Delete buttons
            col_like, col_reply, col_share, col_delete = st.columns([1,1,1,1])
            with col_like:
                if st.button(f"❤️ {likes}", key=f"like_post_{post_id}"):
                    conn = sqlite3.connect(DB)
                    c = conn.cursor()
                    c.execute("SELECT 1 FROM community_likes WHERE post_id=? AND user_id=?", (post_id, user_id))
                    if c.fetchone():
                        st.warning("You already liked this post.")
                    else:
                        c.execute("INSERT INTO community_likes (post_id, user_id) VALUES (?,?)", (post_id, user_id))
                        c.execute("UPDATE community_posts SET likes = likes + 1 WHERE id = ?", (post_id,))
                        conn.commit()
                        st.success("Liked!")
                        st.rerun()
                    conn.close()
            with col_reply:
                if st.button("💬 Reply", key=f"reply_post_{post_id}"):
                    st.session_state.reply_to = post_id
                    st.rerun()
            with col_share:
                share_msg = f"🌸 Essence Flow Story:\n{post_text[:200]}..."
                share_url = f"https://wa.me/?text={urllib.parse.quote(share_msg)}"
                st.markdown(f'<a href="{share_url}" target="_blank"><button style="background:#25D366; color:white; border:none; border-radius:15px; padding:0.3rem 0.8rem;">📤 Share</button></a>', unsafe_allow_html=True)
            with col_delete:
                if post_user_id == user_id or is_admin:
                    if st.button("🗑️ Delete", key=f"delete_post_{post_id}"):
                        conn = sqlite3.connect(DB)
                        c = conn.cursor()
                        if is_admin:
                            c.execute("UPDATE community_posts SET deleted = 1 WHERE id = ?", (post_id,))
                        else:
                            c.execute("UPDATE community_posts SET deleted = 1 WHERE id = ? AND user_id = ?", (post_id, user_id))
                        conn.commit()
                        conn.close()
                        log_user_activity(user_id, "deleted_story", f"Story ID: {post_id}")
                        st.success("Post deleted.")
                        st.rerun()
        
        st.markdown("---")
        st.subheader("💬 Replies")
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        if is_admin:
            c.execute("""
                SELECT r.id, r.user_id, r.username, r.text, r.timestamp, r.deleted
                FROM community_replies r
                WHERE r.post_id = ?
                ORDER BY r.timestamp ASC
            """, (post_id,))
        else:
            c.execute("""
                SELECT r.id, r.user_id, r.username, r.text, r.timestamp, r.deleted
                FROM community_replies r
                JOIN users u ON r.user_id = u.id
                WHERE r.post_id = ? AND r.deleted = 0 AND u.is_admin = 0
                ORDER BY r.timestamp ASC
            """, (post_id,))
        replies = c.fetchall()
        conn.close()
        
        if replies:
            for rep in replies:
                rep_id, rep_user, rep_name, rep_text, rep_time, rep_deleted = rep
                if rep_deleted and not is_admin:
                    continue
                try:
                    rep_dt = datetime.fromisoformat(rep_time)
                    rep_str = rep_dt.strftime("%d %b, %H:%M")
                except:
                    rep_str = rep_time
                # Get profile pic for reply author
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("SELECT profile_pic FROM users WHERE id = ?", (rep_user,))
                pic_row = c.fetchone()
                reply_pic = pic_row[0] if pic_row else ""
                conn.close()
                
                # Display reply with avatar
                with st.container():
                    col_rep_avatar, col_rep_content = st.columns([1, 11])
                    with col_rep_avatar:
                        if reply_pic and os.path.exists(reply_pic):
                            st.image(reply_pic, width=25)
                        else:
                            st.write("🌸")
                    with col_rep_content:
                        display_name = rep_name if not is_admin else rep_name
                        if rep_deleted and is_admin:
                            display_name += " (deleted)"
                        st.markdown(f"**{display_name}** _{rep_str}_")
                        st.write(rep_text)
                    # Delete button for reply
                    if rep_user == user_id or is_admin:
                        if st.button("🗑️", key=f"delete_reply_{rep_id}"):
                            conn = sqlite3.connect(DB)
                            c = conn.cursor()
                            if is_admin:
                                c.execute("UPDATE community_replies SET deleted = 1 WHERE id = ?", (rep_id,))
                            else:
                                c.execute("UPDATE community_replies SET deleted = 1 WHERE id = ? AND user_id = ?", (rep_id, user_id))
                            conn.commit()
                            conn.close()
                            log_user_activity(user_id, "deleted_reply", f"Reply ID: {rep_id}")
                            st.success("Reply deleted.")
                            st.rerun()
        else:
            st.caption("No replies yet. Be the first to reply!")
        
        if st.session_state.get("reply_to") == post_id:
            with st.form(key=f"reply_form_{post_id}"):
                reply_text = st.text_area("Write your reply...", key=f"reply_text_{post_id}")
                reply_anonymous = st.checkbox("Reply anonymously", key=f"reply_anonymous_{post_id}")
                if st.form_submit_button("Post Reply"):
                    if reply_text.strip():
                        if reply_anonymous:
                            display_name = "Anonymous"
                        else:
                            conn = sqlite3.connect(DB)
                            c = conn.cursor()
                            c.execute("SELECT name FROM users WHERE id = ?", (user_id,))
                            row = c.fetchone()
                            real_name = row[0] if row else "Unknown"
                            conn.close()
                            display_name = real_name
                        conn = sqlite3.connect(DB)
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO community_replies (post_id, user_id, username, text, timestamp, deleted)
                            VALUES (?,?,?,?,?,0)
                        """, (post_id, user_id, display_name, reply_text, datetime.now().isoformat()))
                        conn.commit()
                        conn.close()
                        log_user_activity(user_id, "posted_reply", f"Post ID: {post_id}")
                        st.success("Reply posted!")
                        st.session_state.reply_to = None
                        st.rerun()
                    else:
                        st.warning("Please write something.")

# ───────────────── PRIVATE CHAT ─────────────────
def get_chatted_users(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT u.id, u.name, u.profile_pic
        FROM users u
        WHERE u.id IN (
            SELECT from_user FROM private_messages WHERE to_user = ?
            UNION
            SELECT to_user FROM private_messages WHERE from_user = ?
        )
        AND u.id != ?
        AND u.is_admin = 0
    """, (user_id, user_id, user_id))
    rows = c.fetchall()
    conn.close()
    return rows

def search_users_by_name(user_id, query):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        SELECT id, name, profile_pic
        FROM users
        WHERE LOWER(name) LIKE LOWER(?) AND id != ? AND is_admin = 0
    """, (f"%{query}%", user_id))
    rows = c.fetchall()
    conn.close()
    return rows

def private_chat(user_id):
    st.title("💬 Private Messages")
    st.caption("Chat with users you have messaged before, or search for new ones.")
    
    # Get contacts (users with chat history)
    contacts = get_chatted_users(user_id)
    
    # Search for new users
    search_query = st.text_input("🔍 Search for a user by name to start chatting:", placeholder="Type username...")
    search_results = []
    if search_query and len(search_query.strip()) > 0:
        search_results = search_users_by_name(user_id, search_query.strip())
    
    # If we have a selected contact in session state, use it
    selected_id = st.session_state.get("selected_contact_id", None)
    selected_name = st.session_state.get("selected_contact_name", None)
    
    # If selected_id is not set but contacts exist, default to first contact
    if selected_id is None and contacts:
        selected_id = contacts[0][0]
        selected_name = contacts[0][1]
        st.session_state.selected_contact_id = selected_id
        st.session_state.selected_contact_name = selected_name
    
    # Show contacts as clickable cards
    st.subheader("📋 Your Contacts")
    if contacts:
        cols = st.columns(3)
        for idx, (uid, name, pic) in enumerate(contacts):
            with cols[idx % 3]:
                button_label = f"{'🖼️' if pic and os.path.exists(pic) else '🌸'} {name}"
                if st.button(button_label, key=f"contact_{uid}", use_container_width=True):
                    st.session_state.selected_contact_id = uid
                    st.session_state.selected_contact_name = name
                    st.rerun()
                if selected_id == uid:
                    st.success(f"Chatting with {name}")
    else:
        st.info("No contacts yet. Search for a user above to start chatting.")
    
    # Show search results with a "Start Chat" button
    if search_results:
        st.subheader("🔎 Search Results")
        for uid, name, pic in search_results:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{'🖼️' if pic and os.path.exists(pic) else '🌸'} {name}")
            with col2:
                if st.button("Chat", key=f"start_chat_{uid}"):
                    st.session_state.selected_contact_id = uid
                    st.session_state.selected_contact_name = name
                    st.rerun()
    
    # If we have a selected contact, show the chat
    if selected_id:
        # Get the selected user's name (if not already known)
        if not selected_name:
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("SELECT name FROM users WHERE id = ?", (selected_id,))
            row = c.fetchone()
            if row:
                selected_name = row[0]
                st.session_state.selected_contact_name = selected_name
            conn.close()
        
        # ─── BLOCK / UNBLOCK LOGIC ────────────────────────────────────
        is_blocked = is_user_blocked(user_id, selected_id)
        
        # Header with block/unblock button
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### 💬 Chat with {selected_name}")
        with col2:
            if is_blocked:
                if st.button("🔓 Unblock", key="unblock_btn"):
                    unblock_user(user_id, selected_id)
                    st.rerun()
            else:
                if st.button("🚫 Block", key="block_btn"):
                    block_user(user_id, selected_id)
                    st.rerun()
        
        if is_blocked:
            st.warning("⚠️ You have blocked this user. You cannot send or receive messages until you unblock them.")
            # Optionally, we could hide the chat and send form, but we'll show a disabled state.
            # We'll still display past messages? Usually hidden, but we'll keep them visible but with a warning.
            # For safety, we prevent sending.
            st.info("Messages from this user are not shown and you cannot send messages.")
            # We'll still display the messages but with a warning overlay? For simplicity, we'll just show the warning and disable sending.
            # We can still show the message history but grey out.
            # We'll display messages but with a note.
            st.markdown("---")
            st.caption("Past messages are shown for reference, but you have blocked this user.")
            # Display messages anyway (but we can optionally hide them)
        else:
            st.markdown("---")
        
        # Display messages with this contact (only if not blocked or we want to show them)
        # For blocked, we will still show messages, but sending is disabled.
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("""
            SELECT id, from_user, to_user, message, file_path, file_name, timestamp, read
            FROM private_messages
            WHERE (from_user = ? AND to_user = ?) OR (from_user = ? AND to_user = ?)
            ORDER BY timestamp ASC
        """, (user_id, selected_id, selected_id, user_id))
        msgs = c.fetchall()
        conn.close()
        
        # Mark messages as read (only if not blocked? Actually we still mark them read)
        if not is_blocked:
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("UPDATE private_messages SET read = 1 WHERE to_user = ? AND from_user = ?", (user_id, selected_id))
            conn.commit()
            conn.close()
        
        if msgs:
            # Find first unread message id to set as target (for optional glow)
            first_unread_id = None
            for msg in msgs:
                msg_id, sender, receiver, text, file_path, file_name, time, read_status = msg
                if sender != user_id and read_status == 0:
                    first_unread_id = f"msg_{msg_id}"
                    break
            
            # Display messages
            for msg in msgs:
                msg_id, sender, receiver, text, file_path, file_name, time, read_status = msg
                try:
                    dt = datetime.fromisoformat(time)
                    time_str = dt.strftime("%H:%M, %d %b")
                except:
                    time_str = time
                
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("SELECT profile_pic, name FROM users WHERE id = ?", (sender,))
                pic_row = c.fetchone()
                sender_pic = pic_row[0] if pic_row else ""
                sender_name = pic_row[1] if pic_row else "Unknown"
                conn.close()
                
                escaped_text = html.escape(text) if text else ""
                escaped_sender = html.escape(sender_name)
                avatar = sender_pic if sender_pic and os.path.exists(sender_pic) else "🌸"
                
                status = ""
                if sender == user_id:
                    if read_status == 0:
                        status = " ✓"
                    else:
                        status = " ✓✓"
                
                # Check if this is the first unread
                is_first_unread = (sender != user_id and read_status == 0 and f"msg_{msg_id}" == first_unread_id)
                
                with st.container():
                    if is_first_unread:
                        st.markdown('<div id="first_unread"></div>', unsafe_allow_html=True)
                        st.markdown('<div class="unread-glow">', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div id="msg_{msg_id}"></div>', unsafe_allow_html=True)
                    
                    with st.chat_message("user" if sender == user_id else "assistant", avatar=avatar):
                        if sender != user_id:
                            st.write(f"**{escaped_sender}**")
                        else:
                            st.write(f"**You**")
                        st.write(escaped_text + status)
                        st.caption(time_str)
                        
                        if file_path and os.path.exists(file_path):
                            mime, _ = mimetypes.guess_type(file_path)
                            if mime and mime.startswith('image/'):
                                st.image(file_path, width=300)
                            elif mime and mime.startswith('video/'):
                                st.video(file_path)
                            elif mime and mime.startswith('audio/'):
                                st.audio(file_path)
                            else:
                                with open(file_path, "rb") as f:
                                    data = f.read()
                                st.download_button(
                                    label=f"📎 Download {file_name}",
                                    data=data,
                                    file_name=file_name,
                                    mime=mime or "application/octet-stream"
                                )
                        
                        if sender == user_id and read_status == 0:
                            if st.button("🗑️ Delete", key=f"del_msg_{msg_id}"):
                                if delete_message(msg_id, user_id):
                                    st.success("Message deleted.")
                                    st.rerun()
                                else:
                                    st.error("Message cannot be deleted.")
                    
                    if is_first_unread:
                        st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No messages yet. Send your first message!")
        
        # Send message form (disabled if blocked)
        with st.form(key="send_msg_form", clear_on_submit=True):
            msg_text = st.text_area("Type your message...", key="msg_text", label_visibility="collapsed", disabled=is_blocked)
            uploaded_file = st.file_uploader("Attach file (image, audio, video, document) – max 15MB", type=None, key="file_upload", disabled=is_blocked)
            send_button = st.form_submit_button("Send", disabled=is_blocked)
            if send_button:
                if is_blocked:
                    st.error("You cannot send messages to a blocked user.")
                else:
                    file_path_saved = None
                    file_name_saved = None
                    if uploaded_file:
                        if uploaded_file.size > 15 * 1024 * 1024:
                            st.error("File too large. Maximum size is 15MB.")
                        else:
                            os.makedirs("uploads/private", exist_ok=True)
                            ext = uploaded_file.name.split('.')[-1] if '.' in uploaded_file.name else ''
                            filename = f"private_{user_id}_{selected_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                            filepath = os.path.join("uploads/private", filename)
                            with open(filepath, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            file_path_saved = filepath
                            file_name_saved = uploaded_file.name
                            st.success("File uploaded.")
                    if not msg_text.strip() and not file_path_saved:
                        st.warning("Please type a message or attach a file.")
                    else:
                        conn = sqlite3.connect(DB)
                        c = conn.cursor()
                        c.execute("INSERT INTO private_messages (from_user, to_user, message, file_path, file_name, timestamp, read) VALUES (?,?,?,?,?,?,?)",
                                  (user_id, selected_id, msg_text, file_path_saved, file_name_saved, datetime.now().isoformat(), 0))
                        conn.commit()
                        conn.close()
                        log_user_activity(user_id, "sent_private_message", f"To user {selected_id}")
                        st.success("Message sent!")
                        st.session_state.last_unread_count = get_unread_count(user_id)
                        st.rerun()
    else:
        st.info("Select a contact or search for a user to start chatting.")

# ───────────────── ONLINE HUB ─────────────────
def online_hub(user_id):
    set_page_background("online_hub.png")
    st.title(t("online_hub"))
    if not st.session_state.get("online_mode", False):
        st.warning(t("offline_mode_warning"))
        return
    st.caption(t("online_hub_caption"))
    link_groups = [
        (t("ghs_link"), "https://www.ghs.gov.gh/"),
        (t("ambulance_gh"), "tel:193"),
        (t("mental_health_gh"), "tel:233243222222"),
        (t("reproductive_health_gh"), "tel:0800900111"),
        (t("nearest_hospital"), "https://www.google.com/maps/search/hospital+near+me"),
        (t("nearest_pharmacy"), "https://www.google.com/maps/search/pharmacy+near+me"),
        (t("donate_products"), "https://www.google.com/search?q=donate+menstrual+products+near+me"),
        (t("healthy_recipes"), "https://www.edamam.com/widget/smart/search?q=period+friendly+recipes"),
        (t("gentle_stretching"), "https://www.youtube.com/results?search_query=gentle+stretching+for+cramps"),
        (t("walking_workout"), "https://www.youtube.com/results?search_query=walking+workout"),
        (t("relaxing_music"), "https://open.spotify.com/search/relaxing%20music"),
        (t("free_health_books"), "https://www.google.com/search?q=free+menstrual+health+books+pdf"),
        (t("who_menstrual_health"), "https://www.who.int/health-topics/menstrual-health"),
        (t("find_local_clinic"), "https://www.openstreetmap.org/?mlat=5.6037&mlon=-0.1870#map=12/5.6037/-0.1870"),
        (t("nigeria_emergency"), "tel:112"),
        (t("kenya_emergency"), "tel:999"),
        (t("south_africa_emergency"), "tel:10177"),
        (t("period_poverty_info"), "https://www.google.com/search?q=period+poverty+solutions+africa"),
        (t("reusable_pad_tutorial"), "https://www.youtube.com/results?search_query=make+reusable+cloth+pads"),
        (t("whatsapp_teens_example"), "https://chat.whatsapp.com/invite/example"),
        (t("whatsapp_adults_example"), "https://chat.whatsapp.com/invite/example"),
        (t("herbal_remedies_guide"), "https://www.google.com/search?q=local+herbal+remedies+for+cramps"),
        (t("child_helpline"), "tel:116"),
        (t("free_product_map"), "https://www.google.com/maps/search/free+period+products+near+me")
    ]
    cols = st.columns(3)
    for i, (label, url) in enumerate(link_groups):
        with cols[i % 3]:
            st.markdown(f'<a href="{url}" target="_blank"><button style="background:#C28585; color:white; border:none; border-radius:20px; padding:0.5rem; width:100%; margin:0.2rem; cursor:pointer;">{label}</button></a>', unsafe_allow_html=True)
    st.markdown("---")
    st.subheader(t("quick_tools"))
    with st.expander(t("period_calculator")):
        last = st.date_input(t("last_period_start"), max_value=date.today())
        cycle = st.number_input(t("avg_cycle_length"), 20, 45, 28)
        if st.button(t("calculate")):
            next_date = last + timedelta(days=cycle)
            st.success(t("next_period_estimate").format(date=next_date.strftime('%A, %d %B %Y')))

# ───────────────── ADMIN PANEL ─────────────────
def admin_panel():
    st.title(t("admin_panel_title"))
    st.markdown(t("admin_only"))
    
    # ─── Update AI Knowledge Base ───────────────────────────────
    st.subheader("📚 Update AI Knowledge Base")
    st.caption("Upload a new `final_qa_dataset.json` file to update Careth's responses.")
    uploaded_qa = st.file_uploader("Choose JSON file", type="json", key="qa_upload")
    if uploaded_qa:
        try:
            data = json.load(uploaded_qa)
            if isinstance(data, list) and all("question" in item and "answer" in item for item in data):
                with open("final_qa_dataset.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                st.success("✅ Knowledge base updated successfully! Careth will now use the new data.")
                # Force reload
                global _INTENTS, _VECTORIZER, _MATRIX
                _INTENTS = None
                _VECTORIZER = None
                _MATRIX = None
                st.rerun()
            else:
                st.error("Invalid format: must be a list of objects with 'question' and 'answer' keys.")
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
    st.divider()
    
    # ─── Rest of admin panel ──────────────────────────────────────
    st.subheader(t("user_statistics"))
    conn = sqlite3.connect(DB)
    users_df = pd.read_sql_query("SELECT id, name, email, created_at, country, is_admin, is_teen, last_username_change, profile_pic FROM users ORDER BY id", conn)
    conn.close()
    if users_df.empty:
        st.info(t("no_users_found"))
        return
    users_df[t("age_group")] = users_df["is_teen"].map({1: t("teen_under20"), 0: t("adult_20plus"), None: t("not_answered")})
    users_df[t("admin")] = users_df["is_admin"].map({1: t("yes"), 0: t("no")})
    total_users = len(users_df)
    teens = len(users_df[users_df["is_teen"] == 1])
    adults = len(users_df[users_df["is_teen"] == 0])
    admins = len(users_df[users_df["is_admin"] == 1])
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("total_users"), total_users)
    col2.metric(t("teens"), teens)
    col3.metric(t("adults"), adults)
    col4.metric(t("admins"), admins)
    
    st.subheader(t("all_registered_users"))
    st.dataframe(users_df[["id", "name", "email", "country", "created_at", t("age_group"), t("admin"), "last_username_change", "profile_pic"]], use_container_width=True)
    
    st.subheader(t("manage_users"))
    selected_user = st.selectbox(t("select_user"), users_df["name"].tolist())
    if selected_user:
        user_id = users_df[users_df["name"] == selected_user]["id"].values[0]
        user_is_teen = users_df[users_df["id"] == user_id]["is_teen"].values[0]
        user_is_admin = users_df[users_df["id"] == user_id]["is_admin"].values[0]
        user_email = users_df[users_df["id"] == user_id]["email"].values[0]
        user_country = users_df[users_df["id"] == user_id]["country"].values[0]
        last_change = users_df[users_df["id"] == user_id]["last_username_change"].values[0]
        profile_pic = users_df[users_df["id"] == user_id]["profile_pic"].values[0]
        with st.expander(t("user_info").format(name=selected_user), expanded=True):
            st.write(f"**{t('id')}:** {user_id}")
            st.write(f"**{t('email')}:** {user_email if user_email else t('not_provided')}")
            st.write(f"**{t('country')}:** {user_country}")
            st.write(f"**{t('age_group')}:** {t('teen_under20') if user_is_teen == 1 else t('adult_20plus') if user_is_teen == 0 else t('not_answered')}")
            st.write(f"**{t('admin')}:** {t('yes') if user_is_admin == 1 else t('no')}")
            st.write(f"**Last username change:** {last_change if last_change else 'Never'}")
            if profile_pic:
                st.image(profile_pic, width=100)
        
        st.subheader(t("admin_actions"))
        col_a, col_b = st.columns(2)
        with col_a:
            if user_is_admin == 0:
                if st.button(t("make_admin").format(name=selected_user)):
                    conn = sqlite3.connect(DB)
                    c = conn.cursor()
                    c.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
                    conn.commit()
                    conn.close()
                    log_user_activity(user_id, "made_admin", f"By admin {st.session_state.user}")
                    st.success(t("now_admin").format(name=selected_user))
                    st.rerun()
            else:
                if st.button(t("remove_admin").format(name=selected_user)):
                    if admins <= 1:
                        st.error(t("cannot_remove_last_admin"))
                    else:
                        conn = sqlite3.connect(DB)
                        c = conn.cursor()
                        c.execute("UPDATE users SET is_admin = 0 WHERE id = ?", (user_id,))
                        conn.commit()
                        conn.close()
                        log_user_activity(user_id, "removed_admin", f"By admin {st.session_state.user}")
                        st.success(t("no_longer_admin").format(name=selected_user))
                        st.rerun()
        with col_b:
            with st.popover(t("edit_cycle_settings")):
                cur_cycle_len = int(get_user_setting(user_id, "cycle_len", "28"))
                cur_period_dur = int(get_user_setting(user_id, "period_dur", "5"))
                new_cycle_len = st.number_input(t("cycle_length_days"), 20, 45, cur_cycle_len, key="adm_cycle")
                new_period_dur = st.number_input(t("period_duration_days"), 2, 10, cur_period_dur, key="adm_period")
                if st.button(t("save_for_user"), key="save_user_settings"):
                    set_user_setting(user_id, "cycle_len", str(new_cycle_len))
                    set_user_setting(user_id, "period_dur", str(new_period_dur))
                    log_user_activity(user_id, "cycle_settings_changed", f"By admin {st.session_state.user}")
                    st.success(t("settings_updated").format(name=selected_user))
        
        st.subheader(t("danger_zone"))
        if st.button(t("delete_account_permanent").format(name=selected_user), type="secondary"):
            st.warning(t("irreversible_warning"))
            confirm = st.text_input(t("type_name_to_confirm").format(name=selected_user))
            if confirm == selected_user:
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                tables = ["cycles", "symptoms", "product_inventory", "product_usage", "daily_wellness",
                          "calendar_events", "planner_tasks", "custom_symptoms", "symptom_log_custom",
                          "journal", "medications", "medication_log", "bbt", "cervical_mucus",
                          "ovulation_tests", "water_intake", "exercise_log", "sleep_quality",
                          "reminders", "partner_notes", "product_locations", "skipped_cycles", "settings",
                          "chat_logs", "community_posts", "community_replies", "community_likes",
                          "user_activity_log", "private_messages", "blocked_users"]
                for table in tables:
                    c.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
                c.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                conn.close()
                st.success(t("account_deleted").format(name=selected_user))
                st.rerun()
            elif confirm:
                st.error(t("confirmation_mismatch"))
    
    st.divider()
    st.subheader(t("global_whatsapp_settings"))
    teen_link = st.text_input(t("teen_group_link"), value=get_global_setting("whatsapp_teen_group", ""))
    adult_link = st.text_input(t("adult_group_link"), value=get_global_setting("whatsapp_adult_group", ""))
    if st.button(t("save_whatsapp_links")):
        set_global_setting("whatsapp_teen_group", teen_link)
        set_global_setting("whatsapp_adult_group", adult_link)
        st.success(t("whatsapp_links_updated"))
    
    if selected_user:
        st.divider()
        st.subheader(t("full_user_data").format(name=selected_user))
        user_id_view = users_df[users_df["name"] == selected_user]["id"].values[0]
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
            t("cycles"), t("symptoms"), t("wellness"), t("reminders"), 
            t("product_usage"), t("skipped_cycles"), "📨 Chat Logs (AI)", "📢 Community", "🤖 All AI Chats"
        ])
        with tab1:
            cycles = load_cycles(user_id_view)
            if not cycles.empty:
                st.dataframe(cycles, use_container_width=True)
            else:
                st.info(t("no_cycles"))
        with tab2:
            conn = sqlite3.connect(DB)
            sym_df = pd.read_sql_query("SELECT * FROM symptoms WHERE user_id=? ORDER BY date DESC", conn, params=[user_id_view])
            conn.close()
            if not sym_df.empty:
                st.dataframe(sym_df, use_container_width=True)
            else:
                st.info(t("no_symptoms"))
        with tab3:
            wellness = load_wellness(user_id_view)
            if not wellness.empty:
                st.dataframe(wellness, use_container_width=True)
            else:
                st.info(t("no_wellness"))
        with tab4:
            rem = get_all_reminders(user_id_view)
            if not rem.empty:
                st.dataframe(rem, use_container_width=True)
            else:
                st.info(t("no_reminders"))
        with tab5:
            conn = sqlite3.connect(DB)
            usage = pd.read_sql_query("SELECT * FROM product_usage WHERE user_id=? ORDER BY period_start_date DESC", conn, params=[user_id_view])
            conn.close()
            if not usage.empty:
                st.dataframe(usage, use_container_width=True)
            else:
                st.info(t("no_product_usage"))
        with tab6:
            conn = sqlite3.connect(DB)
            skipped = pd.read_sql_query("SELECT * FROM skipped_cycles WHERE user_id=? ORDER BY cycle_start_date DESC", conn, params=[user_id_view])
            conn.close()
            if not skipped.empty:
                st.dataframe(skipped, use_container_width=True)
            else:
                st.info(t("no_skipped_cycles"))
        with tab7:
            st.subheader("AI Chat Logs (permanent)")
            conn = sqlite3.connect(DB)
            chat_df = pd.read_sql_query("SELECT id, user_id, timestamp, user_message, ai_response, flagged FROM chat_logs WHERE user_id=? ORDER BY timestamp DESC", conn, params=[user_id_view])
            conn.close()
            if not chat_df.empty:
                st.dataframe(chat_df, use_container_width=True)
                flagged_df = chat_df[chat_df["flagged"] == 1]
                if not flagged_df.empty:
                    st.warning(f"⚠️ {len(flagged_df)} flagged messages")
                    st.dataframe(flagged_df[["timestamp", "user_message", "ai_response"]], use_container_width=True)
            else:
                st.info("No AI chat logs yet.")
        with tab8:
            st.subheader("Community Activity")
            conn = sqlite3.connect(DB)
            posts = pd.read_sql_query("SELECT * FROM community_posts WHERE user_id=? ORDER BY timestamp DESC", conn, params=[user_id_view])
            replies = pd.read_sql_query("SELECT * FROM community_replies WHERE user_id=? ORDER BY timestamp DESC", conn, params=[user_id_view])
            conn.close()
            if not posts.empty:
                st.write("**Posts**")
                st.dataframe(posts, use_container_width=True)
            if not replies.empty:
                st.write("**Replies**")
                st.dataframe(replies, use_container_width=True)
            if posts.empty and replies.empty:
                st.info("No community activity.")
        with tab9:  # All AI Chats (global)
            st.subheader("🤖 All AI Chat Logs (All Users)")
            conn = sqlite3.connect(DB)
            all_chat_df = pd.read_sql_query("""
                SELECT c.id, u.name as username, c.timestamp, c.user_message, c.ai_response, c.flagged
                FROM chat_logs c
                JOIN users u ON c.user_id = u.id
                ORDER BY c.timestamp DESC
            """, conn)
            conn.close()
            if not all_chat_df.empty:
                st.dataframe(all_chat_df, use_container_width=True)
                show_flagged = st.checkbox("Show only flagged messages", key="show_flagged_global")
                if show_flagged:
                    flagged_df = all_chat_df[all_chat_df["flagged"] == 1]
                    if not flagged_df.empty:
                        st.dataframe(flagged_df, use_container_width=True)
                    else:
                        st.info("No flagged messages.")
                csv_all = all_chat_df.to_csv(index=False)
                st.download_button("📥 Download all AI chats (CSV)", data=csv_all, file_name="all_ai_chats.csv", mime="text/csv")
            else:
                st.info("No AI chat logs recorded yet.")
    
    st.divider()
    st.subheader("📨 All Private Messages")
    conn = sqlite3.connect(DB)
    pm_df = pd.read_sql_query("""
        SELECT pm.id, u1.name as sender, u2.name as receiver, pm.message, pm.file_path, pm.file_name, pm.timestamp, pm.read
        FROM private_messages pm
        JOIN users u1 ON pm.from_user = u1.id
        JOIN users u2 ON pm.to_user = u2.id
        ORDER BY pm.timestamp DESC
    """, conn)
    conn.close()
    if not pm_df.empty:
        st.dataframe(pm_df, use_container_width=True)
    else:
        st.info("No private messages yet.")
    
    st.divider()
    st.subheader("🚫 Blocked Users")
    conn = sqlite3.connect(DB)
    block_df = pd.read_sql_query("""
        SELECT b.user_id, u1.name as blocker, b.blocked_user_id, u2.name as blocked
        FROM blocked_users b
        JOIN users u1 ON b.user_id = u1.id
        JOIN users u2 ON b.blocked_user_id = u2.id
        ORDER BY b.user_id
    """, conn)
    conn.close()
    if not block_df.empty:
        st.dataframe(block_df, use_container_width=True)
    else:
        st.info("No users are blocked.")
    
    st.divider()
    st.subheader("📋 User Activity Logs")
    conn = sqlite3.connect(DB)
    log_df = pd.read_sql_query("""
        SELECT al.id, u.name as user, al.action, al.details, al.timestamp
        FROM user_activity_log al
        JOIN users u ON al.user_id = u.id
        ORDER BY al.timestamp DESC
        LIMIT 200
    """, conn)
    conn.close()
    if not log_df.empty:
        st.dataframe(log_df, use_container_width=True)
    else:
        st.info("No activity logs yet.")

# ───────────────── SETTINGS ─────────────────
def settings_page(user_id):
    set_page_background("settings.png")
    st.title(t("set"))
    tabs = st.tabs([t("cycle"), t("appearance"), t("emergency"), t("account"), "🌐 Connection"])
    with tabs[0]:
        cl = st.number_input(t("cycle_length_days"), 20, 45, int(get_user_setting(user_id, "cycle_len", "28")), key="cl")
        pd = st.number_input(t("period_duration_days"), 2, 10, int(get_user_setting(user_id, "period_dur", "5")), key="pd")
        if st.button(t("save_cycle_settings"), key="save_cycle"):
            set_user_setting(user_id, "cycle_len", str(cl))
            set_user_setting(user_id, "period_dur", str(pd))
            st.success(t("saved"))
    with tabs[1]:
        night = st.checkbox(t("night_mode"), st.session_state.get("night_mode", False), key="night")
        discreet = st.checkbox(t("discreet"), st.session_state.get("discreet", False), key="discreet")
        teen = st.checkbox(t("teen_mode"), st.session_state.get("teen_mode", False), key="teen")
        icon_nav = st.checkbox(t("icon_only_nav"), st.session_state.get("icon_nav", False), key="icon_nav")
        video_enabled = st.checkbox("Enable video background (may affect performance)", st.session_state.get("video_background_enabled", True))
        if video_enabled != st.session_state.get("video_background_enabled"):
            st.session_state.video_background_enabled = video_enabled
            st.rerun()
        if night != st.session_state.get("night_mode"): st.session_state.night_mode = night; st.rerun()
        if discreet != st.session_state.get("discreet"): st.session_state.discreet = discreet; st.rerun()
        if teen != st.session_state.get("teen_mode"): st.session_state.teen_mode = teen; set_user_setting(user_id, "teen_mode", str(teen)); st.rerun()
        if icon_nav != st.session_state.get("icon_nav"): st.session_state.icon_nav = icon_nav; set_user_setting(user_id, "icon_nav", str(icon_nav)); st.rerun()
    with tabs[2]:
        st.subheader(t("emergency_contact"))
        name = st.text_input(t("name"), get_user_setting(user_id, "emergency_name", ""), key="emg_name")
        phone = st.text_input(t("phone"), get_user_setting(user_id, "emergency_phone", ""), key="emg_phone")
        if st.button(t("save_emergency_contact"), key="save_emergency"):
            set_user_setting(user_id, "emergency_name", name)
            set_user_setting(user_id, "emergency_phone", phone)
            st.success(t("saved"))
    with tabs[3]:
        st.subheader("👤 Profile Picture")
        st.caption("Upload a profile picture (icon) – it will appear next to your name.")
        current_pic = st.session_state.get("profile_pic", "")
        if current_pic and os.path.exists(current_pic):
            st.image(current_pic, width=100)
        uploaded_pic = st.file_uploader("Choose an image (JPEG, PNG)", type=["jpg", "jpeg", "png"], key="profile_pic_upload")
        if uploaded_pic:
            os.makedirs("uploads/profiles", exist_ok=True)
            ext = uploaded_pic.name.split('.')[-1]
            filename = f"profile_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
            filepath = os.path.join("uploads/profiles", filename)
            with open(filepath, "wb") as f:
                f.write(uploaded_pic.getbuffer())
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("UPDATE users SET profile_pic = ? WHERE id = ?", (filepath, user_id))
            conn.commit()
            conn.close()
            st.session_state.profile_pic = filepath
            log_user_activity(user_id, "updated_profile_pic", f"New pic: {filepath}")
            st.success("Profile picture updated!")
            st.rerun()
        st.divider()
        st.subheader("👤 Change Username")
        current_username = st.session_state.user
        st.write(f"Current username: **{current_username}**")
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT last_username_change FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        last_change = row[0] if row else None
        if last_change:
            try:
                last_dt = datetime.fromisoformat(last_change)
                days_passed = (datetime.now() - last_dt).days
                st.info(f"Last username change: {last_dt.strftime('%d %b %Y')} ({days_passed} days ago)")
                if days_passed < 30:
                    days_left = 30 - days_passed
                    st.warning(f"You can change your username again in {days_left} days.")
                    change_disabled = True
                else:
                    st.success("You are eligible to change your username.")
                    change_disabled = False
            except:
                change_disabled = False
        else:
            st.info("You have never changed your username. You can change it now.")
            change_disabled = False
        if not change_disabled:
            new_username = st.text_input("New username", value=current_username)
            if st.button("Change Username", key="change_username_btn"):
                if new_username and new_username != current_username:
                    conn = sqlite3.connect(DB)
                    c = conn.cursor()
                    c.execute("SELECT id FROM users WHERE name = ? AND id != ?", (new_username, user_id))
                    if c.fetchone():
                        st.error("Username already taken. Please choose another.")
                    else:
                        c.execute("UPDATE users SET name = ?, last_username_change = ? WHERE id = ?",
                                  (new_username, datetime.now().isoformat(), user_id))
                        conn.commit()
                        conn.close()
                        log_user_activity(user_id, "changed_username", f"From {current_username} to {new_username}")
                        st.session_state.user = new_username
                        st.success(f"Username changed to {new_username}!")
                        st.rerun()
                    conn.close()
                else:
                    st.warning("Please enter a new username.")
        st.divider()
        if st.button(t("logout"), key="logout_btn"):
            del st.session_state.user_id
            del st.session_state.user
            st.rerun()
        if st.button(t("clear_data"), key="delete_data_btn"):
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            for table in ["cycles","symptoms","product_inventory","product_usage","daily_wellness","calendar_events","planner_tasks","bbt","cervical_mucus","ovulation_tests","water_intake","exercise_log","sleep_quality","reminders","partner_notes","product_locations","skipped_cycles"]:
                c.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))
            conn.commit()
            conn.close()
            st.success(t("data_deleted"))
            st.rerun()
    with tabs[4]:
        st.subheader("🌐 Online Mode")
        current_mode = st.session_state.get("online_mode", True)
        new_mode = st.checkbox("Enable online features (hub, external links)", value=current_mode)
        if new_mode != current_mode:
            st.session_state.online_mode = new_mode
            set_user_setting(user_id, "online_mode", str(new_mode))
            st.success("Online mode updated. Some features will be enabled/disabled.")
            st.rerun()
        if not new_mode:
            st.info("You are currently offline. Online Hub and some external links are disabled.")
        else:
            st.success("You are online. All features are available.")

# ───────────────── MOBILE TOP NAVIGATION ─────────────────
def mobile_top_nav():
    # No Messages button – only sidebar
    st.markdown('<div class="top-nav">', unsafe_allow_html=True)
    cols = st.columns(6)
    nav_items = [
        ("🏠", "dashboard"),
        ("🩸", "log_period"),
        ("📝", "symptom_tracker"),
        ("🗓️", "calendar_planner"),
        ("🧘", "wellness_insights"),
        ("⚙️", "settings")
    ]
    for i, (icon, key) in enumerate(nav_items):
        if cols[i].button(icon, key=f"topnav_{key}", help=key.replace("_"," ").title()):
            st.session_state.menu = key
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    with st.expander(t("more_menu_options")):
        lang_options = list(LANG.keys())
        if lang_options:
            cols_lang = st.columns([1, 2])
            with cols_lang[0]:
                st.write("🌍 " + t("language"))
            with cols_lang[1]:
                selected_lang = st.selectbox("", lang_options, index=lang_options.index(st.session_state.get("language", "English")), key="more_lang_select", label_visibility="collapsed")
                if selected_lang != st.session_state.get("language"):
                    st.session_state.language = selected_lang
                    st.rerun()
        if st.button("💬 " + t("chat_with_careth"), key="more_careth"):
            st.session_state.show_main_chat = True
            st.session_state.menu = "main_chat"
            st.rerun()
        st.markdown("---")
        all_items = [
            (t("cycle_history"), "history"),
            (t("pregnancy_info"), "pregnancy"),
            (t("learn_books"), "learn_books"),
            (t("product_supply"), "product"),
            (t("community"), "community"),
            (t("online_hub"), "online_hub"),
            ("Smart Insights", "smart_insights"),
            (t("admin_panel"), "admin") if st.session_state.get("is_admin", False) else None,
        ]
        cols2 = st.columns(3)
        for idx, (label, key) in enumerate([item for item in all_items if item]):
            if cols2[idx % 3].button(label, key=f"expand_{key}"):
                st.session_state.menu = key
                st.rerun()

# ───────────────── MAIN ─────────────────
def main():
    init_db()
    if "user_id" not in st.session_state:
        if st.session_state.get("show_register"):
            register_screen()
        else:
            login_screen()
        return
    user_id = st.session_state.user_id
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT is_teen FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row is not None and row[0] is None:
        with st.container():
            st.markdown(t("teen_question_title"))
            teen_choice = st.radio(
                t("teen_question_prompt"),
                (t("yes_teen"), t("no_adult")),
                index=None
            )
            if st.button(t("continue_button"), use_container_width=True):
                is_teen_val = 1 if teen_choice == t("yes_teen") else 0
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("UPDATE users SET is_teen = ? WHERE id = ?", (is_teen_val, user_id))
                conn.commit()
                conn.close()
                st.rerun()
        st.stop()
    apply_night_mode()
    step = st.session_state.get("step", "main")
    if st.session_state.get("new_user", False):
        if step == "online_choice":
            online_choice_screen()
        elif step == "setup_wizard":
            setup_wizard(user_id)
            return
    set_page_background("default.png")
    if st.session_state.get("new_user", False) and not st.session_state.get("onboarding_shown", False):
        st.session_state.show_onboarding = True
        st.session_state.onboarding_shown = True
    interactive_onboarding()
    mobile_top_nav()
    
    # Sidebar profile pic
    profile_pic = st.session_state.get("profile_pic", "")
    col_sidebar = st.sidebar.columns([1, 3])
    with col_sidebar[0]:
        if profile_pic and os.path.exists(profile_pic):
            st.image(profile_pic, width=50)
        else:
            st.write("🌸")
    with col_sidebar[1]:
        st.sidebar.markdown(f"""
        <div class="sidebar-header">
            <h2 style="margin:0;">Essence Flow</h2>
            <p style="color:#EAA4BE;">{t('hi')}, {st.session_state.user}</p>
        </div>
        """, unsafe_allow_html=True)
    
    p = predict(user_id)
    cd = cd_(p)
    ph = phase(cd, p)
    st.sidebar.markdown(f"""
    <div style="background:rgba(255,255,255,0.08); border-radius:16px; padding:0.8rem; text-align:center;">
        <div style="font-size:1.5rem;">{t('day')} {cd if cd else '?'}</div>
        <div>{ph}</div>
        <small>{t('next')}: {p['next'].strftime('%d %b') if p['next'] else '—'}</small>
    </div>
    """, unsafe_allow_html=True)
    if st.session_state.get("focus_chat", False):
        st.session_state.focus_chat = False
    
    # Sidebar menu with notification badge as plain text count
    icon_nav = st.session_state.get("icon_nav", False)
    is_admin = st.session_state.get("is_admin", False)
    unread = get_unread_count(user_id)
    badge_text = f" ({unread})" if unread > 0 else ""
    
    if icon_nav:
        menu_items = {"🏠": "dashboard", "🩸": "log_period", "📝": "symptom_tracker", "📜": "history", "🤰": "pregnancy",
                      "🗓️": "calendar_planner", "🧘": "wellness_insights", "📚": "learn_books", "🛍️": "product",
                      "💬": "community", "🌐": "online_hub", "⚙️": "settings"}
        if is_admin:
            menu_items["👑"] = "admin"
        menu_items[f"💌 Messages{badge_text}"] = "messages"
        for icon, key in menu_items.items():
            if st.sidebar.button(icon, use_container_width=True, help=key.replace("_"," ").title()):
                st.session_state.menu = key
                st.rerun()
    else:
        menu_items = {t("dashboard"): "dashboard", t("log_period"): "log_period", t("symptom_tracker"): "symptom_tracker",
                      t("cycle_history"): "history", t("pregnancy_info"): "pregnancy", t("calendar_planner"): "calendar_planner",
                      t("wellness_insights"): "wellness_insights", t("learn_books"): "learn_books", t("product_supply"): "product",
                      t("community"): "community", t("online_hub"): "online_hub", t("settings"): "settings"}
        if is_admin:
            menu_items[t("admin_panel")] = "admin"
        menu_items[f"💬 Messages{badge_text}"] = "messages"
        for label, key in menu_items.items():
            if st.sidebar.button(label, use_container_width=True):
                st.session_state.menu = key
                st.rerun()
    st.sidebar.markdown("---")
    sidebar_chat(user_id)
    menu = st.session_state.get("menu", "dashboard")
    if menu == "main_chat":
        main_chat_area(user_id)
    elif menu == "dashboard": dashboard(user_id)
    elif menu == "log_period": log_period(user_id)
    elif menu == "symptom_tracker": symptom_tracker(user_id)
    elif menu == "history": view_history(user_id)
    elif menu == "pregnancy": pregnancy_info(user_id)
    elif menu == "calendar_planner": calendar_planner(user_id)
    elif menu == "wellness_insights": wellness_insights(user_id)
    elif menu == "learn_books": learn_and_books(user_id)
    elif menu == "product": product_tracker(user_id)
    elif menu == "community": community_stories(user_id)
    elif menu == "online_hub": online_hub(user_id)
    elif menu == "messages": private_chat(user_id)
    elif menu == "smart_insights":
        set_page_background("smart_insights.png")
        smart_insights_page(
            user_id,
            load_cycles,
            recent_sym,
            load_wellness,
            predict,
            cd_,
            t=t
        )
    elif menu == "settings": settings_page(user_id)
    elif menu == "admin" and is_admin:
        admin_panel()
    else: dashboard(user_id)
    st.markdown(f'<div class="footer">🌸 {t("footer")}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()