import time

from yeelight import Bulb, LightType


class Light:
    def __init__(self, ip):
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
        self.bulb = Bulb(ip)
        self.ip = ip
        self.wait_time = 0.25
        self.type = None
        self.prop = None
        self.ct_type = None
        self.hsv_type = None
        self.set_type = False
        self.monitor = None
        self.sat = None
        self.brightness = None
        self.pos = None
        self.name = None
        self.start = False
        self.last_h = None
        self.last_s = None
        self.last_v = None
        self.enable = True

    def set_name(self, name=''):
        if name == '':
            self.name = self.ip
        else:
            self.name = name

    def set_sat(self, sat=100):
        self.sat = sat

    def set_brightness(self, brightness=100):
        self.brightness = brightness

    def set_monitor(self, monitor=0):
        self.monitor = monitor

    def set_pos(self, pos=0):
        self.pos = pos

    def set_prop(self, data):
        self.set_pos(data[1])
        self.set_monitor(data[0])
        self.set_brightness(data[2])
        self.set_sat(data[3])
        self.set_name(data[4])
        self.enable = data[5]

    def get_name(self):
        return self.name

    def get_sat(self):
        return self.sat

    def get_brightness(self):
        return self.brightness

    def get_monitor(self):
        return self.monitor

    def get_pos(self):
        return self.pos

    def get_ip(self):
        return self.ip

    def get_prop(self):
        return [self.get_ip(), self.get_monitor(), self.get_pos(), self.get_name(), self.get_brightness(),
                self.get_sat(), self.enable]

    def get_type(self):
        if self.prop is None:
            self.prop = self.bulb.get_capabilities()
            time.sleep(self.wait_time)
        self.ct_type = 0
        if ' set_ct_abx ' in self.prop['support']:
            self.ct_type = 1
        if ' bg_set_ct_abx ' in self.prop['support']:
            if self.ct_type == 1:
                self.ct_type = 3
            else:
                self.ct_type = 2
        self.hsv_type = 0
        if ' set_hsv ' in self.prop['support']:
            self.hsv_type = 1
        if ' bg_set_hsv ' in self.prop['support']:
            if self.hsv_type == 1:
                self.hsv_type = 3
            else:
                self.hsv_type = 2
        self.set_type = True

    def initial_state(self):
        self.start = True
        self.prop = self.bulb.get_capabilities()
        time.sleep(self.wait_time)
        self.bulb.start_music()
        time.sleep(self.wait_time)
        if not self.set_type:
            self.get_type()
        if self.ct_type == 1 or self.ct_type == 3:
            self.initial_brightness = int(self.prop['bright'])
            self.initial_color_temp = int(self.prop['ct'])
        if self.ct_type == 2 or self.ct_type == 3:
            self.bg_initial_brightness = int(self.prop['bg_bright'])
            self.bg_initial_color_temp = int(self.prop['bg_ct'])
        if self.hsv_type == 1 or self.hsv_type == 3:
            self.initial_b_value = int(self.prop['rgb'])
            self.initial_r_value = int(self.initial_b_value / 65536)
            self.initial_b_value %= 65536
            self.initial_g_value = int(self.initial_b_value / 256)
            self.initial_b_value %= 256
        if self.hsv_type == 2 or self.hsv_type == 3:
            self.bg_initial_b_value = int(self.prop['rgb'])
            self.bg_initial_r_value = int(self.bg_initial_b_value / 65536)
            self.bg_initial_b_value %= 65536
            self.bg_initial_g_value = int(self.bg_initial_b_value / 256)
            self.bg_initial_b_value %= 256
        if self.hsv_type == 1 or self.hsv_type == 3 or self.ct_type == 1 or self.ct_type == 3:
            if self.prop['power'] == 'on':
                self.initial_power = True
            else:
                self.initial_power = False
        if self.hsv_type == 2 or self.hsv_type == 3 or self.ct_type == 2 or self.ct_type == 3:
            if self.prop['bg_power'] == 'on':
                self.bg_initial_power = True
            else:
                self.bg_initial_power = False
        if self.hsv_type == 1 or self.hsv_type == 3:
            if not self.initial_power:
                self.bulb.turn_on()
        elif self.ct_type == 1 or self.ct_type == 3:
            if self.initial_power:
                self.bulb.turn_off()
        if self.hsv_type == 2 or self.hsv_type == 3:
            if not self.bg_initial_power:
                self.bulb.turn_on(light_type=LightType.Ambient)
        elif self.ct_type == 2 or self.ct_type == 3:
            if self.bg_initial_power:
                self.bulb.turn_off(light_type=LightType.Ambient)
        if 'color_mode' in self.prop:
            if self.prop['color_mode'] == '2':
                self.initial_color_mode = False
            elif self.prop['color_mode'] == '1' or self.prop['color_mode'] == '3':
                self.initial_color_mode = True
        if 'bg_lmode' in self.prop:
            if self.prop['bg_lmode'] == '2':
                self.bg_initial_color_mode = False
            elif self.prop['bg_lmode'] == '1' or self.prop['bg_lmode'] == '3':
                self.bg_initial_color_mode = True

    def set_color(self, r, g, b):
        if self.hsv_type is None:
            self.get_type()
        if self.hsv_type == 1 or self.hsv_type == 3:
            self.bulb.set_rgb(r, g, b)
        if self.hsv_type == 2 or self.hsv_type == 3:
            self.bulb.set_rgb(r, g, b, light_type=LightType.Ambient)
        time.sleep(.75)

    def set_hsv(self, mon_hsv, rate):
        if not self.start:
            self.initial_state()
        h, s, v = mon_hsv[self.pos]
        s = int(s * self.sat / 100)
        v = int(v * self.brightness / 100)
        if h == self.last_h and s == self.last_h and v == self.last_v:
            return
        self.last_h = h
        self.last_s = s
        self.last_v = v
        if self.hsv_type == 1 or self.hsv_type == 3:
            self.bulb.set_hsv(h, s, v, effect="smooth", duration=int(rate * 1000))
        if self.hsv_type == 2 or self.hsv_type == 3:
            self.bulb.set_hsv(h, s, v, light_type=LightType.Ambient)

    def identify(self):
        self.initial_state()
        self.bulb.set_brightness(100)
        time.sleep(0.25)
        self.set_color(255, 0, 0)
        self.set_color(0, 255, 0)
        self.set_color(0, 0, 255)
        self.revert_to_initial()

    def revert_to_initial(self):
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
            print(self.bg_initial_color_mode)
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
        except:
            pass
        self.start = False

    def light_online(self):
        try:
            if self.bulb.get_capabilities() is None:
                return 0
            return 1
        except:
            return 0


def light_online(ip):
    try:
        if Bulb(ip).get_capabilities() is None:
            return 0
        return 1
    except:
        return 0