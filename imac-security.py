#!/usr/bin/env python3
"""
iMac Security System v1.0.0
Revision 48
A comprehensive security camera system with motion and voice detection
"""

import os
import sys
import time
import threading
import subprocess
import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog

# Set filename for output redirection
log_file = os.path.expanduser("~/Library/Logs/iMacSecuritySystem.log")

# Redirect stderr to hide OpenCV errors
if not sys.warnoptions:
    # Save original stderr
    original_stderr = sys.stderr
    
    # Open log file
    try:
        sys.stderr = open(log_file, 'w')
    except:
        # If we can't open the log file, keep using original stderr
        sys.stderr = original_stderr

# Check if running on macOS
if not sys.platform.startswith('darwin'):
    messagebox.showerror("Platform Error", "This application is designed for macOS only.")
    sys.exit(1)

# Try to import required modules
try:
    import cv2
    import numpy as np
    import datetime
    import pyaudio
    import wave
    import speech_recognition as sr
    from PIL import Image, ImageTk
    
    # Try to import ttkbootstrap but have a fallback
    USE_TTKBOOTSTRAP = True
    try:
        import ttkbootstrap as ttk
        from ttkbootstrap.constants import SUCCESS, DANGER, INFO, SECONDARY
    except (ImportError, Exception) as e:
        print(f"ttkbootstrap not available, using standard ttk: {e}")
        import tkinter.ttk as ttk
        # Define constants for standard ttk (they won't be used the same way, but prevent errors)
        SUCCESS, DANGER, INFO, SECONDARY = "success", "danger", "info", "secondary"
        USE_TTKBOOTSTRAP = False
except ImportError as e:
    messagebox.showerror("Import Error", 
                         f"Missing dependency: {e}\n\n"
                         "Please run the installer script first:\n"
                         "python3 install.py")
    sys.exit(1)

# Configuration manager
class ConfigManager:
    def __init__(self):
        self.config_path = os.path.expanduser("~/Library/Application Support/iMacSecuritySystem")
        self.config_file = os.path.join(self.config_path, "config.json")
        
        # Create config directory if it doesn't exist
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)
            
        # Load or create config
        if os.path.exists(self.config_file):
            self.config = self.load_config()
        else:
            self.config = self.create_default_config()
            
    def create_default_config(self):
        default_config = {
            "output_directory": os.path.expanduser("~/Documents/iMacSecuritySystem"),
            "motion_sensitivity": 20,
            "voice_detection_enabled": True,
            "post_detection_record_time": 10,
            "video_resolution": "480p",  # Default to lower resolution for performance
            "notifications_enabled": True,
            "dark_mode": True,
            "use_simple_motion_detection": True,  # Default to faster motion detection
            "selected_camera_index": 0,
            "selected_microphone_index": None  # Default to system default mic
        }
        
        # Create output directory if it doesn't exist
        if not os.path.exists(default_config["output_directory"]):
            os.makedirs(default_config["output_directory"])
            
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=4)
            
        return default_config
            
    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
                # Add new configuration options if they don't exist (for upgrades)
                if "use_simple_motion_detection" not in config:
                    config["use_simple_motion_detection"] = True
                if "video_resolution" not in config:
                    config["video_resolution"] = "480p"
                if "selected_microphone_index" not in config:
                    config["selected_microphone_index"] = None
                
                return config
        except:
            return self.create_default_config()
                
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

# Camera and motion detection
class CameraManager:
    def __init__(self, config):
        self.config = config
        self.camera = None
        self.available_cameras = []
        self.is_recording = False
        self.motion_detected = False
        
        # Default to lower resolution for better performance
        self.frame_width = 640  # Lower default resolution
        self.frame_height = 480 # Lower default resolution
        
        # Update resolution from config if specified
        if config["video_resolution"] == "720p":
            self.frame_width = 1280
            self.frame_height = 720
        elif config["video_resolution"] == "1080p":
            self.frame_width = 1920
            self.frame_height = 1080
        elif config["video_resolution"] == "480p":  # New lower option
            self.frame_width = 640
            self.frame_height = 480
            
        self.motion_sensitivity = config["motion_sensitivity"]
        self.post_detection_record_time = config["post_detection_record_time"]
        self.output_directory = config["output_directory"]
        
        # Use a simpler background subtractor for better performance
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=50,     # Reduced history for better performance
            varThreshold=30 # Lower threshold for better performance
        )
        
        # Add a previous frame for simpler motion detection
        self.prev_frame = None
        
        self.selected_camera_index = config.get("selected_camera_index", 0)
        
    def get_available_cameras(self):
        """Detect available cameras and return a list of their names and indices"""
        self.available_cameras = []
        
        # Check for multiple camera indices (typically 0-10 is sufficient)
        for i in range(10):
            try:
                temp_camera = cv2.VideoCapture(i)
                if temp_camera.isOpened():
                    # Get camera name if possible
                    ret, frame = temp_camera.read()
                    if ret:
                        # Try to get device name, fall back to generic name if not possible
                        camera_name = f"Camera {i}"
                        if sys.platform.startswith('darwin'):  # macOS specific
                            camera_name = f"Camera {i} (iMac)"
                        self.available_cameras.append({"index": i, "name": camera_name})
                    temp_camera.release()
            except Exception as e:
                print(f"Error checking camera {i}: {e}")
                
        if not self.available_cameras:
            # If no cameras found, add a dummy entry
            self.available_cameras.append({"index": 0, "name": "Default camera"})
            
        return self.available_cameras
        
    def set_camera(self, camera_index):
        """Switch to a different camera"""
        if self.is_recording:
            self.stop_recording()
            
        if self.camera is not None:
            self.camera.release()
            
        self.selected_camera_index = camera_index
        self.config["selected_camera_index"] = camera_index
        return self.open_camera()
        
    def open_camera(self):
        try:
            # Use the selected camera index (default to 0 if not valid)
            index = self.selected_camera_index
            if not isinstance(index, int) or index < 0:
                index = 0
                
            self.camera = cv2.VideoCapture(index)
            
            # Set resolution
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            
            # Set additional camera properties for better performance
            self.camera.set(cv2.CAP_PROP_FPS, 10)  # Lower FPS for better performance
            self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))  # Use MJPG format
            
            if not self.camera.isOpened():
                print(f"Failed to open camera at index {index}, trying fallback to index 0")
                self.camera.release()
                self.camera = cv2.VideoCapture(0)  # Fallback to default camera
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
                self.camera.set(cv2.CAP_PROP_FPS, 10)
                self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            
            return self.camera.isOpened()
        except Exception as e:
            print(f"Error opening camera: {e}")
            return False
            
    def release_camera(self):
        if self.camera is not None:
            self.camera.release()
            
    def get_frame(self):
        if self.camera is None:
            return None
            
        ret, frame = self.camera.read()
        if not ret:
            return None
            
        return frame
        
    def detect_motion(self, frame):
        if frame is None:
            return False
            
        # Option 1: Simple frame difference method (faster)
        if self.config.get("use_simple_motion_detection", True):
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            # If first frame, initialize and return
            if self.prev_frame is None:
                self.prev_frame = gray
                return False
                
            # Calculate absolute difference between current and previous frame
            frame_delta = cv2.absdiff(self.prev_frame, gray)
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            
            # Update previous frame for next time (with some averaging for stability)
            self.prev_frame = cv2.addWeighted(self.prev_frame, 0.7, gray, 0.3, 0)
            
            # Count white pixels (changed pixels)
            white_pixel_count = np.sum(thresh == 255)
            total_pixels = thresh.shape[0] * thresh.shape[1]
            movement_percentage = (white_pixel_count / total_pixels) * 100
            
            # Adjust threshold based on sensitivity
            threshold = (30 - self.motion_sensitivity) / 5  # Range: 1 to 5.8
            
            return movement_percentage > threshold
        
        # Option 2: Background subtraction method (more accurate but slower)
        else:
            # Convert to grayscale and apply Gaussian blur
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            # Apply background subtraction
            fg_mask = self.background_subtractor.apply(gray)
            
            # Thresholding
            thresh = cv2.threshold(fg_mask, 25, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            
            # Count white pixels
            white_pixel_count = np.sum(thresh == 255)
            total_pixels = thresh.shape[0] * thresh.shape[1]
            movement_percentage = (white_pixel_count / total_pixels) * 100
            
            # Detect motion based on sensitivity
            if movement_percentage > (30 - self.motion_sensitivity) / 10:
                return True
            
            return False
        
    def start_recording(self, filename=None):
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_directory, f"motion_{timestamp}.mp4")
            
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(filename, fourcc, 20, 
                                           (self.frame_width, self.frame_height))
        self.is_recording = True
        self.current_recording_file = filename
        return filename
        
    def stop_recording(self):
        if self.is_recording:
            self.video_writer.release()
            self.is_recording = False
            return self.current_recording_file
        return None
        
    def record_frame(self, frame):
        if self.is_recording and frame is not None:
            self.video_writer.write(frame)


# Audio and voice detection
class AudioManager:
    def __init__(self, config):
        self.config = config
        self.voice_detection_enabled = config["voice_detection_enabled"]
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.voice_detected = False
        self.output_directory = config["output_directory"]
        self.recognizer = sr.Recognizer()
        self.frames = []
        
        # Initialize selected microphone
        self.selected_microphone_index = config.get("selected_microphone_index", None)
        
    def get_available_microphones(self):
        """Detect available microphones and return a list of their names and indices"""
        available_mics = []
        
        # Loop through all audio devices
        for i in range(self.audio.get_device_count()):
            try:
                device_info = self.audio.get_device_info_by_index(i)
                # Only include input devices (microphones)
                if device_info['maxInputChannels'] > 0:
                    available_mics.append({
                        "index": i,
                        "name": device_info['name'],
                        "channels": device_info['maxInputChannels'],
                        "sample_rate": int(device_info['defaultSampleRate'])
                    })
            except Exception as e:
                print(f"Error checking microphone {i}: {e}")
        
        # If no microphones found, add a dummy entry
        if not available_mics:
            available_mics.append({"index": None, "name": "Default microphone", "channels": 1, "sample_rate": 16000})
            
        return available_mics
    
    def set_microphone(self, mic_index):
        """Switch to a different microphone"""
        if self.is_recording:
            self.stop_recording()
            
        if self.stream is not None:
            self.stop_stream()
            
        # Update the selected microphone
        self.selected_microphone_index = mic_index
        self.config["selected_microphone_index"] = mic_index
        
        # Restart the stream with the new microphone
        return self.start_stream()
        
    def start_stream(self):
        try:
            # Use the selected microphone index if available
            input_device = None
            if hasattr(self, 'selected_microphone_index') and self.selected_microphone_index is not None:
                input_device = self.selected_microphone_index
                
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=input_device,
                frames_per_buffer=1024
            )
            return True
        except Exception as e:
            print(f"Error starting audio stream: {e}")
            return False
            
    def stop_stream(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            
    def terminate(self):
        self.stop_stream()
        self.audio.terminate()
        
    def detect_voice(self):
        if not self.voice_detection_enabled or self.stream is None:
            return False
            
        try:
            # Create a small audio buffer to analyze
            data = self.stream.read(4096, exception_on_overflow=False)
            
            # Use energy threshold to detect if someone might be speaking
            energy = sum(abs(int.from_bytes(data[i:i+2], byteorder='little', signed=True)) 
                        for i in range(0, len(data), 2)) / (len(data)/2)
            
            # If energy is high, it might be speech (simplified for performance)
            if energy > 1500:  # Higher threshold for better performance
                return True
                
            return False
        except Exception as e:
            print(f"Error in voice detection: {e}")
            return False
            
    def start_recording(self, filename=None):
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_directory, f"audio_{timestamp}.wav")
            
        self.frames = []
        self.is_recording = True
        self.current_recording_file = filename
        return filename
        
    def stop_recording(self):
        if self.is_recording:
            wf = wave.open(self.current_recording_file, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            self.is_recording = False
            self.frames = []
            return self.current_recording_file
        return None
        
    def record_audio(self):
        if self.is_recording and self.stream is not None:
            data = self.stream.read(1024, exception_on_overflow=False)
            self.frames.append(data)


# Main application
class SecurityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("iMac Security System v1.0.0 (Rev 48)")
        
        # Set window size and position to ensure settings are visible
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Calculate window size - wide enough to show preview and settings
        window_width = min(1200, int(screen_width * 0.8))
        window_height = min(800, int(screen_height * 0.8))
        
        # Center the window
        x_pos = (screen_width - window_width) // 2
        y_pos = (screen_height - window_height) // 2
        
        # Set window size and position
        self.root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
        self.root.minsize(1000, 600)
        
        # Store ttk reference for use in methods
        self.ttk = ttk
        
        # Set theme - use ttkbootstrap if available, otherwise standard ttk
        global USE_TTKBOOTSTRAP
        if USE_TTKBOOTSTRAP:
            try:
                self.style = ttk.Style(theme="darkly")
            except Exception as e:
                print(f"Error setting ttkbootstrap theme: {e}")
                USE_TTKBOOTSTRAP = False
                self.style = ttk.Style()
        else:
            # Standard ttk - just use the default style
            self.style = ttk.Style()
        
        # Initialize configuration manager
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        
        # Add performance optimization settings if they don't exist
        if "use_simple_motion_detection" not in self.config:
            self.config["use_simple_motion_detection"] = True
            
        if "video_resolution" not in self.config or self.config["video_resolution"] not in ["480p", "720p", "1080p"]:
            self.config["video_resolution"] = "480p"  # Default to lowest resolution for performance
            
        # Add preview size setting if it doesn't exist
        if "preview_size" not in self.config:
            self.config["preview_size"] = "medium"  # Default size
            
        self.config_manager.save_config()
            
        # Initialize managers
        self.camera_manager = CameraManager(self.config)
        self.audio_manager = AudioManager(self.config)
        
        # Open camera and audio stream
        self.camera_manager.open_camera()
        self.audio_manager.start_stream()
        
        # State variables
        self.monitoring = False
        self.last_motion_time = 0
        self.last_voice_time = 0
        self.last_voice_check_time = 0  # For throttling voice detection
        self.last_ui_update_time = 0    # For throttling UI updates
        
        # Create UI
        self.create_ui()
        
        # Start preview
        self.update_preview()
        
    def create_ui(self):
        # Define button styles for standard ttk if not using ttkbootstrap
        if not USE_TTKBOOTSTRAP:
            # Create button styles to mimic ttkbootstrap
            self.style.configure("Success.TButton", foreground="white", background="green")
            self.style.configure("Danger.TButton", foreground="white", background="red")
            self.style.configure("Info.TButton", foreground="white", background="blue")
            self.style.configure("Secondary.TButton", foreground="white", background="gray")
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create a PanedWindow to allow adjustable size between panels
        paned_window = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True)
        
        # Left panel (preview and controls)
        left_panel = ttk.Frame(paned_window)
        
        # Right panel (settings)
        right_panel = ttk.Frame(paned_window)
        
        # Add panels to paned window with initial position
        # This ensures settings are visible when app starts
        paned_window.add(left_panel, weight=3)  # Preview area gets 3/5 of the space
        paned_window.add(right_panel, weight=2)  # Settings get 2/5 of the space
        
        # Camera preview size options
        preview_size_frame = ttk.LabelFrame(left_panel, text="Preview Size")
        preview_size_frame.pack(fill="x", padx=5, pady=5)
        
        # Preview size radio buttons
        self.preview_size_var = tk.StringVar(value=self.config.get("preview_size", "medium"))
        preview_size_options = ttk.Frame(preview_size_frame)
        preview_size_options.pack(fill="x", padx=5, pady=5)
        
        ttk.Radiobutton(
            preview_size_options,
            text="Small",
            variable=self.preview_size_var,
            value="small",
            command=self.update_preview_size
        ).pack(side="left", padx=10)
        
        ttk.Radiobutton(
            preview_size_options,
            text="Medium",
            variable=self.preview_size_var,
            value="medium",
            command=self.update_preview_size
        ).pack(side="left", padx=10)
        
        ttk.Radiobutton(
            preview_size_options,
            text="Large",
            variable=self.preview_size_var,
            value="large",
            command=self.update_preview_size
        ).pack(side="left", padx=10)
        
        # Camera preview
        preview_frame = ttk.LabelFrame(left_panel, text="Camera Preview")
        preview_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create a container frame with fixed size based on selected preview size
        self.preview_container = ttk.Frame(preview_frame)
        self.preview_container.pack(expand=True, padx=5, pady=5)
        
        # Preview label inside the container
        self.preview_label = ttk.Label(self.preview_container)
        self.preview_label.pack(padx=0, pady=0)
        
        # Set initial preview container size
        self.update_preview_size()
        
        # Control panel
        control_frame = ttk.LabelFrame(left_panel, text="Controls")
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # Create button styles for standard ttk if not using ttkbootstrap
        if not USE_TTKBOOTSTRAP:
            # Create button styles to mimic ttkbootstrap
            self.style.configure("Success.TButton", foreground="white", background="green")
            self.style.configure("Danger.TButton", foreground="white", background="red")
            self.style.configure("Info.TButton", foreground="white", background="blue")
            self.style.configure("Secondary.TButton", foreground="white", background="gray")
        
        # Get the button style parameter name based on whether we're using ttkbootstrap
        button_style_param = "bootstyle" if USE_TTKBOOTSTRAP else "style"
        
        # Start/Stop button
        self.start_stop_button = ttk.Button(
            control_frame, 
            text="Start Monitoring", 
            command=self.toggle_monitoring,
            **{button_style_param: SUCCESS if USE_TTKBOOTSTRAP else "Success.TButton"}
        )
        self.start_stop_button.pack(fill="x", padx=5, pady=5)
        
        # Status indicators
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill="x", padx=5, pady=5)
        
        # Motion status
        motion_frame = ttk.Frame(status_frame)
        motion_frame.pack(side="left", fill="x", expand=True)
        
        ttk.Label(motion_frame, text="Motion:").pack(side="left")
        self.motion_indicator = ttk.Label(motion_frame, text="●", foreground="gray")
        self.motion_indicator.pack(side="left")
        
        # Voice status
        voice_frame = ttk.Frame(status_frame)
        voice_frame.pack(side="right", fill="x", expand=True)
        
        ttk.Label(voice_frame, text="Voice:").pack(side="left")
        self.voice_indicator = ttk.Label(voice_frame, text="●", foreground="gray")
        self.voice_indicator.pack(side="left")
        
        # Settings section in right panel
        settings_notebook = ttk.Notebook(right_panel)
        settings_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Tab 1: Detection Settings
        detection_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(detection_tab, text="Detection")
        
        # Motion sensitivity with value display
        motion_sensitivity_frame = ttk.Frame(detection_tab)
        motion_sensitivity_frame.pack(fill="x", padx=5, pady=10)
        
        # Add a header with label and current value
        motion_header_frame = ttk.Frame(motion_sensitivity_frame)
        motion_header_frame.pack(fill="x")
        
        ttk.Label(motion_header_frame, text="Motion Sensitivity:").pack(side="left")
        self.motion_value_label = ttk.Label(motion_header_frame, text=f"{self.config['motion_sensitivity']}")
        self.motion_value_label.pack(side="right")
        
        self.motion_sensitivity_var = tk.IntVar(value=self.config["motion_sensitivity"])
        motion_sensitivity_scale = ttk.Scale(
            motion_sensitivity_frame,
            from_=1,
            to=25,
            variable=self.motion_sensitivity_var,
            command=self.update_motion_sensitivity
        )
        motion_sensitivity_scale.pack(fill="x", pady=5)
        
        sensitivity_label_frame = ttk.Frame(motion_sensitivity_frame)
        sensitivity_label_frame.pack(fill="x")
        
        ttk.Label(sensitivity_label_frame, text="Low (less sensitive)").pack(side="left")
        ttk.Label(sensitivity_label_frame, text="High (more sensitive)").pack(side="right")
        
        # Motion detection method
        motion_method_frame = ttk.Frame(detection_tab)
        motion_method_frame.pack(fill="x", padx=5, pady=10)
        
        ttk.Label(motion_method_frame, text="Motion Detection Method:").pack(anchor="w")
        
        self.motion_method_var = tk.BooleanVar(value=self.config.get("use_simple_motion_detection", True))
        method_radio_frame = ttk.Frame(motion_method_frame)
        method_radio_frame.pack(fill="x", pady=5)
        
        ttk.Radiobutton(
            method_radio_frame,
            text="Faster (Better Performance)",
            variable=self.motion_method_var,
            value=True,
            command=self.update_motion_method
        ).pack(side="left", padx=10)
        
        ttk.Radiobutton(
            method_radio_frame,
            text="More Accurate (Higher CPU Usage)",
            variable=self.motion_method_var,
            value=False,
            command=self.update_motion_method
        ).pack(side="left", padx=10)
        
        # Voice detection toggle
        voice_frame = ttk.Frame(detection_tab)
        voice_frame.pack(fill="x", padx=5, pady=10)
        
        self.voice_detection_var = tk.BooleanVar(value=self.config["voice_detection_enabled"])
        voice_check = ttk.Checkbutton(
            voice_frame,
            text="Enable Voice Detection",
            variable=self.voice_detection_var,
            command=self.toggle_voice_detection
        )
        voice_check.pack(anchor="w")
        
        # Post detection recording time with value display
        post_detection_frame = ttk.Frame(detection_tab)
        post_detection_frame.pack(fill="x", padx=5, pady=10)
        
        # Add a header with label and current value
        post_header_frame = ttk.Frame(post_detection_frame)
        post_header_frame.pack(fill="x") 
        
        ttk.Label(post_header_frame, text="Record After Detection (seconds):").pack(side="left")
        self.post_value_label = ttk.Label(post_header_frame, text=f"{self.config['post_detection_record_time']}")
        self.post_value_label.pack(side="right")
        
        self.post_detection_var = tk.IntVar(value=self.config["post_detection_record_time"])
        post_detection_scale = ttk.Scale(
            post_detection_frame,
            from_=5,
            to=30,
            variable=self.post_detection_var,
            command=self.update_post_detection_time
        )
        post_detection_scale.pack(fill="x", pady=5)
        
        post_label_frame = ttk.Frame(post_detection_frame)
        post_label_frame.pack(fill="x")
        
        ttk.Label(post_label_frame, text="5 sec").pack(side="left")
        ttk.Label(post_label_frame, text="30 sec").pack(side="right")
        
        # Tab 2: Video Settings
        video_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(video_tab, text="Video")
        
        # Video quality selection
        video_quality_frame = ttk.Frame(video_tab)
        video_quality_frame.pack(fill="x", padx=5, pady=10)
        
        ttk.Label(video_quality_frame, text="Video Quality:").pack(anchor="w")
        
        self.video_quality_var = tk.StringVar(value=self.config["video_resolution"])
        quality_radio_frame = ttk.Frame(video_quality_frame)
        quality_radio_frame.pack(fill="x", pady=5)
        
        ttk.Radiobutton(
            quality_radio_frame,
            text="480p (Better Performance)",
            variable=self.video_quality_var,
            value="480p",
            command=self.update_video_quality
        ).pack(side="left", padx=10)
        
        ttk.Radiobutton(
            quality_radio_frame,
            text="720p",
            variable=self.video_quality_var,
            value="720p",
            command=self.update_video_quality
        ).pack(side="left", padx=10)
        
        ttk.Radiobutton(
            quality_radio_frame,
            text="1080p",
            variable=self.video_quality_var,
            value="1080p",
            command=self.update_video_quality
        ).pack(side="left", padx=10)
        
        # Output directory
        output_dir_frame = ttk.Frame(video_tab)
        output_dir_frame.pack(fill="x", padx=5, pady=10)
        
        ttk.Label(output_dir_frame, text="Output Directory:").pack(anchor="w")
        
        dir_select_frame = ttk.Frame(output_dir_frame)
        dir_select_frame.pack(fill="x", pady=2)
        
        self.output_dir_var = tk.StringVar(value=self.config["output_directory"])
        output_entry = ttk.Entry(dir_select_frame, textvariable=self.output_dir_var)
        output_entry.pack(side="left", fill="x", expand=True)
        
        browse_button = ttk.Button(
            dir_select_frame,
            text="Browse",
            command=self.browse_output_dir,
            **{button_style_param: SECONDARY if USE_TTKBOOTSTRAP else "Secondary.TButton"}
        )
        browse_button.pack(side="right", padx=2)
        
        # Tab 3: Recordings
        recordings_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(recordings_tab, text="Recordings")
        
        # Recordings listbox with scrollbar
        recordings_list_frame = ttk.Frame(recordings_tab)
        recordings_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(recordings_list_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Use tk.Listbox instead of ttk.Listbox (ttkbootstrap doesn't have a Listbox widget)
        self.recordings_listbox = tk.Listbox(
            recordings_list_frame,
            height=6,
            selectmode="browse",
            yscrollcommand=scrollbar.set,
            bg="#2b2b2b",  # Dark background to match theme
            fg="white",    # White text
            selectbackground="#007bff"  # Highlight color
        )
        self.recordings_listbox.pack(fill="both", expand=True)
        
        self.recordings_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.recordings_listbox.yview)
        
        # Recordings buttons
        recordings_buttons_frame = ttk.Frame(recordings_tab)
        recordings_buttons_frame.pack(fill="x", padx=5, pady=5)
        
        open_button = ttk.Button(
            recordings_buttons_frame,
            text="Open Selected",
            command=self.open_selected_recording,
            **{button_style_param: INFO if USE_TTKBOOTSTRAP else "Info.TButton"}
        )
        open_button.pack(side="left", padx=2)
        
        refresh_button = ttk.Button(
            recordings_buttons_frame,
            text="Refresh",
            command=self.refresh_recordings_list,
            **{button_style_param: SECONDARY if USE_TTKBOOTSTRAP else "Secondary.TButton"}
        )
        refresh_button.pack(side="right", padx=2)
        
        # Tab 4: Devices
        devices_tab = ttk.Frame(settings_notebook)
        settings_notebook.add(devices_tab, text="Devices")
        
        # Camera selector
        camera_frame = ttk.LabelFrame(devices_tab, text="Camera")
        camera_frame.pack(fill="x", padx=5, pady=10)
        
        # Get available cameras
        available_cameras = self.camera_manager.get_available_cameras()
        camera_names = [cam["name"] for cam in available_cameras]
        
        # Camera combobox
        ttk.Label(camera_frame, text="Select Camera:").pack(anchor="w", padx=5, pady=2)
        self.camera_var = tk.StringVar()
        self.camera_combobox = ttk.Combobox(camera_frame, textvariable=self.camera_var, values=camera_names, state="readonly")
        self.camera_combobox.pack(fill="x", padx=5, pady=2)
        
        # Set default selection
        if available_cameras and self.camera_manager.selected_camera_index is not None:
            for cam in available_cameras:
                if cam["index"] == self.camera_manager.selected_camera_index:
                    self.camera_var.set(cam["name"])
                    break
            if not self.camera_var.get() and camera_names:
                self.camera_var.set(camera_names[0])
        elif camera_names:
            self.camera_var.set(camera_names[0])
        
        # Apply button
        camera_apply_button = ttk.Button(
            camera_frame,
            text="Apply Camera",
            command=self.change_camera,
            **{button_style_param: SECONDARY if USE_TTKBOOTSTRAP else "Secondary.TButton"}
        )
        camera_apply_button.pack(anchor="e", padx=5, pady=5)
        
        # Microphone selector
        mic_frame = ttk.LabelFrame(devices_tab, text="Microphone")
        mic_frame.pack(fill="x", padx=5, pady=10)
        
        # Get available microphones
        self.audio_manager.selected_microphone_index = self.config.get("selected_microphone_index", None)
        available_mics = self.audio_manager.get_available_microphones()
        mic_names = [mic["name"] for mic in available_mics]
        
        # Microphone combobox
        ttk.Label(mic_frame, text="Select Microphone:").pack(anchor="w", padx=5, pady=2)
        self.mic_var = tk.StringVar()
        self.mic_combobox = ttk.Combobox(mic_frame, textvariable=self.mic_var, values=mic_names, state="readonly")
        self.mic_combobox.pack(fill="x", padx=5, pady=2)
        
        # Set default selection
        if available_mics and self.audio_manager.selected_microphone_index is not None:
            for mic in available_mics:
                if mic["index"] == self.audio_manager.selected_microphone_index:
                    self.mic_var.set(mic["name"])
                    break
            if not self.mic_var.get() and mic_names:
                self.mic_var.set(mic_names[0])
        elif mic_names:
            self.mic_var.set(mic_names[0])
        
        # Apply button
        mic_apply_button = ttk.Button(
            mic_frame,
            text="Apply Microphone",
            command=self.change_microphone,
            **{button_style_param: SECONDARY if USE_TTKBOOTSTRAP else "Secondary.TButton"}
        )
        mic_apply_button.pack(anchor="e", padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var, 
            relief="sunken", 
            anchor="w"
        )
        status_bar.pack(side="bottom", fill="x")
        
        # Initial refresh of recordings
        self.refresh_recordings_list()
        
        # Set up closing event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def update_preview(self):
        """Update the video preview - optimized for performance"""
        if self.camera_manager.camera is None:
            self.root.after(100, self.update_preview)
            return
            
        ret, frame = self.camera_manager.camera.read()
        if not ret or frame is None:
            # If we couldn't get a frame, try again later
            self.root.after(100, self.update_preview)
            return
        
        # Process motion and voice detection only during monitoring
        if self.monitoring:
            # Check for motion - use the optimized detector
            motion_detected = self.camera_manager.detect_motion(frame)
            
            # Don't check for voice every frame to reduce CPU usage
            # Only check every ~300ms
            voice_detected = False
            current_time = time.time()
            if current_time - self.last_voice_check_time > 0.3:
                voice_detected = self.audio_manager.detect_voice()
                self.last_voice_check_time = current_time
            
            # Update indicators
            if motion_detected:
                self.motion_indicator.config(foreground="green")
                self.last_motion_time = time.time()
                self.camera_manager.motion_detected = True
            elif time.time() - self.last_motion_time > 1:
                self.motion_indicator.config(foreground="gray")
                
            if voice_detected:
                self.voice_indicator.config(foreground="green")
                self.last_voice_time = time.time()
                self.audio_manager.voice_detected = True
            elif time.time() - self.last_voice_time > 1:
                self.voice_indicator.config(foreground="gray")
                
            # Handle recording
            if (motion_detected or voice_detected) and not self.camera_manager.is_recording:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                video_file = self.camera_manager.start_recording()
                audio_file = self.audio_manager.start_recording()
                self.status_var.set(f"Recording started at {timestamp}")
                
            # Update recording state
            if self.camera_manager.is_recording:
                # Check if we should continue recording
                if (self.camera_manager.motion_detected or self.audio_manager.voice_detected or 
                        time.time() - max(self.last_motion_time, self.last_voice_time) < self.config["post_detection_record_time"]):
                    # Keep recording
                    self.camera_manager.record_frame(frame)
                    self.audio_manager.record_audio()
                    
                    # Reset detection flags
                    self.camera_manager.motion_detected = False
                    self.audio_manager.voice_detected = False
                else:
                    # Stop recording after timeout
                    video_file = self.camera_manager.stop_recording()
                    audio_file = self.audio_manager.stop_recording()
                    self.status_var.set(f"Recording stopped: {os.path.basename(video_file)}")
                    self.refresh_recordings_list()
        
        # Process frame for display - resize to match container size
        try:
            # Get the current container dimensions
            container_width = self.preview_container.winfo_width()
            container_height = self.preview_container.winfo_height()
            
            # Only resize if we have valid dimensions
            if container_width > 10 and container_height > 10:
                # Calculate scaling ratio
                ratio = min(container_width / frame.shape[1], container_height / frame.shape[0])
                
                # Resize the frame to fit the container
                new_width = max(int(frame.shape[1] * ratio), 1)
                new_height = max(int(frame.shape[0] * ratio), 1)
                
                # Use INTER_NEAREST for faster resizing (less quality but better performance)
                display_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
            else:
                # Invalid dimensions, use original frame
                display_frame = frame
                
            # Convert to RGB for display
            display_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PhotoImage
            img = Image.fromarray(display_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Update display
            self.preview_label.imgtk = imgtk
            self.preview_label.config(image=imgtk)
            
        except Exception as e:
            print(f"Error updating preview: {e}")
        
        # Schedule next update - use 100ms (10 fps) for better performance
        self.root.after(100, self.update_preview)
        
    def toggle_monitoring(self):
        self.monitoring = not self.monitoring
        
        if self.monitoring:
            # Check if we're using ttkbootstrap for styling
            if USE_TTKBOOTSTRAP:
                self.start_stop_button.config(text="Stop Monitoring", bootstyle=DANGER)
            else:
                self.start_stop_button.config(text="Stop Monitoring", style="Danger.TButton")
            self.status_var.set("Monitoring active - waiting for motion or voice")
        else:
            # Check if we're using ttkbootstrap for styling
            if USE_TTKBOOTSTRAP:
                self.start_stop_button.config(text="Start Monitoring", bootstyle=SUCCESS)
            else:
                self.start_stop_button.config(text="Start Monitoring", style="Success.TButton")
            self.status_var.set("Monitoring stopped")
            
            # Stop any active recording
            if self.camera_manager.is_recording:
                self.camera_manager.stop_recording()
                self.audio_manager.stop_recording()
                self.refresh_recordings_list()
                
    def update_preview_size(self, *args):
        """Update the size of the preview container based on user selection"""
        size = self.preview_size_var.get()
        self.config["preview_size"] = size
        self.config_manager.save_config()
        
        # Set container dimensions based on size
        if size == "small":
            width, height = 320, 240
        elif size == "large":
            width, height = 640, 480
        else:  # medium (default)
            width, height = 480, 360
            
        # Configure the container frame to the fixed size
        self.preview_container.configure(width=width, height=height)
        
        # Force the container to maintain this size
        self.preview_container.pack_propagate(False)
        
    def update_motion_sensitivity(self, value):
        sensitivity = int(float(value))
        self.camera_manager.motion_sensitivity = sensitivity
        self.config["motion_sensitivity"] = sensitivity
        self.config_manager.save_config()
        # Update the displayed value
        self.motion_value_label.config(text=f"{sensitivity}")
        
    def update_video_quality(self):
        """Update video quality/resolution"""
        resolution = self.video_quality_var.get()
        self.config["video_resolution"] = resolution
        
        # Update frame size
        if resolution == "480p":
            self.camera_manager.frame_width = 640
            self.camera_manager.frame_height = 480
        elif resolution == "720p":
            self.camera_manager.frame_width = 1280
            self.camera_manager.frame_height = 720
        else:  # 1080p
            self.camera_manager.frame_width = 1920
            self.camera_manager.frame_height = 1080
            
        # Reset camera to apply new resolution
        current_camera = self.camera_manager.selected_camera_index
        self.camera_manager.set_camera(current_camera)
        self.config_manager.save_config()
        
    def update_motion_method(self):
        """Update motion detection method"""
        use_simple = self.motion_method_var.get()
        self.config["use_simple_motion_detection"] = use_simple
        self.config_manager.save_config()
        
        # Reset the previous frame when changing methods
        self.camera_manager.prev_frame = None
        
    def toggle_voice_detection(self):
        enabled = self.voice_detection_var.get()
        self.audio_manager.voice_detection_enabled = enabled
        self.config["voice_detection_enabled"] = enabled
        self.config_manager.save_config()
        
    def update_post_detection_time(self, value):
        seconds = int(float(value))
        self.camera_manager.post_detection_record_time = seconds
        self.config["post_detection_record_time"] = seconds
        self.config_manager.save_config()
        # Update the displayed value
        self.post_value_label.config(text=f"{seconds}")
        
    def browse_output_dir(self):
        directory = filedialog.askdirectory(
            initialdir=self.config["output_directory"],
            title="Select Output Directory"
        )
        
        if directory:
            self.output_dir_var.set(directory)
            self.config["output_directory"] = directory
            self.camera_manager.output_directory = directory
            self.audio_manager.output_directory = directory
            self.config_manager.save_config()
            
            # Make sure the directory exists
            if not os.path.exists(directory):
                os.makedirs(directory)
                
    def refresh_recordings_list(self):
        # Clear current list
        self.recordings_listbox.delete(0, tk.END)
        
        # Get recordings from the output directory
        output_dir = self.config["output_directory"]
        if not os.path.exists(output_dir):
            return
            
        files = os.listdir(output_dir)
        recordings = [f for f in files if f.endswith('.mp4') or f.endswith('.wav')]
        recordings.sort(reverse=True)  # Most recent first
        
        # Add to listbox
        for recording in recordings[:20]:  # Limit to 20 most recent
            self.recordings_listbox.insert(tk.END, recording)
            
    def open_selected_recording(self):
        selected = self.recordings_listbox.curselection()
        if not selected:
            return
            
        filename = self.recordings_listbox.get(selected[0])
        file_path = os.path.join(self.config["output_directory"], filename)
        
        if os.path.exists(file_path):
            # Use macOS's 'open' command to open the file with default app
            subprocess.call(['open', file_path])
        else:
            messagebox.showerror("Error", "File not found. It may have been deleted.")
            self.refresh_recordings_list()
            
    def change_camera(self):
        """Change to the selected camera"""
        selected_camera_name = self.camera_var.get()
        available_cameras = self.camera_manager.get_available_cameras()
        
        # Find the selected camera's index
        for camera in available_cameras:
            if camera["name"] == selected_camera_name:
                # Switch to the selected camera
                if self.camera_manager.set_camera(camera["index"]):
                    self.status_var.set(f"Switched to {selected_camera_name}")
                else:
                    self.status_var.set(f"Failed to switch to {selected_camera_name}")
                break
    
    def change_microphone(self):
        """Change to the selected microphone"""
        selected_mic_name = self.mic_var.get()
        available_mics = self.audio_manager.get_available_microphones()
        
        # Find the selected microphone's index
        for mic in available_mics:
            if mic["name"] == selected_mic_name:
                # Switch to the selected microphone
                if self.audio_manager.set_microphone(mic["index"]):
                    self.status_var.set(f"Switched to {selected_mic_name}")
                else:
                    self.status_var.set(f"Failed to switch to {selected_mic_name}")
                break
                
    def on_closing(self):
        # Stop monitoring
        self.monitoring = False
        
        # Stop any active recording
        if self.camera_manager.is_recording:
            self.camera_manager.stop_recording()
            self.audio_manager.stop_recording()
            
        # Release resources
        self.camera_manager.release_camera()
        self.audio_manager.terminate()
        
        # Save settings
        self.config_manager.save_config()
        
        # Close application
        self.root.destroy()


# Modified main entry point with additional error handling
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = SecurityApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        if "pyaudio" in str(e).lower():
            print("\nPyAudio installation may require portaudio on macOS.")
            print("Try running these commands in Terminal:")
            print("  brew install portaudio")
            print("  pip install pyaudio")
        elif "cv2" in str(e).lower():
            print("\nOpenCV installation issue. Try:")
            print("  pip install opencv-python")
        elif "ttkbootstrap" in str(e).lower() or "-style" in str(e).lower():
            print("\nttkbootstrap issue. Try:")
            print("  pip install --upgrade ttkbootstrap")
            print("Or run without ttkbootstrap by modifying the code to use standard ttk")
        elif "import" in str(e).lower():
            print("\nMissing dependency. Try manually installing:")
            print("  pip install opencv-python numpy pyaudio SpeechRecognition Pillow ttkbootstrap")
        sys.exit(1)
