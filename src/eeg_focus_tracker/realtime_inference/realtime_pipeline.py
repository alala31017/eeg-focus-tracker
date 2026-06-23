import asyncio
import os
import numpy as np
import pandas as pd
import joblib
import time
from scipy.signal import butter, filtfilt, welch, resample
from muse_stream_client import MuseStreamClient
from muse_discovery import find_muse_devices
from src.eeg_focus_tracker.realtime_inference import shared_state

import warnings
warnings.filterwarnings('ignore', category=UserWarning)
import lightgbm as lgb
lgb.basic._LIB

WINDOW_SEC = 6
STRIDE_SEC = 3
SF = 256

WINDOW_SIZE = WINDOW_SEC * SF
STRIDE_SIZE = STRIDE_SEC * SF

BASELINE_SEC = 30
baseline_buffer = []
baseline_ref = None
baseline_windows = []

eeg_buffer = []

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "..", "..", "..", "models") 

feature_columns = joblib.load(os.path.join(MODEL_DIR, "feature_names.pkl"))
scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
model = joblib.load(os.path.join(MODEL_DIR, "focus_model.pkl"))
model.set_params(verbose=-1)


def process_eeg(data):
    global eeg_buffer, baseline_buffer, baseline_ref, baseline_windows

    if data is None:
        return

    if 'channels' not in data or data['channels'] is None:
        return

    channels = data['channels']
    required = ['TP9', 'AF7', 'AF8', 'TP10']
    if not all(ch in channels for ch in required):
        return
    
    shared_state.device_connected = True

    for ch in required:
        if channels[ch] is None or any(v is None for v in channels[ch]):
            return

    samples = np.array([
        channels['TP9'],
        channels['AF7'],
        channels['AF8'],
        channels['TP10']
    ], dtype=float).T

    if not np.isfinite(samples).all():
        return  


    # ---- BASELINE COLLECTION ----
    if not shared_state.baseline_ready and baseline_ref is not None: # reset
        baseline_buffer.clear()
        baseline_windows.clear()
        baseline_ref = None
        eeg_buffer.clear()

    if not shared_state.baseline_ready:
        baseline_buffer.extend(samples)

        # baseline collection progress bar UI
        shared_state.baseline_progress = len(baseline_buffer) / (BASELINE_SEC * SF)

        if len(baseline_buffer) >= BASELINE_SEC * SF:
            print("Computing baseline...")

            baseline_array = np.array(baseline_buffer)
            baseline_array = band_pass_filter(baseline_array, lowcut=1, highcut=30, sf=256)

            baseline_array = reject_artifacts(baseline_array)

            if baseline_array is None:
                print("Baseline rejected — recollecting")
                baseline_buffer.clear()
                return

            baseline_windows.clear()

            # safer window loop
            for i in range(0, len(baseline_array) - WINDOW_SIZE + 1, STRIDE_SIZE):
                baseline_windows.append(
                    baseline_array[i:i+WINDOW_SIZE]
                )

            # guard against empty baseline
            if len(baseline_windows) == 0:
                print("No valid baseline windows — recollecting")
                baseline_buffer.clear()
                return

            baseline_features = pd.concat(
                [extract_features(w) for w in baseline_windows],
                ignore_index=True
            )

            baseline_ref = baseline_features.median()

            shared_state.baseline_ready = True
            shared_state.baseline_progress = 1.0
            shared_state.session_start_time = time.time()

            print("Baseline ready. Starting predictions.")

        return

 
    # ---- PREDICTION BUFFER ----
    eeg_buffer.extend(samples)

    while len(eeg_buffer) >= WINDOW_SIZE:

        if not shared_state.session_active:
            return

        window = np.array(eeg_buffer[:WINDOW_SIZE])
        eeg_buffer[:] = eeg_buffer[STRIDE_SIZE:]

        window = resample_to_256(window)
        window = band_pass_filter(window, lowcut=1, highcut=30, sf=256)

        window = reject_artifacts(window)
        if window is None:
            continue

        features = extract_features(window)
        features = normalize_with_baseline(features, baseline_ref)
        features = features[feature_columns]

        X = scaler.transform(features)
        

        # ---------------- UPDATE SHARED STATE ----------------
        focus = model.predict_proba(X)[0][1]

        shared_state.focus_value = float(focus)
        shared_state.prediction_started = True 

        # bandpower averages
        shared_state.theta_power = float(
            features[[c for c in features.columns if "theta" in c]].mean(axis=1).iloc[0]
        )

        shared_state.alpha_power = float(
            features[[c for c in features.columns if "alpha" in c]].mean(axis=1).iloc[0]
        )

        shared_state.beta_power = float(
            features[[c for c in features.columns if "beta" in c]].mean(axis=1).iloc[0]
        )

        # signal quality
        signal_quality = 1 - (np.mean(np.abs(window) > 380))
        shared_state.signal_quality = float(signal_quality)

        # channel heatmap (alpha)
        shared_state.channel_power = {
            "TP9": float(features["TP9_alpha"].iloc[0]),
            "AF7": float(features["AF7_alpha"].iloc[0]),
            "AF8": float(features["AF8_alpha"].iloc[0]),
            "TP10": float(features["TP10_alpha"].iloc[0])
        }

        print(f"Focus: {focus:.2f}")


def process_heart_rate(data):
    if data is None:
        return
    shared_state.heart_rate = float(data)
        

# ---------------- DSP FUNCTIONS ----------------
def resample_to_256(window):
    target = WINDOW_SIZE
    if len(window) == target:
        return window
    return resample(window, target, axis=0)


#apply band pass filter
def band_pass_filter(df, lowcut=1, highcut=30, sf=256, order=4):
    if df is None:
        return None

    if np.isnan(df).any():
        return None
    
    nyq = 0.5 * sf
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')

    return filtfilt(b, a, df, axis=0)


#artifact rejection
def reject_artifacts(window, threshold=380):

    # guard against None
    if window is None:
        return None

    # guard against empty
    if len(window) == 0:
        return None

    ratio = np.mean(np.abs(window) > threshold)

    if ratio > 0.20:
        return None

    return window


#calculate bandpower
def bandpower(data, sf, band):
    freqs, psd = welch(data, sf, nperseg=sf*2)
    idx = np.logical_and(freqs >= band[0], freqs <= band[1])
    return np.trapezoid(psd[idx], freqs[idx])


#feature engineering
def extract_features(window, sf=256):

    feature = {}

    for i, ch in enumerate(['TP9', 'AF7', 'AF8', 'TP10']):
        signal = window[:, i]

        theta = bandpower(signal, sf, (4, 8))
        alpha = bandpower(signal, sf, (8, 13))
        beta  = bandpower(signal, sf, (13, 30))

        feature[f'{ch}_theta'] = theta
        feature[f'{ch}_alpha'] = alpha
        feature[f'{ch}_beta']  = beta

        feature[f'{ch}_theta_alpha'] = theta / alpha if alpha > 0 else 0
        feature[f'{ch}_beta_alpha']  = beta / alpha if alpha > 0 else 0
        feature[f'{ch}_engagement']  = beta / (alpha + theta) if (alpha + theta) > 0 else 0

    feature['alpha_asymmetry'] = (
        feature['AF7_alpha'] - feature['AF8_alpha']
    )

    return pd.DataFrame([feature])


#baseline normalization
def normalize_with_baseline(features_df, baseline_ref):

    normalized_df = features_df.copy()

    for col in features_df.columns:
        baseline_value = baseline_ref[col]

        if baseline_value != 0:
            normalized_df[col] = features_df[col] / baseline_value
        else:
            normalized_df[col] = 0

    return normalized_df


async def main():
    print("Starting realtime pipeline...")
    shared_state.device_connected = False

    devices = await find_muse_devices(timeout=10.0)
    if not devices:
        print("No Muse device found!")
        return

    device = devices[0]
    print(f"Found Muse: {device.name}")

    # Reset session state before starting
    shared_state.session_active = True
    shared_state.baseline_ready = False
    shared_state.baseline_progress = 0.0

    client = MuseStreamClient(
        save_raw=False,
        decode_realtime=True,
        verbose=True
    )

    client.on_eeg(process_eeg)
    client.on_heart_rate(process_heart_rate)
    print("Connecting and streaming...")

    stream_task = asyncio.create_task(
        client.connect_and_stream(
            device.address,
            duration_seconds=0,
            preset='p1035'
        )
    )

    while shared_state.session_active:
        await asyncio.sleep(0.5)

    print("\nSession ended by user. Disconnecting...")
    stream_task.cancel()
    try:
        await stream_task
    except (asyncio.CancelledError, Exception):
        pass



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped")

