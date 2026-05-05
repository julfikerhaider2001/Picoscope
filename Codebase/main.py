# ============================================================
#  Pocket Oscilloscope Pro v4.0 — Raspberry Pi Pico 2
#  MicroPython | ILI9341 2.8" TFT | XPT2046 Touch
# ============================================================

import _thread
import gc
import math
import utime
from machine import ADC, Pin, PWM, SPI

from ili9341 import Display, color565
from xpt2046 import Touch

# ─────────────────────────────────────────────
#  PIN DEFINITIONS
# ─────────────────────────────────────────────
TFT_CS, TFT_DC, TFT_RST = 17, 19, 20
TFT_SCK, TFT_MOSI        = 6,  7

TOUCH_IRQ  = 13
TOUCH_CS   = 9
TOUCH_SCK  = 10
TOUCH_MOSI = 11
TOUCH_MISO = 12

PROBE_PIN    = 26          # ADC0
BATT_ADC_PIN = 29          # ADC3 -> VSYS/3 (built-in Pico divider)
BTN_HOLD     = Pin(3, Pin.IN, Pin.PULL_UP)

# ─────────────────────────────────────────────
#  DISPLAY & TOUCH INIT
# ─────────────────────────────────────────────
# Set baudrate to 62.5MHz (Pico 2 handles high SPI speeds well)
spi_disp = SPI(0, baudrate=62_500_000, sck=Pin(TFT_SCK), mosi=Pin(TFT_MOSI))
display  = Display(spi_disp, dc=Pin(TFT_DC), cs=Pin(TFT_CS),
                    rst=Pin(TFT_RST), width=320, height=240, rotation=90)

spi_touch = SPI(1, baudrate=1_000_000, sck=Pin(TOUCH_SCK),
                mosi=Pin(TOUCH_MOSI), miso=Pin(TOUCH_MISO))
touch = Touch(spi_touch, cs=Pin(TOUCH_CS, Pin.OUT),
              irq=Pin(TOUCH_IRQ, Pin.IN))

# ─────────────────────────────────────────────
#  COLOR PALETTE (DSO 510 Style)
# ─────────────────────────────────────────────
C_BLACK, C_WHITE, C_RED = color565(0,0,0), color565(255,255,255), color565(255,40,40)
C_BG        = color565(4, 4, 10)      # Deep Navy
C_GRID      = color565(25, 40, 25)    # Dim Green
C_GRID_CTR  = color565(45, 65, 45)    # Center axis
C_WAVE      = color565(0, 255, 100)   # Sharp Green
C_CYAN, C_YELLOW, C_ORANGE = color565(0,220,255), color565(255,210,0), color565(255,130,0)
C_GRAY, C_DARK_GRAY = color565(80,80,80), color565(18,18,25)
C_BTN_BG, C_BTN_ACT = color565(22,22,40), color565(0,70,180)
C_BAR_BG, C_TRIG_COL = color565(8,8,18), color565(255,180,0)
C_CURSOR, C_MEAS_BG = color565(200,200,255), color565(6,6,16)

def batt_color(pct):
    if pct > 60: return color565(30, 200, 80)
    if pct > 25: return C_YELLOW
    return C_RED

# ─────────────────────────────────────────────
#  LAYOUT CONSTANTS
# ─────────────────────────────────────────────
TOP_H, BOT_Y = 26, 200
WAVE_X0, WAVE_Y0 = 0, TOP_H
WAVE_X1, WAVE_Y1 = 319, BOT_Y - 1
WAVE_W, WAVE_H = 320, (BOT_Y - 1) - TOP_H + 1
CENTRE_Y = WAVE_Y0 + WAVE_H // 2

BOT_BTNS = [(0,64,"V/Div"), (64,128,"T/Div"), (128,192,"Trig"), (192,256,"Cursor"), (256,320,"Meas")]

# ─────────────────────────────────────────────
#  SCALE TABLES
# ─────────────────────────────────────────────
V_RANGE_LABEL = ["50V","20V","10V"," 5V"," 2V"," 1V","0.5V","0.2V","0.1V","50mV"]
V_RANGE_VPD   = [50.0, 20.0, 10.0, 5.0, 2.0, 1.0, 0.5, 0.2, 0.1, 0.05]
H_RANGE_LABEL = ["50ms","20ms","10ms"," 5ms"," 2ms"," 1ms","500u","200u","100u"," 50u"]
H_RANGE_US    = [5000, 2000, 1000, 500, 200, 100, 50, 20, 10, 5]

# ─────────────────────────────────────────────
#  OSCILLOSCOPE STATE
# ─────────────────────────────────────────────
vRange, hRange, trigMode, trigDir, trigLevel = 5, 5, 0, 0, 2048
holdFlag, singleDone, activeMenu = False, False, -1
cursorMode, curX1, curX2, curY1, curY2 = 0, 80, 240, WAVE_Y0+40, WAVE_Y0+130
dragging, measVisible = -1, False
_last_touch_ms, _last_btn_ms = 0, 0

# ─────────────────────────────────────────────
#  DUAL-CORE RING BUFFER
# ─────────────────────────────────────────────
# Pico 2 has plenty of RAM; we use a 512-sample ring buffer for stability
RING_SIZE = 512
RING_MASK = RING_SIZE - 1
ring_buf = bytearray(RING_SIZE * 2) # Store as 16-bit
ring_write, ring_read = 0, 0
buf_lock = _thread.allocate_lock()

# Local buffer for Core 0 processing
waveBuff = [0] * 320
prevY = [CENTRE_Y] * 320

# ─────────────────────────────────────────────
#  BATTERY MONITORING
# ─────────────────────────────────────────────
_last_batt_pct, _batt_check_ms = 100, 0
BATT_INTERVAL = 10_000 # Check every 10s

def read_battery_pct():
    adc_batt = ADC(BATT_ADC_PIN)
    raw = adc_batt.read_u16()
    # VSYS/3 divider is used on Pico. Multiply by 3 and 3.3V ref.
    vsys = raw * (3.3 / 65535.0) * 3.0
    # Li-Ion range: 3.0V (0%) to 4.2V (100%)
    pct = int((vsys - 3.0) / (4.2 - 3.0) * 100)
    return max(0, min(100, pct))

# ─────────────────────────────────────────────
#  CORE 1 — CONTINUOUS ADC SAMPLER
# ─────────────────────────────────────────────
def _sampler_core1():
    global ring_write
    _adc = ADC(Pin(PROBE_PIN))
    while True:
        delay = H_RANGE_US[hRange]
        
        # Capture 320 points at the current timebase
        wr = ring_write
        for _ in range(320):
            sample = _adc.read_u16() >> 4 # 12-bit
            # Write to ring buffer
            idx = (wr & RING_MASK) << 1
            ring_buf[idx] = sample >> 8
            ring_buf[idx+1] = sample & 0xFF
            wr = (wr + 1) & 0x3FFFFFFF # Large wrap
            
            if delay >= 10: utime.sleep_us(delay)
            
        buf_lock.acquire()
        ring_write = wr
        buf_lock.release()

# ─────────────────────────────────────────────
#  TRIGGER & CONSUMPTION
# ─────────────────────────────────────────────
def consume_ring():
    global ring_read
    buf_lock.acquire()
    wr = ring_write
    buf_lock.release()

    rr = ring_read
    available = (wr - rr) & 0x3FFFFFFF
    if available < 320: return False

    # Pull latest window
    tmp = [0] * min(available, RING_SIZE)
    for i in range(len(tmp)):
        idx = ((rr + i) & RING_MASK) << 1
        tmp[i] = (ring_buf[idx] << 8) | ring_buf[idx+1]

    # Simple Trigger Search
    start = 0
    if trigMode != 0: # Normal or Single
        prev = tmp[0]
        for i in range(1, len(tmp) - 320):
            cur = tmp[i]
            if (trigDir == 0 and prev < trigLevel <= cur) or \
               (trigDir == 1 and prev > trigLevel >= cur):
                start = i
                break
            prev = cur

    # Transfer to waveBuff
    for i in range(320):
        waveBuff[i] = tmp[start + i] if (start+i) < len(tmp) else tmp[-1]

    ring_read = (rr + start + 320) & 0x3FFFFFFF
    return True

# ─────────────────────────────────────────────
#  MEASUREMENTS (DSO 510)
# ─────────────────────────────────────────────
def compute_measurements():
    vpd = V_RANGE_VPD[vRange]
    scale = (vpd * 8.0) / 4096.0 # 8 Vertical Divisions
    mn, mx = min(waveBuff), max(waveBuff)
    vpp, vmin, vmax = (mx-mn)*scale, mn*scale, mx*scale
    vavg = sum(waveBuff) * scale / 320
    
    # Frequency estimation (crossing based)
    lvl, crossings = (mn + mx) // 2, []
    prev = waveBuff[0]
    for i in range(1, 320):
        cur = waveBuff[i]
        if (trigDir == 0 and prev < lvl <= cur) or (trigDir == 1 and prev > lvl >= cur):
            crossings.append(i)
        prev = cur
    
    freq, period = 0.0, 0.0
    if len(crossings) >= 2:
        # Time per pixel = H_RANGE_US[hRange] / (WAVE_W / 8 divs)
        period = (crossings[-1] - crossings[0]) / (len(crossings)-1) * H_RANGE_US[hRange]
        freq = 1_000_000.0 / period if period > 0 else 0
        
    return {"Vpp": vpp, "Vmin": vmin, "Vmax": vmax, "Vavg": vavg, "freq": freq, "period": period, "duty": 50.0}

# ─────────────────────────────────────────────
#  DRAWING FUNCTIONS
# ─────────────────────────────────────────────
def _wave_y(val):
    y = int(WAVE_Y0 + WAVE_H - (val * WAVE_H / 4095))
    return max(WAVE_Y0 + 1, min(WAVE_Y1 - 1, y))

def _grid_color_at(x, y):
    if y == CENTRE_Y or x == 160: return C_GRID_CTR
    if x % 40 == 0 or (y - WAVE_Y0) % (WAVE_H // 4) == 0: return C_GRID
    return C_BG

def draw_grid():
    display.fill_rectangle(WAVE_X0, WAVE_Y0, WAVE_W, WAVE_H, C_BG)
    for x in range(0, 320, 40):
        display.draw_line(x, WAVE_Y0, x, WAVE_Y1, C_GRID)
    for y in range(WAVE_Y0, WAVE_Y1, WAVE_H // 4):
        display.draw_line(0, y, 319, y, C_GRID)
    display.draw_line(0, CENTRE_Y, 319, CENTRE_Y, C_GRID_CTR)
    display.draw_line(160, WAVE_Y0, 160, WAVE_Y1, C_GRID_CTR)

def draw_top_bar():
    display.fill_rectangle(0, 0, 320, TOP_H - 1, C_BAR_BG)
    # V/Div & T/Div info
    display.draw_text8x8(3, 9, "CH1: " + V_RANGE_LABEL[vRange], C_CYAN)
    display.draw_text8x8(100, 9, H_RANGE_LABEL[hRange] + "/d", C_YELLOW)
    
    # Trigger Status
    t_mode = ["Auto", "Norm", "Sngl"][trigMode]
    display.draw_text8x8(185, 9, t_mode + (" R" if trigDir == 0 else " F"), C_WHITE)
    
    # Run/Hold Status
    rect_col = C_ORANGE if singleDone else (C_RED if holdFlag else color565(0,90,20))
    display.fill_rectangle(249, 1, 44, TOP_H - 3, rect_col)
    display.draw_text8x8(252, 9, "DONE" if singleDone else ("HOLD" if holdFlag else " RUN"), C_WHITE)
    
    # Battery
    bc = batt_color(_last_batt_pct)
    display.draw_text8x8(296, 9, "{:3d}%".format(_last_batt_pct), bc)
    display.draw_line(0, TOP_H - 1, 319, TOP_H - 1, C_GRAY)

def draw_bottom_bar():
    display.fill_rectangle(0, BOT_Y, 320, 40, C_DARK_GRAY)
    for i, (x1, x2, label) in enumerate(BOT_BTNS):
        bg = C_BTN_ACT if i == activeMenu else C_BTN_BG
        display.fill_rectangle(x1 + 1, BOT_Y + 2, (x2 - x1) - 2, 36, bg)
        display.draw_text8x8(x1 + 10, BOT_Y + 16, label, C_WHITE)

def draw_measurements_panel():
    if not measVisible: return
    m = compute_measurements()
    display.fill_rectangle(170, WAVE_Y0 + 5, 145, 140, C_MEAS_BG)
    display.draw_rectangle(170, WAVE_Y0 + 5, 145, 140, C_GRAY)
    
    lines = [
        ("Vpp", "{:.2f}V".format(m["Vpp"])),
        ("Vmax", "{:.2f}V".format(m["Vmax"])),
        ("Freq", "{:.1f}Hz".format(m["freq"]) if m["freq"] < 1000 else "{:.1f}kHz".format(m["freq"]/1000)),
        ("Per", "{:.1f}ms".format(m["period"]/1000))
    ]
    for i, (l, v) in enumerate(lines):
        display.draw_text8x8(175, WAVE_Y0 + 15 + i*20, l + ":" + v, C_YELLOW)

def draw_full_screen():
    draw_grid()
    draw_top_bar()
    draw_bottom_bar()

# ─────────────────────────────────────────────
#  INPUT HANDLING
# ─────────────────────────────────────────────
def remap_touch(raw_x, raw_y):
    # Mapping based on your last working calibration
    mx = int((215 - raw_y) * 320 / 175)
    my = int((270 - raw_x) * 240 / 230)
    return max(0, min(319, mx)), max(0, min(239, my))

def check_touch():
    global activeMenu, holdFlag, vRange, hRange, trigLevel, trigDir, trigMode, singleDone, cursorMode, measVisible, _last_touch_ms
    pt = touch.get_touch()
    if pt is None: return
    
    now = utime.ticks_ms()
    if utime.ticks_diff(now, _last_touch_ms) < 200: return
    _last_touch_ms = now
    
    x, y = remap_touch(pt[0], pt[1])
    
    if y < TOP_H:
        if x > 240: # RUN/HOLD Toggle
            holdFlag = not holdFlag
            singleDone = False
            draw_top_bar()
    elif y >= BOT_Y: # Menu Selection
        for i, (x1, x2, _) in enumerate(BOT_BTNS):
            if x1 <= x < x2:
                activeMenu = -1 if activeMenu == i else i
                if i == 3: cursorMode = (cursorMode + 1) % 3
                if i == 4: # Measure Toggle
                    measVisible = not measVisible
                    draw_grid() # Refresh background
                draw_bottom_bar()
    else: # Interaction with Waveform Area
        if activeMenu == 0: # V/Div
            vRange = max(0, min(9, vRange + (1 if y > CENTRE_Y else -1)))
        elif activeMenu == 1: # T/Div
            hRange = max(0, min(9, hRange + (1 if x > 160 else -1)))
        elif activeMenu == 2: # Trigger settings
            if x < 160: trigMode = (trigMode + 1) % 3
            else: trigDir = 1 - trigDir
            trigLevel = int(4095 * (WAVE_Y1 - y) / WAVE_H)
            draw_grid()
        draw_top_bar()

# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
def main():
    global _last_batt_pct, _batt_check_ms, holdFlag, singleDone
    
    # Initialize UI
    _last_batt_pct = read_battery_pct()
    draw_full_screen()
    
    # Start Sampling on Core 1
    _thread.start_new_thread(_sampler_core1, ())
    
    m_count = 0
    while True:
        check_touch()
        
        # Periodic Battery Check
        if utime.ticks_diff(utime.ticks_ms(), _batt_check_ms) > BATT_INTERVAL:
            _last_batt_pct = read_battery_pct()
            _batt_check_ms = utime.ticks_ms()
            draw_top_bar()

        if not holdFlag:
            if consume_ring():
                # Optimized Plotting: Erase and Draw Waveform
                for x in range(320):
                    ny = _wave_y(waveBuff[x])
                    if prevY[x] != ny:
                        # Erase old pixel by restoring grid/bg
                        display.draw_pixel(x, prevY[x], _grid_color_at(x, prevY[x]))
                        # Draw new pixel
                        display.draw_pixel(x, ny, C_WAVE)
                        prevY[x] = ny
                
                # Single Trigger handling
                if trigMode == 2:
                    holdFlag, singleDone = True, True
                    draw_top_bar()
                
                # Update measurements periodically to save cycles
                m_count += 1
                if measVisible and m_count > 10:
                    draw_measurements_panel()
                    m_count = 0
        
        utime.sleep_ms(1)
        gc.collect()

if __name__ == "__main__":
    main()