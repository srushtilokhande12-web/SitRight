import json
import os
import datetime

ANALYTICS_PATH = "data/analytics.json"


# ------------------------------------------------------------------ #
#  Public API                                                          #
# ------------------------------------------------------------------ #
def log_session(summary):
    """
    Appends one session record to analytics.json.

    Parameters
    ----------
    summary : dict returned by monitor.get_session_summary()
              Must contain: good_secs, bad_secs, total_secs,
                            alert_count, avg_score, good_pct

    Returns True on success, False on failure.
    """
    if not _is_valid_summary(summary):
        print(
            f"[SitRight] analytics: invalid summary, skipping log. Got: {summary}")
        return False

    record = _build_record(summary)
    data = _load_or_create()

    data["sessions"].append(record)
    data["total_sessions"] = len(data["sessions"])

    return _save(data)


def load_analytics():
    """
    Loads analytics.json and returns the full dict.
    Returns a fresh empty structure if the file doesn't exist.
    Never crashes.
    """
    return _load_or_create()


def get_recent_sessions(n=7):
    """
    Returns the n most recent session records as a list,
    most recent first.
    Returns an empty list if no sessions exist.
    """
    data = _load_or_create()
    sessions = data.get("sessions", [])
    return list(reversed(sessions[-n:]))


# ------------------------------------------------------------------ #
#  Internal helpers                                                    #
# ------------------------------------------------------------------ #
def _build_record(summary):
    """
    Builds a clean session record dict from the summary.
    Adds date, time, and a human-readable duration.
    """
    now = datetime.datetime.now()

    return {
        "date":          now.strftime("%Y-%m-%d"),
        "time":          now.strftime("%H:%M"),
        "good_secs":     round(summary["good_secs"],   1),
        "bad_secs":      round(summary["bad_secs"],    1),
        "total_secs":    round(summary["total_secs"],  1),
        "alert_count":   summary["alert_count"],
        "avg_score":     round(summary.get("avg_score", 0), 1),
        "good_pct":      round(summary["good_pct"],    1),
    }


def _is_valid_summary(summary):
    """
    Returns True only if the summary has all required keys
    and the session lasted at least 5 seconds.
    Prevents logging accidental zero-second sessions.
    """
    required = ["good_secs", "bad_secs",
                "total_secs", "alert_count", "good_pct"]
    for key in required:
        if key not in summary:
            return False
    return summary["total_secs"] >= 5


def _load_or_create():
    """
    Loads analytics.json if it exists.
    Returns a fresh structure if it doesn't or if the file is corrupt.
    """
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(ANALYTICS_PATH):
        return _empty_structure()

    try:
        with open(ANALYTICS_PATH, "r") as f:
            data = json.load(f)

        # Validate structure — file might exist but be malformed
        if "sessions" not in data:
            return _empty_structure()

        return data

    except (json.JSONDecodeError, IOError):
        print("[SitRight] analytics.json is corrupt — starting fresh.")
        return _empty_structure()


def _empty_structure():
    return {
        "sessions":       [],
        "total_sessions": 0,
    }


def _save(data):
    """
    Writes data dict to analytics.json.
    Returns True on success, False on failure.
    """
    try:
        os.makedirs("data", exist_ok=True)
        with open(ANALYTICS_PATH, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except IOError as e:
        print(f"[SitRight] Failed to save analytics: {e}")
        return False
