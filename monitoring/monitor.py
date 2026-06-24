import time


# ------------------------------------------------------------------ #
#  Constants                                                           #
# ------------------------------------------------------------------ #
GOOD_THRESHOLD = 75     # score >= this is considered good posture
ALERT_DELAY_SECS = 7    # seconds of continuous bad posture before alert fires


# ------------------------------------------------------------------ #
#  Session state initialisation                                        #
# ------------------------------------------------------------------ #
def init_session(st):
    """
    Sets all session tracking keys to their starting values.
    Call this once when the user presses Start.
    Safe to call multiple times — only sets keys that don't exist yet
    if reset=False, but Start always passes reset=True.
    """
    st.session_state.good_secs = 0.0
    st.session_state.bad_secs = 0.0
    st.session_state.alert_count = 0
    st.session_state.bad_timer = 0.0
    st.session_state.last_tick = time.time()
    st.session_state.session_active = True
    st.session_state.score_total = 0.0
    st.session_state.score_frames = 0


def stop_session(st):
    """
    Marks the session as inactive.
    Call this when the user presses Stop.
    """
    st.session_state.session_active = False
    st.session_state.running = False


# ------------------------------------------------------------------ #
#  Per-frame update                                                    #
# ------------------------------------------------------------------ #
def update_session(st, score):
    """
    Called once per frame with the current posture score.
    Updates all session counters and returns a dict of current stats
    plus a boolean indicating whether an alert should fire.

    Parameters
    ----------
    st    : the Streamlit module (passed in so this file has no
            direct Streamlit import at the top — keeps it testable)
    score : float 0–100 from compute_deviation_score()

    Returns
    -------
    dict with keys:
        good_secs    float  total good posture seconds this session
        bad_secs     float  total bad posture seconds this session
        bad_timer    float  consecutive bad posture seconds right now
        alert_count  int    total alerts fired this session
        should_alert bool   True if an alert should fire this frame
    """
    now = time.time()
    elapsed = now - st.session_state.get("last_tick", now)

    # Clamp elapsed to 0.5s max — prevents a large jump if the loop
    # pauses briefly (e.g. during calibration)
    elapsed = min(elapsed, 0.5)

    st.session_state.last_tick = now

    alert_threshold = st.session_state.get("alert_delay", ALERT_DELAY_SECS)
    should_alert = False

    # Accumulate score for session average
    st.session_state.score_total = st.session_state.get(
        "score_total",  0.0) + score
    st.session_state.score_frames = st.session_state.get("score_frames", 0) + 1

    if score >= GOOD_THRESHOLD:
        # Good posture frame
        st.session_state.good_secs += elapsed
        st.session_state.bad_timer = 0.0        # reset consecutive bad timer

    else:
        # Bad posture frame
        st.session_state.bad_secs += elapsed
        st.session_state.bad_timer += elapsed

        # Check if bad posture has lasted long enough to trigger alert
        if st.session_state.bad_timer >= alert_threshold:
            should_alert = True
            st.session_state.alert_count += 1
            st.session_state.bad_timer = 0.0  # reset so it doesn't fire every frame

    return {
        "good_secs":   st.session_state.good_secs,
        "bad_secs":    st.session_state.bad_secs,
        "bad_timer":   st.session_state.bad_timer,
        "alert_count": st.session_state.alert_count,
        "should_alert": should_alert,
    }


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #
def format_duration(seconds):
    """
    Converts a float number of seconds into a readable string.
    Examples:
        72.4  -> "1m 12s"
        45.0  -> "0m 45s"
        3661  -> "61m 1s"  (no hours — sessions rarely exceed an hour)
    """
    seconds = int(seconds)
    m = seconds // 60
    s = seconds % 60
    return f"{m}m {s}s"


def get_session_summary(st):
    """
    Returns a dict summarising the completed session.
    Call this right before stop_session() to capture final stats.
    """
    good = st.session_state.get("good_secs",    0.0)
    bad = st.session_state.get("bad_secs",     0.0)
    total = good + bad

    frames = st.session_state.get("score_frames", 0)
    total_score = st.session_state.get("score_total", 0.0)
    avg_score = round(total_score / frames, 1) if frames > 0 else 0.0

    return {
        "good_secs":   round(good,  1),
        "bad_secs":    round(bad,   1),
        "total_secs":  round(total, 1),
        "alert_count": st.session_state.get("alert_count", 0),
        "avg_score":   avg_score,
        "good_pct":    round((good / total * 100) if total > 0 else 0, 1),
    }
