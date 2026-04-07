
"""
- decode a binary data file into dataframe
- process bandpass filter (1-30Hz)
- remove artifacts & create epochs
- calculate bandpower (alpha, beta, theta)
- feature engineering (theta/alpha ratio, beta/alpha ratio, frontal alpha asymmetry, engagement score)
- add task labels
- create a csv file with new features
"""

import re
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, welch

from muse_raw_stream import MuseRawStream
from muse_realtime_decoder import MuseRealtimeDecoder


def main():

    #enter raw data file path of a recording session
    file_path = input("Enter the EEG session recording file (.bin) path:")
    events_path = input("Enter the events csv file path:")

    session_num = int(re.search(r"session(\d+)", file_path).group(1))

    if session_num % 2 != 0:
        task1_label = 1 #focus
        task2_label = 0 #distraction
    else:
        task1_label = 0 #distraction
        task2_label = 1 #focus

    events = pd.read_csv(events_path)
    events_dict = dict(zip(events['event'], events['time']))

    df_baseline, df_task1, df_task2 = load_eeg_from_bin(file_path, events_dict)
    print(f"Total missing data in Task1: {df_task1.isnull().sum()}")
    print(f"Total missing data in Task2: {df_task2.isnull().sum()}")
    print(f"Task1 data quality check: {df_task1[['TP9', 'AF7', 'AF8', 'TP10']].abs().max()}")
    print(f"Task2 data quality check: {df_task2[['TP9', 'AF7', 'AF8', 'TP10']].abs().max()}")

    #process baseline reference
    baseline_ref = calculate_baseline(df_baseline)

    #process task1 recording
    df_task1 = band_pass_filter(df_task1)
    windows_task1 = create_windows(df_task1)
    features_df_task1 = extract_features(windows_task1)
    features_task1 = normalize_with_baseline(features_df_task1, baseline_ref)
    features_task1["label"] = task1_label
    print(f"Task 1 samples: {len(features_task1)}")

    #process task2 recording
    df_task2 = band_pass_filter(df_task2)
    windows_task2 = create_windows(df_task2)
    features_df = extract_features(windows_task2)
    features_task2 = normalize_with_baseline(features_df, baseline_ref)
    features_task2["label"] = task2_label
    print(f"Task 2 samples: {len(features_task2)}")

    #merge & save
    new_df = pd.concat([features_task1, features_task2], ignore_index=True)
    print(new_df.head())
    print(f"Total samples: {len(new_df)}")
    new_df.to_csv(f"data/sessions/session{session_num}.csv")

    print("Done!")


#decoding binary raw eeg file and create dataframe
def load_eeg_from_bin(file_path, events_dict):
    stream = MuseRawStream(file_path)
    stream.open_read()

    decoder = MuseRealtimeDecoder()
    rows = []
    CHANNELS = ['TP9', 'AF7', 'AF8', 'TP10']
    SAMPLING_RATE = 256  # Muse S default
    t0 = None

    for packet in stream.read_packets():
        decoded = decoder.decode(packet.data, packet.timestamp)

        if decoded.eeg:
            eeg_dict = decoded.eeg
            n_samples = len(eeg_dict["TP9"])
            if t0 is None:
                t0 = decoded.timestamp

            for i in range(n_samples):
                row = {}
                relative_time = (decoded.timestamp - t0).total_seconds() + (i / SAMPLING_RATE)
                row["time"] = relative_time

                for ch in CHANNELS:
                    if ch in eeg_dict:
                        row[ch] = eeg_dict[ch][i]
                rows.append(row)

    stream.close()

    df = pd.DataFrame(rows)
    df = df.dropna().reset_index(drop=True)

    offset = events_dict["baseline_start"] - df["time"].iloc[0]
    df["time"] += offset
    df["time"] = df["time"].astype(float)

    df_baseline = df[(events_dict["baseline_start"] <= df["time"]) & (df["time"] <= events_dict["baseline_end"])]
    df_task1 = df[(events_dict["task1_start"] <= df["time"]) & (df["time"] <= events_dict["task1_end"])]
    df_task2 = df[(events_dict["task2_start"] <= df["time"]) & (df["time"] <= events_dict["task2_end"])]

    return df_baseline, df_task1, df_task2


#apply band pass filter
def band_pass_filter(df, lowcut=1, highcut=30, sf=256, order=4):

    nyq = 0.5 * sf
    low = lowcut / nyq
    high = highcut / nyq

    b, a = butter(order, [low, high], btype='band')

    filtered_df = pd.DataFrame()

    for ch in ['TP9', 'AF7', 'AF8', 'TP10']:
        filtered_df[ch] = filtfilt(b, a, df[ch])

    return filtered_df


#create epochs
def create_windows(df, window_sec=6, stride_sec=3, sf=256, threshold=380):
    window_size = window_sec * sf
    stride = stride_sec * sf

    data = df[['TP9', 'AF7', 'AF8', 'TP10']].values
    windows = []
    removed = 0
    kept = 0

    for start in range(0, len(data) - window_size, stride):
        end = start + window_size

        if end > len(data):
            break

        window = data[start:end]

        # artifact removal
        if np.mean(np.abs(window) > threshold) > 0.20:
            removed += 1
            continue

        kept += 1

        windows.append(window)

    print("Removal ratio:", removed/(removed+kept))

    return windows


#calculate bandpower
def bandpower(data, sf, band):

    freqs, psd = welch(data, sf, nperseg=sf*2)
    idx = np.logical_and(freqs >= band[0], freqs <= band[1])

    return np.trapezoid(psd[idx], freqs[idx])


#feature engineering
def extract_features(windows, sf=256):

    features = []

    for window in windows:
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

        # Frontal Alpha Asymmetry
        feature['alpha_asymmetry'] = (
            feature['AF7_alpha'] - feature['AF8_alpha']
        )

        features.append(feature)

    return pd.DataFrame(features)


#calculate baseline band power reference (median) for baseline normalization
def calculate_baseline(baseline_df):

    baseline_df = band_pass_filter(baseline_df, lowcut=1, highcut=30, sf=256)
    baseline_windows = create_windows(baseline_df)
    baseline_features = extract_features(baseline_windows)
    baseline_ref = baseline_features.median()

    return baseline_ref


#normalize with baseline reference to minimize the variability between sessions
def normalize_with_baseline(features_df, baseline_ref):

    normalized_df = features_df.copy()

    for col in features_df.columns:
        if col == "label":
            continue

        baseline_value = baseline_ref[col]

        if baseline_value != 0:
            normalized_df[col] = (features_df[col] / baseline_value) / baseline_value
        else:
            normalized_df[col] = 0

    return normalized_df


if __name__ == "__main__":
    main()