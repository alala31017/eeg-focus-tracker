# Focus Tracker with Muse S Athena

A personal EEG-based focus monitoring system that streams real-time brainwave data from a Muse S Athena headset, classifies focus state using a trained LightGBM model, and displays live predictions in a bilingual (EN/JA) Streamlit dashboard. Includes a Demo mode that replays pre-recorded sessions, so the app can be explored without owning the headset.

**Live demo:** [your-app-url.streamlit.app](#) <!-- replace with actual deployed URL -->

---

## Overview

This project pipelines raw EEG data from a consumer-grade BLE headset through signal processing and machine learning to produce a real-time focus probability score. The score updates every 3 seconds and is displayed alongside brainwave band powers, channel activity, heart rate, and session history.

The system has four main components:

- **Data collection** — structured recording sessions (baseline + focus + distraction tasks) saved as binary files
- **Offline preprocessing & training** — signal filtering, epoch segmentation, feature extraction, and LightGBM classifier training, documented step by step in `notebooks/`
- **Real-time inference** — live BLE stream → DSP pipeline → model prediction → Streamlit UI
- **Demo mode** — replays a recorded `.bin` session through the same inference pipeline, so the app is explorable without Bluetooth hardware (used for the hosted deployment)

---

## Hardware

- **Device:** Muse S Athena
- **Channels:** TP9, AF7, AF8, TP10 (4 electrodes)
- **Sampling rate:** 256 Hz
- **OS:** macOS only for Live mode (BLE stack via `bleak` / CoreBluetooth). Demo mode has no OS restriction.

---

## Project Structure

```
eeg-focus-tracker/
├── src/
│   └── eeg_focus_tracker/
│       ├── realtime_inference/
│       │   ├── realtime_pipeline.py   # BLE stream → DSP → model inference
│       │   ├── shared_state.py        # JSON-based inter-process state (pipeline ↔ UI)
│       │   └── state.json             # auto-generated at runtime, do not edit manually
│       ├── data_collection/
│       │   ├── data_recording.py      # structured session recorder
│       │   └── preprocessing.py       # process recorded binary EEG data into csv format for training
│       └── training/
│           └── model.py               # trains and exports the final deployed model
├── app/
│   ├── streamlit-app.py           # bilingual real-time dashboard (Demo / Live mode)
│   └── demo/
│       ├── replay.py               # replays a .bin file through the same inference pipeline
│       └── data/
│           └── demo_session.bin    # sample session bundled for the hosted demo
├── models/                        # trained model artifacts (gitignored)
├── data/
│   ├── recordings/                # raw binary EEG recordings (gitignored)
│   └── sessions/                  # per-session feature CSVs (gitignored)
├── notebooks/                     # preprocessing, EDA & training notebooks
│   ├── 01_preprocessing.ipynb
│   ├── 02_exploratory.ipynb
│   └── 03_modeling.ipynb
├── requirements.txt                # deployment / demo-mode dependencies
├── requirements-live.txt           # additional dependencies for Live mode (BLE)
└── README.md
```

---

## Installation

Python 3.10.1 is required.

```bash
git clone https://github.com/alala31017/eeg-focus-tracker.git
cd eeg-focus-tracker

python3.10 -m venv .venv
source .venv/bin/activate
```

### Demo mode only (no Bluetooth device required)
```bash
pip install -r requirements.txt
```

### Full setup including Live mode (requires Muse S Athena headset)
```bash
pip install -r requirements.txt -r requirements-live.txt
```

**macOS Bluetooth permissions:** on first run, macOS will prompt for Bluetooth access. Grant it in System Settings → Privacy & Security → Bluetooth. If the device isn't found, toggle Bluetooth off and on and retry.

---

## Usage

### 1. Data Collection

Run a 30-minute recording session (baseline → task 1 → break → task 2):

```bash
python -m src.eeg_focus_tracker.data_collection.data_recording
```

Sessions alternate between focus-first and distraction-first order based on the session number (odd = focus first, even = distraction first).
Once a recording session is completed, 3 files will be saved to `data/recordings/`: a raw binary data file (naming convention: `session{n}_{condition}_{timestamp}.bin`), an events CSV recording the start/end time of each task block for cross-referencing during preprocessing, and a metadata JSON summarizing the session.

### 2. Preprocessing

Decode a binary data file from a single recording session, process the data (signal filtering, artifact removal, epoch segmentation, and feature extraction), and save a CSV with 26 columns (25 features + label).

```bash
python -m src.eeg_focus_tracker.data_collection.preprocessing
```

### 3. Training

Train the final LightGBM classifier on the clean session subset, using the hyperparameters selected in `03_modeling.ipynb` (LightGBM + Leave-One-Session-Out CV; see [Model](#model) below for why LOSO was chosen over K-Fold).

```bash
python -m src.eeg_focus_tracker.training.model
```

This saves `focus_model.pkl`, `scaler.pkl`, and `feature_names.pkl` to `models/`.

### 4a. Real-Time Inference — Live mode

Launch the app:

```bash
streamlit run app/streamlit-app.py
```

Select **Live Mode** on the landing screen, then click **Start Live Session**. This launches `realtime_pipeline.py` as a background subprocess, which scans for the Muse device, connects over BLE, and begins streaming. Once connected, a 30-second baseline calibration begins; after calibration, the dashboard updates with live focus scores, band powers, channel activity, and heart rate every ~3 seconds.

### 4b. Real-Time Inference — Demo mode

Select **Demo Mode** on the landing screen. You can either upload your own recorded `.bin` session or click **Use sample session** to replay the bundled demo recording. The same inference pipeline (`process_eeg`) used in Live mode processes the replayed data, so Demo mode is a faithful reproduction of the live experience — just without needing the headset. Playback runs at 4x speed.

### Ending a session

Click **End Session** (Live) or wait for playback to finish (Demo) to see the summary screen: session duration, average/peak/min focus, a colored focus timeline, time spent in each focus zone, average band powers, and a short list of auto-generated insights. From there you can start a new session, replay the same demo file, or switch modes entirely via **← Change Mode**.

---

## Signal Processing Pipeline

Each incoming EEG window goes through the following steps:

1. **Bandpass filter** — 1–30 Hz (Butterworth order 4)
2. **Epoch segmentation** — 6-second windows with 3-second stride (50% overlap)
3. **Artifact rejection** — windows where >20% of samples exceed ±380 µV are discarded
4. **FFT / Welch PSD** — band power extraction for θ (4–8 Hz), α (8–13 Hz), β (13–30 Hz)
5. **Feature engineering** — 25 features per window across 4 channels:
   - Per-channel: theta, alpha, beta, theta/alpha, beta/alpha, engagement index
   - Global: frontal alpha asymmetry (AF7 − AF8)
6. **Baseline normalization** — each feature divided by its session-specific baseline median (`value / baseline`) to reduce session-to-session variability

---

## Model

**Classifier:** LightGBM. Labels are binary: 1 = focused (reading, maths), 0 = distracted (Instagram, YouTube Shorts).

### K-Fold vs. Leave-One-Session-Out (LOSO): a key finding

Initial evaluation used standard K-Fold cross-validation, which showed strong performance. However, K-Fold splits at the *window* level, and EEG windows from the same session share session-level characteristics (electrode contact, time-of-day state) that leak between train and test splits when adjacent windows end up on opposite sides of a fold. This inflates the apparent score.

To get an honest estimate of generalization to an unseen session — which matches the real deployment scenario — models were re-evaluated with **Leave-One-Session-Out (LOSO) CV**, holding out one full recording session at a time:

| Model | K-Fold ROC-AUC | LOSO ROC-AUC | Gap |
|-------|----------------|--------------|-----|
| SVM (full)       | 0.809 | 0.568 | 0.241 |
| LightGBM (clean) | 0.759 | 0.587 | 0.172 |
| LightGBM (full)  | 0.700 | 0.561 | 0.139 |
| RF (full)        | 0.644 | 0.530 | 0.114 |

**LOSO is treated as the primary evaluation metric for this project**, since it reflects real-world performance on a genuinely new session (which is what happens every time the headset is worn).

### Final model performance (LightGBM, LOSO, clean sessions)

| Metric | LOSO Score |
|--------|-----------|
| ROC-AUC | 0.587 |
| F1 | 0.524 |
| Accuracy | 0.570 |

Sessions 4, 7, and 8 were excluded from the "clean" subset based on a-priori signal quality thresholds (mean CV > 0.6, outlier rate > 15%, label balance ratio < 0.7, or mean θ/α ratio > 1.6 — see `02_exploratory.ipynb` for the full criteria and per-session breakdown). Excluding these sessions improved LOSO AUC by roughly +0.03 versus the full dataset; the effect was real but modest. Feature selection was also tested and did not improve LOSO performance over using all 25 features.

The model is personal — trained and calibrated on a single subject. It is not expected to generalize to other users without retraining.

---

## Architecture Notes

### Inter-process communication

The Live-mode pipeline (`realtime_pipeline.py`) runs as a separate subprocess from the Streamlit UI, since BLE streaming on macOS (via `bleak`/CoreBluetooth) is more stable outside of Streamlit's own thread/rerun model. Data is shared between the two processes through `shared_state.py`, a thin wrapper around a JSON file with atomic writes (`os.replace`).

This was chosen for simplicity in a local, single-user setup. It has known limitations:
- Not safe for concurrent multi-user access (the hosted Demo mode shares one state file across all visitors)
- Not suitable for high-frequency updates (file I/O latency), though the current ~3 second update interval is well within its limits

A production version of this app would replace this with Redis pub/sub or a WebSocket connection to support concurrent sessions safely.

### Demo mode design

Demo mode reuses `process_eeg` and `process_heart_rate` from `realtime_pipeline.py` unchanged — `app/demo/replay.py` simply reads a `.bin` file and calls the same callbacks that the BLE client would call, with timing reconstructed from the original packet timestamps (scaled by a configurable speed multiplier). This means Live and Demo modes are guaranteed to process EEG data identically; only the data source differs.

---

## Known Limitations

- **Single-subject model** — retraining is required for use by a different person
- **Label separability is weak** — mean Cohen's d across features is ~0.25, and LOSO ROC-AUC (~0.59) is well above chance but far from strong. This reflects the genuine difficulty of single-channel consumer EEG classification with a single-subject, ~15-session dataset
- **JSON-based state sharing is single-user** — see Architecture Notes above
- **macOS only for Live mode** — BLE streaming relies on CoreBluetooth via `bleak`; untested on other platforms. Demo mode has no such restriction
- **Demo mode in the hosted deployment is shared across visitors** — concurrent demo sessions may interfere with each other's progress (see Architecture Notes)

---

## Roadmap

- [ ] Collect additional sessions and retrain to improve LOSO performance
- [ ] Explore time-domain features (PSD slope, sample entropy) to improve label separability
- [ ] Move inter-process state to Redis or WebSockets to support concurrent users
- [ ] Improve code readability — refactor preprocessing into reusable modules shared between offline and realtime pipelines
- [ ] Add a model confidence threshold — suppress/flag predictions when signal quality is low

---

## Dependencies

**`requirements.txt`** (deployment / Demo mode):
```
streamlit     # dashboard
numpy
pandas
scipy
joblib        # model serialization
lightgbm      # gradient boosting classifier
scikit-learn
altair        # focus timeline charts
```

**`requirements-live.txt`** (additional, Live mode only):
```
amused        # Muse S BLE streaming and decoding
chime         # audio cues during recording sessions
```

---

## Acknowledgements

This project uses the `amused` package for EEG data streaming, adapted from:
https://github.com/Amused-EEG/amused-py

The original repository provides tools for working with Muse S Athena devices.