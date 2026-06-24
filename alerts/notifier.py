import time
import platform
import os

# ------------------------------------------------------------------ #
#  Constants                                                           #
# ------------------------------------------------------------------ #
COOLDOWN_SECS = 15          # minimum seconds between notifications
ALERT_WAV_PATH = "assets/alert.wav"

# ------------------------------------------------------------------ #
#  Internal state                                                      #
# ------------------------------------------------------------------ #
_last_alert_time = 0.0       # timestamp of the last alert that fired


# ------------------------------------------------------------------ #
#  Public API                                                          #
# ------------------------------------------------------------------ #
def send_alert(
    title="SitRight",
    message="Sit up straight — your posture needs attention.",
    play_sound=True,
    send_notif=True,
):
    """
    Sends a desktop notification and/or plays alert sound.
    Respects the play_sound and send_notif toggles from settings.
    Does nothing if called within COOLDOWN_SECS of the last alert.
    Returns True if the alert fired, False if suppressed by cooldown.
    """
    global _last_alert_time

    now = time.time()
    if now - _last_alert_time < COOLDOWN_SECS:
        return False

    _last_alert_time = now

    if send_notif:
        _send_notification(title, message)

    if play_sound:
        _play_sound()

    return True


def seconds_until_next_alert():
    """
    Returns how many seconds remain in the current cooldown.
    Returns 0 if the notifier is ready to fire immediately.
    Useful for showing a cooldown countdown in the UI.
    """
    elapsed = time.time() - _last_alert_time
    remaining = COOLDOWN_SECS - elapsed
    return max(0.0, round(remaining, 1))


def reset_cooldown():
    """
    Resets the cooldown timer to zero.
    Call this when a new session starts so the first alert
    of the new session is not suppressed by the previous session.
    """
    global _last_alert_time
    _last_alert_time = 0.0


# ------------------------------------------------------------------ #
#  Internal helpers                                                    #
# ------------------------------------------------------------------ #
def _send_notification(title, message):
    """
    Sends a desktop notification using plyer.
    Fails silently if plyer is not installed or the platform
    does not support notifications.
    """
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="SitRight",
            timeout=8,              # notification disappears after 8 seconds
        )
    except Exception as e:
        # Never let notification failure crash the monitoring loop
        print(f"[SitRight] Notification error: {e}")


def _play_sound():
    """
    Plays assets/alert.wav.
    Uses winsound on Windows (no extra install).
    Uses pygame on Mac and Linux.
    Fails silently if the wav file is missing or audio fails.
    """
    if not os.path.exists(ALERT_WAV_PATH):
        print(f"[SitRight] Sound file not found: {ALERT_WAV_PATH}")
        return

    system = platform.system()

    try:
        if system == "Windows":
            import winsound
            winsound.PlaySound(
                ALERT_WAV_PATH, winsound.SND_FILENAME | winsound.SND_ASYNC)

        else:
            # Mac and Linux — use pygame mixer
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(ALERT_WAV_PATH)
            pygame.mixer.music.play()

    except Exception as e:
        print(f"[SitRight] Sound error: {e}")
