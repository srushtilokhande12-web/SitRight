# SitRight

## Overview

SitRight is an AI-powered posture monitoring application that helps users maintain healthy sitting habits while working on their computers. Using computer vision and pose estimation, SitRight learns a user's ideal posture through a quick calibration process and continuously monitors their posture in real time.

When the user's posture deviates significantly from their personalized baseline, SitRight instantly alerts them to sit upright. All processing is performed locally on the user's device, ensuring complete privacy and offline functionality.

---

## Problem Statement

People often develop poor posture while working for long hours on a computer without realizing it. A real-time system is needed to instantly detect bad posture and alert users to sit correctly.

---

## Features

### Personalized Calibration

* User sits in their ideal posture for a few seconds.
* SitRight captures and stores posture landmarks.
* Creates a personalized posture baseline for each user.

### Real-Time Posture Monitoring

* Continuously analyzes posture using the laptop webcam.
* Tracks head, neck, and shoulder alignment in real time.

### Smart Alerts

* Detects prolonged poor posture.
* Sends desktop notifications.
* Plays an alert sound to remind users to sit upright.

### Posture Score

* Calculates a posture score based on posture quality during a session.
* Helps users track and improve their posture habits.

### Daily Analytics

* Tracks:

  * Good posture duration
  * Bad posture duration
  * Number of posture alerts
* Displays posture insights through an intuitive dashboard.

### Privacy-First Design

* Works completely offline.
* No cloud storage.
* No external APIs.
* No user data leaves the device.

---

## Tech Stack

### Frontend

* Streamlit

### Computer Vision

* OpenCV

### Pose Estimation

* MediaPipe Pose

### Numerical Computation

* NumPy

### Notifications

* Plyer

### Audio Alerts

* winsound / pygame

### Data Storage

* JSON

### Packaging

* PyInstaller

---

## How It Works

### Step 1: Calibration

The user sits in their ideal posture and clicks the **Calibrate** button.

SitRight:

1. Captures posture landmarks using MediaPipe.
2. Records multiple frames.
3. Calculates an average posture baseline.
4. Stores the baseline locally.

### Step 2: Monitoring

While the user works:

1. Webcam continuously captures frames.
2. MediaPipe extracts body landmarks.
3. Current posture is compared against the stored baseline.
4. A posture deviation score is calculated.

### Step 3: Alerting

If poor posture persists for a predefined duration:

* Desktop notification is displayed.
* Alert sound is played.
* Posture event is logged for analytics.

---

## System Architecture

Frontend (Streamlit)
↓
Webcam Feed (OpenCV)
↓
Pose Detection (MediaPipe)
↓
Posture Analysis Engine (NumPy)
↓
Deviation Detection
↓
Alerts + Analytics

---

## Project Structure

```text
SitRight/

├── app.py
│
├── calibration/
│   └── calibrate.py
│
├── monitoring/
│   └── monitor.py
│
├── posture/
│   └── analyzer.py
│
├── alerts/
│   └── notifier.py
│
├── data/
│   ├── baseline.json
│   ├── analytics.json
│   └── settings.json
│
├── assets/
│   └── alert.wav
│
├── requirements.txt
│
└── README.md
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/your-username/SitRight.git
cd SitRight
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
streamlit run app.py
```

---

## Future Enhancements

* Multiple posture profiles
* Personalized sensitivity settings
* Weekly posture reports
* Stretch break reminders
* Productivity analytics
* Cross-platform desktop application
* AI-generated posture improvement suggestions

---

## Why SitRight?

Most posture-correction solutions require wearable devices, subscriptions, or cloud-based processing. SitRight offers a lightweight, personalized, privacy-first alternative that works entirely offline using only a laptop webcam.

By providing real-time posture feedback, SitRight helps users build healthier sitting habits and reduce the risk of posture-related discomfort over time.

---

## License

This project is open-source and available under the MIT License.

