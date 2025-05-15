<div align="center">
  
# 🔒 iMac Security System

<img src="docs/images/logo.png" alt="iMac Security System Logo" width="200"/>

**Transform your iMac into an intelligent security camera with motion & voice detection**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Version: 1.0.0](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/yourusername/imac-security-system)

<p align="center">
  <img src="docs/images/demo.gif" alt="iMac Security System Demo" width="800"/>
</p>

</div>

## ✨ Features

<table>
  <tr>
    <td width="50%">
      <h3>🔍 Motion Detection</h3>
      <ul>
        <li>Advanced motion detection algorithms</li>
        <li>Adjustable sensitivity controls</li>
        <li>Silent background operation</li>
        <li>Automatic recording on detection</li>
      </ul>
    </td>
    <td width="50%">
      <h3>🔊 Voice Recognition</h3>
      <ul>
        <li>Detect and respond to human voices</li>
        <li>Toggle voice detection on/off</li>
        <li>Audio recording synchronized with video</li>
        <li>Adjustable audio sensitivity</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td>
      <h3>📹 Smart Recording</h3>
      <ul>
        <li>Automatic event-triggered recording</li>
        <li>Configurable post-detection duration</li>
        <li>Multiple video quality options</li>
        <li>Organized file management system</li>
      </ul>
    </td>
    <td>
      <h3>🖥️ Clean UI Design</h3>
      <ul>
        <li>Modern dark interface</li>
        <li>Adjustable preview size</li>
        <li>Real-time status indicators</li>
        <li>Tabbed settings organization</li>
      </ul>
    </td>
  </tr>
</table>

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/imac-security-system.git

# Navigate to the project directory
cd imac-security-system

# Run the application
python3 imac_security.py
```

## 🛠️ Installation

### Prerequisites

- macOS (designed specifically for iMac)
- Python 3.7 or higher
- Built-in iMac camera or compatible webcam
- Microphone (built-in or external)

### Dependencies

The application requires these Python packages:

```bash
pip3 install opencv-python numpy pyaudio SpeechRecognition Pillow
```

If you have installation issues with PyAudio on macOS:

```bash
brew install portaudio
pip3 install pyaudio
```

## 📖 Usage Guide

<details>
<summary><b>Starting Surveillance</b> 🔍</summary>
<p>

1. Launch the application using `python3 imac_security.py`
2. Adjust settings as needed (sensitivity, recording time, etc.)
3. Click the "START MONITORING" button
4. The system will now monitor for motion and/or voice

</p>
</details>

<details>
<summary><b>Adjusting Settings</b> ⚙️</summary>
<p>

The application includes three settings tabs:

1. **Detection Settings**
   - Motion Sensitivity: Adjust how sensitive the system is to movement
   - Motion Detection Method: Choose between performance and accuracy
   - Voice Detection: Enable/disable voice-triggered recording
   - Recording Duration: Set how long to record after activity stops

2. **Video Settings**
   - Video Quality: Choose between 480p, 720p, or 1080p
   - Output Directory: Select where recordings are saved

3. **Recordings**
   - View recent recordings
   - Open recordings with default media player
   - Refresh the recordings list

</p>
</details>

<details>
<summary><b>Viewing Recordings</b> 📼</summary>
<p>

1. Go to the "Recordings" tab
2. Select a recording from the list
3. Click "Open Selected" to view with your default media player
4. Recordings are saved to the configured output directory (default: ~/Documents/iMacSecuritySystem)

</p>
</details>

## 🧰 Technical Details

### Architecture

<p align="center">
  <img src="docs/images/architecture.png" alt="iMac Security System Architecture" width="600"/>
</p>

The application is built on a modular architecture:

- **ConfigManager**: Handles settings persistence and management
- **CameraManager**: Controls camera operations and motion detection
- **AudioManager**: Handles microphone input and voice detection 
- **SecurityApp**: Main application UI and business logic

### Performance Optimizations

- Two motion detection algorithms: Fast (frame differencing) and Accurate (background subtraction)
- Adjustable preview size to reduce CPU usage
- Framerate limiting for better performance
- Voice detection throttling to reduce CPU usage

## 🎨 Customization

### Video Quality Settings

| Setting | Resolution | Best For |
|---------|------------|----------|
| 480p | 640×480 | Better performance, lower storage usage |
| 720p | 1280×720 | Balanced quality and performance |
| 1080p | 1920×1080 | Highest quality, more storage usage |

### Motion Sensitivity

Adjust the sensitivity slider to control how easily motion is detected:
- **Low**: Only detect significant movement (less false positives)
- **High**: Detect subtle movements (may increase false positives)

## 🤝 Contributing

Contributions make the open source community amazing! Any contributions you make are **greatly appreciated**.

<details>
<summary>How to contribute</summary>
<br>

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

</details>

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

## 👏 Acknowledgments

* [OpenCV](https://opencv.org/) - Computer vision capabilities
* [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) - Voice detection
* [PyAudio](https://pypi.org/project/PyAudio/) - Audio processing

---

<p align="center">
  Made with ❤️ for iMac users everywhere
  <br>
  <a href="https://github.com/yourusername">@yourusername</a>
</p>
