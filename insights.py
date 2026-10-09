# insights.py – fully translated
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
from datetime import date, timedelta

def _build_daily_health_frame(symptoms, wellness, health_context=None):
    """Join the user's structured health logs by date; never ingest free text."""
    symptom_data = symptoms.copy() if symptoms is not None else pd.DataFrame()
    if "date" not in symptom_data:
        symptom_data = pd.DataFrame(columns=["date", "pain"])
    symptom_data["date"] = pd.to_datetime(symptom_data["date"], errors="coerce").dt.normalize()
    if "pain" not in symptom_data:
        symptom_data["pain"] = np.nan
    symptom_data["pain"] = pd.to_numeric(symptom_data["pain"], errors="coerce")
    symptom_data = (symptom_data.dropna(subset=["date", "pain"]).sort_values("date")
                    .drop_duplicates("date", keep="last"))

    wellness_data = wellness.copy() if wellness is not None else pd.DataFrame()
    if "date" not in wellness_data:
        wellness_data = pd.DataFrame({"date": pd.Series(dtype="datetime64[ns]")})
    wellness_data["date"] = pd.to_datetime(wellness_data["date"], errors="coerce").dt.normalize()
    for column in ["sleep_hours", "water_glasses", "exercise_minutes"]:
        if column not in wellness_data:
            wellness_data[column] = np.nan
        wellness_data[column] = pd.to_numeric(wellness_data[column], errors="coerce")
    wellness_data = wellness_data[["date", "sleep_hours", "water_glasses", "exercise_minutes"]]
    wellness_data = wellness_data.dropna(subset=["date"]).drop_duplicates("date", keep="last")

    daily = symptom_data.merge(wellness_data, on="date", how="left")
    context = health_context.copy() if isinstance(health_context, pd.DataFrame) else pd.DataFrame()
    if "date" in context:
        context["date"] = pd.to_datetime(context["date"], errors="coerce").dt.normalize()
        context = context.dropna(subset=["date"]).drop_duplicates("date", keep="last")
        context_columns = [column for column in context.columns if column != "date" and column not in daily.columns]
        daily = daily.merge(context[["date"] + context_columns], on="date", how="left")

    for standard, fallback in [("sleep_hours", "tracked_sleep_hours"),
                               ("water_glasses", "tracked_water_glasses"),
                               ("exercise_minutes", "tracked_exercise_minutes")]:
        if fallback in daily:
            daily[standard] = daily[standard].combine_first(pd.to_numeric(daily[fallback], errors="coerce"))
    if "energy" not in daily:
        daily["energy"] = np.nan
    daily["energy"] = pd.to_numeric(daily["energy"], errors="coerce")
    return daily.sort_values("date").reset_index(drop=True)


def _render_personal_ml_insight(user_id, cycles, recent_sym_func, load_wellness_func, t, health_context=None):
    """Fit and explain a per-user next-day higher-pain model from consecutive daily logs."""
    st.subheader(t("smart_ml_header"))
    st.caption(t("smart_ml_intro"))

    symptoms = recent_sym_func(user_id, 730)
    daily = _build_daily_health_frame(
        symptoms, load_wellness_func(user_id), health_context
    )
    if daily.empty:
        st.info(t("insight_log_symptoms_first"))
        return

    cycle_starts = []
    if cycles is not None and not cycles.empty and "start_date" in cycles:
        cycle_starts = (pd.to_datetime(cycles["start_date"], errors="coerce")
                        .dropna().sort_values().tolist())
    def get_cycle_day(day):
        earlier = [start for start in cycle_starts if start <= day]
        return (day - earlier[-1]).days + 1 if earlier else np.nan
    daily["cycle_day"] = daily["date"].apply(get_cycle_day)

    # For every day with a symptom log, use only that day's entries to estimate
    # whether the following calendar day's logged pain is high (6/10 or above).
    daily["next_date"] = daily["date"].shift(-1)
    daily["next_pain"] = pd.to_numeric(daily["pain"].shift(-1), errors="coerce")
    pairs = daily[(daily["next_date"] - daily["date"]).dt.days == 1].dropna(subset=["next_pain"]).copy()
    pairs["high_pain_next"] = (pairs["next_pain"] >= 6).astype(int)
    pair_count = len(pairs)
    high_count = int(pairs["high_pain_next"].sum())
    low_count = pair_count - high_count
    if pair_count < 40 or high_count < 8 or low_count < 8:
        st.info(t("smart_ml_data_needed").format(pairs=pair_count, high=high_count, low=low_count))
        return

    numeric_sources = {
        "previous_pain": "pain", "previous_energy": "energy", "previous_cycle_day": "cycle_day",
        "previous_sleep_hours": "sleep_hours", "previous_water_glasses": "water_glasses",
        "previous_exercise_minutes": "exercise_minutes", "previous_sleep_quality": "sleep_quality_rating",
        "previous_bbt_temperature": "bbt_temperature", "previous_custom_symptom_count": "custom_symptom_count",
    }
    categorical_sources = {
        "previous_mood": "mood", "previous_cramps": "cramps", "previous_flow": "flow",
        "previous_bloating": "bloating", "previous_appetite": "appetite", "previous_headache": "headache",
        "previous_skin": "skin", "previous_bleeding_intensity": "bleeding_intensity",
        "previous_anemia_symptoms": "anemia_symptoms", "previous_lower_back_pain": "lower_back_pain",
        "previous_breast_tenderness": "breast_tenderness", "previous_cervical_mucus": "mucus_type",
        "previous_ovulation_test": "ovulation_test_result",
    }
    raw_features = pd.DataFrame(index=pairs.index)
    for feature, source in numeric_sources.items():
        values = pairs[source] if source in pairs else pd.Series(np.nan, index=pairs.index)
        raw_features[feature] = pd.to_numeric(values, errors="coerce")
    for feature, source in categorical_sources.items():
        values = pairs[source] if source in pairs else pd.Series("Unknown", index=pairs.index)
        raw_features[feature] = values.fillna("Unknown").astype(str)

    y = pairs["high_pain_next"].astype(int).reset_index(drop=True)
    raw_features = raw_features.reset_index(drop=True)
    split_at = int(len(y) * 0.8)
    if split_at <= 0 or split_at >= len(y):
        st.info(t("smart_ml_unavailable"))
        return

    train_labels = y.iloc[:split_at]
    train_counts = train_labels.value_counts()
    if len(train_counts) < 2 or int(train_counts.min()) < 5:
        st.info(t("smart_ml_train_balance_needed"))
        return
    st.caption(t("smart_ml_sample_details").format(pairs=pair_count, high=high_count, low=low_count))

    # Remove features with no observed variation in the training period.
    numeric_features = [name for name in numeric_sources
                        if raw_features.loc[:split_at - 1, name].notna().any()
                        and raw_features.loc[:split_at - 1, name].nunique(dropna=True) > 1]
    categorical_features = [name for name in categorical_sources
                            if raw_features.loc[:split_at - 1, name].nunique(dropna=True) > 1]
    feature_names = numeric_features + categorical_features
    if not feature_names:
        st.info(t("smart_ml_unavailable"))
        return
    raw_features = raw_features[feature_names]

    def encode(frame):
        if not categorical_features:
            return frame.copy()
        return pd.get_dummies(frame, columns=categorical_features, prefix=categorical_features, dtype=int)

    train_encoded = encode(raw_features.iloc[:split_at])
    test_encoded = encode(raw_features.iloc[split_at:]).reindex(columns=train_encoded.columns, fill_value=0)
    medians = train_encoded[numeric_features].median().fillna(0) if numeric_features else pd.Series(dtype=float)
    train_x = train_encoded.fillna(medians).fillna(0)
    test_x = test_encoded.fillna(medians).fillna(0)
    test_y = y.iloc[split_at:]

    def make_model():
        return RandomForestClassifier(
            n_estimators=200, max_depth=6, min_samples_leaf=3,
            class_weight="balanced_subsample", random_state=23, n_jobs=1,
        )

    try:
        validation_model = make_model()
        validation_model.fit(train_x, train_labels)
        if test_y.nunique() > 1:
            score = balanced_accuracy_score(test_y, validation_model.predict(test_x))
            st.metric(t("smart_ml_backtest_label"), f"{score:.0%}")
            st.caption(t("smart_ml_backtest_details").format(count=len(test_y)))
        else:
            st.caption(t("smart_ml_backtest_unavailable"))

        full_encoded = encode(raw_features)
        full_medians = full_encoded[numeric_features].median().fillna(0) if numeric_features else pd.Series(dtype=float)
        full_x = full_encoded.fillna(full_medians).fillna(0)
        latest = daily.iloc[-1]
        future_values = {}
        for feature in numeric_features:
            source = numeric_sources[feature]
            future_values[feature] = pd.to_numeric(pd.Series([latest.get(source, np.nan)]), errors="coerce").iloc[0]
        for feature in categorical_features:
            source = categorical_sources[feature]
            value = latest.get(source, "Unknown")
            future_values[feature] = "Unknown" if pd.isna(value) else str(value)
        future_raw = pd.DataFrame([future_values])[feature_names]
        future_encoded = encode(future_raw).reindex(columns=full_encoded.columns, fill_value=0)
        future_x = future_encoded.fillna(full_medians).fillna(0)

        final_model = make_model()
        final_model.fit(full_x, y)
        class_index = list(final_model.classes_).index(1)
        likelihood = float(final_model.predict_proba(future_x)[0][class_index])
        forecast_date = daily.iloc[-1]["date"] + pd.Timedelta(days=1)
        st.metric(t("smart_ml_estimate_label"), f"{likelihood:.0%}")
        st.caption(t("smart_ml_estimate_date").format(date=daily.iloc[-1]["date"].strftime("%d %b %Y")))
        if forecast_date.date() < date.today():
            st.caption(t("smart_ml_stale_note"))

        st.markdown(f"**{t('smart_ml_drivers_header')}**")
        st.caption(t("smart_ml_drivers_intro"))
        importances = pd.Series(final_model.feature_importances_, index=full_encoded.columns).sort_values(ascending=False)
        leaders = [(name, float(value)) for name, value in importances.items() if value > 0][:3]
        for name, value in leaders:
            label = name.replace("_", " ")
            st.write(f"{label.title()} · {value:.0%}")
        st.caption(t("smart_ml_safety"))
    except (ValueError, TypeError, KeyError, IndexError):
        st.info(t("smart_ml_unavailable"))

def smart_insights_page(user_id, 
                        load_cycles_func, 
                        recent_sym_func, 
                        load_wellness_func, 
                        predict_func, 
                        cd_func,
                        t,
                        health_context_func=None,
                        wellness_score_func=None):
    """
    Displays personalised insights using the user's data.
    All visible strings are passed through t() for translation.
    """
    st.title(t("smart_insights_title"))
    st.markdown(t("smart_insights_subtitle"))
    
    cycles = load_cycles_func(user_id)
    all_symptoms = recent_sym_func(user_id, 3650)
    wellness_all = load_wellness_func(user_id)
    context = health_context_func(user_id) if health_context_func else {}
    if not isinstance(context, dict):
        context = {}
    health_context = context.get("daily", pd.DataFrame())
    counts = context.get("counts", {})

    st.subheader("Your connected health data")
    coverage_rows = [
        ("Cycle history", len(cycles)),
        ("Symptom Tracker days", len(all_symptoms)),
        ("Daily Wellness days", 0 if wellness_all is None else len(wellness_all)),
        ("Basal temperature readings", counts.get("bbt", 0)),
        ("Cervical mucus observations", counts.get("mucus", 0)),
        ("Ovulation tests", counts.get("ovulation", 0)),
        ("Separate sleep / water / exercise logs", counts.get("separate_trackers", 0)),
        ("Custom symptom entries", counts.get("custom_symptoms", 0)),
        ("Medication-log records", counts.get("medications", 0)),
        ("Product-use records", counts.get("product_usage", 0)),
        ("Product-inventory records", counts.get("inventory", 0)),
        ("Planner and calendar records", counts.get("planner_calendar", 0)),
        ("Reminder and private-note records", counts.get("reminders", 0) + counts.get("private_notes", 0)),
    ]
    with st.expander("Connected data sources", expanded=True):
        st.dataframe(pd.DataFrame(coverage_rows, columns=["Your data source", "Records available"]),
                     width="stretch", hide_index=True)
        st.caption("Date-matched cycle, symptom, wellness, custom-symptom, and body-sign logs inform exploratory analysis. Medication, product, planner, calendar, reminder, and private-note entries are shown as counts only. Message/community content and all free-text notes or titles are not read or used as health signals.")

    st.subheader("Your 7-day Wellness Score")
    wellness_summary = wellness_score_func(wellness_all) if wellness_score_func else None
    if wellness_summary is None or wellness_summary["score"] is None:
        st.info("Your Wellness Score is calculated in Wellness Insights from its daily sleep and water logs. Save a few logs there to see the score here.")
    else:
        component_values = wellness_summary["components"]
        component_labels = [("Sleep", component_values["sleep"]),
                            ("Hydration", component_values["hydration"])]
        lowest_component = min((item for item in component_labels if item[1] is not None), key=lambda item: item[1], default=("No component data", None))
        score_col, coverage_col, focus_col = st.columns(3)
        score_col.metric("Tracking score (0–100)", f"{wellness_summary['score']:.0f}",
                         delta=f"{wellness_summary['delta']:+.0f} vs prior week" if wellness_summary["delta"] is not None else None)
        coverage_col.metric("Logged days this week", f"{wellness_summary['days_logged']} / 7")
        focus_col.metric("Lowest tracked component", f"{lowest_component[0]} · {lowest_component[1]:.0f}/100" if lowest_component[1] is not None else "Not enough data")
        st.progress(max(0.0, min(1.0, wellness_summary["score"] / 100)))
        st.caption("This is the same 50/50 sleep-and-water score shown in Wellness Insights, calculated there from your daily logs. It is a personal tracking indicator, not a medical assessment.")
        if wellness_summary["days_logged"] < 4:
            st.info("Early estimate: log on at least 4 different days for a steadier weekly picture.")

    if cycles.empty:
        st.info(t("insight_log_period_first"))
        p = {"next": None, "last": None, "avg_cl": None, "cycle_count": 0, "ov": None}
        cd = None
    else:
        p = predict_func(user_id)
        cd = cd_func(p)

    # --- Next period prediction ---
    st.subheader(t("insight_next_period_header"))
    if p["next"]:
        delta = (p["next"] - date.today()).days
        if delta < 0:
            st.warning(t("insight_period_overdue").format(days=abs(delta)))
        elif delta == 0:
            st.success(t("insight_period_today"))
        else:
            st.info(t("insight_next_period_prediction").format(delta=delta, date=p['next'].strftime('%d %b %Y')))
        st.caption(t("insight_based_on_cycles").format(count=p['cycle_count'], avg=p['avg_cl']))
    else:
        st.info(t("insight_not_enough_cycles"))

    # --- Tomorrow's predicted symptoms ---
    st.subheader(t("insight_tomorrow_header"))
    if cd is None:
        st.info(t("insight_not_enough_data"))
    else:
        sym_df = recent_sym_func(user_id, 365)
        if sym_df.empty:
            st.info(t("insight_log_symptoms_first"))
        else:
            last_start = date.fromisoformat(cycles['start_date'].iloc[-1])
            sym_df['cycle_day'] = sym_df['date'].apply(lambda d: (date.fromisoformat(d) - last_start).days + 1)
            day_avg = sym_df.groupby('cycle_day')[['pain', 'energy']].mean().reset_index()
            tomorrow_cd = cd + 1
            row = day_avg[day_avg['cycle_day'] == tomorrow_cd]
            if not row.empty:
                col1, col2 = st.columns(2)
                col1.metric(t("predicted_pain"), f"{row['pain'].values[0]:.1f}/10")
                col2.metric(t("predicted_energy"), f"{row['energy'].values[0]:.1f}/5")
                pain_val = row['pain'].values[0]
                if pain_val > 6:
                    st.warning(t("high_pain_tomorrow_warning"))
                elif pain_val > 3:
                    st.info(t("moderate_pain_tomorrow"))
                else:
                    st.success(t("low_pain_tomorrow"))
            else:
                st.info(t("insight_insufficient_data"))

    _render_personal_ml_insight(user_id, cycles, recent_sym_func, load_wellness_func, t, health_context)

    # --- Date-matched wellness and next-day symptom associations ---
    st.subheader("Wellness and next-day symptom patterns")
    sym_df = recent_sym_func(user_id, 730)
    wellness_df = load_wellness_func(user_id)
    if sym_df.empty:
        st.info(t("insight_log_symptoms_first"))
    else:
        merged = _build_daily_health_frame(sym_df, wellness_df, health_context)
        if len(merged) < 11:
            st.info("Log more daily symptoms and wellness details to review personal patterns; at least 10 consecutive next-day pairs are required.")
        else:
            merged["next_date"] = merged["date"].shift(-1)
            merged["next_pain"] = pd.to_numeric(merged["pain"].shift(-1), errors="coerce")
            pairs = merged[(merged["next_date"] - merged["date"]).dt.days == 1].dropna(subset=["next_pain"])
            factors = ["sleep_hours", "water_glasses", "exercise_minutes", "sleep_quality_rating",
                       "bbt_temperature", "custom_symptom_count"]
            rows = []
            for factor in factors:
                if factor not in pairs:
                    continue
                valid = pairs[[factor, "next_pain"]].apply(pd.to_numeric, errors="coerce").dropna()
                if len(valid) >= 10 and valid[factor].nunique() > 1 and valid["next_pain"].nunique() > 1:
                    rows.append({"Logged factor": factor.replace("_", " ").title(),
                                 "Correlation with next-day pain": round(float(valid[factor].corr(valid["next_pain"])), 2),
                                 "Consecutive day pairs": len(valid)})
            if rows:
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
                st.caption("These are personal, descriptive associations only. They do not establish causes, diagnoses, or treatment advice.")
            else:
                st.info("There are not yet 10 consecutive day-pairs with varied, matched measurements for a reliable comparison.")

    # --- Irregularity impact on energy ---
    st.subheader(t("insight_irregularity_impact_header"))
    if len(cycles) < 3:
        st.info(t("insight_log_three_cycles"))
    else:
        cycles = cycles.sort_values('start_date')
        cycles['cycle_length'] = pd.to_numeric(cycles['cycle_length'], errors='coerce')
        cycles = cycles.dropna(subset=['cycle_length'])
        if len(cycles) >= 3:
            cycles['var'] = cycles['cycle_length'].rolling(3, min_periods=2).std()
            cycles['cycle_num'] = range(1, len(cycles)+1)
            sym_df = recent_sym_func(user_id, 500)
            sym_df['date'] = pd.to_datetime(sym_df['date'])
            cycles['start_date'] = pd.to_datetime(cycles['start_date'])
            cycle_energy = []
            for idx, row in cycles.iterrows():
                start = row['start_date']
                next_start = cycles[cycles['start_date'] > start]['start_date'].min() if idx < len(cycles)-1 else start + timedelta(days=40)
                mask = (sym_df['date'] >= start) & (sym_df['date'] < next_start)
                cycle_sym = sym_df[mask]
                if not cycle_sym.empty:
                    cycle_energy.append({
                        'cycle_num': row['cycle_num'],
                        'variability': row['var'],
                        'avg_energy': cycle_sym['energy'].mean()
                    })
            if cycle_energy:
                impact_df = pd.DataFrame(cycle_energy)
                fig, ax = plt.subplots(figsize=(8,4))
                ax.plot(impact_df['cycle_num'], impact_df['variability'], 'o-', label=t("variability_label"), color='purple', linewidth=2)
                ax.set_xlabel(t("cycle_number_label"))
                ax.set_ylabel(t("variability_days_label"), color='purple')
                ax2 = ax.twinx()
                ax2.plot(impact_df['cycle_num'], impact_df['avg_energy'], 's-', label=t("avg_energy_label"), color='green', linewidth=2)
                ax2.set_ylabel(t("avg_energy_scale_label"), color='green')
                ax.legend(loc='upper left')
                ax2.legend(loc='upper right')
                st.pyplot(fig)
                if len(impact_df) > 1:
                    if impact_df['avg_energy'].nunique(dropna=True) > 1 and impact_df['variability'].nunique(dropna=True) > 1:
                        corr = impact_df['avg_energy'].corr(impact_df['variability'])
                        if corr < -0.4:
                            st.warning(t("irregularity_energy_warning").format(corr=corr))
                        else:
                            st.info(t("irregularity_energy_ok").format(max_var=impact_df['variability'].max()))
                    else:
                        st.info(t("insight_log_daily_symptoms"))
            else:
                st.info(t("insight_log_daily_symptoms"))

    # --- Mood distribution (nicer pie chart) ---
    st.subheader(t("mood_insight_header"))
    sym_df = recent_sym_func(user_id, 90)
    if sym_df.empty:
        st.info(t("insight_log_moods"))
    else:
        mood_counts = sym_df['mood'].value_counts()
        if not mood_counts.empty:
            mood_colors = {
                "Happy": "#FFD966",
                "Neutral": "#A0AAB5",
                "Sad": "#6C8EBF",
                "Irritable": "#E68A8A"
            }
            colors = [mood_colors.get(m, "#C28585") for m in mood_counts.index]
            fig2, ax2 = plt.subplots(figsize=(7,7))
            wedges, texts, autotexts = ax2.pie(
                mood_counts.values, 
                labels=None,
                autopct='%1.0f%%', 
                colors=colors, 
                startangle=90,
                wedgeprops={'edgecolor': 'white', 'linewidth': 1.5},
                textprops={'fontsize': 11, 'color': 'black'}
            )
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(12)
            ax2.legend(wedges, mood_counts.index,
                       title=t("mood_distribution_title"),
                       loc="center left",
                       bbox_to_anchor=(1, 0, 0.5, 1),
                       frameon=True, fancybox=True, shadow=True)
            ax2.set_title(t("mood_distribution_title"), fontsize=14, fontweight='bold')
            st.pyplot(fig2)
            top_mood = mood_counts.idxmax()
            st.info(t("most_common_mood_insight").format(mood=top_mood))

    # --- Cycle length trend ---
    st.subheader(t("cycle_trend_header"))
    cycles = load_cycles_func(user_id)
    if len(cycles) >= 2:
        cycles = cycles.sort_values('start_date')
        cycles['cycle_num'] = range(1, len(cycles)+1)
        fig3, ax3 = plt.subplots(figsize=(8,4))
        ax3.plot(cycles['cycle_num'], cycles['cycle_length'], 'o-', color='#C28585', markersize=6)
        ax3.axhline(y=cycles['cycle_length'].mean(), color='gray', linestyle='--', label=t("average_label_cycle").format(avg=cycles['cycle_length'].mean()))
        ax3.set_xlabel(t("cycle_number_label"))
        ax3.set_ylabel(t("cycle_length_days"))
        ax3.legend()
        ax3.grid(True, linestyle='--', alpha=0.3)
        st.pyplot(fig3)
        if len(cycles) >= 3:
            first = cycles['cycle_length'].iloc[0]
            last = cycles['cycle_length'].iloc[-1]
            change = last - first
            if change > 3:
                st.warning(t("cycle_lengthening").format(change=change))
            elif change < -3:
                st.warning(t("cycle_shortening").format(change=abs(change)))
            else:
                st.success(t("cycle_stable_insight"))
    else:
        st.info(t("insight_log_two_cycles"))

    # --- Wellness score over time ---
    st.subheader(t("wellness_score_header"))
    wellness_history = (wellness_summary or {}).get("recent_history", pd.DataFrame(columns=["date", "score"]))
    if wellness_history is None or wellness_history.empty:
        st.info(t("insight_log_wellness_weekly"))
    else:
        wellness_history = wellness_history.sort_values("date")
        fig4, ax4 = plt.subplots(figsize=(10,4))
        ax4.plot(wellness_history["date"], wellness_history["score"], "o-", color="teal")
        ax4.fill_between(wellness_history["date"], wellness_history["score"], alpha=0.2, color="teal")
        ax4.set_ylim(0, 100)
        ax4.set_ylabel(t("wellness_score"))
        ax4.set_xlabel(t("date_label"))
        ax4.grid(True, linestyle='--', alpha=0.3)
        st.pyplot(fig4)
        if wellness_summary["delta"] is not None:
            if wellness_summary["delta"] >= 5:
                st.success(t("wellness_improving"))
            elif wellness_summary["delta"] <= -5:
                st.warning(t("wellness_declining"))
            else:
                st.info(t("wellness_stable"))
