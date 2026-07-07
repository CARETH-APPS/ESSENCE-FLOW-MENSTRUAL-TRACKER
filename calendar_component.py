import calendar
import streamlit as st
from datetime import date, timedelta
import pandas as pd

def render_beautiful_calendar(
    year, month, periods_df, events_df, prediction, current_cycle_day,
    add_event_callback, log_period_callback, log_symptom_callback,
    tasks_df=None,
    add_planner_task_callback=None,
    reminders_df=None,
    t=None
):
    if t is None:
        def t(x): return x

    # Navigation state
    if "cal_year" not in st.session_state:
        st.session_state.cal_year = year
    if "cal_month" not in st.session_state:
        st.session_state.cal_month = month
    year = st.session_state.cal_year
    month = st.session_state.cal_month

    cal_matrix = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    today = date.today()

    # Build day_info (unchanged from your original)
    day_info = {}

    if not periods_df.empty:
        for _, row in periods_df.iterrows():
            start = date.fromisoformat(row["start_date"])
            dur = int(row["period_duration"]) if not pd.isna(row["period_duration"]) else 5
            for d in range(dur):
                day_date = start + timedelta(days=d)
                if day_date.year == year and day_date.month == month:
                    day_info[day_date.day] = {"type": "period", "title": "🩸"}

    avg_cycle = prediction.get("avg_cl", 28)
    last_period = prediction.get("last")
    if last_period:
        next_pred = last_period
        for _ in range(3):
            next_pred += timedelta(days=avg_cycle)
            for d in range(prediction.get("pd", 5)):
                day_date = next_pred + timedelta(days=d)
                if day_date.year == year and day_date.month == month:
                    if day_date.day not in day_info:
                        day_info[day_date.day] = {"type": "predicted_period", "title": "🩸"}

    if prediction.get("ov"):
        ov_date = prediction["ov"]
        if ov_date.year == year and ov_date.month == month:
            day_info[ov_date.day] = {"type": "ovulation", "title": "🥚"}

    if prediction.get("ov"):
        ov_date = prediction["ov"]
        for delta in range(-3, 1):
            fd = ov_date + timedelta(days=delta)
            if fd.year == year and fd.month == month:
                if fd.day not in day_info or day_info[fd.day]["type"] != "ovulation":
                    day_info[fd.day] = {"type": "fertile", "title": "🌸"}

    if not events_df.empty:
        for _, ev in events_df.iterrows():
            ev_date = date.fromisoformat(ev["event_date"])
            if ev_date.year == year and ev_date.month == month:
                short_title = ev["title"][:6] if ev["title"] else t("event")
                day_info[ev_date.day] = {"type": "custom", "title": short_title}

    if tasks_df is not None and not tasks_df.empty:
        for _, row in tasks_df.iterrows():
            task_date = date.fromisoformat(row["date"])
            if task_date.year == year and task_date.month == month:
                if task_date.day in day_info:
                    existing = day_info[task_date.day]
                    task_count = existing.get("task_count", 0) + 1
                    existing["task_count"] = task_count
                    existing["title"] = f"{existing.get('title', '')} 📋{task_count}"
                else:
                    day_info[task_date.day] = {"type": "task", "title": "📋", "task_count": 1}

    if reminders_df is not None and not reminders_df.empty:
        for _, row in reminders_df.iterrows():
            rem_date = date.fromisoformat(row["reminder_date"])
            if rem_date.year == year and rem_date.month == month:
                short_title = row["title"][:6] if row["title"] else t("reminder")
                if rem_date.day in day_info:
                    existing = day_info[rem_date.day]
                    existing["reminder"] = {"title": short_title, "desc": row["description"]}
                    existing["title"] = f"{existing.get('title', '')} {short_title}"
                else:
                    day_info[rem_date.day] = {"type": "reminder", "title": short_title, "reminder_desc": row["description"]}

    # --- Helper to get translated text with fallback for all languages ---
    def get_text(key, fallback_map):
        """Return translation from t() if available, else fallback based on language."""
        val = t(key)
        if val != key:  # translation exists
            return val
        lang = st.session_state.get("language", "English")
        return fallback_map.get(lang, fallback_map.get("English", key))

    # --- Navigation buttons with fallbacks ---
    prev_text = get_text("previous_month", {
        "English": "◀ Previous",
        "Ewe": "◀ Ɣleti si va yi",
        "Ga": "◀ Nyɔŋmɔ ni ho",
        "Dagbani": "◀ Goli din daa gari",
        "Hausa": "◀ Watan da ya gabata",
        "Twi": "◀ Bosome a atwam"
    })
    next_text = get_text("next_month", {
        "English": "Next ▶",
        "Ewe": "Ɣleti si gbɔna ▶",
        "Ga": "Nyɔŋmɔ ni ba ▶",
        "Dagbani": "Goli din yɛn ti kana ▶",
        "Hausa": "Wata mai zuwa ▶",
        "Twi": "Bosome a ɛreba ▶"
    })
    today_text = get_text("today_button", {
        "English": "Today",
        "Ewe": "Egbea",
        "Ga": "Ŋmɛnɛ",
        "Dagbani": "Zuŋɔ",
        "Hausa": "Yau",
        "Twi": "Ɛnnɛ"
    })

    col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
    with col1:
        if st.button(prev_text):
            if month == 1:
                st.session_state.cal_year = year - 1
                st.session_state.cal_month = 12
            else:
                st.session_state.cal_month = month - 1
            st.rerun()
    with col2:
        st.markdown(f"<h2 style='text-align:center;'>{month_name} {year}</h2>", unsafe_allow_html=True)
    with col3:
        if st.button(today_text):
            st.session_state.cal_year = today.year
            st.session_state.cal_month = today.month
            st.rerun()
    with col4:
        if st.button(next_text):
            if month == 12:
                st.session_state.cal_year = year + 1
                st.session_state.cal_month = 1
            else:
                st.session_state.cal_month = month + 1
            st.rerun()

    # --- Current cycle day and phase (unchanged, uses t()) ---
    if current_cycle_day:
        pd_dur = prediction.get("pd", 5)
        ov_day = (prediction.get("ov") - prediction.get("last")).days + 1 if prediction.get("ov") and prediction.get("last") else None
        discreet = st.session_state.get("discreet", False)
        teen = st.session_state.get("teen_mode", False)

        if discreet:
            if current_cycle_day <= pd_dur:
                phase = t("phase_1") if t("phase_1") != "phase_1" else "Phase 1"
            elif ov_day and current_cycle_day < ov_day:
                phase = t("phase_2") if t("phase_2") != "phase_2" else "Phase 2"
            elif ov_day and current_cycle_day == ov_day:
                phase = t("phase_3") if t("phase_3") != "phase_3" else "Phase 3"
            else:
                phase = t("phase_4") if t("phase_4") != "phase_4" else "Phase 4"
        elif teen:
            if current_cycle_day <= pd_dur:
                phase = t("phase_teen_period")
            elif ov_day and current_cycle_day < ov_day:
                phase = t("phase_teen_growing")
            elif ov_day and current_cycle_day == ov_day:
                phase = t("phase_teen_ovulation")
            else:
                phase = t("phase_teen_pre")
        else:
            if current_cycle_day <= pd_dur:
                phase = t("phase_menstrual")
            elif ov_day and current_cycle_day < ov_day:
                phase = t("phase_follicular")
            elif ov_day and current_cycle_day == ov_day:
                phase = t("phase_ovulation")
            else:
                phase = t("phase_luteal")

        next_date_str = prediction['next'].strftime('%d %b') if prediction.get('next') else "—"
        day_text = get_text("day", {
            "English": "Day",
            "Ewe": "Ŋkeke",
            "Ga": "Gbɛkɛ",
            "Dagbani": "Dabisili",
            "Hausa": "Rana",
            "Twi": "Da"
        })
        next_label = get_text("next", {
            "English": "Next",
            "Ewe": "Si kplɔe ɖo",
            "Ga": "Ni baaba",
            "Dagbani": "Din yɛn ti kana",
            "Hausa": "Na gaba",
            "Twi": "Deɛ ɛdi hɔ"
        })
        st.markdown(f"""
        <div class="mini-cycle-card" style="background:rgba(255,255,255,0.08); border-radius:16px; padding:0.8rem; margin:0.5rem 0; text-align:center; color:#F0E6EF;">
            <div style="font-size:1.5rem; font-weight:700;">{day_text} {current_cycle_day}</div>
            <span class="phase-badge" style="background:#5E3A4A; padding:0.4rem 1.5rem; border-radius:30px; font-weight:700;">{phase}</span>
            <small>📅 {next_label}: {next_date_str}</small>
        </div>
        """, unsafe_allow_html=True)

    # --- Legend with full hardcoded fallbacks for all five languages ---
    current_lang = st.session_state.get("language", "English")
    legend_map = {
        "English": {
            "title": "📖 Legend",
            "items": [
                "🔴 Actual period days",
                "🔴 Predicted period days",
                "🥚 Ovulation day",
                "🌸 Fertile window",
                "🟢 Custom events",
                "📋 Planner tasks",
                "🔔 Reminders",
                "🌟 Today's date",
                "⚫ No special event"
            ]
        },
        "Ewe": {
            "title": "📖 Dzesiwo – Nusiwo wonyɔ",
            "items": [
                "🔴 Ɛ̃ – Ɣleti siwo do",
                "🔴 Ɛ̃ gbã – Ɣleti siwo ado",
                "🥚 Babi – Ɣleti si me aɖewo le",
                "🌸 Aŋilika – Vidzidzi ɣeyiɣi",
                "🟢 Gade – Eyiadan siwo nètsɔ kpe ɖe eŋu",
                "📋 Babi – Dɔwɔwɔwo",
                "🔔 Ŋkuɖoɖo",
                "🌟 Sika – Egbea ŋkeke",
                "⚫ Babi – Nu aɖeke mele o"
            ]
        },
        "Ga": {
            "title": "📖 Atsirii – Nɔ ni akɛtsɔɔɔ",
            "items": [
                "🔴 Kɔkɔɔ – Yei anɔ gbɛji ni eba",
                "🔴 Kɔkɔɔ – Yei ni abaana",
                "🥚 Kɔkɔɔ – Ovulation gbɛkɛ",
                "🌸 Akutu – Gbekɛbii he be",
                "🟢 Aduadu – Nɔ́i ni oto",
                "📋 Kpã – Nitsumɔi",
                "🔔 Kaimɔi",
                "🌟 Sika kɔkɔɔ – Ŋmɛnɛ",
                "⚫ Kpã – Nɔ́ ko bɛ"
            ]
        },
        "Dagbani": {
            "title": "📮 Wuhiri – Di gbunni",
            "items": [
                "🔴 Zee – Biɛɣu din daa niŋ",
                "🔴 Zee – Biɛɣu din yɛn ti niŋ",
                "🥚 Pee – Ovulation dabisili",
                "🌸 Lam – Puu saha",
                "🟢 Bihi – A maŋa zaŋ",
                "📋 Zee – Tuma nima",
                "🔔 Teebu",
                "🌟 Anzari – Zuŋɔ dabisili",
                "⚫ Zee – Shɛli ka"
            ]
        },
        "Hausa": {
            "title": "📖 Alamar – Ma'anar alamomin",
            "items": [
                "🔴 Ja – Kwanakin al'ada na gaske",
                "🔴 Ja mai haske – Kwanakin al'ada da aka hasashen",
                "🥚 Purple – Ranar ovulation",
                "🌸 Orange – Tagar haihuwa",
                "🟢 Kore – Abubuwan da kuka ƙara",
                "📋 Dark – Ayyukan tsarawa",
                "🔔 Tunatarwa",
                "🌟 Zinariya – Ranar yau",
                "⚫ Ba abin mamaki ba"
            ]
        },
        "Twi": {
            "title": "📖 Ahyɛnsode – Nkyerɛkyerɛmu",
            "items": [
                "🔴 Kɔkɔɔ – Abosom nna a ɛbaa",
                "🔴 Kɔkɔɔ – Abosom nna a wɔhwɛ kwan",
                "🥚 Opepɔ – Ovulation da",
                "🌸 Anɔnsu – Awo mu ɛba",
                "🟢 Ahahan – Eyiadan a woaka ho",
                "📋 Sum – Dwumadie",
                "🔔 Nkaeɛ",
                "🌟 Sika kɔkɔɔ – Ɛnnɛ da",
                "⚫ Sum – Hwee nni hɔ"
            ]
        }
    }
    legend_data = legend_map.get(current_lang, legend_map["English"])
    with st.expander(legend_data["title"]):
        for item in legend_data["items"]:
            st.markdown(f"- {item}")

    # --- Weekday headers with fallbacks for all languages ---
    weekday_map = {
        "English": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "Ewe": ["Dzoɖa", "Braɖa", "Kuɖa", "Yawoɖa", "Fiɖa", "Memleɖa", "Kɔsiɖa"],
        "Ga": ["Ju", "Bla", "Ku", "Ya", "Fia", "Ho", "So"],
        "Dagbani": ["Tani", "Talata", "Larba", "Lamisi", "Alizama", "Sibiri", "Alahiri"],
        "Hausa": ["Lit", "Tal", "Lar", "Alg", "Jum", "Asa", "Lah"],
        "Twi": ["Dwo", "Ben", "Wuku", "Yaw", "Fida", "Mem", "Kwas"]
    }
    weekdays = weekday_map.get(current_lang, weekday_map["English"])

    # --- Hidden input and JavaScript (unchanged) ---
    st.text_input("", key="calendar_clicked_day", label_visibility="collapsed")

    js = """
    <script>
    function setDay(year, month, day) {
        var input = window.parent.document.querySelector('input[aria-label="calendar_clicked_day"]');
        if (input) {
            input.value = year + '-' + month + '-' + day;
            input.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)

    # --- HTML calendar grid (unchanged except weekday headers) ---
    html_grid = f"""
    <style>
    .calendar-grid {{
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 8px;
        margin-top: 15px;
    }}
    .calendar-day {{
        background-color: #3A2430;
        border-radius: 16px;
        padding: 12px 4px;
        text-align: center;
        font-weight: 500;
        transition: all 0.2s;
        color: #F0E6EF;
        cursor: pointer;
        min-height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 4px;
        font-size: 1rem;
        position: relative;
    }}
    .calendar-day:hover {{ transform: translateY(-3px); box-shadow: 0 6px 12px rgba(0,0,0,0.3); }}
    .calendar-day.period {{ background-color: #C28585; }}
    .calendar-day.predicted_period {{ background-color: #C28585; opacity: 0.6; }}
    .calendar-day.ovulation {{ background-color: #7B68EE; }}
    .calendar-day.fertile {{ background-color: #FFB347; color: #1B3B1B; }}
    .calendar-day.custom {{ background-color: #90EE90; }}
    .calendar-day.task {{ background-color: #5E3A4A; }}
    .calendar-day.reminder {{ background-color: #5E3AA0; }}
    .calendar-day.today {{ background-color: #FFD700; color: #2E1B2E; border: 2px solid white; }}
    .day-number {{ font-size: 1.3rem; font-weight: bold; }}
    .day-icon {{ font-size: 1.2rem; }}
    .reminder-tooltip {{
        visibility: hidden;
        background-color: #333;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px 10px;
        position: absolute;
        z-index: 1;
        bottom: 110%;
        left: 50%;
        transform: translateX(-50%);
        white-space: nowrap;
        font-size: 0.8rem;
    }}
    .calendar-day:hover .reminder-tooltip {{
        visibility: visible;
    }}
    </style>
    <div class="calendar-grid">
    """
    for header in weekdays:
        html_grid += f'<div style="text-align:center; font-weight:bold; background:#5E3A4A; padding:8px; border-radius:12px;">{header}</div>'

    for week in cal_matrix:
        for day in week:
            if day == 0:
                html_grid += '<div></div>'
                continue
            info = day_info.get(day, {})
            cell_type = info.get("type", "")
            icon = info.get("title", "")
            is_today = (year == today.year and month == today.month and day == today.day)
            cls = cell_type
            if is_today and not cell_type:
                cls = "today"
            elif is_today and cell_type:
                cls = cell_type + " today"
            onclick = f"setDay({year}, {month}, {day})"
            reminder_desc = info.get("reminder_desc", "") or info.get("reminder", {}).get("desc", "")
            tooltip_html = f'<span class="reminder-tooltip">{reminder_desc}</span>' if reminder_desc else ""
            html_grid += f'''
            <div class="calendar-day {cls}" onclick="{onclick}">
                <div class="day-number">{day}</div>
                <div class="day-icon">{icon}</div>
                {tooltip_html}
            </div>
            '''
    html_grid += "</div>"

    st.components.v1.html(html_grid, height=700, scrolling=False)

    # --- Process clicked day (unchanged) ---
    if st.session_state.calendar_clicked_day:
        try:
            parts = st.session_state.calendar_clicked_day.split('-')
            clicked = date(int(parts[0]), int(parts[1]), int(parts[2]))
            st.session_state.selected_cal_day = clicked
            st.session_state.show_calendar_log = True
            st.session_state.calendar_clicked_day = ""
            st.rerun()
        except:
            pass

    # --- Sidebar form (unchanged, uses t() with English fallback) ---
    if st.session_state.get("show_calendar_log"):
        with st.sidebar:
            st.subheader(f"📅 {t('log_for_date')} {st.session_state.selected_cal_day}")
            action = st.radio(t("choose_option"), [
                t("log_period_start"),
                t("log_symptom"),
                t("add_custom_event"),
                t("add_planner_task")
            ])
            if action == t("log_period_start"):
                dur = st.number_input(t("duration_days"), 1, 10, 5)
                if st.button(t("save_period")):
                    log_period_callback(st.session_state.selected_cal_day.isoformat(), dur, "", 0, "")
                    st.success(t("period_saved"))
                    st.session_state.show_calendar_log = False
                    st.rerun()
            elif action == t("add_custom_event"):
                title = st.text_input(t("event_title"))
                if st.button(t("save_event")):
                    add_event_callback(st.session_state.selected_cal_day.isoformat(), title, "custom")
                    st.success(t("event_added"))
                    st.session_state.show_calendar_log = False
                    st.rerun()
            elif action == t("log_symptom"):
                cramps = st.selectbox(t("cramps"), [t("none"), t("mild"), t("medium"), t("severe")])
                mood = st.selectbox(t("mood"), [t("neutral"), t("happy"), t("sad"), t("irritable")])
                flow = st.selectbox(t("flow"), [t("none_flow"), t("light"), t("normal"), t("heavy")])
                pain = st.slider(t("pain"), 1, 10, 1)
                energy = st.slider(t("energy"), 1, 5, 3)
                if st.button(t("save_symptom")):
                    log_symptom_callback(
                        st.session_state.selected_cal_day.isoformat(),
                        cramps, mood, flow, pain, energy,
                        t("no"), t("normal"), "", t("no"), ""
                    )
                    st.success(t("symptom_saved"))
                    st.session_state.show_calendar_log = False
                    st.rerun()
            elif action == t("add_planner_task") and add_planner_task_callback:
                task_text = st.text_input(t("task_description"))
                suggested_phase = st.selectbox(t("suggested_phase"), ["", t("phase_menstrual"), t("phase_follicular"), t("phase_ovulation"), t("phase_luteal")])
                user_type = st.selectbox(t("i_am"), [t("general"), t("student"), t("office_worker"), t("trader"), t("farmer")])
                if st.button(t("add_task")):
                    add_planner_task_callback(
                        st.session_state.selected_cal_day,
                        task_text,
                        suggested_phase or t("auto"),
                        user_type
                    )
                    st.success(t("task_added"))
                    st.session_state.show_calendar_log = False
                    st.rerun()
            if st.button(t("cancel")):
                st.session_state.show_calendar_log = False
                st.rerun()