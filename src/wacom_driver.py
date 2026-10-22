#!/data/data/com.termux/files/usr/bin/python
import os, sys, time, ctypes, fcntl, glob, struct

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
BTN_STYLUS = 0x14b
BTN_STYLUS2 = 0x14c
SYN_REPORT = 0
ABS_CNT = 0x40

KEY_ENTER = 0x1c
KEY_E = 0x12

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
        fcntl.ioctl(self.fd, UI_SET_KEYBIT, BTN_STYLUS)
        fcntl.ioctl(self.fd, UI_SET_KEYBIT, BTN_STYLUS2)
        fcntl.ioctl(self.fd, UI_SET_KEYBIT, KEY_ENTER)
        fcntl.ioctl(self.fd, UI_SET_KEYBIT, KEY_E)
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
        self.libusb = None
        self.dev_handle = None
        self.button1_pressed = False
        self.button2_pressed = False

    def connect(self):
        libusb_path = '/data/data/com.termux/files/usr/lib/libusb-1.0.so'
        
        try:
            for dev_dir in glob.glob('/sys/bus/usb/devices/*'):
                try:
                    vid_path = os.path.join(dev_dir, 'idVendor')
                    pid_path = os.path.join(dev_dir, 'idProduct')
                    if os.path.exists(vid_path) and os.path.exists(pid_path):
                        with open(vid_path, 'r') as f:
                            vid = f.read().strip()
                        with open(pid_path, 'r') as f:
                            pid = f.read().strip()
                        if int(vid, 16) == WACOM_VENDOR_ID and int(pid, 16) == WACOM_PRODUCT_ID:
                            base_dev = os.path.basename(dev_dir)
                            for intf_dir in glob.glob(os.path.join(dev_dir, f'{base_dev}:*')):
                                driver_link = os.path.join(intf_dir, 'driver')
                                if os.path.exists(driver_link):
                                    driver_name = os.path.basename(os.readlink(driver_link))
                                    if driver_name == 'usbhid':
                                        intf_name = os.path.basename(intf_dir)
                                        unbind_path = f'/sys/bus/usb/drivers/usbhid/unbind'
                                        if os.path.exists(unbind_path):
                                            with open(unbind_path, 'w') as u:
                                                u.write(intf_name)
                                            print(f"✓ Unbound {intf_name} from usbhid via sysfs")
                except Exception:
                    continue
        except Exception as e:
            print(f"⚠ Sysfs unbind note: {e}")

        try:
            self.libusb = ctypes.CDLL(libusb_path)
        except Exception as e:
            print(f"❌ Failed to load libusb: {e}")
            return False

        self.libusb.libusb_init.argtypes = [ctypes.c_void_p]
        self.libusb.libusb_init.restype = ctypes.c_int
        
        self.libusb.libusb_open_device_with_vid_pid.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_uint16]
        self.libusb.libusb_open_device_with_vid_pid.restype = ctypes.c_void_p

        self.libusb.libusb_detach_kernel_driver.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.libusb.libusb_detach_kernel_driver.restype = ctypes.c_int

        self.libusb.libusb_claim_interface.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.libusb.libusb_claim_interface.restype = ctypes.c_int

        self.libusb.libusb_control_transfer.argtypes = [ctypes.c_void_p, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint16, ctypes.c_uint16, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint16, ctypes.c_uint32]
        self.libusb.libusb_control_transfer.restype = ctypes.c_int

        self.libusb.libusb_interrupt_transfer.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_uint32]
        self.libusb.libusb_interrupt_transfer.restype = ctypes.c_int

        self.libusb.libusb_init(None)

        print(f"Looking for Wacom tablet {hex(WACOM_VENDOR_ID)}:{hex(WACOM_PRODUCT_ID)}...")
        self.dev_handle = self.libusb.libusb_open_device_with_vid_pid(None, WACOM_VENDOR_ID, WACOM_PRODUCT_ID)
        if not self.dev_handle:
            print("❌ Wacom device not found!")
            return False

        try:
            self.libusb.libusb_detach_kernel_driver(self.dev_handle, 0)
        except Exception:
            pass

        ret = self.libusb.libusb_claim_interface(self.dev_handle, 0)
        if ret < 0:
            print(f"⚠ Claim interface warning code: {ret}")
        else:
            print("✓ USB interface 0 claimed successfully via libusb")

        try:
            init_data = (ctypes.c_ubyte * 8)(0x02, 0x02, 0x02, 0, 0, 0, 0, 0)
            self.libusb.libusb_control_transfer(
                self.dev_handle, 
                0x21, 0x09, 0x0302, 0x00, 
                init_data, 8, 1000
            )
            print("✓ Hardware initialized: Report ID 0x02 absolute mode unlocked")
        except Exception as e:
            print(f"⚠ Control transfer note: {e}")

        return True

    def send_key(self, key):
        self.uinput.send_event(EV_KEY, key, 1)
        self.uinput.sync()
        time.sleep(0.01)
        self.uinput.send_event(EV_KEY, key, 0)
        self.uinput.sync()

    def run(self):
        print("\n=== Driver Running (Buttons: Lower=Enter, Upper=E) ===")
        print("Please test in ebookcc.com/create or SketchBook, then press Ctrl+C to finish.\n")

        buf = (ctypes.c_ubyte * 64)()
        actual_length = ctypes.c_int(0)

        try:
            while True:
                ret = self.libusb.libusb_interrupt_transfer(
                    self.dev_handle, 0x81, buf, 64, ctypes.byref(actual_length), 600000
                )
                
                if ret < 0 or actual_length.value < 4:
                    continue

                data = bytes(buf[:actual_length.value])
                report_id = data[0]
                
                if report_id == 0x02 and len(data) >= 8:
                    status = data[1]
                    in_range = bool(status & 0x20 or status & 0x80 or status & 0x01)
                    tip_switch = bool(status & 0x01)
                    button1 = bool(status & 0x02)
                    button2 = bool(status & 0x04)
                    
                    raw_x = struct.unpack('<H', data[2:4])[0]
                    raw_y = struct.unpack('<H', data[4:6])[0]
                    raw_pressure = struct.unpack('<H', data[6:8])[0]
                    
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
                    
                    if button1 and not self.button1_pressed:
                        self.send_key(KEY_ENTER)
                    if button2 and not self.button2_pressed:
                        self.send_key(KEY_E)
                        
                    self.button1_pressed = button1
                    self.button2_pressed = button2
                    
                    self.uinput.send_event(EV_KEY, BTN_TOOL_PEN, 1 if in_range else 0)
                    if in_range:
                        self.uinput.send_event(EV_ABS, ABS_X, screen_x)
                        self.uinput.send_event(EV_ABS, ABS_Y, screen_y)
                        self.uinput.send_event(EV_KEY, BTN_TOUCH, 1 if tip_switch else 0)
                        self.uinput.send_event(EV_KEY, BTN_STYLUS, 1 if button1 else 0)
                        self.uinput.send_event(EV_KEY, BTN_STYLUS2, 1 if button2 else 0)
                        self.uinput.send_event(EV_ABS, ABS_PRESSURE, pressure)
                    self.uinput.sync()
                    
                elif report_id == 0x01:
                    continue
                    
        except KeyboardInterrupt:
            print("\nSafely exiting the driver...")
        finally:
            if self.dev_handle and self.libusb:
                try:
                    self.libusb.libusb_release_interface(self.dev_handle, 0)
                    self.libusb.libusb_close(self.dev_handle)
                except:
                    pass
            self.uinput.close()

if __name__ == '__main__':
    d = WacomDriver()
    if d.connect(): 
        d.run()
