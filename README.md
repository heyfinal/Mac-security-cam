# iMac Security System 🔒

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/yourusername/imac-security-system)
[![Python](https://img.shields.io/badge/python-3.6%2B-brightgreen)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey)](https://www.apple.com/macos)

> A comprehensive security camera system for macOS with motion detection, voice detection, and SSH remote control capabilities.

<p align="center">
  <img src="https://raw.githubusercontent.com/yourusername/imac-security-system/main/screenshots/dashboard.png" alt="iMac Security System Dashboard" width="700">
</p>

## ✨ Features

- 📹 Real-time video monitoring using your Mac's camera
- 👂 Voice detection with audio recording
- 🔍 Smart motion detection with configurable sensitivity
- 🎬 Automatic recording when motion or voice is detected
- 🌃 Dark mode UI with modern interface
- 📱 Camera and microphone device selection
- 📊 Performance optimizations for lower CPU usage
- 🎮 GUI control panel for easy configuration
- 🖥️ **SSH Remote Control** - start/stop monitoring from anywhere
- ⏱️ Scheduled monitoring with automatic shutdown
- 📂 Organized video and audio storage

## 🚀 Installation

### Prerequisites

- macOS 10.13 or higher
- Python 3.6 or higher

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/imac-security-system.git
cd imac-security-system

# Install dependencies
pip3 install -r requirements.txt
```

### Dependencies

- OpenCV (cv2)
- NumPy
- PyAudio
- SpeechRecognition
- Pillow (PIL)
- ttkbootstrap (optional, for enhanced UI)

## 🔧 Usage

### GUI Mode

Launch the application with its full graphical interface:

```bash
python3 imac-security.py
```

### SSH Remote Control 🔥 NEW!

Control your security system remotely via SSH:

```bash
# Start monitoring remotely
ssh user@imac-host "python3 /path/to/imac-security.py --start-monitoring"

# Start monitoring for a specific duration (e.g., 60 minutes)
ssh user@imac-host "python3 /path/to/imac-security.py --start-monitoring --duration 60"

# Stop monitoring remotely
ssh user@imac-host "python3 /path/to/imac-security.py --stop-monitoring"

# Check monitoring status
ssh user@imac-host "python3 /path/to/imac-security.py --status"
```

### Headless Mode

Run the application without a GUI (perfect for background operation):

```bash
python3 imac-security.py --headless
```

## 📋 Command-Line Options

| Option | Description |
|--------|-------------|
| `--headless` | Run in headless mode (no GUI) |
| `--start-monitoring` | Start monitoring immediately |
| `--stop-monitoring` | Stop active monitoring |
| `--duration [minutes]` | Set monitoring duration (0 for indefinite) |
| `--config [path]` | Path to custom config file |
| `--status` | Check monitoring status |

## ⚙️ Configuration

The application stores its configuration in:
```
~/Library/Application Support/iMacSecuritySystem/config.json
```

### Key Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `motion_sensitivity` | Motion detection sensitivity (1-25) | 20 |
| `voice_detection_enabled` | Enable/disable voice detection | true |
| `post_detection_record_time` | Seconds to continue recording after detection | 10 |
| `video_resolution` | Video resolution ("480p", "720p", "1080p") | "480p" |
| `use_simple_motion_detection` | Use faster motion detection algorithm | true |
| `output_directory` | Directory to store recordings | ~/Documents/iMacSecuritySystem |

## 🖼️ Screenshots

<p align="center">
  <img src="https://raw.githubusercontent.com/yourusername/imac-security-system/main/screenshots/detection.png" alt="Motion Detection" width="400">
  <img src="https://raw.githubusercontent.com/yourusername/imac-security-system/main/screenshots/settings.png" alt="Settings Panel" width="400">
</p>

## 📝 Logs

Logs are stored at:
```
~/Library/Logs/iMacSecuritySystem.log
```

## 🛠️ Advanced Setup

### Creating a Launch Agent

To run the monitoring system at startup:

1. Create a launch agent file:

```bash
cat > ~/Library/LaunchAgents/com.yourusername.imacsecurity.plist << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.yourusername.imacsecurity</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/path/to/imac-security.py</string>
    <string>--headless</string>
    <string>--start-monitoring</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
</dict>
</plist>
EOL
```

2. Load the launch agent:

```bash
launchctl load ~/Library/LaunchAgents/com.yourusername.imacsecurity.plist
```

## 🔒 Privacy Considerations

This application accesses your camera and microphone. macOS will prompt for permissions when first launched.

## 🙋‍♀️ FAQ

**Q: How much storage space do recordings use?**  
A: A 1-minute recording at 480p uses approximately 5-10MB of storage space.

**Q: Does this work on Windows or Linux?**  
A: This application is designed specifically for macOS. Windows/Linux support may be added in the future.

**Q: Can I receive notifications when motion is detected?**  
A: Not currently, but this is planned for a future release.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📬 Contact

Your Name - [@yourusername](https://twitter.com/yourusername) - email@example.com

Project Link: [https://github.com/yourusername/imac-security-system](https://github.com/yourusername/imac-security-system)

---

<p align="center">
  Made with ❤️ for iMac users who value security
</p>
