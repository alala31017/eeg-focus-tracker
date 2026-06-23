import os
import csv
import asyncio
import time
import chime
import json
from muse_stream_client import MuseStreamClient
from muse_discovery import find_muse_devices
chime.theme('sonic')


async def main():
    events = []

    # 1. enter session number
    session_num = int(input('Enter session number: '))

    # 2. set condition (odd = focus first; even = distraction first)
    condition = 'focus_first' if session_num % 2 != 0 else 'distraction_first'

    # 3. connect muse device
    for _ in range(3):
        devices = await find_muse_devices(timeout=10.0)
        if devices:
            break
    if not devices:
        print("No Muse device found!")
        return

    device = devices[0]
    print(f"Found: {device.name}")

    # 4. start recording
    client = MuseStreamClient(
        save_raw=True,
        decode_realtime=False,
        data_dir="data/recordings",
        verbose=True
    )

    # Connect and stream
    stream_task = asyncio.create_task(
        client.connect_and_stream(
            device.address,
            duration_seconds=0,
            preset='p1035'
        )
    )

    start_time = time.time()
    print("Recording started. Prepare for baseline...")
    await asyncio.sleep(2)  # Stabilizing

    # 5. baseline
    await asyncio.to_thread(input, "Press Enter to start baseline")
    events.append(("baseline_start", time.time() - start_time))
    print('Baseline recording started!')
    await timer(300)
    events.append(("baseline_end", time.time() - start_time))

    # 6. task1
    if condition == 'focus_first':
        print("\nTask 1: Focus Task")
    else:
        print("\nTask 1: Distraction Task")

    await asyncio.to_thread(input, "Press Enter to start Task 1")
    events.append(("task1_start", time.time() - start_time))
    print('Task 1 recording started!')
    await timer(600)
    events.append(("task1_end", time.time() - start_time))

    # 7. break
    print("\n5 minute break")
    events.append(("break_start", time.time() - start_time))
    print('Break recording started!')
    await timer(300)
    events.append(("break_end", time.time() - start_time))

    # 8. task2
    if condition == 'focus_first':
        print("\nTask 2: Distraction Task")
    else:
        print("\nTask 2: Focus Task")

    await asyncio.to_thread(input, "Press Enter to start Task 2")
    events.append(("task2_start", time.time() - start_time))
    print('Task 2 recording started!')
    await timer(600)
    events.append(("task2_end", time.time() - start_time))

    # 9. stop recording
    print("Stopping recording...")
    stream_task.cancel()
    try:
        await stream_task
    except asyncio.CancelledError:
        pass


    # 10. save
    summary = client.get_summary()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    if 'file_info' in summary:
        old_path = summary['file_info']['filepath']
        new_path = os.path.join("data/recordings", f"session{session_num}_{condition}_{timestamp}.bin")
        os.rename(old_path, new_path)
        print(f"Renamed to: {new_path}")

    events_path = os.path.join("data/recordings", f"session{session_num}_events.csv")
    with open(events_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["event", "time"])
        writer.writerows(events)

    current_hour = time.localtime().tm_hour
    if 5 <= current_hour < 12:
        time_of_day = "morning"
    elif 12 <= current_hour < 18:
        time_of_day = "afternoon"
    elif 18 <= current_hour < 23:
        time_of_day = "evening"
    else:
        time_of_day = "night"

    metadata = {
        "session": session_num,
        "condition": condition,
        "time of day": time_of_day,
        "hour": current_hour,
        "sampling_rate": 256,
        "durations": {
            "baseline": 300,
            "task": 600,
            "break": 300
        }
    }

    with open(os.path.join("data/recordings", f"session{session_num}_meta.json"), "w") as f:
        json.dump(metadata, f, indent=2)


async def timer(seconds):
    await asyncio.sleep(seconds)
    print(f"\n{seconds/60} min finished!")
    chime.info()


if __name__ == '__main__':
    asyncio.run(main())