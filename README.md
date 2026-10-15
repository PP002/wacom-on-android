# Wacom Android Userspace Driver (CTL-471 & Intuos Edition)

### *Turn any rooted Android device into a full Wacom drawing tablet*

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Android Tested](https://img.shields.io/badge/Android-Rooted%20Termux-green)](#)

> **No kernel modules (`wacom.ko`). No recompilation. Full absolute coordinates, pressure, and hover support.**  
> Optimized and tested for classical Wacom tablets (such as **CTL-471**, `0x056a:0x0300`) on rooted Android via Termux.

---

## 🚀 Key Technical Enhancements in This Fork

Unlike standard upstream drivers, this version includes critical fixes for running smoothly on mobile Android/Termux environments:
- **Explicit `libusb` Backend Binding**: Resolves `NoBackendError` in Termux by explicitly linking to `/data/data/com.termux/files/usr/lib/libusb-1.0.so`.
- **USB Control Transfer Initialization**: Sends proprietary Wacom control commands (`Report ID 0x02`) to wake up the tablet from default mouse-only relative mode into full 1024-level absolute pressure mode.
- **Robust Interface Claiming**: Implements `usb.util.claim_interface(self.device, 0)` to eliminate `Errno 19 (No such device)` disconnection errors during data polling.
- **270-Degree Rotation & Mapping**: Perfectly maps the tablet's raw coordinates with the **USB cable positioned at the top**, preventing aspect ratio distortion on vertical phone screens.
- **Gamma 1.2 Pressure Curve**: Fine-tunes tactile feedback so light strokes feel natural and responsive.

---

## Features

| Feature | Status |
|------------------------|-----------|
| Hover cursor | Supported |
| 1024 / 2048-level pressure | Supported (Gamma 1.2 tuned) |
| Tip click & touch events | Supported |
| 100% active area absolute mapping | Supported |
| Pure Python + `libusb` + `uinput` | Supported |

---

## Requirements

- **Rooted Android Device** (Magisk, KernelSU, etc.)
- **Termux** app installed
- **USB OTG cable / adapter**
- **Wacom Tablet** (Tested on CTL-471 `0x056a:0x0300` and compatible models)
- **Stylus-aware painting app** (SketchBook, Infinite Painter, Medibang, or web-based canvas)

---

## Quick Start

### 1. Install Termux Dependencies
Open Termux and run:
```bash
pkg update && pkg install python libusb git clang make
pip install pyusb
2. Clone the Repository
Bash
git clone [https://github.com/PP002/wacom-on-android.git](https://github.com/PP002/wacom-on-android.git)
cd wacom-on-android/src
3. Run the Driver
Grant root privileges and launch the driver script:

Bash
su -c "python wacom_driver.py"
(Press Ctrl+C to exit safely at any time.)

Automation (One-Click Shortcut)
To avoid typing long commands every time you plug in the tablet, create a quick launcher script (run.sh):

Bash
cat << 'EOF' > run.sh
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")"
su -c "/data/data/com.termux/files/usr/bin/python wacom_driver.py"
EOF

chmod +x run.sh
Now you can launch your drawing pad instantly with:

Bash
./run.sh
Configuration
You can tweak screen resolution, raw hardware boundaries, or pressure curves directly inside wacom_driver.py:

Python
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 2340

TABLET_RAW_MAX_X = 15200
TABLET_RAW_MAX_Y = 9500
Troubleshooting
NoBackendError: Ensure libusb is installed via Termux (pkg install libusb) and the backend path in the script points correctly to /data/data/com.termux/files/usr/lib/libusb-1.0.so.

Errno 19 No such device: Ensure interface 0 is successfully claimed before reading endpoints.

No Pressure / Mouse Mode: Verify that the USB control transfer initialization packet (Report ID 0x02) executes successfully upon connection.

Credits & Acknowledgments
Original Project: NoxProductions/wacom-on-android

Linux HID & uinput Documentation

Wacom HID Protocol Reference

"Why let old hardware gather dust when you can turn your phone into a portable graphics tablet for free?"

License
GPL v3 License
