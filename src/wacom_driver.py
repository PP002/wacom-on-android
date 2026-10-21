#!/data/data/com.termux/files/usr/bin/python
import usb.core, usb.util, usb.backend.libusb1, struct, os, sys, time, ctypes, fcntl

UINPUT_PATH = '/dev/uinput'
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_SET_ABSBIT = 0x40045567
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502

BUS_USB = 0x03
EV_SYN = 0x00
EV_KEY = 0x01
EV_ABS = 0x03

ABS_X = 0x00
ABS_Y = 0x01
ABS_PRESSURE = 0x18
BTN_TOUCH = 0x14a
BTN_TOOL_PEN = 0x140
SYN_REPORT = 0
ABS_CNT = 0x40

class uinput_user_dev(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 80),
        ("id", ctypes.c_uint16 * 4),
        ("ff_effects_max", ctypes.c_int),
        ("absmax", ctypes.c_int * ABS_CNT),
        ("absmin", ctypes.c_int * ABS_CNT),
        ("absfuzz", ctypes.c_int * ABS_CNT),
        ("absflat", ctypes.c_int * ABS_CNT)
    ]

class input_event(ctypes.Structure):
    _fields_ = [
        ("time_sec", ctypes.c_long),
        ("time_usec", ctypes.c_long),
        ("type", ctypes.c_uint16),
        ("code", ctypes.c_uint16),
        ("value", ctypes.c_int32)
    ]

WACOM_VENDOR_ID = 0x056a
WACOM_PRODUCT_ID = 0x0300
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 2340

TABLET_RAW_MAX_X = 15200
TABLET_RAW_MAX_Y = 9500

class UInputDevice:
    def __init__(self):
        self.fd = os.open(UINPUT_PATH, os.O_WRONLY | os.O_NONBLOCK)
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_SYN)
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_KEY)
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_ABS)
        fcntl.ioctl(self.fd, UI_SET_KEYBIT, BTN_TOUCH)
        fcntl.ioctl(self.fd, UI_SET_KEYBIT, BTN_TOOL_PEN)
        fcntl.ioctl(self.fd, UI_SET_ABSBIT, ABS_X)
        fcntl.ioctl(self.fd, UI_SET_ABSBIT, ABS_Y)
        fcntl.ioctl(self.fd, UI_SET_ABSBIT, ABS_PRESSURE)
        
        udev = uinput_user_dev()
        udev.name = b'Wacom CTL-471 Sensitive Pressure'
        udev.id[0] = BUS_USB
        udev.id[1] = WACOM_VENDOR_ID
        udev.id[2] = WACOM_PRODUCT_ID
        udev.id[3] = 1
        udev.absmax[ABS_X] = SCREEN_WIDTH
        udev.absmax[ABS_Y] = SCREEN_HEIGHT
        udev.absmax[ABS_PRESSURE] = 1023
        os.write(self.fd, bytes(udev))
        fcntl.ioctl(self.fd, UI_DEV_CREATE)
        time.sleep(0.2)

    def send_event(self, t, c, v):
        ev = input_event()
        t_now = time.time()
        ev.time_sec = int(t_now)
        ev.time_usec = int((t_now - ev.time_sec) * 1000000)
        ev.type, ev.code, ev.value = t, c, v
        os.write(self.fd, bytes(ev))

    def sync(self):
        self.send_event(EV_SYN, SYN_REPORT, 0)

    def close(self):
        if self.fd:
            fcntl.ioctl(self.fd, UI_DEV_DESTROY)
            os.close(self.fd)

class WacomDriver:
    def __init__(self):
        self.uinput = UInputDevice()
        self.device = None
        self.endpoint = None

    def connect(self):
        libusb_path = '/data/data/com.termux/files/usr/lib/libusb-1.0.so'
        backend = usb.backend.libusb1.get_backend(find_library=lambda x: libusb_path)
        print(f"Looking for Wacom tablet {hex(WACOM_VENDOR_ID)}:{hex(WACOM_PRODUCT_ID)}...")
        self.device = usb.core.find(idVendor=WACOM_VENDOR_ID, idProduct=WACOM_PRODUCT_ID, backend=backend)
        if not self.device: 
            print("❌ Wacom device not found!")
            return False
        
        # Only separate the core driver, do not manually claim the interface to avoid conflicts.
        try:
            if self.device.is_kernel_driver_active(0):
                self.device.detach_kernel_driver(0)
                print("✓ Successfully detached kernel driver from interface 0")
        except Exception as e:
            print(f"⚠ Detach kernel driver note: {e}")
            
        try: 
            self.device.set_configuration()
        except: 
            pass

        try:
            init_data = [0x02, 0x02, 0x02] + [0x00] * 5
            self.device.ctrl_transfer(
                bmRequestType=0x21, 
                bRequest=0x09, 
                wValue=0x0302, 
                wIndex=0x00, 
                data_or_wLength=init_data, 
                timeout=600000
            )
            print("✓ Hardware initialized: Report ID 0x02 absolute mode unlocked")
        except Exception as e:
            print(f"⚠ Control transfer note: {e}")

        cfg = self.device.get_active_configuration()
        self.endpoint = usb.util.find_descriptor(cfg[(0,0)], custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)
        return self.endpoint is not None

    def run(self):
        print("\n=== Driver Running (Rotation, Scaling & Pressure Curve) ===")
        print("Please test in SketchBook or ebookcc.com/create, then press Ctrl+C to finish.\n")

        try:
            while True:
                try:
                    data = self.endpoint.read(64, timeout=600000)
                except usb.core.USBTimeoutError:
                    continue

                if len(data) < 4:
                    continue

                report_id = data[0]
                
                if report_id == 0x02 and len(data) >= 8:
                    status = data[1]
                    in_range = bool(status & 0x20 or status & 0x80 or status & 0x01)
                    tip_switch = bool(status & 0x01)
                    
                    raw_x = struct.unpack('<H', bytes(data[2:4]))[0]
                    raw_y = struct.unpack('<H', bytes(data[4:6]))[0]
                    raw_pressure = struct.unpack('<H', bytes(data[6:8]))[0]
                    
                    if raw_pressure > 0:
                        normalized = raw_pressure / 1023.0
                        pressure = int(min(1023, (normalized ** 1.2) * 1023))
                    else:
                        pressure = 0
                    
                    nx = raw_x / TABLET_RAW_MAX_X
                    ny = raw_y / TABLET_RAW_MAX_Y
                    screen_x = int((1.0 - ny) * SCREEN_WIDTH)
                    screen_y = int(nx * SCREEN_HEIGHT)
                    
                    screen_x = max(0, min(SCREEN_WIDTH, screen_x))
                    screen_y = max(0, min(SCREEN_HEIGHT, screen_y))
                    
                    self.uinput.send_event(EV_KEY, BTN_TOOL_PEN, 1 if in_range else 0)
                    if in_range:
                        self.uinput.send_event(EV_ABS, ABS_X, screen_x)
                        self.uinput.send_event(EV_ABS, ABS_Y, screen_y)
                        self.uinput.send_event(EV_KEY, BTN_TOUCH, 1 if tip_switch else 0)
                        self.uinput.send_event(EV_ABS, ABS_PRESSURE, pressure)
                    self.uinput.sync()
                    
                elif report_id == 0x01:
                    continue
                    
        except KeyboardInterrupt:
            print("\nSafely exiting the driver...")
        finally:
            try:
                self.uinput.close()
            except:
                pass

if __name__ == '__main__':
    d = WacomDriver()
    if d.connect(): 
        d.run()
