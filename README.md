# Motion Detection Camera Server

This program is a simple Flask-based web server that streams live video from available cameras and automatically records video when motion is detected.

<p align="center">
  <img src="https://images.icon-icons.com/112/PNG/512/python_18894.png" alt="Python" height="100">
  <img src="https://opencv.org/wp-content/uploads/2020/07/OpenCV_logo_black-2.png" alt="OpenCV" height="100">
</p>

## Features
- Automatically detects and initializes up to 5 connected cameras.
- Streams live video feeds via browser.
- Motion detection using frame differencing.
- Records MP4 video files when motion is detected.
- Continues recording a few seconds after motion stops.
- Saves recordings to the `recordings/` directory.
- Simple device authorization via **User-Agent** (replace with a secure method for production).

## Requirements
- Python 3.x
- Flask
- OpenCV (`cv2`)

Install dependencies – the dependencies are stored in a .txt file:
```bash
pip install -r requirements.txt
```

## Usage
1. Connect your cameras.
2. Run the server:
```bash
python app.py
```
3. Open a browser on an authorized device and voila : )

## Configuration
- ```RECORDINGS_DIR``` – Path to store video recordings. This can be changed to cloud stored folder, but I recommend writing a more secure authentication first
- ```MAX_CAMERAS_TO_CHECK``` – Number of camera indexes to check at startup. Default is the computer's internal camera, but you add more external cameras.
- ```ALLOWED_USER_AGENTS``` – List of allowed devices (based on User-Agent). This should also be updated if you decide to use it

### Note
This code is for testing and simple setups.
For production use, implement secure authentication and consider cloud storage for recordings.
I ran the program on my machine and hosted it through CloudFlare – a really fun project : )
