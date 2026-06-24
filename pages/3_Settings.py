import streamlit as st
import json
import os

SETTINGS_PATH = "data/settings.json"

st.set_page_config(
    page_title="SitRight — Settings",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Settings")
st.caption("Adjust how SitRight monitors and alerts you.")

# ------------------------------------------------------------------ #
#  Load existing settings or use defaults                              #
# ------------------------------------------------------------------ #
DEFAULT_SETTINGS = {
    "sensitivity":        5,
    "alert_delay_secs":   20,
    "cooldown_secs":      60,
    "sound_enabled":      True,
    "notifications_enabled": True,
    "good_threshold":     75,
}


def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_PATH, "r") as f:
            saved = json.load(f)
        # Merge with defaults so new keys added later always exist
        merged = DEFAULT_SETTINGS.copy()
        merged.update(saved)
        return merged
    except (json.JSONDecodeError, IOError):
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    os.makedirs("data", exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)


current = load_settings()

# ------------------------------------------------------------------ #
#  Form                                                                #
# ------------------------------------------------------------------ #
st.markdown("#### Detection sensitivity")

sensitivity = st.slider(
    "Sensitivity",
    min_value=1,
    max_value=10,
    value=current["sensitivity"],
    step=1,
    help="Higher = stricter. Score drops faster on small deviations. "
         "Start at 5 and adjust if alerts fire too often or not enough."
)

good_threshold = st.slider(
    "Good posture threshold",
    min_value=50,
    max_value=95,
    value=current["good_threshold"],
    step=5,
    help="Score above this is considered good posture. "
         "Lower if alerts fire too often. Raise if they fire too rarely."
)

st.markdown("---")
st.markdown("#### Alert behaviour")

alert_delay = st.slider(
    "Alert after N seconds of bad posture",
    min_value=5,
    max_value=60,
    value=current["alert_delay_secs"],
    step=5,
    help="How long you must be in bad posture before an alert fires. "
         "15–25 seconds is a good starting range."
)

cooldown = st.slider(
    "Minimum seconds between alerts",
    min_value=15,
    max_value=180,
    value=current["cooldown_secs"],
    step=15,
    help="Prevents alert spam. 60 seconds is recommended."
)

st.markdown("---")
st.markdown("#### Alert types")

sound_on = st.toggle(
    "Sound alert",
    value=current["sound_enabled"],
    help="Plays assets/alert.wav when an alert fires."
)

notif_on = st.toggle(
    "Desktop notification",
    value=current["notifications_enabled"],
    help="Shows an OS desktop notification when an alert fires."
)

st.markdown("---")

# ------------------------------------------------------------------ #
#  Save button                                                         #
# ------------------------------------------------------------------ #
if st.button("Save settings", type="primary"):
    new_settings = {
        "sensitivity":           sensitivity,
        "alert_delay_secs":      alert_delay,
        "cooldown_secs":         cooldown,
        "sound_enabled":         sound_on,
        "notifications_enabled": notif_on,
        "good_threshold":        good_threshold,
    }
    save_settings(new_settings)
    st.success(
        f"Settings saved. "
        f"Sensitivity: {sensitivity} | "
        f"Alert after: {alert_delay}s | "
        f"Cooldown: {cooldown}s"
    )
    st.session_state.settings_saved = True

# Reset to defaults button
if st.button("Reset to defaults"):
    save_settings(DEFAULT_SETTINGS.copy())
    st.info("Settings reset to defaults. Refresh the page to see them.")
