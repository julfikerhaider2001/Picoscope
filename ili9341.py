"""ILI9341 display driver for MicroPython"""
from time import sleep
from micropython import const

def color565(r, g, b):
    return (r & 0xf8) << 8 | (g & 0xfc) << 3 | b >> 3

class Display:
    # ILI9341 commands
    SWRESET = const(0x01)
    SLPIN = const(0x10)
    SLPOUT = const(0x11)
    INVOFF = const(0x20)
    INVON = const(0x21)
    DISPLAY_OFF = const(0x28)
    DISPLAY_ON = const(0x29)
    SET_COLUMN = const(0x2A)
    SET_PAGE = const(0x2B)
    WRITE_RAM = const(0x2C)
    MADCTL = const(0x36)
    PIXFMT = const(0x3A)
    FRMCTR1 = const(0xB1)
    DFUNCTR = const(0xB6)
    PWCTR1 = const(0xC0)
    PWCTR2 = const(0xC1)
    PWCTRA = const(0xCB)
    PWCTRB = const(0xCF)
    VMCTR1 = const(0xC5)
    VMCTR2 = const(0xC7)
    GMCTRP1 = const(0xE0)
    GMCTRN1 = const(0xE1)
    DTCA = const(0xE8)
    DTCB = const(0xEA)
    POSC = const(0xED)
    ENABLE3G = const(0xF2)
    PUMPRC = const(0xF7)
    GAMMASET = const(0x26)

    def __init__(self, spi, cs, dc, rst, width=240, height=320, rotation=0):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.width = width
        self.height = height
        
        rotations = {0: 0x48, 90: 0x28, 180: 0x88, 270: 0xE8}
        self.rotation = rotations.get(rotation, 0x48)
        
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=1)
        
        # Reset
        self.rst(0)
        sleep(0.05)
        self.rst(1)
        sleep(0.05)
        
        self.write_cmd(self.SWRESET)
        sleep(0.1)
        
        # Initialize
        self.write_cmd(self.PWCTRB, 0x00, 0xC1, 0x30)
        self.write_cmd(self.POSC, 0x64, 0x03, 0x12, 0x81)
        self.write_cmd(self.DTCA, 0x85, 0x00, 0x78)
        self.write_cmd(self.PWCTRA, 0x39, 0x2C, 0x00, 0x34, 0x02)
        self.write_cmd(self.PUMPRC, 0x20)
        self.write_cmd(self.DTCB, 0x00, 0x00)
        self.write_cmd(self.PWCTR1, 0x23)
        self.write_cmd(self.PWCTR2, 0x10)
        self.write_cmd(self.VMCTR1, 0x3E, 0x28)
        self.write_cmd(self.VMCTR2, 0x86)
        self.write_cmd(self.MADCTL, self.rotation)
        self.write_cmd(self.PIXFMT, 0x55)
        self.write_cmd(self.FRMCTR1, 0x00, 0x18)
        self.write_cmd(self.DFUNCTR, 0x08, 0x82, 0x27)
        self.write_cmd(self.ENABLE3G, 0x00)
        self.write_cmd(self.GAMMASET, 0x01)
        self.write_cmd(self.GMCTRP1, 0x0F, 0x31, 0x2B, 0x0C, 0x0E, 0x08,
                       0x4E, 0xF1, 0x37, 0x07, 0x10, 0x03, 0x0E, 0x09, 0x00)
        self.write_cmd(self.GMCTRN1, 0x00, 0x0E, 0x14, 0x03, 0x11, 0x07,
                       0x31, 0xC1, 0x48, 0x08, 0x0F, 0x0C, 0x31, 0x36, 0x0F)
        self.write_cmd(self.SLPOUT)
        sleep(0.1)
        self.write_cmd(self.DISPLAY_ON)
        sleep(0.1)
        self.clear()

    def write_cmd(self, cmd, *args):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)
        if args:
            self.write_data(bytearray(args))

    def write_data(self, data):
        self.dc(1)
        self.cs(0)
        self.spi.write(data)
        self.cs(1)

    def block(self, x0, y0, x1, y1, data):
        self.write_cmd(self.SET_COLUMN, x0 >> 8, x0 & 0xff, x1 >> 8, x1 & 0xff)
        self.write_cmd(self.SET_PAGE, y0 >> 8, y0 & 0xff, y1 >> 8, y1 & 0xff)
        self.write_cmd(self.WRITE_RAM)
        self.write_data(data)

    def clear(self, color=0):
        w = self.width
        h = self.height
        line = color.to_bytes(2, 'big') * w * 8
        for y in range(0, h, 8):
            self.block(0, y, w - 1, min(y + 7, h - 1), line)

    def fill_rectangle(self, x, y, w, h, color):
        if x < 0 or y < 0 or x + w > self.width or y + h > self.height:
            return
        line = color.to_bytes(2, 'big') * w
        for row in range(y, y + h):
            self.block(x, row, x + w - 1, row, line)

    def draw_pixel(self, x, y, color):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        self.block(x, y, x, y, color.to_bytes(2, 'big'))

    def draw_hline(self, x, y, w, color):
        self.fill_rectangle(x, y, w, 1, color)

    def draw_vline(self, x, y, h, color):
        self.fill_rectangle(x, y, 1, h, color)

    def draw_line(self, x1, y1, x2, y2, color):
        if y1 == y2:
            self.draw_hline(min(x1, x2), y1, abs(x2 - x1) + 1, color)
            return
        if x1 == x2:
            self.draw_vline(x1, min(y1, y2), abs(y2 - y1) + 1, color)
            return
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while True:
            self.draw_pixel(x1, y1, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def draw_rectangle(self, x, y, w, h, color):
        self.draw_hline(x, y, w, color)
        self.draw_hline(x, y + h - 1, w, color)
        self.draw_vline(x, y, h, color)
        self.draw_vline(x + w - 1, y, h, color)

    def draw_text8x8(self, x, y, text, color, background=0):
        from framebuf import FrameBuffer, RGB565
        w = len(text) * 8
        h = 8
        buf = bytearray(w * h * 2)
        fbuf = FrameBuffer(buf, w, h, RGB565)
        
        if background != 0:
            fb = ((background >> 8) & 0xFF) | ((background & 0xFF) << 8)
            fbuf.fill(fb)
        
        fc = ((color >> 8) & 0xFF) | ((color & 0xFF) << 8)
        fbuf.text(text, 0, 0, fc)
        self.block(x, y, x + w - 1, y + h - 1, buf)

    def fill_circle(self, x0, y0, r, color):
        self.draw_vline(x0, y0 - r, 2 * r + 1, color)
        f = 1 - r
        ddF_x = 1
        ddF_y = -2 * r
        x = 0
        y = r
        
        while x < y:
            if f >= 0:
                y -= 1
                ddF_y += 2
                f += ddF_y
            x += 1
            ddF_x += 2
            f += ddF_x
            self.draw_vline(x0 + x, y0 - y, 2 * y + 1, color)
            self.draw_vline(x0 - x, y0 - y, 2 * y + 1, color)
            self.draw_vline(x0 + y, y0 - x, 2 * x + 1, color)
            self.draw_vline(x0 - y, y0 - x, 2 * x + 1, color)