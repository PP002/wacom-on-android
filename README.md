
# Wacom Android Userspace Driver

### *Turn any rooted Android tablet into a full Wacom Intuos*

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Android 14 Tested](https://img.shields.io/badge/Android-14%20Tested-green)](#)

> **No kernel modules. No recompilation. Full hover, pressure, and undo/redo.**  
> Works on **Samsung Galaxy Tab S2 (LineageOS 21)** — and any rooted Android with `/dev/uinput`.

---

## Features

| Feature                | Status    |
|------------------------|-----------|
| Hover cursor           | Supported |
| 2048-level pressure    | Supported (tunable) |
| Tip click & barrel buttons | Supported |
| Button 1 → **Undo (Ctrl+Z)** | Supported |
| Button 2 → **Redo (Ctrl+Y)** | Supported |
| 100% active area mapping | Supported |
| Pure Python + `libusb` + `uinput` | Supported |

---

## Demo ( Coming soon )

![Hover + Pressure](screenshots/hover.jpg)  
*Hovering shows cursor. Pressure changes stroke weight in Infinite Painter.*

![Undo/Redo GIF](screenshots/undo_redo.gif)  
*Barrel buttons trigger Ctrl+Z / Ctrl+Y in any app.*

---

## Requirements

- **Rooted Android** (Magisk, KernelSU, etc.)
- **Termux** with `tsu` or `su`
- **USB OTG cable**
- **Wacom Intuos CTL-480** (or compatible)
- **Stylus-aware app** (Infinite Painter, Medibang, Sketchbook)

---

## Quick Start


# 1. Install Termux packages
- pkg install python libusb git

# 2. Install Python deps
- pip install pyusb

# 3. Clone & run
- git clone https://github.com/PP002/wacom-on-android
- cd wacom-on-android/src
- su
- /data/data/com.termux/files/usr/bin/python wacom_driver.py
- Press Ctrl+C to stop.

## Configuration
- Edit src/wacom_driver.py:
- SCREEN_WIDTH = 2048
- SCREEN_HEIGHT = 1536

# Pressure curve (easier max pressure)
- PRESSURE_EASING = 1.8
- PRESSURE_OFFSET = 50
- PRESSURE_CLAMP_MIN = 100

## Troubleshooting
- See TROUBLESHOOTING.md

## License
- GPL V3 — This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

## Credits
- Wacom HID report format: Linux hid-wacom driver
- uinput legacy API: Linux kernel docs
- @noxbitx — for resurrecting old hardware

“Why spend $40 on a half-working stylus when you can run a real Wacom for free?”

---


[![Stars](https://img.shields.io/github/stars/noxbitx/wacom-on-android?style=social)](#)
[![Forks](https://img.shields.io/github/forks/noxbitx/wacom-on-android?style=social)](#)


