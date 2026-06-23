import time
import numpy as np
from muse_raw_stream import MuseRawStream
from muse_realtime_decoder import MuseRealtimeDecoder


def replay_bin_file(bin_path, callback, speed=1.0, on_finish=None, on_heart_rate=None):
    """
    保存された.binファイルを読み込み、あたかもリアルタイムで
    EEGデータが届いているかのようにcallbackを呼び出す。

    Args:
        bin_path: 再生する.binファイルのパス
        callback: 各チャンクを処理する関数（process_eegと同じ形式）
        speed: 再生速度（1.0=実時間、2.0=2倍速など）
    """
    stream = MuseRawStream(bin_path)
    stream.open_read()
    decoder = MuseRealtimeDecoder()

    last_timestamp = None

    for packet in stream.read_packets():
        decoded = decoder.decode(packet.data, packet.timestamp)

        if decoded.heart_rate and on_heart_rate:
            on_heart_rate(decoded.heart_rate)

        if decoded.eeg:
            if last_timestamp is not None:
                elapsed = (decoded.timestamp - last_timestamp).total_seconds()
                time.sleep(max(0, elapsed / speed))
            last_timestamp = decoded.timestamp

            callback({'channels': decoded.eeg, 'timestamp': decoded.timestamp})

    stream.close()

    if on_finish:
        on_finish() 