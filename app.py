import streamlit as st

st.set_page_config(
    page_title="SitRight",
    page_icon="🪑",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("SitRight")
st.markdown("#### AI-powered posture monitoring for your desk setup")

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("##### 📹 Monitor")
    st.write(
        "Start a live monitoring session. "
        "Calibrate your posture baseline and get "
        "real-time feedback and alerts."
    )

with col2:
    st.markdown("##### 📊 Analytics")
    st.write(
        "View your posture history. "
        "See good vs bad posture time, "
        "alert trends, and session scores."
    )

with col3:
    st.markdown("##### ⚙️ Settings")
    st.write(
        "Adjust alert sensitivity, "
        "alert delay, sound, and "
        "notification preferences."
    )

st.markdown("---")
st.caption("Use the sidebar to navigate between pages.")
