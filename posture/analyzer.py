import numpy as np

# Landmark indices from MediaPipe's 33-point pose model
NOSE = 0
LEFT_EAR = 7
RIGHT_EAR = 8
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12


def extract_landmarks(results):
    """
    Takes a MediaPipe pose results object.
    Returns a dict of the 6 landmark (x, y) coords we care about.
    Returns None if any key landmark is missing or has low visibility.
    """
    if results.pose_landmarks is None:
        return None

    lm = results.pose_landmarks.landmark

    # Reject the frame if any critical landmark is not clearly visible
    key_indices = [NOSE, LEFT_EAR, RIGHT_EAR, LEFT_SHOULDER, RIGHT_SHOULDER]

    for idx in key_indices:
        if lm[idx].visibility < 0.6:
            return None

    return {
        "nose": [lm[NOSE].x, lm[NOSE].y],
        "left_ear": [lm[LEFT_EAR].x, lm[LEFT_EAR].y],
        "right_ear": [lm[RIGHT_EAR].x, lm[RIGHT_EAR].y],
        "left_shoulder": [lm[LEFT_SHOULDER].x, lm[LEFT_SHOULDER].y],
        "right_shoulder": [lm[RIGHT_SHOULDER].x, lm[RIGHT_SHOULDER].y],
    }


def get_ear_midpoint(landmarks):
    """
    Returns the midpoint between left and right ear.
    Used as a proxy for head/neck position.
    """
    left = np.array(landmarks["left_ear"])
    right = np.array(landmarks["right_ear"])
    return ((left + right) / 2).tolist()


def get_shoulder_midpoint(landmarks):
    """
    Returns the midpoint between left and right shoulder.
    """
    left = np.array(landmarks["left_shoulder"])
    right = np.array(landmarks["right_shoulder"])
    return ((left + right) / 2).tolist()


def compute_angle(a, b, c):
    """
    Computes the angle at point b, in the triangle a-b-c.
    All inputs are [x, y] lists or numpy arrays.
    Returns angle in degrees.
    """
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    ba = a - b
    bc = c - b

    dot = np.dot(ba, bc)
    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)

    # Clip to [-1, 1] to prevent arccos errors
    cosine = np.clip(
        dot / (norm_ba * norm_bc + 1e-6),
        -1.0,
        1.0
    )

    return float(np.degrees(np.arccos(cosine)))


def compute_baseline_angles(landmarks):
    """
    Given a landmarks dict, computes the two angles used as baseline.

    Neck angle: angle at the shoulder midpoint between the ear midpoint
    and a point directly above it (vertical reference).

    Shoulder tilt: absolute y difference between left and right shoulder.
    """
    ear_mid = get_ear_midpoint(landmarks)
    shoulder_mid = get_shoulder_midpoint(landmarks)

    # Point directly above shoulder midpoint
    vertical_ref = [
        shoulder_mid[0],
        shoulder_mid[1] - 0.1
    ]

    neck_angle = compute_angle(
        ear_mid,
        shoulder_mid,
        vertical_ref
    )

    shoulder_tilt = abs(
        landmarks["left_shoulder"][1]
        - landmarks["right_shoulder"][1]
    )

    return {
        "neck_angle": neck_angle,
        "shoulder_tilt": shoulder_tilt
    }


def compute_live_angles(landmarks):
    """
    Computes the same angles as compute_baseline_angles()
    but on a live frame instead of a calibration average.
    Must use identical math so the comparison is valid.
    """
    ear_mid = get_ear_midpoint(landmarks)
    shoulder_mid = get_shoulder_midpoint(landmarks)

    vertical_ref = [
        shoulder_mid[0],
        shoulder_mid[1] - 0.1
    ]

    neck_angle = compute_angle(
        ear_mid,
        shoulder_mid,
        vertical_ref
    )

    shoulder_tilt = abs(
        landmarks["left_shoulder"][1]
        - landmarks["right_shoulder"][1]
    )

    return {
        "neck_angle": neck_angle,
        "shoulder_tilt": shoulder_tilt
    }


def compute_deviation_score(landmarks, baseline, sensitivity=5):
    """
    Compares live landmark angles against the saved baseline.
    Returns a posture score from 0 (terrible) to 100 (perfect).

    sensitivity: int 1–10 from the Settings page.
                 Higher = stricter = score drops faster on small deviations.
    """
    live_angles = compute_live_angles(landmarks)

    # Neck angle deviation
    neck_deviation = abs(
        live_angles["neck_angle"] - baseline["neck_angle"]
    )

    # Shoulder tilt deviation
    shoulder_deviation = abs(
        live_angles["shoulder_tilt"]
        - baseline["shoulder_tilt"]
    ) * 100

    # Sensitivity multiplier
    sensitivity_multiplier = sensitivity / 5.0

    # Weighted combination
    combined_deviation = (
        (neck_deviation * 0.70) +
        (shoulder_deviation * 0.30)
    ) * sensitivity_multiplier

    # Convert deviation to score
    score = max(
        0.0,
        min(
            100.0,
            100.0 - (combined_deviation * 3.0)
        )
    )

    return round(score, 1)
