import streamlit as st
import pandas as pd
import os
from analytics import load_analytics, get_recent_sessions
from monitoring.monitor import format_duration

st.set_page_config(
    page_title="SitRight — Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Analytics")
st.caption("Your posture history across all sessions.")

# ------------------------------------------------------------------ #
#  Refresh button — re-reads analytics.json without full page reload  #
# ------------------------------------------------------------------ #
if st.button("↻  Refresh"):
    st.rerun()

# ------------------------------------------------------------------ #
#  Load data                                                           #
# ------------------------------------------------------------------ #
data = load_analytics()
sessions = data.get("sessions", [])

# ------------------------------------------------------------------ #
#  Empty state — shown when no sessions exist yet                      #
# ------------------------------------------------------------------ #
if len(sessions) == 0:
    st.info(
        "No sessions recorded yet.  \n"
        "Go to the **Monitor** page, run a session of at least 5 seconds, "
        "press Stop, then come back here."
    )
    st.stop()

# ------------------------------------------------------------------ #
#  Build DataFrame — handle missing columns from old sessions          #
# ------------------------------------------------------------------ #
df = pd.DataFrame(sessions)

# Guarantee all expected columns exist with safe fallback values
expected_columns = {
    "date":        "Unknown",
    "time":        "—",
    "good_secs":   0.0,
    "bad_secs":    0.0,
    "total_secs":  0.0,
    "alert_count": 0,
    "avg_score":   0.0,
    "good_pct":    0.0,
}
for col, fallback in expected_columns.items():
    if col not in df.columns:
        df[col] = fallback

# Convert seconds to minutes for charts
df["good_mins"] = (df["good_secs"] / 60).round(2)
df["bad_mins"] = (df["bad_secs"] / 60).round(2)

# Add a session number column for x-axis when dates repeat
df["session_num"] = [f"#{i+1}" for i in range(len(df))]

# ------------------------------------------------------------------ #
#  Compute summary stats safely                                        #
# ------------------------------------------------------------------ #
total_good = float(df["good_secs"].sum())
total_bad = float(df["bad_secs"].sum())
total_time = float(df["total_secs"].sum())
total_alerts = int(df["alert_count"].sum())
avg_score = round(float(df["avg_score"].mean()), 1) if len(df) > 0 else 0.0
overall_pct = round((total_good / total_time * 100)
                    if total_time > 0 else 0.0, 1)
best_session = df.loc[df["good_pct"].idxmax()]
best_pct = round(float(best_session["good_pct"]), 1)

# ------------------------------------------------------------------ #
#  Summary metric cards                                                #
# ------------------------------------------------------------------ #
st.markdown("#### Overall summary")

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric(
    "Sessions",
    len(sessions)
)
col2.metric(
    "Good posture time",
    format_duration(total_good)
)
col3.metric(
    "Bad posture time",
    format_duration(total_bad)
)
col4.metric(
    "Overall good %",
    f"{overall_pct}%"
)
col5.metric(
    "Total alerts",
    total_alerts
)
col6.metric(
    "Avg score",
    f"{avg_score}/100"
)

# Best session callout
st.success(
    f"Best session: {best_session['date']} at {best_session['time']} "
    f"— {best_pct}% good posture"
)

st.markdown("---")

# ------------------------------------------------------------------ #
#  Chart 1 — Good vs bad posture per session                           #
# ------------------------------------------------------------------ #
st.markdown("#### Good vs bad posture per session (minutes)")
st.caption(
    "Each bar is one session. "
    "Green = good posture time. Red = bad posture time."
)

if len(df) > 0:
    chart1_df = df[["session_num", "good_mins", "bad_mins"]].copy()
    chart1_df = chart1_df.rename(columns={
        "session_num": "Session",
        "good_mins":   "Good posture (min)",
        "bad_mins":    "Bad posture (min)",
    })
    chart1_df = chart1_df.set_index("Session")
    st.bar_chart(chart1_df, use_container_width=True, height=300)
else:
    st.info("No data to display.")

st.markdown("---")

# ------------------------------------------------------------------ #
#  Chart 2 — Posture score trend                                       #
# ------------------------------------------------------------------ #
st.markdown("#### Posture score trend (avg per session)")
st.caption(
    "Higher is better. "
    "A rising trend means your posture is improving over time."
)

if len(df) > 0 and df["avg_score"].sum() > 0:
    chart2_df = df[["session_num", "avg_score"]].copy()
    chart2_df = chart2_df.rename(columns={
        "session_num": "Session",
        "avg_score":   "Avg score",
    })
    chart2_df = chart2_df.set_index("Session")
    st.line_chart(chart2_df, use_container_width=True, height=250)
else:
    st.info("Score data not available. Run a new session to see this chart.")

st.markdown("---")

# ------------------------------------------------------------------ #
#  Chart 3 — Alerts per session                                        #
# ------------------------------------------------------------------ #
st.markdown("#### Alerts per session")
st.caption("Fewer alerts over time = your posture habits are improving.")

if len(df) > 0:
    chart3_df = df[["session_num", "alert_count"]].copy()
    chart3_df = chart3_df.rename(columns={
        "session_num":  "Session",
        "alert_count":  "Alerts",
    })
    chart3_df = chart3_df.set_index("Session")
    st.line_chart(chart3_df, use_container_width=True, height=250)
else:
    st.info("No alert data yet.")

st.markdown("---")

# ------------------------------------------------------------------ #
#  Chart 4 — Good posture % per session                                #
# ------------------------------------------------------------------ #
st.markdown("#### Good posture % per session")
st.caption("Aim to keep this above 70% consistently.")

if len(df) > 0:
    chart4_df = df[["session_num", "good_pct"]].copy()
    chart4_df = chart4_df.rename(columns={
        "session_num": "Session",
        "good_pct":    "Good posture %",
    })
    chart4_df = chart4_df.set_index("Session")
    st.line_chart(chart4_df, use_container_width=True, height=250)
else:
    st.info("No data yet.")

st.markdown("---")

# ------------------------------------------------------------------ #
#  Recent sessions table                                               #
# ------------------------------------------------------------------ #
st.markdown("#### Session history")
st.caption(f"Showing all {len(sessions)} sessions, most recent first.")

recent = get_recent_sessions(n=len(sessions))

if recent:
    table_df = pd.DataFrame(recent)

    # Guarantee columns exist before selecting them
    for col, fallback in expected_columns.items():
        if col not in table_df.columns:
            table_df[col] = fallback

    # Format duration column
    table_df["Duration"] = table_df["total_secs"].apply(format_duration)

    # Select and rename for display
    display_df = table_df[[
        "date", "time", "Duration",
        "good_pct", "avg_score", "alert_count"
    ]].copy()

    display_df = display_df.rename(columns={
        "date":        "Date",
        "time":        "Time",
        "good_pct":    "Good posture %",
        "avg_score":   "Avg score",
        "alert_count": "Alerts",
    })

    # Highlight good_pct column — green if above 70, red if below 50
    def highlight_good_pct(val):
        try:
            v = float(val)
            if v >= 70:
                return "color: #3B6D11"
            elif v < 50:
                return "color: #A32D2D"
            return ""
        except (ValueError, TypeError):
            return ""

    styled = display_df.style.map(
        highlight_good_pct,
        subset=["Good posture %"]
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)

# ------------------------------------------------------------------ #
#  Danger zone — clear all data                                        #
# ------------------------------------------------------------------ #
st.markdown("---")
with st.expander("⚠️  Danger zone"):
    st.warning(
        "Deleting your analytics data is permanent. "
        "This cannot be undone."
    )
    confirm = st.checkbox(
        "I understand this will delete all my session history")
    if st.button("Delete all analytics data", disabled=not confirm):
        if os.path.exists("data/analytics.json"):
            os.remove("data/analytics.json")
        st.success("All analytics data deleted.")
        st.rerun()
