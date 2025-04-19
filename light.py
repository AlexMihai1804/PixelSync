import time
from yeelight import Bulb, LightType, BulbException

class Light:
    def __init__(self, ip: str) -> None:
        self.ip = ip
        self.bulb = Bulb(ip)
        self.wait_time = 0.25

        # Initial state variables
        self.initial_color_mode = None
        self.initial_power = None
        self.bg_initial_power = None
        self.initial_brightness = None
        self.initial_color_temp = None
        self.bg_initial_brightness = None
        self.bg_initial_color_temp = None
        self.initial_r_value = None
        self.initial_g_value = None
        self.initial_b_value = None
        self.bg_initial_r_value = None
        self.bg_initial_g_value = None
        self.bg_initial_b_value = None
        self.bg_initial_color_mode = None

        self.prop = None
        self.ct_type = None
        self.hsv_type = None
        self.set_type = False

        # User settings
        self.monitor = None
        self.sat = None
        self.brightness = None
        self.pos = None
        self.name = None
        self.enable = True

        # Variables for updates
        self.start = False
        self.last_h = None
        self.last_s = None
        self.last_v = None
        
        # Connection management
        self.connection_error = False
        self.last_error_time = 0
        self.retry_count = 0
        self.max_retries = 3
        self.retry_backoff = 5  # seconds between retry attempts

    def set_name(self, name: str = '') -> None:
        self.name = name if name else self.ip

    def set_sat(self, sat: int = 100) -> None:
        self.sat = sat

    def set_brightness(self, brightness: int = 100) -> None:
        self.brightness = brightness

    def set_monitor(self, monitor: int = 0) -> None:
        self.monitor = monitor

    def get_monitor(self) -> int:
        return self.monitor

    def set_pos(self, pos: int = 0) -> None:
        self.pos = pos

    def set_prop(self, data: list) -> None:
        # data = [monitor, pos, brightness, sat, name, enable]
        try:
            self.set_monitor(data[0])
            self.set_pos(data[1])
            self.set_brightness(data[2])
            self.set_sat(data[3])
            self.set_name(data[4])
            self.enable = data[5]
        except IndexError:
            print(f"Error setting properties for {self.ip}: Invalid data format")

    def get_prop(self) -> list:
        # Return [ip, monitor, pos, brightness, sat, name, enable] to maintain consistency
        return [self.ip, self.monitor, self.pos, self.brightness, self.sat, self.name, self.enable]

    def get_type(self) -> None:
        try:
            if self.prop is None:
                self.prop = self.bulb.get_capabilities()
                time.sleep(self.wait_time)
            # Determine CT support
            self.ct_type = 0
            if ' set_ct_abx ' in self.prop['support']:
                self.ct_type = 1
            if ' bg_set_ct_abx ' in self.prop['support']:
                self.ct_type = 3 if self.ct_type == 1 else 2
            # Determine HSV support
            self.hsv_type = 0
            if ' set_hsv ' in self.prop['support']:
                self.hsv_type = 1
            if ' bg_set_hsv ' in self.prop['support']:
                self.hsv_type = 3 if self.hsv_type == 1 else 2
            self.set_type = True
            self.connection_error = False
            self.retry_count = 0
        except Exception as e:
            print(f"Error getting light type for {self.ip}: {str(e)}")
            self.connection_error = True
            self.last_error_time = time.time()
            self.retry_count += 1

    def should_retry(self) -> bool:
        if not self.connection_error:
            return True
        
        # If max retries exceeded, don't retry
        if self.retry_count > self.max_retries:
            return False
            
        # Calculate if enough time has passed for backoff
        current_time = time.time()
        backoff_time = self.retry_backoff * (2 ** (self.retry_count - 1))  # Exponential backoff
        return (current_time - self.last_error_time) > backoff_time

    def initial_state(self) -> bool:
        """Initialize light state, returns True if successful, False otherwise"""
        if self.connection_error and not self.should_retry():
            return False
            
        try:
            self.start = True
            self.prop = self.bulb.get_capabilities()
            time.sleep(self.wait_time)
            self.bulb.start_music()
            time.sleep(self.wait_time)
            if not self.set_type:
                self.get_type()
            # Save initial state for CT mode
            if self.ct_type in [1, 3]:
                self.initial_brightness = int(self.prop['bright'])
                self.initial_color_temp = int(self.prop['ct'])
            if self.ct_type in [2, 3]:
                self.bg_initial_brightness = int(self.prop['bg_bright'])
                self.bg_initial_color_temp = int(self.prop['bg_ct'])
            # Save initial state for HSV mode
            if self.hsv_type in [1, 3]:
                rgb_value = int(self.prop['rgb'])
                self.initial_r_value = int(rgb_value / 65536)
                rgb_value %= 65536
                self.initial_g_value = int(rgb_value / 256)
                self.initial_b_value = rgb_value % 256
            if self.hsv_type in [2, 3]:
                bg_rgb_value = int(self.prop['rgb'])
                self.bg_initial_r_value = int(bg_rgb_value / 65536)
                bg_rgb_value %= 65536
                self.bg_initial_g_value = int(bg_rgb_value / 256)
                self.bg_initial_b_value = bg_rgb_value % 256
            # Save power state
            if self.hsv_type in [1, 3] or self.ct_type in [1, 3]:
                self.initial_power = (self.prop['power'] == 'on')
            if self.hsv_type in [2, 3] or self.ct_type in [2, 3]:
                self.bg_initial_power = (self.prop['bg_power'] == 'on')
            # Turn on/off based on initial state
            if self.hsv_type in [1, 3]:
                if not self.initial_power:
                    self.bulb.turn_on()
            elif self.ct_type in [1, 3]:
                if self.initial_power:
                    self.bulb.turn_off()
            if self.hsv_type in [2, 3]:
                if not self.bg_initial_power:
                    self.bulb.turn_on(light_type=LightType.Ambient)
            elif self.ct_type in [2, 3]:
                if self.bg_initial_power:
                    self.bulb.turn_off(light_type=LightType.Ambient)
            # Set initial color mode
            if 'color_mode' in self.prop:
                if self.prop['color_mode'] == '2':
                    self.initial_color_mode = False
                elif self.prop['color_mode'] in ['1', '3']:
                    self.initial_color_mode = True
            if 'bg_lmode' in self.prop:
                if self.prop['bg_lmode'] == '2':
                    self.bg_initial_color_mode = False
                elif self.prop['bg_lmode'] in ['1', '3']:
                    self.bg_initial_color_mode = True
                    
            self.connection_error = False
            self.retry_count = 0
            return True
            
        except BulbException as e:
            print(f"Bulb connection error for {self.ip}: {str(e)}")
            self.connection_error = True
            self.last_error_time = time.time()
            self.retry_count += 1
            self.start = False
            return False
        except Exception as e:
            print(f"Error initializing state for {self.ip}: {str(e)}")
            self.connection_error = True
            self.last_error_time = time.time()
            self.retry_count += 1
            self.start = False
            return False

    def set_color(self, r: int, g: int, b: int) -> bool:
        """Set color, returns True if successful, False otherwise"""
        if self.connection_error and not self.should_retry():
            return False
            
        try:
            if self.hsv_type is None:
                self.get_type()
            if self.hsv_type in [1, 3]:
                self.bulb.set_rgb(r, g, b)
            if self.hsv_type in [2, 3]:
                self.bulb.set_rgb(r, g, b, light_type=LightType.Ambient)
            time.sleep(0.75)
            self.connection_error = False
            self.retry_count = 0
            return True
        except Exception as e:
            print(f"Error setting color for {self.ip}: {str(e)}")
            self.connection_error = True
            self.last_error_time = time.time()
            self.retry_count += 1
            return False

    def set_hsv(self, mon_hsv: list, rate: float, color_correction=False, red_gain=100, green_gain=100, blue_gain=100, gamma=100) -> bool:
        """Set HSV values, returns True if successful, False otherwise"""
        if self.connection_error and not self.should_retry():
            return False
            
        try:
            if not self.start:
                success = self.initial_state()
                if not success:
                    return False
                    
            h, s, v = mon_hsv[self.pos]
            s = int(s * self.sat / 100)
            v = int(v * self.brightness / 100)
            
            # Apply color correction if enabled
            if color_correction:
                # Convert HSV to RGB
                r, g, b = self._hsv_to_rgb(h, s/100, v/100)
                
                # Apply gain correction
                r = min(255, max(0, r * red_gain / 100))
                g = min(255, max(0, g * green_gain / 100))
                b = min(255, max(0, b * blue_gain / 100))
                
                # Apply gamma correction
                gamma_value = gamma / 100
                if gamma_value != 1.0:
                    r = int(255 * pow(r / 255, 1 / gamma_value))
                    g = int(255 * pow(g / 255, 1 / gamma_value))
                    b = int(255 * pow(b / 255, 1 / gamma_value))
                
                # Convert back to HSV
                h, s, v = self._rgb_to_hsv(r, g, b)
                s = int(s * 100)
                v = int(v * 100)
            
            if h == self.last_h and s == self.last_s and v == self.last_v:
                return True
                
            self.last_h = h
            self.last_s = s
            self.last_v = v
            
            if self.hsv_type in [1, 3]:
                self.bulb.set_hsv(h, s, v, effect="smooth", duration=int(rate * 1000))
            if self.hsv_type in [2, 3]:
                self.bulb.set_hsv(h, s, v, light_type=LightType.Ambient)
                
            self.connection_error = False
            self.retry_count = 0
            return True
            
        except BulbException as e:
            print(f"Bulb connection error for {self.ip}: {str(e)}")
            self.connection_error = True
            self.last_error_time = time.time()
            self.retry_count += 1
            self.start = False
            return False
        except Exception as e:
            print(f"Error setting HSV for {self.ip}: {str(e)}")
            self.connection_error = True
            self.last_error_time = time.time()
            self.retry_count += 1
            self.start = False
            return False
            
    def _hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB values (0-255)"""
        h = h / 360
        if s == 0.0:
            return int(v * 255), int(v * 255), int(v * 255)
            
        i = int(h * 6)
        f = (h * 6) - i
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))
        
        if i % 6 == 0:
            r, g, b = v, t, p
        elif i % 6 == 1:
            r, g, b = q, v, p
        elif i % 6 == 2:
            r, g, b = p, v, t
        elif i % 6 == 3:
            r, g, b = p, q, v
        elif i % 6 == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
            
        return int(r * 255), int(g * 255), int(b * 255)
        
    def _rgb_to_hsv(self, r, g, b):
        """Convert RGB (0-255) to HSV values"""
        r, g, b = r/255.0, g/255.0, b/255.0
        mx = max(r, g, b)
        mn = min(r, g, b)
        df = mx - mn
        
        if mx == mn:
            h = 0
        elif mx == r:
            h = (60 * ((g - b) / df) + 360) % 360
        elif mx == g:
            h = (60 * ((b - r) / df) + 120) % 360
        elif mx == b:
            h = (60 * ((r - g) / df) + 240) % 360
            
        s = 0 if mx == 0 else df / mx
        v = mx
        
        return h, s, v

    def identify(self) -> None:
        # Identify the bulb by cycling through colors
        try:
            if self.initial_state():
                self.bulb.set_brightness(100)
                time.sleep(0.25)
                self.set_color(255, 0, 0)
                self.set_color(0, 255, 0)
                self.set_color(0, 0, 255)
                self.revert_to_initial()
        except Exception as e:
            print(f"Error identifying light {self.ip}: {str(e)}")
            self.connection_error = True
            self.last_error_time = time.time()
            self.retry_count += 1
            self.start = False

    def revert_to_initial(self) -> None:
        # Restore the initial state
        if self.connection_error and not self.should_retry():
            return
            
        try:
            if self.initial_color_mode is True:
                self.bulb.set_brightness(self.initial_brightness)
                time.sleep(self.wait_time)
                self.bulb.set_rgb(self.initial_r_value, self.initial_g_value, self.initial_b_value)
                time.sleep(self.wait_time)
            elif self.initial_color_mode is False:
                self.bulb.set_brightness(self.initial_brightness)
                time.sleep(self.wait_time)
                self.bulb.set_color_temp(self.initial_color_temp)
                time.sleep(self.wait_time)
            if self.bg_initial_color_mode is True:
                self.bulb.set_brightness(self.bg_initial_brightness, light_type=LightType.Ambient)
                time.sleep(self.wait_time)
                self.bulb.set_rgb(self.bg_initial_r_value, self.bg_initial_g_value, self.bg_initial_b_value,
                                light_type=LightType.Ambient)
                time.sleep(self.wait_time)
            elif self.bg_initial_color_mode is False:
                self.bulb.set_brightness(self.bg_initial_brightness, light_type=LightType.Ambient)
                time.sleep(self.wait_time)
                self.bulb.set_color_temp(self.bg_initial_color_temp, light_type=LightType.Ambient)
                time.sleep(self.wait_time)
            if not self.initial_power:
                self.bulb.turn_off()
                time.sleep(self.wait_time)
            if not self.bg_initial_power:
                self.bulb.turn_off(light_type=LightType.Ambient)
                time.sleep(self.wait_time)
            try:
                self.bulb.stop_music()
            except Exception:
                pass
            self.start = False
            self.connection_error = False
            self.retry_count = 0
        except Exception as e:
            print(f"Error reverting light {self.ip} to initial state: {str(e)}")
            self.connection_error = True
            self.last_error_time = time.time()
            self.retry_count += 1
            self.start = False

    def light_online(self) -> int:
        try:
            if self.connection_error and not self.should_retry():
                return 0
                
            if self.bulb.get_capabilities() is None:
                return 0
                
            self.connection_error = False
            self.retry_count = 0
            return 1
        except Exception:
            self.connection_error = True
            self.last_error_time = time.time()
            self.retry_count += 1
            return 0

def light_online(ip: str) -> int:
    try:
        if Bulb(ip).get_capabilities() is None:
            return 0
        return 1
    except Exception:
        return 0

