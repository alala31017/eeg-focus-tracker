import sys
import os
import streamlit as st
import time
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="NeuroFocus", layout="wide", page_icon="🧠")

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif !important;
    background-color: #060E1A !important;
    color: #E6F1FB !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #0A1628 !important;
    border-right: 0.5px solid rgba(55,138,221,0.2) !important;
    min-width: 230px !important;
    max-width: 230px !important;
}
[data-testid="stSidebar"] * { color: #B5D4F4 !important; }

/* Metric cards */
[data-testid="stMetric"] {
    background: #0A1628 !important;
    border: 0.5px solid rgba(55,138,221,0.18) !important;
    border-radius: 8px !important;
    padding: 12px 14px !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 10px !important;
    color: #888780 !important;
    letter-spacing: 0.05em !important;
}
[data-testid="stMetricValue"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 20px !important;
    color: #B5D4F4 !important;
}

/* Progress bar */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #185FA5, #378ADD) !important;
    border-radius: 3px !important;
}
[data-testid="stProgressBar"] {
    background: rgba(55,138,221,0.12) !important;
    border-radius: 3px !important;
    height: 6px !important;
}

/* Buttons */
.stButton > button {
    font-family: 'Syne', sans-serif !important;
    border-radius: 6px !important;
    border: 0.5px solid rgba(55,138,221,0.4) !important;
    background: transparent !important;
    color: #85B7EB !important;
    letter-spacing: 0.05em !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: rgba(55,138,221,0.12) !important;
    color: #E6F1FB !important;
}

/* End session button override */
.end-session-btn > button {
    border-color: rgba(226,75,74,0.5) !important;
    color: #F09595 !important;
}

/* Charts */
[data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] {
    background: #0A1628 !important;
    border-radius: 8px !important;
    border: 0.5px solid rgba(55,138,221,0.18) !important;
    padding: 12px !important;
}

/* Divider */
hr { border-color: rgba(55,138,221,0.15) !important; }

/* Warning */
[data-testid="stAlert"] {
    background: rgba(239,159,39,0.08) !important;
    border: 0.5px solid rgba(239,159,39,0.3) !important;
    border-radius: 8px !important;
    color: #EF9F27 !important;
}

/* Selectbox / radio */
[data-testid="stSelectbox"] select,
[data-testid="stRadio"] label {
    background: #0A1628 !important;
    color: #85B7EB !important;
}

/* Info box */
[data-testid="stInfo"] {
    background: rgba(55,138,221,0.08) !important;
    border: 0.5px solid rgba(55,138,221,0.25) !important;
    border-radius: 8px !important;
    color: #85B7EB !important;
}

/* Sidebar always expanded */
[data-testid="stSidebar"] {
    transform: none !important;
    visibility: visible !important;
}
[data-testid="stSidebar"][aria-expanded="false"] {
    margin-left: 0 !important;
    width: 230px !important;
    min-width: 230px !important;
}
/* Hide toggle buttons */
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Translations ──────────────────────────────────────────────────────────────
TRANSLATIONS = {
    "en": {
        # Sidebar
        "app_sub":           "EEG Monitor v1.0",
        "nav_session":       "SESSION",
        "nav_live":          "Live Monitor",
        "nav_summary":       "Summary",
        "nav_device":        "DEVICE",
        "connected":         "🟢 Connected",
        "disconnected":      "⚫ Disconnected",
        "nav_status":        "STATUS",
        "recording":         "● Recording",
        "baseline_ready":    "Baseline: Ready",
        "baseline_pending":  "Baseline: Collecting…",
        "language":          "LANGUAGE",

        # Baseline view
        "calibrating":       "Calibrating Baseline…",
        "baseline_info":     "Collecting {sec} / 30 sec — stay still and relaxed.",

        # Live monitor
        "live_monitor":      "Live Monitor",
        "end_session":       "⏹ End Session",
        "focus_score":       "Focus Score",
        "signal_quality":    "Signal Quality",
        "heart_rate":        "Heart Rate",
        "samples":           "Samples",
        "processed":         "Processed",
        "normal":            "Normal",
        "excellent":         "Excellent",
        "good":              "Good",
        "poor":              "Poor",
        "high_focus":        "High focus",
        "medium_focus":      "Medium focus",
        "low_focus":         "Low focus",
        "focus_gauge":       "FOCUS GAUGE",
        "focus_state_high":  "● HIGH FOCUS",
        "focus_state_mid":   "● MEDIUM FOCUS",
        "focus_state_low":   "● LOW FOCUS",
        "focus_trend":       "FOCUS TREND (last 60s)",
        "brainwave_power":   "BRAINWAVE POWER",
        "channel_activity":  "CHANNEL ACTIVITY (Alpha)",
        "poor_signal_warn":  "⚠️ Poor signal quality — adjust headset.",
        "session_time":      "Session Time",

        # Summary
        "session_summary":   "Session Summary",
        "new_session":       "+ New Session",
        "duration":          "Duration",
        "avg_focus":         "Avg Focus",
        "peak_focus":        "Peak Focus",
        "min_focus":         "Min Focus",
        "focus_timeline":    "FOCUS SCORE — FULL SESSION",
        "focus_zones":       "TIME IN FOCUS ZONES",
        "zone_high":         "High (>0.7)",
        "zone_mid":          "Medium (0.4–0.7)",
        "zone_low":          "Low (<0.4)",
        "avg_bands":         "AVG BRAINWAVE POWER",
        "insights":          "SESSION INSIGHTS",
        "insight_strong":    "You spent {pct}% of the time in high focus.",
        "insight_peak":      "Peak focus reached {val:.2f}.",
        "insight_low":       "Focus dipped to {val:.2f}.",
        "session_ended":     "● SESSION ENDED",

        "landing_title":        "🧠 NeuroFocus",
        "landing_subtitle":     "Choose how you'd like to explore this app",
        "demo_mode_title":      "📁 Demo Mode",
        "demo_mode_desc1":      "Upload a pre-recorded EEG session and replay it as if it were live.",
        "demo_mode_desc2":      "No device required.",
        "demo_mode_select_btn": "Select Demo Mode",
        "live_mode_title":      "📡 Live Mode",
        "live_mode_desc1":      "Connect to a Muse S Athena headset and monitor focus in real time.",
        "live_mode_desc2":      "Requires Bluetooth and the device.",
        "live_mode_select_btn": "Select Live Mode",

        "live_unavailable":  "Live mode is not available in this environment. Please run the app in a local environment with the required dependencies.",
        "live_page_title":   "🧠 NeuroFocus — Live Mode",
        "live_info":          "This will connect to your Muse S Athena headset via Bluetooth and start the inference pipeline. Make sure the device is powered on and nearby.",
        "live_start_btn":    "▶ Start Live Session",

        "demo_page_title":        "🧠 NeuroFocus — Demo Mode",
        "demo_info":               "Upload a recorded EEG session (.bin file) to simulate live monitoring.",
        "demo_uploader_label":     "Upload .bin file",
        "demo_start_uploaded_btn": "▶ Play uploaded file",
        "demo_start_sample_btn":  "▶ Use sample session",

        "demo_complete_title": "Demo session complete",
        "demo_complete_desc":  "The recorded session has finished playing.",
        "demo_replay_btn":     "🔁 Replay same file",
        "demo_new_file_btn":   "← Choose new file",

        "change_mode_btn": "← Change Mode",
        "demo_data_label": "📁 Demo data (replayed)",
    },
    "ja": {
        # Sidebar
        "app_sub":           "EEG モニター v1.0",
        "nav_session":       "セッション",
        "nav_live":          "ライブモニター",
        "nav_summary":       "サマリー",
        "nav_device":        "デバイス",
        "connected":         "🟢 接続中",
        "disconnected":      "⚫ 未接続",
        "nav_status":        "ステータス",
        "recording":         "● 記録中",
        "baseline_ready":    "ベースライン: 完了",
        "baseline_pending":  "ベースライン: 収集中…",
        "language":          "言語",

        # Baseline view
        "calibrating":       "ベースライン調整中…",
        "baseline_info":     "{sec} / 30 秒収集中 — なるべく動かず、リラックスしてください。",

        # Live monitor
        "live_monitor":      "ライブモニター",
        "end_session":       "⏹ セッション終了",
        "focus_score":       "集中スコア",
        "signal_quality":    "信号品質",
        "heart_rate":        "心拍数",
        "samples":           "サンプル数",
        "processed":         "処理済み",
        "normal":            "正常",
        "excellent":         "優秀",
        "good":              "良好",
        "poor":              "低品質",
        "high_focus":        "集中度： 高",
        "medium_focus":      "集中度： 中",
        "low_focus":         "集中度： 低",
        "focus_gauge":       "集中ゲージ",
        "focus_state_high":  "● 集中度： 高",
        "focus_state_mid":   "● 集中度： 中",
        "focus_state_low":   "● 集中度： 低",
        "focus_trend":       "集中スコアの推移（直近60秒）",
        "brainwave_power":   "脳波パワー",
        "channel_activity":  "チャンネル活動（アルファ波）",
        "poor_signal_warn":  "⚠️ 信号品質が低いです。ヘッドセットを調整してください。",
        "session_time":      "セッション時間",

        # Summary
        "session_summary":   "セッションサマリー",
        "new_session":       "+ 新しいセッション",
        "duration":          "セッション時間",
        "avg_focus":         "平均集中度",
        "peak_focus":        "最高集中度",
        "min_focus":         "最低集中度",
        "focus_timeline":    "集中スコア — セッション全体",
        "focus_zones":       "集中ゾーン別時間",
        "zone_high":         "高集中（>0.7）",
        "zone_mid":          "中程度（0.4〜0.7）",
        "zone_low":          "低集中（<0.4）",
        "avg_bands":         "平均脳波パワー",
        "insights":          "セッションインサイト",
        "insight_strong":    "高集中状態が {pct}% を占めました。",
        "insight_peak":      "集中のピークは {val:.2f} に達しました。",
        "insight_low":       "集中が {val:.2f} まで低下しました。",
        "session_ended":     "● セッション終了",

        "landing_title":        "🧠 NeuroFocus",
        "landing_subtitle":     "このアプリの体験方法を選んでください",
        "demo_mode_title":      "📁 デモモード",
        "demo_mode_desc1":      "事前に録音されたEEGセッションをアップロードし、ライブのように再生します。",
        "demo_mode_desc2":      "デバイスは不要です。",
        "demo_mode_select_btn": "デモモードを選択",
        "live_mode_title":      "📡 ライブモード",
        "live_mode_desc1":      "Muse S Athenaヘッドセットに接続し、リアルタイムで集中度を計測します。",
        "live_mode_desc2":      "Bluetoothとデバイスが必要です。",
        "live_mode_select_btn": "ライブモードを選択",

        "live_unavailable":  "ライブモードはこの環境では利用できません。必要な依存関係が整ったローカル環境で実行してください。",
        "live_page_title":   "🧠 NeuroFocus — ライブモード",
        "live_info":          "Muse S AthenaヘッドセットにBluetoothで接続し、推論パイプラインを開始します。デバイスの電源を入れ、近くに置いてください。",
        "live_start_btn":    "▶ ライブセッションを開始",

        "demo_page_title":        "🧠 NeuroFocus — デモモード",
        "demo_info":               "記録済みのEEGセッション（.binファイル）をアップロードして、ライブ計測を再現します。",
        "demo_uploader_label":     ".binファイルをアップロード",
        "demo_start_uploaded_btn": "▶ ファイルを再生",
        "demo_start_sample_btn":  "▶ サンプルセッションを使用",

        "demo_complete_title": "デモセッション終了",
        "demo_complete_desc":  "録音されたセッションの再生が完了しました。",
        "demo_replay_btn":     "🔁 同じファイルをもう一度再生",
        "demo_new_file_btn":   "← 別のファイルを選ぶ",

        "change_mode_btn": "← モードを変更",
        "demo_data_label": "📁 デモデータ（再生中）",
    }
}

def t(key, **kwargs):
    lang = st.session_state.get("lang", "en")
    text = TRANSLATIONS[lang].get(key, key)
    return text.format(**kwargs) if kwargs else text


# ─ MODE SELECTION ──────────────────────────────────────────────────────────────

if "app_mode" not in st.session_state:
    st.session_state.app_mode = None

def _start_demo_replay(bin_path, shared_state):
    import threading
    from app.demo.replay import replay_bin_file
    from src.eeg_focus_tracker.realtime_inference.realtime_pipeline import process_eeg,  process_heart_rate

    shared_state.baseline_ready     = False
    shared_state.baseline_progress  = 0.0
    shared_state.focus_value        = 0.0
    shared_state.session_active     = True
    shared_state.session_start_time = None
    shared_state.demo_finished      = False

    st.session_state.demo_started  = True
    st.session_state.demo_bin_path = bin_path

    def run_demo():
        def _on_finish():
            shared_state.demo_finished = True

        replay_bin_file(
            bin_path,
            callback=process_eeg,
            speed=4.0,
            on_finish=_on_finish,
            on_heart_rate=process_heart_rate,
        )

    thread = threading.Thread(target=run_demo, daemon=True)
    thread.start()
    st.rerun()


def _start_live_pipeline():
    import subprocess
    import sys

    try:
        from src.eeg_focus_tracker.realtime_inference import shared_state
    except ImportError:
        st.warning(t("live_unavailable"))
        return
    
    shared_state.baseline_ready     = False
    shared_state.baseline_progress  = 0.0
    shared_state.focus_value        = 0.0
    shared_state.prediction_started = False
    shared_state.session_active     = True
    shared_state.device_connected   = False
    shared_state.session_start_time = None

    process = subprocess.Popen(
        [sys.executable, "-m", "src.eeg_focus_tracker.realtime_inference.realtime_pipeline"],
        cwd=ROOT,
    )

    st.session_state.live_process = process
    st.session_state.live_started = True


if st.session_state.app_mode is None:
    col_spacer, col_lang_en, col_lang_ja = st.columns([6, 1, 1])
    with col_lang_en:
        if st.button("EN", key="landing_en"):
            st.session_state.lang = "en"
            st.rerun()
    with col_lang_ja:
        if st.button("JP", key="landing_ja"):
            st.session_state.lang = "ja"
            st.rerun()

    st.markdown("<div style='text-align:center; padding-top:20px;'>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:32px; font-weight:600;'>{t('landing_title')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:14px; color:#888780; margin-bottom:40px;'>{t('landing_subtitle')}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### {t('demo_mode_title')}")
        st.write(t("demo_mode_desc1"))
        st.write(t("demo_mode_desc2"))
        if st.button(t("demo_mode_select_btn"), use_container_width=True):
            st.session_state.app_mode = "Demo"
            st.rerun()

    with col2:
        st.markdown(f"### {t('live_mode_title')}")
        st.write(t("live_mode_desc1"))
        st.write(t("live_mode_desc2"))
        if st.button(t("live_mode_select_btn"), use_container_width=True):
            st.session_state.app_mode = "Live"
            st.rerun()

    st.stop()

mode = st.session_state.app_mode

if mode == "Demo":
    from src.eeg_focus_tracker.realtime_inference import shared_state

    if "demo_started" not in st.session_state:
        st.session_state.demo_started = False

    if not st.session_state.demo_started:
        col_spacer, col_lang_en, col_lang_ja = st.columns([6, 1, 1])
        with col_lang_en:
            if st.button("EN", key="demo_en"):
                st.session_state.lang = "en"
                st.rerun()
        with col_lang_ja:
            if st.button("JP", key="demo_ja"):
                st.session_state.lang = "ja"
                st.rerun()

        st.title(t("demo_page_title"))
        st.info(t("demo_info"))

        uploaded_file = st.file_uploader(t("demo_uploader_label"), type=["bin"])

        col_upload, col_sample = st.columns(2)

        with col_upload:
            if st.button(t("demo_start_uploaded_btn"),
                         disabled=uploaded_file is None,
                         use_container_width=True):
                import tempfile
                tmp_path = os.path.join(tempfile.gettempdir(), "demo_upload.bin")
                with open(tmp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                _start_demo_replay(tmp_path, shared_state)

        with col_sample:
            if st.button(t("demo_start_sample_btn"), use_container_width=True):
                sample_path = os.path.join(ROOT, "app", "demo", "data", "demo_session.bin")
                _start_demo_replay(sample_path, shared_state)

        st.stop()

elif mode == "Live":
    try:
        from src.eeg_focus_tracker.realtime_inference import shared_state
    except ImportError:
        st.warning(t("live_unavailable"))
        st.stop()

    if "live_started" not in st.session_state:
        st.session_state.live_started = False
    if "live_process" not in st.session_state:
        st.session_state.live_process = None

    if not st.session_state.live_started:
        col_spacer, col_lang_en, col_lang_ja = st.columns([6, 1, 1])
        with col_lang_en:
            if st.button("EN", key="live_en"):
                st.session_state.lang = "en"
                st.rerun()
        with col_lang_ja:
            if st.button("日本語", key="live_ja"):
                st.session_state.lang = "ja"
                st.rerun()

        st.title(t("live_page_title"))
        st.info(t("live_info"))

        if st.button(t("live_start_btn"), type="primary", use_container_width=True):
            _start_live_pipeline()
            st.rerun()

        st.stop()

# ── Session state init ────────────────────────────────────────────────────────
for k, v in {
    "focus_history": [],
    "timestamps": [],
    "session_ended": False,
    "summary": None,
    "lang": "en",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_duration(secs):
    m, s = divmod(int(secs), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"

def focus_color(val):
    if val > 0.7:  return "normal"
    if val > 0.4:  return "off"
    return "inverse"

def focus_label(val):
    if val > 0.7:  return t("high_focus")
    if val > 0.4:  return t("medium_focus")
    return t("low_focus")

def focus_state(val):
    if val > 0.7:  return t("focus_state_high")
    if val > 0.4:  return t("focus_state_mid")
    return t("focus_state_low")

def sq_label(val):
    if val >= 0.85: return t("excellent")
    if val >= 0.6:  return t("good")
    return t("poor")

def reset_session():
    st.session_state.focus_history = []
    st.session_state.timestamps = []
    st.session_state.session_ended = False
    st.session_state.summary = None
    shared_state.baseline_ready   = False
    shared_state.baseline_progress = 0.0
    shared_state.focus_value       = 0.0
    shared_state.theta_power       = 0.0
    shared_state.alpha_power       = 0.0
    shared_state.beta_power        = 0.0
    shared_state.signal_quality    = 1.0
    shared_state.session_start_time = None
    shared_state.channel_power     = {"TP9": 0, "AF7": 0, "AF8": 0, "TP10": 0}
    shared_state.session_active    = True
    shared_state.demo_finished     = False
    shared_state.prediction_started = False

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:0 0 14px 0;border-bottom:0.5px solid rgba(55,138,221,0.15);margin-bottom:16px;">
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:28px;height:28px;border-radius:6px;background:#185FA5;display:flex;align-items:center;justify-content:center;font-size:14px;">🧠</div>
        <div>
          <div style="font-size:13px;font-weight:600;color:#B5D4F4;letter-spacing:0.03em;">NeuroFocus</div>
          <div style="font-size:10px;color:#888780;font-family:'DM Mono',monospace;">{t('app_sub')}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div style='font-size:9px;letter-spacing:0.12em;color:#888780;font-family:DM Mono,monospace;margin-bottom:8px;'>{t('nav_session')}</div>", unsafe_allow_html=True)

    if st.session_state.session_ended:
        st.markdown(f"<div style='padding:7px 10px;border-radius:6px;font-size:12px;color:#85B7EB;'>📡 {t('nav_live')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='padding:7px 10px;border-radius:6px;background:rgba(55,138,221,0.15);font-size:12px;color:#B5D4F4;'>📊 {t('nav_summary')}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='padding:7px 10px;border-radius:6px;background:rgba(55,138,221,0.15);font-size:12px;color:#B5D4F4;'>📡 {t('nav_live')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='padding:7px 10px;border-radius:6px;font-size:12px;color:#85B7EB;'>📊 {t('nav_summary')}</div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:9px;letter-spacing:0.12em;color:#888780;font-family:DM Mono,monospace;margin-bottom:8px;'>{t('nav_device')}</div>", unsafe_allow_html=True)

    if mode == "Demo":
        conn_text  = t("demo_data_label")
        conn_color = "#85B7EB"
    else:
        is_connected = bool(getattr(shared_state, "device_connected", False))
        conn_text  = t("connected") if is_connected else t("disconnected")
        conn_color = "#1D9E75" if is_connected else "#888780"

    st.markdown(f"""
    <div style='padding:8px 10px;'>
      <div style='font-size:11px;color:#85B7EB;margin-bottom:4px;'>MuseS-0AD4</div>
      <div style='font-size:10px;color:{conn_color};font-family:DM Mono,monospace;'>{conn_text}</div>
      <div style='font-size:9px;color:#888780;margin-top:4px;font-family:DM Mono,monospace;'>SF: 256 Hz · Window: 6s</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:9px;letter-spacing:0.12em;color:#888780;font-family:DM Mono,monospace;margin-bottom:8px;'>{t('nav_status')}</div>", unsafe_allow_html=True)

    baseline_ok = shared_state.baseline_ready
    st.markdown(f"""
    <div style='background:rgba(55,138,221,0.08);border:0.5px solid rgba(55,138,221,0.2);border-radius:8px;padding:12px;'>
      <div style='font-size:11px;color:#85B7EB;font-family:DM Mono,monospace;'>{t('recording')}</div>
      <div style='font-size:10px;color:#888780;margin-top:4px;font-family:DM Mono,monospace;'>{t('baseline_ready') if baseline_ok else t('baseline_pending')}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:9px;letter-spacing:0.12em;color:#888780;font-family:DM Mono,monospace;margin-bottom:8px;'>{t('language')}</div>", unsafe_allow_html=True)

    col_en, col_ja = st.columns(2)
    with col_en:
        if st.button("EN", use_container_width=True):
            st.session_state.lang = "en"
            st.rerun()
    with col_ja:
        if st.button("JP", use_container_width=True):
            st.session_state.lang = "ja"
            st.rerun()

    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

    if st.button(t("change_mode_btn"), use_container_width=True):
        shared_state.session_active = False

        if st.session_state.get("live_process"):
            try:
                st.session_state.live_process.wait(timeout=3)
            except Exception:
                st.session_state.live_process.terminate()
            st.session_state.live_process = None

        st.session_state.live_started = False
        st.session_state.focus_history = []
        st.session_state.timestamps = []
        st.session_state.signal_quality_history = []
        st.session_state.session_ended = False
        st.session_state.summary = None
        st.session_state.demo_started = False

        shared_state.baseline_ready     = False
        shared_state.baseline_progress  = 0.0
        shared_state.focus_value        = 0.0
        shared_state.prediction_started = False
        shared_state.demo_finished      = False
        shared_state.session_start_time = None

        st.session_state.app_mode = None
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# VIEW 1 — SESSION SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.session_ended and st.session_state.summary:
    s = st.session_state.summary

    st.markdown(f"<div style='padding:20px 20px 0;font-size:15px;font-weight:600;color:#E6F1FB;'>{t('session_summary')}</div>", unsafe_allow_html=True)

    if s.get("is_demo"):
        st.markdown(f"""
        <div style='margin:10px 20px 0;padding:10px 14px;background:rgba(55,138,221,0.1);
                    border:0.5px solid rgba(55,138,221,0.3);border-radius:8px;
                    font-size:12px;color:#85B7EB;'>
          ✅ {t('demo_complete_title')} — {t('demo_complete_desc')}
        </div>
        """, unsafe_allow_html=True)

    with st.container():
        st.markdown("<div style='padding:0 20px;'>", unsafe_allow_html=True)

        # Top metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t("duration"),    fmt_duration(s["duration"]))
        c2.metric(t("avg_focus"),   f"{s['avg_focus']:.2f}")
        c3.metric(t("peak_focus"),  f"{s['peak_focus']:.2f}")
        c4.metric(t("min_focus"),   f"{s['min_focus']:.2f}")

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

        # Full session focus timeline (colored bar chart)
        st.markdown(f"<div style='background:#0A1628;border:0.5px solid rgba(55,138,221,0.18);border-radius:8px;padding:14px;margin-bottom:10px;'><div style='font-size:10px;letter-spacing:0.1em;color:#888780;font-family:DM Mono,monospace;margin-bottom:10px;'>{t('focus_timeline')}</div>", unsafe_allow_html=True)

        df_timeline = pd.DataFrame({
            "Time (s)": s["timestamps"],
            "Focus":    s["focus_history"],
        })
        df_timeline["color"] = df_timeline["Focus"].apply(
            lambda v: "#639922" if v > 0.7 else ("#BA7517" if v > 0.4 else "#A32D2D")
        )

        import altair as alt
        chart = alt.Chart(df_timeline).mark_bar(size=3).encode(
            x=alt.X("Time (s):Q", axis=alt.Axis(labelColor="#888780", tickColor="#888780", domainColor="transparent", gridColor="rgba(55,138,221,0.08)", labelFont="DM Mono", labelFontSize=10)),
            y=alt.Y("Focus:Q", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(labelColor="#888780", tickColor="#888780", domainColor="transparent", gridColor="rgba(55,138,221,0.08)", labelFont="DM Mono", labelFontSize=10, tickCount=5)),
            color=alt.Color("color:N", scale=None),
            tooltip=["Time (s)", alt.Tooltip("Focus:Q", format=".2f")]
        ).properties(height=120).configure_view(strokeWidth=0, fill="#0A1628").configure(background="#0A1628")

        st.altair_chart(chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Two columns: zones + insights
        col_left, col_right = st.columns(2)

        with col_left:
            n = len(s["focus_history"])
            high_pct   = sum(1 for f in s["focus_history"] if f > 0.7)  / n * 100 if n else 0
            medium_pct = sum(1 for f in s["focus_history"] if 0.4 < f <= 0.7) / n * 100 if n else 0
            low_pct    = sum(1 for f in s["focus_history"] if f <= 0.4) / n * 100 if n else 0

            st.markdown(f"""
            <div style='background:#0A1628;border:0.5px solid rgba(55,138,221,0.18);border-radius:8px;padding:14px;margin-bottom:10px;'>
              <div style='font-size:10px;letter-spacing:0.1em;color:#888780;font-family:DM Mono,monospace;margin-bottom:12px;'>{t('focus_zones')}</div>
              <div style='display:flex;align-items:center;gap:8px;margin-bottom:10px;'>
                <div style='width:8px;height:8px;border-radius:50%;background:#97C459;flex-shrink:0;'></div>
                <div style='font-size:11px;color:#85B7EB;width:120px;'>{t('zone_high')}</div>
                <div style='flex:1;height:6px;background:rgba(55,138,221,0.1);border-radius:3px;overflow:hidden;'><div style='height:100%;width:{high_pct:.0f}%;background:#639922;border-radius:3px;'></div></div>
                <div style='font-size:11px;font-family:DM Mono,monospace;color:#B5D4F4;width:36px;text-align:right;'>{high_pct:.0f}%</div>
              </div>
              <div style='display:flex;align-items:center;gap:8px;margin-bottom:10px;'>
                <div style='width:8px;height:8px;border-radius:50%;background:#EF9F27;flex-shrink:0;'></div>
                <div style='font-size:11px;color:#85B7EB;width:120px;'>{t('zone_mid')}</div>
                <div style='flex:1;height:6px;background:rgba(55,138,221,0.1);border-radius:3px;overflow:hidden;'><div style='height:100%;width:{medium_pct:.0f}%;background:#BA7517;border-radius:3px;'></div></div>
                <div style='font-size:11px;font-family:DM Mono,monospace;color:#B5D4F4;width:36px;text-align:right;'>{medium_pct:.0f}%</div>
              </div>
              <div style='display:flex;align-items:center;gap:8px;margin-bottom:14px;'>
                <div style='width:8px;height:8px;border-radius:50%;background:#F09595;flex-shrink:0;'></div>
                <div style='font-size:11px;color:#85B7EB;width:120px;'>{t('zone_low')}</div>
                <div style='flex:1;height:6px;background:rgba(55,138,221,0.1);border-radius:3px;overflow:hidden;'><div style='height:100%;width:{low_pct:.0f}%;background:#A32D2D;border-radius:3px;'></div></div>
                <div style='font-size:11px;font-family:DM Mono,monospace;color:#B5D4F4;width:36px;text-align:right;'>{low_pct:.0f}%</div>
              </div>
              <div style='font-size:10px;letter-spacing:0.1em;color:#888780;font-family:DM Mono,monospace;margin-bottom:10px;'>{t('avg_bands')}</div>
              <div style='display:flex;align-items:center;gap:8px;margin-bottom:8px;'>
                <div style='font-size:10px;font-family:DM Mono,monospace;color:#888780;width:36px;'>θ</div>
                <div style='flex:1;height:6px;background:rgba(55,138,221,0.1);border-radius:3px;overflow:hidden;'><div style='height:100%;width:{min(s.get("avg_theta",0.4)*100,100):.0f}%;background:#85B7EB;border-radius:3px;'></div></div>
                <div style='font-size:10px;font-family:DM Mono,monospace;color:#85B7EB;width:32px;text-align:right;'>{s.get("avg_theta",0.4):.2f}</div>
              </div>
              <div style='display:flex;align-items:center;gap:8px;margin-bottom:8px;'>
                <div style='font-size:10px;font-family:DM Mono,monospace;color:#888780;width:36px;'>α</div>
                <div style='flex:1;height:6px;background:rgba(55,138,221,0.1);border-radius:3px;overflow:hidden;'><div style='height:100%;width:{min(s.get("avg_alpha",0.6)*100,100):.0f}%;background:#378ADD;border-radius:3px;'></div></div>
                <div style='font-size:10px;font-family:DM Mono,monospace;color:#85B7EB;width:32px;text-align:right;'>{s.get("avg_alpha",0.6):.2f}</div>
              </div>
              <div style='display:flex;align-items:center;gap:8px;'>
                <div style='font-size:10px;font-family:DM Mono,monospace;color:#888780;width:36px;'>β</div>
                <div style='flex:1;height:6px;background:rgba(55,138,221,0.1);border-radius:3px;overflow:hidden;'><div style='height:100%;width:{min(s.get("avg_beta",0.75)*100,100):.0f}%;background:#185FA5;border-radius:3px;'></div></div>
                <div style='font-size:10px;font-family:DM Mono,monospace;color:#85B7EB;width:32px;text-align:right;'>{s.get("avg_beta",0.75):.2f}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        with col_right:
            insights_html = f"""
            <div style='background:#0A1628;border:0.5px solid rgba(55,138,221,0.18);border-radius:8px;padding:18px;'>
            <div style='font-size:11px;letter-spacing:0.1em;color:#888780;font-family:DM Mono,monospace;margin-bottom:16px;'>{t('insights')}</div>
            <div style='display:flex;gap:14px;align-items:flex-start;padding:16px 0;border-bottom:0.5px solid rgba(55,138,221,0.1);'>
                <div style='width:36px;height:36px;border-radius:8px;background:rgba(99,153,34,0.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:18px;'>🎯</div>
                <div style='font-size:13px;color:#85B7EB;line-height:1.7;padding-top:4px;'>{t('insight_strong', pct=int(high_pct))}</div>
            </div>
            <div style='display:flex;gap:14px;align-items:flex-start;padding:16px 0;border-bottom:0.5px solid rgba(55,138,221,0.1);'>
                <div style='width:36px;height:36px;border-radius:8px;background:rgba(55,138,221,0.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:18px;'>📈</div>
                <div style='font-size:13px;color:#85B7EB;line-height:1.7;padding-top:4px;'>{t('insight_peak', val=s['peak_focus'])}</div>
            </div>
            <div style='display:flex;gap:14px;align-items:flex-start;padding:16px 0;'>
                <div style='width:36px;height:36px;border-radius:8px;background:rgba(239,159,39,0.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:18px;'>⚠️</div>
                <div style='font-size:13px;color:#85B7EB;line-height:1.7;padding-top:4px;'>{t('insight_low', val=s['min_focus'])}</div>
            </div>
            </div>
            """
            st.markdown(insights_html, unsafe_allow_html=True)

        if s.get("is_demo"):
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(t("demo_replay_btn"), use_container_width=True):
                    reset_session()
                    _start_demo_replay(st.session_state.demo_bin_path, shared_state)
            with col_b:
                if st.button(t("demo_new_file_btn"), use_container_width=True):
                    st.session_state.app_mode = None
                    st.session_state.demo_started = False
                    reset_session()
                    st.rerun()
        else:
            if st.button(t("new_session"), type="primary", use_container_width=True):
                reset_session()
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# VIEW 2 — BASELINE CALIBRATION
# ══════════════════════════════════════════════════════════════════════════════
if not shared_state.baseline_ready:
    st.markdown(f"<div style='padding:40px 20px 10px;font-size:15px;font-weight:600;color:#E6F1FB;'>🧠 NeuroFocus</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='padding:0 20px;font-size:13px;color:#85B7EB;margin-bottom:20px;'>{t('calibrating')}</div>", unsafe_allow_html=True)

    progress = min(float(shared_state.baseline_progress), 1.0)
    sec_collected = int(progress * 30)

    with st.container():
        st.markdown("<div style='padding:0 20px;'>", unsafe_allow_html=True)
        st.progress(progress)
        st.info(t("baseline_info", sec=sec_collected))
        st.markdown("</div>", unsafe_allow_html=True)

    time.sleep(0.5)
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# VIEW 3 — LIVE MONITOR
# ══════════════════════════════════════════════════════════════════════════════

if (mode == "Demo"
        and getattr(shared_state, "demo_finished", False)
        and not st.session_state.session_ended):

    history = st.session_state.focus_history
    if history:
        st.session_state.summary = {
            "duration":      st.session_state.timestamps[-1] if st.session_state.timestamps else 0,
            "avg_focus":     sum(history) / len(history),
            "peak_focus":    max(history),
            "min_focus":     min(history),
            "focus_history": list(history),
            "timestamps":    list(st.session_state.timestamps),
            "avg_theta":     float(shared_state.theta_power),
            "avg_alpha":     float(shared_state.alpha_power),
            "avg_beta":      float(shared_state.beta_power),
            "is_demo":       True,   # ← VIEW1でバナー・ボタンを切り替えるためのフラグ
        }
    st.session_state.session_ended = True
    st.rerun()

# Record sample
focus = float(shared_state.focus_value)
t0    = shared_state.session_start_time

elapsed = time.time() - float(t0) if t0 else 0

if t0 and getattr(shared_state, "prediction_started", False):
    st.session_state.focus_history.append(focus)
    st.session_state.timestamps.append(round(elapsed, 1))

st.markdown(f"<div style='padding:20px 20px 0;'>", unsafe_allow_html=True)

# Top bar
col_title, col_timer, col_end = st.columns([3, 2, 1])
with col_title:
    st.markdown(f"<div style='font-size:15px;font-weight:600;color:#E6F1FB;padding-top:4px;'>{t('live_monitor')}</div>", unsafe_allow_html=True)
with col_timer:
    if t0:
        m, s = divmod(int(elapsed), 60)
        h, m = divmod(m, 60)
        timer_str = f"{h:02d}:{m:02d}:{s:02d}"
    else:
        timer_str = "00:00:00"
    st.markdown(f"<div style='font-family:DM Mono,monospace;font-size:18px;color:#378ADD;letter-spacing:0.05em;padding-top:2px;'>{timer_str}</div>", unsafe_allow_html=True)
with col_end:
    st.markdown('<div class="end-session-btn">', unsafe_allow_html=True)
    if st.button(t("end_session"), use_container_width=True):
        shared_state.session_active = False
        if mode == "Live" and st.session_state.get("live_process"):
            try:
                st.session_state.live_process.wait(timeout=5)
            except Exception:
                st.session_state.live_process.terminate() 
        history = st.session_state.focus_history
        if history:
            st.session_state.summary = {
                "duration":      elapsed if t0 else 0,
                "avg_focus":     sum(history) / len(history),
                "peak_focus":    max(history),
                "min_focus":     min(history),
                "focus_history": list(history),
                "timestamps":    list(st.session_state.timestamps),
                "avg_theta":     float(shared_state.theta_power),
                "avg_alpha":     float(shared_state.alpha_power),
                "avg_beta":      float(shared_state.beta_power),
            }
        st.session_state.session_ended = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

# Metrics row
sq = float(shared_state.signal_quality)
m1, m2, m3, m4 = st.columns(4)
m1.metric(t("focus_score"),    f"{focus:.2f}",  delta=focus_label(focus))
m2.metric(t("signal_quality"), f"{sq:.2f}",     delta=sq_label(sq))
hr = float(shared_state.heart_rate) if hasattr(shared_state, 'heart_rate') else 0.0
hr_str = f"{hr:.0f} BPM" if hr > 0 else "— BPM"
m3.metric(t("heart_rate"), hr_str, delta=t("normal"))
m4.metric(t("samples"),        f"{len(st.session_state.focus_history):,}", delta=t("processed"))

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

# Focus gauge + trend
col_gauge, col_trend = st.columns(2)

with col_gauge:
    arc_len = 175.9
    offset = arc_len * (1 - focus)
    if focus > 0.7:
        arc_color = "#97C459"
    elif focus > 0.4:
        arc_color = "#EF9F27"
    else:
        arc_color = "#F09595"

    st.markdown(f"""
    <div style='background:#0A1628;border:0.5px solid rgba(55,138,221,0.18);border-radius:8px;padding:14px;'>
      <div style='font-size:10px;letter-spacing:0.1em;color:#888780;font-family:DM Mono,monospace;margin-bottom:10px;'>{t('focus_gauge')}</div>
      <div style='display:flex;flex-direction:column;align-items:center;gap:6px;'>
        <svg width="140" height="80" viewBox="0 0 140 80">
          <path d="M 14 70 A 56 56 0 0 1 126 70" fill="none" stroke="rgba(55,138,221,0.12)" stroke-width="10" stroke-linecap="round"/>
          <path d="M 14 70 A 56 56 0 0 1 126 70" fill="none" stroke="{arc_color}" stroke-width="10" stroke-linecap="round"
            stroke-dasharray="{arc_len}" stroke-dashoffset="{offset:.1f}"/>
          <circle cx="70" cy="70" r="4" fill="{arc_color}"/>
        </svg>
        <div style='font-size:28px;font-weight:600;font-family:DM Mono,monospace;color:#B5D4F4;'>{focus:.2f}</div>
        <div style='font-size:11px;font-weight:500;color:{arc_color};letter-spacing:0.05em;'>{focus_state(focus)}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_trend:
    st.markdown(f"""
    <div style='background:#0A1628;border:0.5px solid rgba(55,138,221,0.18);border-radius:8px;padding:14px;'>
      <div style='font-size:10px;letter-spacing:0.1em;color:#888780;font-family:DM Mono,monospace;margin-bottom:4px;'>{t('focus_trend')}</div>
    """, unsafe_allow_html=True)

    if st.session_state.focus_history:
        recent_n = min(60, len(st.session_state.focus_history))
        trend_df = pd.DataFrame({
            "Time (s)": st.session_state.timestamps[-recent_n:],
            "Focus":    st.session_state.focus_history[-recent_n:],
        })
        import altair as alt
        trend_chart = alt.Chart(trend_df).mark_area(
            line={"color": "#378ADD", "strokeWidth": 1.5},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color="rgba(55,138,221,0.3)", offset=0),
                    alt.GradientStop(color="rgba(55,138,221,0.0)", offset=1),
                ],
                x1=1, x2=1, y1=1, y2=0,
            ),
            interpolate="monotone",
        ).encode(
            x=alt.X("Time (s):Q", axis=alt.Axis(labelColor="#888780", labelFont="DM Mono", labelFontSize=9, domainColor="transparent", tickColor="transparent", gridColor="rgba(55,138,221,0.07)")),
            y=alt.Y("Focus:Q", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(labelColor="#888780", labelFont="DM Mono", labelFontSize=9, domainColor="transparent", tickColor="transparent", gridColor="rgba(55,138,221,0.07)", tickCount=4)),
        ).properties(height=110).configure_view(strokeWidth=0, fill="#0A1628").configure(background="#0A1628")
        st.altair_chart(trend_chart, use_container_width=True)
    else:
        st.markdown("<div style='height:110px;display:flex;align-items:center;justify-content:center;color:#888780;font-size:11px;font-family:DM Mono,monospace;'>Waiting for data…</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

# Brainwave + channels
col_bands, col_ch = st.columns(2)

theta = float(shared_state.theta_power)
alpha = float(shared_state.alpha_power)
beta  = float(shared_state.beta_power)
max_band = max(theta, alpha, beta, 0.001)

with col_bands:
    t_pct = int(theta / max_band * 100)
    a_pct = int(alpha / max_band * 100)
    b_pct = int(beta  / max_band * 100)
    st.markdown(f"""
    <div style='background:#0A1628;border:0.5px solid rgba(55,138,221,0.18);border-radius:8px;padding:14px;'>
      <div style='font-size:10px;letter-spacing:0.1em;color:#888780;font-family:DM Mono,monospace;margin-bottom:12px;'>{t('brainwave_power')}</div>
      <div style='display:flex;align-items:center;gap:8px;margin-bottom:10px;'>
        <div style='font-size:10px;font-family:DM Mono,monospace;color:#888780;width:36px;'>θ Theta</div>
        <div style='flex:1;height:6px;background:rgba(55,138,221,0.1);border-radius:3px;overflow:hidden;'><div style='height:100%;width:{t_pct}%;background:#85B7EB;border-radius:3px;'></div></div>
        <div style='font-size:10px;font-family:DM Mono,monospace;color:#85B7EB;width:40px;text-align:right;'>{theta:.3f}</div>
      </div>
      <div style='display:flex;align-items:center;gap:8px;margin-bottom:10px;'>
        <div style='font-size:10px;font-family:DM Mono,monospace;color:#888780;width:36px;'>α Alpha</div>
        <div style='flex:1;height:6px;background:rgba(55,138,221,0.1);border-radius:3px;overflow:hidden;'><div style='height:100%;width:{a_pct}%;background:#378ADD;border-radius:3px;'></div></div>
        <div style='font-size:10px;font-family:DM Mono,monospace;color:#85B7EB;width:40px;text-align:right;'>{alpha:.3f}</div>
      </div>
      <div style='display:flex;align-items:center;gap:8px;'>
        <div style='font-size:10px;font-family:DM Mono,monospace;color:#888780;width:36px;'>β Beta</div>
        <div style='flex:1;height:6px;background:rgba(55,138,221,0.1);border-radius:3px;overflow:hidden;'><div style='height:100%;width:{b_pct}%;background:#185FA5;border-radius:3px;'></div></div>
        <div style='font-size:10px;font-family:DM Mono,monospace;color:#85B7EB;width:40px;text-align:right;'>{beta:.3f}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_ch:
    ch = dict(shared_state.channel_power)
    ch_max = max(ch.values(), default=0.001)

    ch_cards_html = ""
    for name, val in ch.items():
        pct = int(val / ch_max * 100) if ch_max > 0 else 0
        ch_cards_html += (
            "<div style='background:rgba(55,138,221,0.06);border:0.5px solid rgba(55,138,221,0.15);"
            "border-radius:6px;padding:8px 10px;'>"
            f"<div style='font-size:10px;font-family:DM Mono,monospace;color:#888780;'>{name}</div>"
            f"<div style='font-size:14px;font-weight:600;font-family:DM Mono,monospace;color:#85B7EB;margin-top:2px;'>{val:.3f}</div>"
            "<div style='height:3px;background:rgba(55,138,221,0.15);border-radius:2px;margin-top:6px;overflow:hidden;'>"
            f"<div style='height:100%;width:{pct}%;background:#378ADD;border-radius:2px;'></div>"
            "</div></div>"
        )

    st.markdown(
        "<div style='background:#0A1628;border:0.5px solid rgba(55,138,221,0.18);border-radius:8px;padding:14px;'>"
        f"<div style='font-size:10px;letter-spacing:0.1em;color:#888780;font-family:DM Mono,monospace;margin-bottom:12px;'>{t('channel_activity')}</div>"
        f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;'>{ch_cards_html}</div>"
        "</div>",
        unsafe_allow_html=True
    )

# Poor signal warning
if sq < 0.5:
    st.warning(t("poor_signal_warn"))

st.markdown("</div>", unsafe_allow_html=True)

# Auto-refresh
if shared_state.session_active:
    time.sleep(0.5)
    st.rerun()