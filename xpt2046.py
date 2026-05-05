# xpt2046.py
from machine import SPI, Pin
import utime

class Touch:
    def __init__(self, spi, cs, irq=None):
        self.spi = spi
        self.cs = cs
        self.irq = irq
        self.cs(1)

    def _read_raw(self, cmd):
        buf = bytearray(2)
        self.cs(0)
        utime.sleep_us(10)
        self.spi.write(bytearray([cmd]))
        self.spi.readinto(buf)
        self.cs(1)
        utime.sleep_us(10)
        return ((buf[0] << 8) | buf[1]) >> 3

    def get_raw(self):
        xs, ys = [], []
        for _ in range(5):
            x = self._read_raw(0xD0)
            y = self._read_raw(0x90)
            if x > 100 and y > 100:
                xs.append(x)
                ys.append(y)
            utime.sleep_us(200)
        if not xs:
            return None
        return (sum(xs) // len(xs), sum(ys) // len(ys))

    def get_touch(self):
        # Calibration values from your hardware
        X_MIN = 443
        X_MAX = 3567
        Y_MIN = 535
        Y_MAX = 3712
        X_RES = 320
        Y_RES = 240

        if self.irq and self.irq.value() == 1:
            return None  # not touched

        raw = self.get_raw()
        if raw is None:
            return None

        raw_x, raw_y = raw

        # Both axes inverted — use (MAX - raw) instead of (raw - MIN)
        x = int((X_MAX - raw_x) * X_RES / (X_MAX - X_MIN))
        y = int((Y_MAX - raw_y) * Y_RES / (Y_MAX - Y_MIN))

        x = max(0, min(X_RES - 1, x))
        y = max(0, min(Y_RES - 1, y))

        return (x, y)