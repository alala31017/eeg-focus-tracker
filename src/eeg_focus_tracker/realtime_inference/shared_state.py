import json
import os

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")

_defaults = {
    "focus_value": 0.0,
    "baseline_ready": False,
    "baseline_progress": 0.0,
    "heart_rate": 0.0,
    "theta_power": 0.0,
    "alpha_power": 0.0,
    "beta_power": 0.0,
    "signal_quality": 1.0,
    "channel_power": {"TP9": 0, "AF7": 0, "AF8": 0, "TP10": 0},
    "session_start_time": None,
    "session_active": True,
    "device_connected": False, 
    "demo_finished": False, 
}

def _read():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return dict(_defaults)

def _write(state):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, STATE_FILE)  # atomic on all platforms

def _get(key):
    try:
        state = _read()
    except Exception:
        state = dict(_defaults)

    if key in state:
        return state[key]
    if key in _defaults:
        return _defaults[key]

    raise AttributeError(key)

def _set(key, value):
    state = _read()
    state[key] = value
    _write(state)

# --- property-style access so existing code requires minimal changes ---

class _StateProxy:
    def __getattr__(self, key):
        if key.startswith("_"):
            raise AttributeError(key)
        return _get(key)

    def __setattr__(self, key, value):
        if key.startswith("_"):
            super().__setattr__(key, value)
        else:
            _set(key, value)

# replace module-level variables with proxy
import sys
sys.modules[__name__] = _StateProxy()