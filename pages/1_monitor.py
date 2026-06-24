import cv2
import time
import streamlit as st
import mediapipe as mp

from monitoring.monitor import (
    init_session,
    stop_session,
    update_session,
    format_duration,
    get_session_summary,
)
from alerts.notifier import send_alert, reset_cooldown, seconds_until_next_alert
from posture.analyzer import extract_landmarks, compute_deviation_score
from calibration.calibrate import calibrate, load_baseline
from analytics import log_session, load_analytics

import json
import os


def _load_settings():
    defaults = {
        "sensitivity":           5,
        "alert_delay_secs":      20,
        "cooldown_secs":         60,
        "sound_enabled":         True,
        "notifications_enabled": True,
        "good_threshold":        75,
    }
    path = "data/settings.json"
    if not os.path.exists(path):
        return defaults
    try:
        with open(path, "r") as f:
            saved = json.load(f)
        defaults.update(saved)
        return defaults
    except (json.JSONDecodeError, IOError):
        return defaults


# ------------------------------------------------------------------ #
#  Page config                                                         #
# ------------------------------------------------------------------ #
st.set_page_config(
    page_title="SitRight — Monitor",
    page_icon="📹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------ #
#  MediaPipe — initialised once at module level, not inside the loop  #
# ------------------------------------------------------------------ #
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# ------------------------------------------------------------------ #
#  Session state defaults                                              #
# ------------------------------------------------------------------ #
for key, default in {
    "running":     False,
    "calibrating": False,
    "good_secs":   0.0,
    "bad_secs":    0.0,
    "alert_count": 0,
    "bad_timer":   0.0,
    "last_score":  None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ------------------------------------------------------------------ #
#  Sidebar                                                             #
# ------------------------------------------------------------------ #
st.sidebar.header("SitRight")

start_btn = st.sidebar.button(
    "▶  Start monitoring",  disabled=st.session_state.running)
stop_btn = st.sidebar.button(
    "■  Stop monitoring",   disabled=not st.session_state.running)
calibrate_btn = st.sidebar.button(
    "◎  Calibrate posture", disabled=not st.session_state.running)

# Load settings once per run
settings = _load_settings()
st.session_state.alert_delay = settings["alert_delay_secs"]
st.session_state.good_threshold = settings["good_threshold"]

st.sidebar.markdown("---")

# Baseline status in sidebar
baseline = load_baseline()
if baseline:
    st.sidebar.success(
        f"Baseline ready  \n"
        f"Neck angle: {baseline['neck_angle']:.1f}°  \n"
        f"Shoulder tilt: {baseline['shoulder_tilt']:.4f}"
    )
else:
    st.sidebar.warning("No baseline. Start monitoring then calibrate.")

st.sidebar.markdown("---")
st.sidebar.caption("Session stats")
good_placeholder = st.sidebar.empty()
bad_placeholder = st.sidebar.empty()
alert_placeholder_sidebar = st.sidebar.empty()

# ------------------------------------------------------------------ #
#  Main area layout                                                    #
# ------------------------------------------------------------------ #
st.title("Live monitor")

col_feed, col_stats = st.columns([3, 1])

with col_feed:
    frame_placeholder = st.empty()

with col_stats:
    st.markdown("#### Posture score")
    score_placeholder = st.empty()
    status_placeholder = st.empty()
    st.markdown("---")
    st.markdown("#### Angles (live)")
    neck_placeholder = st.empty()
    shoulder_placeholder = st.empty()

# ------------------------------------------------------------------ #
#  Button state transitions                                            #
# ------------------------------------------------------------------ #
if start_btn:
    st.session_state.running = True
    init_session(st)
    reset_cooldown()
    st.rerun()

if stop_btn:
    summary = get_session_summary(st)
    saved = log_session(summary)

    if saved:
        st.sidebar.success(
            f"Session saved  \n"
            f"Duration: {format_duration(summary['total_secs'])}  \n"
            f"Good posture: {summary['good_pct']}%"
        )
    else:
        st.sidebar.warning("Session too short to save (under 5 seconds).")

    stop_session(st)
    st.rerun()

if calibrate_btn:
    st.session_state.calibrating = True

# ------------------------------------------------------------------ #
#  Monitoring loop                                                     #
# ------------------------------------------------------------------ #
if st.session_state.running:

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error(
            "Webcam not found. Make sure it is connected and not used by another app.")
        st.session_state.running = False
        st.stop()

    # Reload baseline inside the loop block so calibration updates take effect
    baseline = load_baseline()

    if baseline is None:
        st.warning(
            "No baseline found. Press **◎ Calibrate posture** in the sidebar first.")

    with mp_pose.Pose(
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose:

        while st.session_state.running:

            ret, frame = cap.read()
            if not ret:
                st.error("Lost webcam feed. Check your connection.")
                break

            # ---- Frame prep ----------------------------------------
            frame = cv2.resize(frame, (640, 480))
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # ---- Pose detection ------------------------------------
            results = pose.process(rgb_frame)

            # ---- Draw skeleton ------------------------------------
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    rgb_frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing.DrawingSpec(
                        color=(0, 255, 0), thickness=4, circle_radius=4
                    ),
                    connection_drawing_spec=mp_drawing.DrawingSpec(
                        color=(255, 255, 255), thickness=2
                    ),
                )

            # ---- Display frame ------------------------------------
            frame_placeholder.image(
                rgb_frame, channels="RGB", use_container_width=True)

            # ---- Calibration mid-session -------------------------
            if st.session_state.calibrating:
                status_placeholder.warning(
                    "Calibrating — sit up straight and stay still...")
                success, message = calibrate(cap, pose)
                st.session_state.calibrating = False

                if success:
                    baseline = load_baseline()
                    status_placeholder.success(f"✓ {message}")
                else:
                    status_placeholder.error(f"✗ {message}")
                continue

            # ---- Landmark extraction + scoring -------------------
            landmarks = extract_landmarks(results)

            if landmarks is None or baseline is None:
                score_placeholder.metric("Score", "—")
                status_placeholder.info(
                    "Make sure your ears and shoulders are visible.")
                neck_placeholder.caption("Neck angle: —")
                shoulder_placeholder.caption("Shoulder tilt: —")
                continue

            score = compute_deviation_score(
                landmarks, baseline,
                sensitivity=settings["sensitivity"]
            )
            st.session_state.last_score = score

            # ---- Score display ------------------------------------
            score_placeholder.metric(
                label="Score",
                value=f"{score}/100",
                delta=None
            )

            # ---- Status color ------------------------------------
            if score >= 75:
                status_placeholder.success("Good posture")
            elif score >= 50:
                status_placeholder.warning("Posture slipping")
            else:
                status_placeholder.error("Sit up straight")

            # ---- Live angle readout ------------------------------
            from posture.analyzer import compute_live_angles
            live_angles = compute_live_angles(landmarks)
            neck_placeholder.caption(
                f"Neck angle: {live_angles['neck_angle']:.1f}°  "
                f"(baseline {baseline['neck_angle']:.1f}°)"
            )
            shoulder_placeholder.caption(
                f"Shoulder tilt: {live_angles['shoulder_tilt']:.4f}  "
                f"(baseline {baseline['shoulder_tilt']:.4f})"
            )

            # ---- Session update via monitor.py-----------------------------------
            stats = update_session(st, score)
            # ---- Sidebar session stats ---------------------------
            good_placeholder.metric(
                "Good posture", format_duration(stats["good_secs"])
            )

            bad_placeholder.metric(
                "Bad posture", format_duration(stats["bad_secs"])
            )
            alert_placeholder_sidebar.metric(
                "Alerts fired", stats["alert_count"]
            )
            # Show cooldown remaining so user knows when next alert can fire
            cooldown_remaining = seconds_until_next_alert()
            if cooldown_remaining > 0:
                st.sidebar.caption(f"Next alert in {cooldown_remaining}s")

            # ---- Alert trigger (notifier wired in next block) ----
            if stats["should_alert"]:
                fired = send_alert(
                    title="SitRight — posture alert",
                    message="You have been slouching. Sit up straight and roll your shoulders back."
                )
                if fired:
                    status_placeholder.warning("Alert sent — sit up straight!")

    cap.release()

else:
    # ---- Not running state ---------------------------------------
    frame_placeholder.info(
        "Press **▶ Start monitoring** in the sidebar to begin.")
    score_placeholder.metric("Score", "—")
