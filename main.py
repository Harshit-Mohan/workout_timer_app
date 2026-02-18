import eventlet
eventlet.monkey_patch()
import time
import random
import uuid
import threading
import json
import os
import re
import requests
import html
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# ================= DYNAMIC DATA STORE =================
# Base building blocks (Lists of exercises)
BASE_ROUTINES = {
    "daily_warmup": [ 
        ("GET READY", 10, "prep"), 
        ("CLOCKWISE ARM ROTATION", 15, "work"), ("ANTI CLOCKWISE ARM ROTATION", 15, "work"), 
        ("CLAP ARM", 15, "work"), ("ARM UP", 15, "work"), 
        ("ELBOW HOLD RIGHT", 15, "work"), ("ELBOW HOLD LEFT", 15, "work"), 
        ("RIGHT PALM HOLD UP", 15, "work"), ("PALM HOLD DOWN", 15, "work"), 
        ("THUMB HOLD UP", 15, "work"), ("PALM HOLD REVERSE", 15, "work"), 
        ("LEFT PALM HOLD UP", 15, "work"), ("PALM HOLD DOWN", 15, "work"), 
        ("THUMB HOLD UP", 15, "work"), ("PALM HOLD REVERSE", 15, "work"), 
        ("HIP CLOCKWISE", 15, "work"), ("HIP ANTI-CLOCKWISE", 15, "work"), 
        ("RIGHT LEG UP", 15, "work"), ("RIGHT LEG SIDE", 15, "work"), 
        ("RIGHT LEG BACK", 15, "work"), ("LEFT LEG UP", 15, "work"), 
        ("LEFT LEG SIDE", 15, "work"), ("LEFT LEG BACK", 15, "work"), 
        ("TOE TOUCHES", 15, "work"), ("NECK CLOCKWISE", 15, "work"), 
        ("NECK ANTI-CLOCKWISE", 15, "work") 
    ],
    "main_routine": [
        ("GET READY FOR SQUATS", 15, "prep"),
        ("SQUATS × 15", None, "manual"), ("REST", 60, "rest"),
        ("SQUATS × 15", None, "manual"), ("REST", 60, "rest"),
        ("SQUATS × 15", None, "manual"),
        ("GET READY FOR PUSHUPS", 60, "prep"),
        ("PUSHUPS × 15", None, "manual"), ("REST", 90, "rest"),
        ("PUSHUPS × 15", None, "manual"), ("REST", 90, "rest"),
        ("PUSHUPS × 15", None, "manual"),
        ("GET READY FOR HIP THRUSTERS", 60, "prep"),
        ("HIP THRUSTERS × 40 EACH LEG", None, "manual"), ("REST", 90, "rest"),
        ("HIP THRUSTERS × 40 EACH LEG", None, "manual"), ("REST", 90, "rest"),
        ("HIP THRUSTERS × 40 EACH LEG", None, "manual"),
        ("GET READY FOR TOWEL ROWS", 60, "prep"),
        ("TOWEL ROWS × 15", None, "manual"), ("REST", 60, "rest"),        
        ("TOWEL ROWS × 15", None, "manual"), ("REST", 60, "rest"),        
        ("TOWEL ROWS × 15", None, "manual"),
        ("GET READY FOR WALL SIT", 60, "prep"),
        ("WALL SIT", 60, "work"), ("REST", 90, "rest"),
        ("WALL SIT", 60, "work"), ("REST", 90, "rest"),
        ("WALL SIT", 30, "work"),
    ],
    "daily_abs": [
        ("GET READY FOR CORE", 120, "prep"),
        ("RUSSIAN TWISTS",30,"work"), ("REST", 10, "rest"), 
        ("HALF SIT UP",30,"work"), ("REST", 10, "rest"), 
        ("PADDLES",30,"work"), ("REST", 10, "rest"), 
        ("SIDE TO SIDE",30,"work"), ("REST", 10, "rest"), 
        ("SCISSORS",30,"work"), ("REST", 10, "rest"), 
        ("BUTTERFLY CRUNCH",30,"work"), ("REST", 10, "rest"), 
        ("UP LEG PRESS",30,"work"), ("REST", 10, "rest"), 
        ("PLANK",30,"work"), ("REST", 10, "rest"), 
        ("CYCLES",30,"work"), ("REST", 10, "rest"), 
        ("ARM PLANK",30,"work"), ("REST", 10, "rest"), 
        ("REVERSE CRUNCHES",30,"work"), ("REST", 10, "rest"), 
        ("LEGS PLANK",30,"work"), ("REST", 10, "rest"), 
        ("PYRAMID",30,"work"), ("REST", 10, "rest"), 
        ("LEFT PLANK DIPS",30,"work"), ("REST", 10, "rest"), 
        ("RIGHT PLANK",30,"work"), ("REST", 10, "rest"), 
        ("FRONT DIPS", 60, "work"), ("REST", 90, "rest"), 
        ("PLANK HOLD",120,"work") 
    ],
    "deadhang_routine": [ 
        ("GET READY", 10, "prep"), 
        ("HANG", 45, "work"), ("REST", 120, "rest"), 
        ("HANG", 40, "work"), ("REST", 120, "rest"), 
        ("HANG", 30, "work"),
        ("PULL UP × 5", None, "manual"), ("REST", 120, "rest"),
        ("PULL UP × 5", None, "manual"), ("REST", 120, "rest"),
        ("PULL UP × 5", None, "manual"), ("REST", 120, "rest"),
        ("PULL UP HOLD", 30, "work"), ("REST", 120, "rest"),
        ("BICEP PULL UP × 5", None, "manual"), ("REST", 120, "rest"),
        ("BICEP PULL UP × 5", None, "manual"), ("REST", 120, "rest"),
        ("BICEP PULL UP × 5", None, "manual"), ("REST", 120, "rest"),
        ("BICEP PULL UP HOLD", 30, "work"), ("REST", 120, "rest")
    ]
}

# Menu configurations (Combinations of base routines)
WORKOUT_CONFIGS = {
    "main": {
        "label": "COMPLETE WORKOUT",
        "sequence": ["daily_warmup", "main_routine", "daily_abs"]
    },
    "deadhang": {
        "label": "DEADHANG PRACTICE",
        "sequence": ["deadhang_routine"]
    }
}

# Global Settings
SETTINGS = {
    "pinterest_url": ""
}
IMAGE_CACHE = {}

# ================= PERSISTENCE =================
DATA_FILE = 'workout_data.json'

def load_data():
    """Loads custom routines from disk if they exist."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                if 'base_routines' in data:
                    BASE_ROUTINES.update(data['base_routines'])
                if 'workout_configs' in data:
                    WORKOUT_CONFIGS.update(data['workout_configs'])
                if 'settings' in data:
                    SETTINGS.update(data['settings'])
        except Exception as e:
            print(f"Error loading data: {e}")

def save_data():
    """Saves current routines to disk."""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({
                'base_routines': BASE_ROUTINES,
                'workout_configs': WORKOUT_CONFIGS,
                'settings': SETTINGS
            }, f, indent=4)
    except Exception as e:
        print(f"Error saving data: {e}")

# Load data immediately on startup
load_data()

# ================= GLOBAL STATE =================
state = {
    "active_routine": [],
    "segments": [],
    "phase_index": -1,
    "time_left": 0,
    "paused": False,
    "running": False,
    "current_phase_data": None,
    "timer_id": None
}

timer_thread = None
timer_lock = threading.Lock()

def is_timer_running():
    global timer_thread
    if timer_thread is None:
        return False
    # Standard Thread
    if hasattr(timer_thread, 'is_alive'):
        return timer_thread.is_alive()
    # Eventlet GreenThread
    if hasattr(timer_thread, 'dead'):
        return not timer_thread.dead
    return False

def background_timer(my_id):
    """The main loop that ticks seconds and broadcasts state."""
    global state
    while state["running"]:
        if state.get("timer_id") != my_id:
            return

        if not state["paused"]:
            # Check if we need to move to next phase
            if state["time_left"] is not None and state["time_left"] < 0:
                next_phase()
            
            # If it's a manual phase (time_left is None), we just wait for a skip
            if state["time_left"] is not None:
                # Broadcast time
                socketio.emit('update', get_ui_state())
                
                # Beep logic
                if state["current_phase_data"] and state["current_phase_data"][2] in ["rest", "prep"]:
                    if state["time_left"] in [3, 2, 1]:
                        socketio.start_background_task(socketio.emit, 'beep', {'type': 'warning'})
                
                # Sleep in chunks to allow immediate interruption if phase changes
                slept = 0
                interrupted = False
                while slept < 10: # 10 * 0.1s = 1 second
                    if not state["running"]:
                        break
                    socketio.sleep(0.1)
                    if state.get("fresh_phase", False):
                        interrupted = True
                        break
                    slept += 1

                if interrupted:
                    state["fresh_phase"] = False
                    continue # Skip decrement and restart loop immediately
                
                if state["current_phase_data"] and state["current_phase_data"][2] == "complete":
                    state["time_left"] += 1
                else:
                    state["time_left"] -= 1
            else:
                # Manual phase, just broadcast state and wait
                socketio.emit('update', get_ui_state())
                socketio.sleep(0.5)
        else:
            socketio.emit('update', get_ui_state())
            socketio.sleep(0.5)

def start_timer_thread():
    global timer_thread
    new_id = str(uuid.uuid4())
    state["timer_id"] = new_id
    timer_thread = socketio.start_background_task(background_timer, new_id)

def next_phase():
    state["phase_index"] += 1
    if state["phase_index"] < len(state["active_routine"]):
        phase = state["active_routine"][state["phase_index"]]
        state["current_phase_data"] = phase
        state["time_left"] = phase[1] # Can be None for manual
        
        # Play start/rest sound
        p_type = phase[2]
        if p_type in ["work", "manual"]:
            socketio.start_background_task(socketio.emit, 'beep', {'type': 'start'})
            socketio.start_background_task(socketio.emit, 'speak', {'text': phase[0]})
        elif p_type in ["rest", "prep"]:
            socketio.start_background_task(socketio.emit, 'beep', {'type': 'rest'})
            
            # Speak phase name and the next exercise
            speak_text = phase[0]
            next_idx = state["phase_index"] + 1
            if next_idx < len(state["active_routine"]):
                next_name = state["active_routine"][next_idx][0]
                speak_text += f". Next, {next_name}"
            socketio.start_background_task(socketio.emit, 'speak', {'text': speak_text})
            
    else:
        # Workout complete
        state["current_phase_data"] = ("WORKOUT COMPLETE", 0, "complete")
        state["time_left"] = 0
        socketio.emit('update', get_ui_state())
        socketio.start_background_task(socketio.emit, 'speak', {'text': "Workout Complete"})

def get_ui_state():
    phase = state["current_phase_data"]
    if not phase:
        return {"title": "READY", "time": "--:--", "color": "white", "paused": False}
    
    title, seconds, p_type = phase
    
    # Color logic
    color = "#00ff88" if p_type in ("work", "manual") else "#4da6ff" if p_type == "rest" else "#ffcc00"
    color = "#00ff88" if p_type in ("work", "manual") else "#4da6ff" if p_type == "rest" else "#ffffff" if p_type == "complete" else "#ffcc00"
    
    # Time formatting
    if state["time_left"] is None:
        time_str = title.upper()
        title = ""
    else:
        mins, sec = divmod(max(0, state["time_left"]), 60)
        time_str = f"{mins:02d}:{sec:02d}"

    # Progress logic (Count only work/manual phases)
    progress_text = ""
    if p_type in ["work", "manual"]:
        # Find which segment we are currently in
        current_segment = state.get("segments", [state["active_routine"]])[0]
        cumulative_len = 0
        relative_idx = 0
        
        for seg in state.get("segments", []):
            if state["phase_index"] < cumulative_len + len(seg):
                current_segment = seg
                relative_idx = state["phase_index"] - cumulative_len
                break
            cumulative_len += len(seg)
            
        total_exercises = sum(1 for p in current_segment if p[2] in ["work", "manual"])
        current_exercise = sum(1 for i in range(relative_idx + 1) 
                               if current_segment[i][2] in ["work", "manual"])
        progress_text = f"EXERCISE {current_exercise} / {total_exercises}"

    # Next Exercise Logic (Show during REST)
    next_exercise_text = ""
    if p_type in ["rest", "prep"]:
        next_idx = state["phase_index"] + 1
        if next_idx < len(state["active_routine"]):
            next_phase = state["active_routine"][next_idx]
            next_exercise_text = f"NEXT: {next_phase[0]}"

    return {
        "title": title,
        "time": time_str,
        "color": color,
        "paused": state["paused"],
        "instruction": "PRESS NEXT WHEN DONE" if state["time_left"] is None else "",
        "progress": progress_text,
        "next_exercise": next_exercise_text,
        "is_manual": state["time_left"] is None
    }

@app.route('/')
def index():
    return render_template('index.html')

# ================= EDITOR EVENTS =================
@socketio.on('get_menu_data')
def handle_get_menu():
    emit('menu_data', WORKOUT_CONFIGS)

@socketio.on('get_editor_data')
def handle_get_editor_data():
    emit('editor_data', {"base_routines": BASE_ROUTINES, "workout_configs": WORKOUT_CONFIGS, "settings": SETTINGS})

@socketio.on('save_base_routine')
def handle_save_base(data):
    name = data.get('name')
    phases = data.get('phases')
    if name and phases:
        BASE_ROUTINES[name] = phases
        save_data()
        emit('editor_save_success', {"type": "base"})
        emit('backup_data', {'base_routines': BASE_ROUTINES, 'workout_configs': WORKOUT_CONFIGS}, broadcast=True)

@socketio.on('save_workout_config')
def handle_save_config(data):
    key = data.get('key')
    label = data.get('label')
    sequence = data.get('sequence')
    if key and label and sequence:
        WORKOUT_CONFIGS[key] = {"label": label, "sequence": sequence}
        save_data()
        emit('editor_save_success', {"type": "workout"})
        emit('menu_data', WORKOUT_CONFIGS, broadcast=True)
        emit('backup_data', {'base_routines': BASE_ROUTINES, 'workout_configs': WORKOUT_CONFIGS}, broadcast=True)

@socketio.on('delete_base_routine')
def handle_delete_base(data):
    name = data.get('name')
    if name and name in BASE_ROUTINES:
        del BASE_ROUTINES[name]
        save_data()
        emit('editor_save_success', {"type": "base_deleted"})
        emit('backup_data', {'base_routines': BASE_ROUTINES, 'workout_configs': WORKOUT_CONFIGS}, broadcast=True)

@socketio.on('delete_workout_config')
def handle_delete_config(data):
    key = data.get('key')
    if key and key in WORKOUT_CONFIGS:
        del WORKOUT_CONFIGS[key]
        save_data()
        emit('editor_save_success', {"type": "workout_deleted"})
        emit('menu_data', WORKOUT_CONFIGS, broadcast=True)
        emit('backup_data', {'base_routines': BASE_ROUTINES, 'workout_configs': WORKOUT_CONFIGS}, broadcast=True)

def fetch_and_broadcast_images(url):
    # Check cache (valid for 1 hour)
    if url in IMAGE_CACHE and (time.time() - IMAGE_CACHE[url]['timestamp'] < 3600):
        print(f"Serving {len(IMAGE_CACHE[url]['images'])} images from cache")
        socketio.emit('pinterest_images', IMAGE_CACHE[url]['images'])
        return

    # Clean up URL to get base board URL
    board_url = url
    if board_url.endswith('.rss'):
        board_url = board_url[:-4]
    if board_url.endswith('/'):
        board_url = board_url[:-1]
    
    rss_url = board_url + '.rss'
    images = set()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    # 1. Try RSS (Reliable but limited)
    try:
        resp = requests.get(rss_url, headers=headers, timeout=5)
        if resp.status_code == 200:
            content = html.unescape(resp.text)
            matches = re.findall(r'src="([^"]+)"', content)
            for img in matches:
                if "i.pinimg.com" in img:
                    img = re.sub(r'/[0-9]+x/', '/736x/', img)
                    images.add(img)
    except Exception as e:
        print(f"Error fetching Pinterest RSS: {e}")

    final_images = list(images)
    # Filter for valid image extensions to be safe
    final_images = [img for img in final_images if img.endswith(('.jpg', '.png', '.webp', '.jpeg'))]
    
    random.shuffle(final_images)
    print(f"Fetched {len(final_images)} unique images from Pinterest")
    
    if final_images:
        IMAGE_CACHE[url] = {'images': final_images, 'timestamp': time.time()}
        
    socketio.emit('pinterest_images', final_images)

@socketio.on('get_settings')
def handle_get_settings():
    emit('settings_data', SETTINGS)

@socketio.on('save_settings')
def handle_save_settings(data):
    url = data.get('pinterest_url', '').strip()
    SETTINGS['pinterest_url'] = url
    save_data()
    emit('editor_save_success', {"type": "settings"})
    # Trigger image fetch for everyone
    if url:
        socketio.start_background_task(fetch_and_broadcast_images, url)
    else:
        emit('pinterest_images', [], broadcast=True)

@socketio.on('restore_data')
def handle_restore(data):
    """Restores data sent from a client's local storage."""
    if not data: return
    
    if 'base_routines' in data:
        BASE_ROUTINES.update(data['base_routines'])
    if 'workout_configs' in data:
        WORKOUT_CONFIGS.update(data['workout_configs'])
    if 'settings' in data:
        SETTINGS.update(data['settings'])
        
    save_data() # Keep local file updated if running locally
    emit('menu_data', WORKOUT_CONFIGS, broadcast=True)
    # Ensure all other connected clients get this latest state
    emit('backup_data', {'base_routines': BASE_ROUTINES, 'workout_configs': WORKOUT_CONFIGS}, broadcast=True)

@socketio.on('start_routine')
def handle_start(data):
    global timer_thread
    routine_key = data.get('routine', 'main')
    
    config = WORKOUT_CONFIGS.get(routine_key)
    if not config:
        return

    # Fetch background images if configured
    if SETTINGS.get('pinterest_url'):
        socketio.start_background_task(fetch_and_broadcast_images, SETTINGS['pinterest_url'])

    # Build segments dynamically from the config sequence
    state["segments"] = []
    for base_name in config["sequence"]:
        if base_name in BASE_ROUTINES:
            state["segments"].append(BASE_ROUTINES[base_name])
            
    if not state["segments"]:
        return

    # Flatten segments for the actual execution logic
    state["active_routine"] = [item for seg in state["segments"] for item in seg]
    state["phase_index"] = -1
    state["running"] = True
    state["paused"] = False

    # If restarting while running, prevent immediate decrement
    with timer_lock:
        if is_timer_running():
            state["fresh_phase"] = True
        else:
            state["fresh_phase"] = False
        
        next_phase() # Start first phase
        
        if not is_timer_running():
            start_timer_thread()

@socketio.on('pause')
def handle_pause():
    state["paused"] = not state["paused"]

@socketio.on('next')
def handle_next():
    next_phase()
    state["fresh_phase"] = True
    socketio.emit('update', get_ui_state())

@socketio.on('previous')
def handle_previous():
    global timer_thread
    # If at start, just reset the current phase
    if state["phase_index"] <= 0:
        state["phase_index"] = 0
    else:
        state["phase_index"] -= 1

    # Load the phase data
    if state["phase_index"] < len(state["active_routine"]):
        phase = state["active_routine"][state["phase_index"]]
        state["current_phase_data"] = phase
        state["time_left"] = phase[1]
        state["fresh_phase"] = True
        
        # Ensure timer is running (in case we came back from "Workout Complete")
        if not state["running"]:
            state["running"] = True
            with timer_lock:
                if not is_timer_running():
                    start_timer_thread()
        
        socketio.emit('update', get_ui_state())

@socketio.on('quit_workout')
def handle_quit():
    state["running"] = False
    state["paused"] = False
    state["phase_index"] = -1
    emit('return_to_menu', broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)