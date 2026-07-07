# insights.py – fully translated
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import date, timedelta

def smart_insights_page(user_id, 
                        load_cycles_func, 
                        recent_sym_func, 
                        load_wellness_func, 
                        predict_func, 
                        cd_func,
                        t):
    """
    Displays personalised insights using the user's data.
    All visible strings are passed through t() for translation.
    """
    st.title(t("smart_insights_title"))
    st.markdown(t("smart_insights_subtitle"))
    
    cycles = load_cycles_func(user_id)
    if cycles.empty:
        st.info(t("insight_log_period_first"))
        return

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

    # --- Trigger detection ---
    st.subheader(t("insight_triggers_header"))
    sym_df = recent_sym_func(user_id, 60)
    wellness_df = load_wellness_func(user_id)
    if sym_df.empty or wellness_df.empty:
        st.info(t("insight_log_wellness_first"))
    else:
        sym_df['date'] = pd.to_datetime(sym_df['date'])
        wellness_df['date'] = pd.to_datetime(wellness_df['date'])
        merged = pd.merge(sym_df, wellness_df, on='date', how='inner')
        if len(merged) < 5:
            st.info(t("insight_need_more_combined_data"))
        else:
            merged = merged.sort_values('date')
            merged['next_pain'] = merged['pain'].shift(-1)
            merged = merged.dropna(subset=['next_pain'])
            if len(merged) > 3:
                factors = ['sleep_hours', 'water_glasses', 'exercise_minutes']
                corr_pain = {}
                for f in factors:
                    corr_pain[f] = merged[f].corr(merged['next_pain'])
                st.write(t("correlation_explanation"))
                df_corr = pd.DataFrame({
                    t("factor_column"): [t("sleep_hours_label"), t("water_glasses_label"), t("exercise_minutes_label")],
                    t("correlation_column"): [corr_pain['sleep_hours'], corr_pain['water_glasses'], corr_pain['exercise_minutes']]
                })
                st.dataframe(df_corr, use_container_width=True)
                
                bad_triggers = []
                for f in factors:
                    if corr_pain[f] < -0.3:
                        bad_triggers.append(t("trigger_format_low").format(factor=f.replace('_', ' ')))
                if bad_triggers:
                    st.warning(t("triggers_found_prefix") + "\n" + "\n".join([f"- {tr}" for tr in bad_triggers]))
                else:
                    st.success(t("no_triggers_found"))
            else:
                st.info(t("insight_need_more_sequential_data"))

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
                    corr = impact_df['avg_energy'].corr(impact_df['variability'])
                    if corr < -0.4:
                        st.warning(t("irregularity_energy_warning").format(corr=corr))
                    else:
                        st.info(t("irregularity_energy_ok").format(max_var=impact_df['variability'].max()))
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
    wellness_df = load_wellness_func(user_id)
    if wellness_df.empty or len(wellness_df) < 7:
        st.info(t("insight_log_wellness_weekly"))
    else:
        wellness_df['date'] = pd.to_datetime(wellness_df['date'])
        wellness_df = wellness_df.sort_values('date')
        wellness_df['score'] = (wellness_df['water_glasses'] / 8 * 25) + (wellness_df['sleep_hours'] / 8 * 25) + (wellness_df['exercise_minutes'] / 30 * 25) + 25
        wellness_df['score'] = wellness_df['score'].clip(0, 100)
        fig4, ax4 = plt.subplots(figsize=(10,4))
        ax4.plot(wellness_df['date'], wellness_df['score'], 'o-', color='teal')
        ax4.fill_between(wellness_df['date'], wellness_df['score'], alpha=0.2, color='teal')
        ax4.set_ylabel(t("wellness_score"))
        ax4.set_xlabel(t("date_label"))
        ax4.grid(True, linestyle='--', alpha=0.3)
        st.pyplot(fig4)
        if len(wellness_df) >= 3:
            x = np.arange(len(wellness_df))
            slope = np.polyfit(x, wellness_df['score'], 1)[0]
            if slope > 0.5:
                st.success(t("wellness_improving"))
            elif slope < -0.5:
                st.warning(t("wellness_declining"))
            else:
                st.info(t("wellness_stable"))