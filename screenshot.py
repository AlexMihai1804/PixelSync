import platform

import cv2
import mss
import numpy as np

if platform.system() == 'Windows':
    import dxcam


class Monitor:
    def __init__(self, monitor_index: int, bar_correction: bool, bar_update: float) -> None:
        self.mon_n = monitor_index
        self.bar_correction = bar_correction
        self.bar_update = bar_update
        self.k = 0
        self.bbox = (0, 0, 119, 119)
        if platform.system() == 'Windows':
            self.platform = 0
            self.camera = dxcam.create(output_idx=self.mon_n - 1)
            self.mon = None
        else:
            self.platform = 1
            self.mon = mss.mss().monitors[self.mon_n]
            self.camera = None

    def get_mon_hsv(self) -> list:
        # Capture and process screenshot to get HSV values for 13 regions
        scr = self.resize_scr()
        hsv_values = [self.determine_hsv(scr, pos) for pos in range(13)]
        return hsv_values

    def take_scr(self):
        if self.platform == 0:
            img = self.camera.grab()
            while img is None:
                img = self.camera.grab()
        else:
            img = mss.mss().grab(self.mon)
        return img

    def resize_scr(self):
        scr = np.array(self.take_scr())
        scr = cv2.resize(scr, (120, 120), interpolation=cv2.INTER_AREA)
        scr = scr[:, :, :3]
        if self.bar_correction:
            bbox2 = self.trim(scr)
            if self.bbox == bbox2:
                self.k += 1
                if self.k > 4:
                    if bbox2 != (0, 0, 119, 119):
                        left, upper, right, lower = bbox2
                        scr = scr[upper:lower, left:right]
                        scr = cv2.resize(scr, (3, 3), interpolation=cv2.INTER_AREA)
                    else:
                        scr = cv2.resize(scr, (3, 3), interpolation=cv2.INTER_AREA)
                else:
                    scr = cv2.resize(scr, (3, 3), interpolation=cv2.INTER_AREA)
            else:
                self.bbox = bbox2
                self.k = 1
                scr = cv2.resize(scr, (3, 3), interpolation=cv2.INTER_AREA)
        else:
            scr = cv2.resize(scr, (3, 3), interpolation=cv2.INTER_AREA)
        return scr

    def trim(self, im: np.ndarray) -> tuple:
        # Determine the bounding box of nonzero pixels for black bar correction
        y_nonzero, x_nonzero, _ = np.nonzero(im)
        left, upper, right, lower = int(np.min(x_nonzero)), int(np.min(y_nonzero)), int(np.max(x_nonzero)), int(
            np.max(y_nonzero))
        x = min(left, 119 - right, 40)
        y = min(upper, 119 - lower, 20)
        return (x, y, 119 - x, 119 - y)

    def determine_hsv(self, scr, position: int) -> tuple:
        # Calculate HSV values for the specified region
        r = g = b = 0
        if position == 0:
            for x in range(3):
                for y in range(3):
                    k, i, j = scr[x][y]
                    r += k
                    g += i
                    b += j
            r //= 9;
            g //= 9;
            b //= 9
        elif position == 1:
            for x in range(3):
                k, i, j = scr[0][x]
                r += k;
                g += i;
                b += j
            r //= 3;
            g //= 3;
            b //= 3
        elif position == 2:
            for x in range(3):
                k, i, j = scr[x][0]
                r += k;
                g += i;
                b += j
            r //= 3;
            g //= 3;
            b //= 3
        elif position == 3:
            for x in range(3):
                k, i, j = scr[2][x]
                r += k;
                g += i;
                b += j
            r //= 3;
            g //= 3;
            b //= 3
        elif position == 4:
            for x in range(3):
                k, i, j = scr[x][2]
                r += k;
                g += i;
                b += j
            r //= 3;
            g //= 3;
            b //= 3
        elif position == 5:
            r, g, b = scr[0][1]
        elif position == 6:
            r, g, b = scr[1][0]
        elif position == 7:
            r, g, b = scr[2][1]
        elif position == 8:
            r, g, b = scr[1][2]
        elif position == 9:
            r, g, b = scr[0][0]
        elif position == 10:
            r, g, b = scr[2][0]
        elif position == 11:
            r, g, b = scr[2][2]
        elif position == 12:
            r, g, b = scr[0][2]
        if self.platform == 1:
            r, g, b = b, g, r
        r, g, b = r / 255.0, g / 255.0, b / 255.0
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
        s = 0 if mx == 0 else (df / mx) * 100
        v = mx * 100
        return h, s, v


def mon_number() -> int:
    return len(mss.mss().monitors)
