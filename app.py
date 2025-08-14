from flask import Flask, render_template, Response, request
import cv2
import datetime
import time
import os
from pathlib import Path
import requests
app = Flask(__name__)

# config
RECORDINGS_DIR = "recordings"

# This will allow only specific devices/browsers to login. I'd recommend changing this something more secure if you think about actually using this
ALLOWED_USER_AGENTS = []

# Create recordings directory if it doesn't exist
# This can be changed to some other folder – maybe in the cloud, options are endless
Path(RECORDINGS_DIR).mkdir(exist_ok=True)

# Init cameras dynamically
caps = {}
MAX_CAMERAS_TO_CHECK = 5  # Maximum number of cameras to check

for i in range(MAX_CAMERAS_TO_CHECK):
    try:
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Set reasonable resolution 
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            caps[f'camera_{i}'] = cap
            print(f"Successfully opened camera at index {i}")
        else:
            cap.release()
    except Exception as e:
        print(f"Error initializing camera at index {i}: {e}")

def check_auth():
    user_agent = request.headers.get('User-Agent')
    ALLOWED_USER_AGENTS.append(user_agent)
    return user_agent in ALLOWED_USER_AGENTS

def generate_frames(camera_name):
    if camera_name not in caps:
        print(f"Camera {camera_name} not available")
        return
    
    cap = caps[camera_name]
    detection = False
    timer_started = False
    detection_stopped_time = None
    SECONDS_TO_RECORD_AFTER_DETECTION = 5
    out = None
    frame_size = None
    avg = None
    
    while True:
        try:
            success, frame = cap.read()
            if not success:
                print(f"Failed to read frame from {camera_name} camera")
                time.sleep(0.1)
                continue
            
            # Init VideoWriter when first frame is received
            if frame_size is None:
                height, width = frame.shape[:2]
                frame_size = (width, height)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            
            # Motion detection using frame differencing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if avg is None:
                avg = gray.copy().astype("float")
                continue
            
            cv2.accumulateWeighted(gray, avg, 0.5)
            frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
            thresh = cv2.threshold(frame_delta, 5, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            motion_detected = any(cv2.contourArea(c) > 500 for c in contours)
            
            if motion_detected:
                if detection: 
                    timer_started = False
                else:
                    detection = True
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
                    filename = os.path.join(RECORDINGS_DIR, f"{current_time}_{camera_name}.mp4")
                    out = cv2.VideoWriter(filename, fourcc, 20.0, frame_size)
                    print(f"Started recording {camera_name} camera to {filename}")
            elif detection:
                if timer_started:
                    if time.time() - detection_stopped_time >= SECONDS_TO_RECORD_AFTER_DETECTION:
                        detection = False
                        timer_started = False
                        if out:
                            out.release()
                            out = None
                            print(f"Stopped recording {camera_name} camera")
                else:
                    timer_started = True
                    detection_stopped_time = time.time()
            
            if detection and out is not None:
                out.write(frame)
            
            # Stream the frame
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Failed to encode frame")
                continue
                
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        except Exception as e:
            print(f"Error in {camera_name} camera stream: {e}")
            time.sleep(0.1)
            continue

@app.route('/')
def index():
    if not check_auth():
        return "Access denied. Please use an authorized device.", 403
    return render_template('index.html', camera_count=len(caps))

@app.route('/video_feed/<int:camera_index>')
def video_feed(camera_index):
    if not check_auth():
        return "Access denied", 403
    camera_name = f'camera_{camera_index}'
    if camera_name not in caps:
        return f"Camera {camera_index} not available", 503
    return Response(generate_frames(camera_name), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        # Cleanup on exit
        for name, cap in caps.items():
            if cap is not None:
                cap.release()
        print("Released all camera resources")