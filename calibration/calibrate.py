import cv2
import json
import os
import time
import numpy as np
import mediapipe as mp

from posture.analyzer import (
    extract_landmarks,
    compute_baseline_angles
)

BASELINE_PATH = "data/baseline.json"
FRAMES_NEEDED = 30


def calibrate(cap, pose):
    """
    Captures FRAMES_NEEDED frames from the already-open webcam cap,
    extracts landmarks from each, averages them, computes baseline
    angles, and saves to baseline.json.

    Returns (True, "message") on success.
    Returns (False, "error message") on failure.
    """
    collected = []
    attempts = 0
    max_attempts = 150  # try up to 150 frames to get 30 good ones

    while len(collected) < FRAMES_NEEDED and attempts < max_attempts:
        ret, frame = cap.read()
        attempts += 1

        if not ret:
            continue

        frame = cv2.resize(frame, (640, 480))
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)

        landmarks = extract_landmarks(results)

        if landmarks is None:
            # Frame not confident enough — skip it silently
            continue

        collected.append(landmarks)

        # Small pause so frames aren't all from the same millisecond
        time.sleep(0.05)

    if len(collected) < FRAMES_NEEDED:
        return False, (
            f"Only captured {len(collected)} good frames out of {FRAMES_NEEDED} needed. "
            "Make sure your face, ears, and shoulders are clearly visible."
        )

    # --- Average all collected landmarks ---
    avg_landmarks = _average_landmarks(collected)

    # --- Compute baseline angles from averaged landmarks ---
    angles = compute_baseline_angles(avg_landmarks)

    # --- Build the baseline record ---
    baseline = {
        "landmarks":      avg_landmarks,
        "neck_angle":     angles["neck_angle"],
        "shoulder_tilt":  angles["shoulder_tilt"],
        "frames_used":    len(collected),
    }

    # --- Save to disk ---
    os.makedirs("data", exist_ok=True)
    with open(BASELINE_PATH, "w") as f:
        json.dump(baseline, f, indent=2)

    return True, (
        f"Calibration complete. "
        f"Neck angle: {angles['neck_angle']:.1f}°, "
        f"Shoulder tilt: {angles['shoulder_tilt']:.4f}"
    )


def load_baseline():
    """
    Loads baseline.json from disk.
    Returns the dict on success, None if file doesn't exist.
    """
    if not os.path.exists(BASELINE_PATH):
        return None
    with open(BASELINE_PATH, "r") as f:
        return json.load(f)


def _average_landmarks(collected):
    """
    Takes a list of landmark dicts and returns a single dict
    where each coordinate is the mean across all frames.
    """
    keys = ["nose", "left_ear", "right_ear", "left_shoulder", "right_shoulder"]
    averaged = {}

    for key in keys:
        coords = np.array([frame[key]
                          for frame in collected])  # shape: (30, 2)
        averaged[key] = np.mean(coords, axis=0).tolist()        # shape: (2,)

    return averaged
