#!/usr/bin/env python3
"""
iMac Security System - Installation Script
This script handles dependency installation and launches the main program
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import threading

def main():
    """Main installation and launcher function"""
    print("iMac Security System - Setup Script")
    
    # Check platform
    if not sys.platform.startswith('darwin'):
        print("Error: This application is designed for macOS only.")
        if tk_available():
            tk.messagebox.showerror("Platform Error", "This application is designed for macOS only.")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required.")
        if tk_available():
            tk.messagebox.showerror("Python Version Error", "Python 3.7 or higher is required.")
        sys.exit(1)
    
    # Dependencies to install
    dependencies = [
        "opencv-python",
        "numpy",
        "pyaudio",
        "SpeechRecognition",
        "Pillow",
        "ttkbootstrap"
    ]
    
    # Create installer GUI
    root = tk.Tk()
    root.title("iMac Security System - Installer")
    root.geometry("500x400")
    
    # Center the window
    window_width = 500
    window_height = 400
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    # Prevent closing during installation
    def on_close():
        if not installation_complete[0]:
            if messagebox.askokcancel("Quit", "Installation in progress. Are you sure you want to quit?"):
                root.destroy()
                sys.exit(0)
        else:
            root.destroy()
            
    root.protocol("WM_DELETE_WINDOW", on_close)
    
    # Header
    header_label = tk.Label(root, text="iMac Security System", font=("Helvetica", 18, "bold"))
    header_label.pack(pady=(20, 5))
    
    subtitle_label = tk.Label(root, text="Dependency Installer", font=("Helvetica", 12))
    subtitle_label.pack(pady=(0, 20))
    
    # Progress frame
    progress_frame = tk.Frame(root)
    progress_frame.pack(fill="both", expand=True, padx=20, pady=5)
    
    # Progress bar
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=len(dependencies) + 1)
    progress_bar.pack(fill="x", pady=10)
    
    # Status label
    status_var = tk.StringVar(value="Preparing to install dependencies...")
    status_label = tk.Label(progress_frame, textvariable=status_var, anchor="w")
    status_label.pack(fill="x", pady=(5, 10))
    
    # Log text
    log_frame = tk.Frame(progress_frame)
    log_frame.pack(fill="both", expand=True)
    
    scrollbar = tk.Scrollbar(log_frame)
    scrollbar.pack(side="right", fill="y")
    
    log_text = tk.Text(log_frame, height=10, yscrollcommand=scrollbar.set)
    log_text.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=log_text.yview)
    
    # Control buttons frame
    button_frame = tk.Frame(root)
    button_frame.pack(fill="x", padx=20, pady=15)
    
    # Start/Close button
    start_button = ttk.Button(button_frame, text="Start Installation", width=20)
    start_button.pack(side="left", padx=5)
    
    cancel_button = ttk.Button(button_frame, text="Cancel", width=20, command=root.destroy)
    cancel_button.pack(side="right", padx=5)
    
    # Installation status flag
    installation_complete = [False]
    installation_successful = [False]
    
    # Add log message
    def add_log(message):
        log_text.config(state="normal")
        log_text.insert("end", message + "\n")
        log_text.see("end")
        log_text.config(state="disabled")
        root.update_idletasks()
    
    # Update progress
    def update_progress(value, status):
        progress_var.set(value)
        status_var.set(status)
        root.update_idletasks()
    
    # Install portaudio if needed
    def install_portaudio():
        try:
            # Check if PyAudio can be imported
            try:
                import pyaudio
                add_log("✓ PyAudio already installed")
                return True
            except ImportError:
                pass
                
            add_log("Installing portaudio with homebrew (required for PyAudio)...")
            update_progress(0.2, "Installing portaudio...")
            
            # Check if homebrew is installed
            which_process = subprocess.run(["which", "brew"], 
                                         capture_output=True, 
                                         text=True)
            
            if which_process.returncode != 0:
                add_log("❌ Homebrew not found. Installing Homebrew...")
                update_progress(0.3, "Installing Homebrew...")
                
                brew_install = subprocess.run(["/bin/bash", "-c", 
                                             '$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)'],
                                            capture_output=True,
                                            text=True)
                
                if brew_install.returncode != 0:
                    add_log("❌ Failed to install Homebrew. Please install manually.")
                    add_log("Run this command in Terminal:")
                    add_log('   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
                    return False
                else:
                    add_log("✓ Homebrew installed successfully")
            
            # Install portaudio with homebrew
            add_log("Installing portaudio...")
            update_progress(0.4, "Installing portaudio...")
            
            portaudio_process = subprocess.run(["brew", "install", "portaudio"], 
                                             capture_output=True, 
                                             text=True)
            
            if portaudio_process.returncode == 0:
                add_log("✓ Portaudio installed successfully")
                return True
            else:
                add_log(f"❌ Failed to install portaudio: {portaudio_process.stderr}")
                add_log("You may need to install it manually:")
                add_log("   brew install portaudio")
                return False
                
        except Exception as e:
            add_log(f"❌ Error installing portaudio: {str(e)}")
            return False
    
    # Install Python dependencies
    def install_dependencies():
        try:
            missing = []
            progress_step = 1
            
            # Upgrade pip first
            add_log("Upgrading pip...")
            update_progress(progress_step, "Upgrading pip...")
            
            pip_upgrade = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                                       capture_output=True,
                                       text=True)
            
            if pip_upgrade.returncode == 0:
                add_log("✓ Pip upgraded successfully")
            else:
                add_log("❌ Failed to upgrade pip, continuing with installations...")
            
            progress_step += 1
            
            # Install each dependency
            for dep in dependencies:
                update_progress(progress_step, f"Installing {dep}...")
                add_log(f"Installing {dep}...")
                
                # Special handling for pyaudio on macOS
                if dep == "pyaudio" and sys.platform.startswith('darwin'):
                    if not install_portaudio():
                        add_log("⚠️ Portaudio installation may have failed, attempting to install PyAudio anyway...")
                
                # Install the dependency
                install_process = subprocess.run([sys.executable, "-m", "pip", "install", dep],
                                              capture_output=True,
                                              text=True)
                
                if install_process.returncode == 0:
                    add_log(f"✓ Successfully installed {dep}")
                else:
                    add_log(f"❌ Failed to install {dep}: {install_process.stderr}")
                    missing.append(dep)
                
                progress_step += 1
            
            # Verify installations
            update_progress(len(dependencies), "Verifying installations...")
            add_log("\nVerifying installations...")
            
            verification_failures = []
            try:
                import cv2
                add_log("✓ OpenCV installed")
            except ImportError:
                add_log("❌ OpenCV verification failed")
                verification_failures.append("opencv-python")
                
            try:
                import numpy
                add_log("✓ NumPy installed")
            except ImportError:
                add_log("❌ NumPy verification failed")
                verification_failures.append("numpy")
                
            try:
                import pyaudio
                add_log("✓ PyAudio installed")
            except ImportError:
                add_log("❌ PyAudio verification failed")
                verification_failures.append("pyaudio")
                
            try:
                import speech_recognition
                add_log("✓ SpeechRecognition installed")
            except ImportError:
                add_log("❌ SpeechRecognition verification failed")
                verification_failures.append("SpeechRecognition")
                
            try:
                import PIL
                add_log("✓ Pillow installed")
            except ImportError:
                add_log("❌ Pillow verification failed")
                verification_failures.append("Pillow")
                
            try:
                import ttkbootstrap
                add_log("✓ ttkbootstrap installed")
            except ImportError:
                add_log("❌ ttkbootstrap verification failed")
                verification_failures.append("ttkbootstrap")
            
            # Final status
            if not missing and not verification_failures:
                update_progress(len(dependencies) + 1, "Installation complete!")
                add_log("\n✅ All dependencies installed successfully!")
                return True
            else:
                all_failures = list(set(missing + verification_failures))
                update_progress(len(dependencies) + 1, "Installation completed with errors")
                add_log(f"\n⚠️ Installation completed with issues: {', '.join(all_failures)}")
                
                # Special handling for PyAudio on macOS
                if "pyaudio" in all_failures and sys.platform.startswith('darwin'):
                    add_log("\nFor PyAudio on macOS, please try these steps:")
                    add_log("1. Install portaudio: brew install portaudio")
                    add_log("2. Install pyaudio: pip install pyaudio")
                    
                return False
                
        except Exception as e:
            add_log(f"\n❌ Error during installation: {str(e)}")
            update_progress(len(dependencies) + 1, "Installation failed")
            return False
    
    # Launch main application
    def launch_main_app():
        try:
            add_log("\nLaunching iMac Security System...")
            
            # Get the directory of this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            main_script = os.path.join(script_dir, "imac_security.py")
            
            if os.path.exists(main_script):
                # Run the main script
                subprocess.Popen([sys.executable, main_script])
                add_log("✅ Application launched successfully!")
            else:
                add_log(f"❌ Main script not found at: {main_script}")
                add_log("Please make sure imac_security.py is in the same directory.")
                return False
                
            return True
        except Exception as e:
            add_log(f"❌ Error launching application: {str(e)}")
            return False
    
    # Main installation thread
    def installation_thread():
        try:
            success = install_dependencies()
            installation_successful[0] = success
            
            if success:
                add_log("\nReady to launch the application!")
                update_progress(len(dependencies) + 1, "Installation complete!")
                start_button.config(text="Launch Application", command=launch_and_close)
            else:
                add_log("\nInstallation completed with issues. You may need to install some dependencies manually.")
                add_log("You can still try to launch the application.")
                start_button.config(text="Launch Anyway", command=launch_and_close)
            
            cancel_button.config(text="Close")
            installation_complete[0] = True
        except Exception as e:
            add_log(f"\n❌ Error during installation: {str(e)}")
            start_button.config(text="Retry Installation", command=start_installation)
            cancel_button.config(text="Close")
            installation_complete[0] = True
    
    # Start installation
    def start_installation():
        start_button.config(state="disabled")
        cancel_button.config(state="disabled")
        threading.Thread(target=installation_thread, daemon=True).start()
    
    # Launch and close
    def launch_and_close():
        if launch_main_app():
            root.destroy()
    
    # Set button command
    start_button.config(command=start_installation)
    
    # Run the GUI
    root.mainloop()

def tk_available():
    """Check if tkinter is available"""
    try:
        import tkinter
        return True
    except ImportError:
        return False

if __name__ == "__main__":
    main()
