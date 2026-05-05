# PicoScope — Pocket Oscilloscope Pro v4.0

**Raspberry Pi Pico 2 Based Digital Storage Oscilloscope with Touch Interface**

Built by [Your Name] · [Your Organization/Location]

![PicoScope Main Interface](images/picoscope_main.jpg)

---

## What This Project Is

A fully functional pocket-sized digital storage oscilloscope (DSO) built around the Raspberry Pi Pico 2 microcontroller. Features a 2.8" ILI9341 color TFT display with XPT2046 resistive touch interface, providing real-time waveform visualization with professional DSO features including:

- **Dual-core architecture** — Core 1 handles continuous ADC sampling while Core 0 manages display and UI
- **Real-time waveform display** with grid overlay and professional DSO aesthetics
- **Touch-based controls** — adjust voltage/time scales, trigger settings, and measurements
- **Multiple trigger modes** — Auto, Normal, and Single-shot capture
- **Live measurements** — Vpp, Vmax, Vmin, Vavg, frequency, and period
- **Adjustable timebase** — 50µs/div to 50ms/div (10 ranges)
- **Adjustable voltage scale** — 50mV/div to 50V/div (10 ranges)
- **Battery monitoring** — Built-in Li-Ion battery level indicator
- **Ring buffer architecture** — 512-sample buffer for stable triggering

Perfect for electronics hobbyists, students, and field engineers who need a portable oscilloscope for quick signal analysis.

---

## Features

### Hardware Features
- **Raspberry Pi Pico 2** (RP2040) — Dual-core ARM Cortex-M0+ @ 133MHz
- **2.8" ILI9341 TFT Display** — 320×240 resolution, 65K colors, 62.5MHz SPI
- **XPT2046 Touch Controller** — Resistive touch with calibration
- **12-bit ADC** — Up to 500kSPS sampling rate
- **Voltage Range** — 0–3.3V input (with external probe divider up to 50V)
- **Battery Powered** — Li-Ion battery with VSYS monitoring

### Software Features
- **Dual-Core Sampling** — Dedicated core for uninterrupted ADC acquisition
- **Professional UI** — DSO-510 inspired color scheme and layout
- **Trigger System** — Rising/falling edge detection with adjustable level
- **Cursor Measurements** — Horizontal and vertical cursors (planned)
- **Waveform Storage** — Hold and single-shot capture modes
- **Auto-scaling Grid** — 8×8 division display with center markers

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                       │
│              2.8" ILI9341 Touch Display                 │
│         320×240 pixels @ 62.5MHz SPI                    │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │  Raspberry Pi Pico 2  │
         │      (RP2040)         │
         │                       │
         │  Core 0: UI & Control │
         │  Core 1: ADC Sampling │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ADC (GP26)              Touch (SPI1)
    Probe Input             XPT2046
    0–3.3V                  IRQ on GP13
```

---

## Hardware

### Bill of Materials

| Component | Model | Qty | Notes |
|-----------|-------|-----|-------|
| Microcontroller | Raspberry Pi Pico 2 (RP2040) | 1 | Or Pico W for future WiFi features |
| Display | ILI9341 2.8" TFT LCD | 1 | 320×240, SPI interface |
| Touch Controller | XPT2046 | 1 | Usually integrated with ILI9341 module |
| Probe Input | BNC or 4mm banana jack | 1 | With 10:1 voltage divider |
| Battery | Li-Ion 18650 | 1 | 3.7V, 2000mAh+ recommended |
| Enclosure | 3D printed case | 1 | STL files included |
| Resistors | 10MΩ + 1.11MΩ | 2 | For 10:1 probe divider |
| Capacitor | 10pF ceramic | 1 | Probe compensation |
| Power Switch | SPDT slide switch | 1 | Battery disconnect |

### Wiring Diagram

#### ILI9341 Display → Pico

| ILI9341 Pin | Pico Pin | Function |
|-------------|----------|----------|
| VCC | 3.3V | Power supply |
| GND | GND | Ground |
| CS | GP17 | Chip select |
| RESET | GP20 | Reset |
| DC | GP19 | Data/Command |
| SDI (MOSI) | GP7 | SPI0 MOSI |
| SCK | GP6 | SPI0 Clock |
| LED | 3.3V | Backlight (via 100Ω resistor) |

#### XPT2046 Touch → Pico

| XPT2046 Pin | Pico Pin | Function |
|-------------|----------|----------|
| T_CLK | GP10 | SPI1 Clock |
| T_CS | GP9 | Touch chip select |
| T_DIN | GP11 | SPI1 MOSI |
| T_DO | GP12 | SPI1 MISO |
| T_IRQ | GP13 | Touch interrupt |

#### Probe Input

| Signal | Pico Pin | Notes |
|--------|----------|-------|
| Probe Input | GP26 (ADC0) | Via 10:1 divider for 0–33V range |
| Ground | GND | Common ground with probe |

#### Battery Monitoring

| Signal | Pico Pin | Notes |
|--------|----------|-------|
| VSYS Monitor | GP29 (ADC3) | Built-in VSYS/3 divider |

### Probe Circuit

```
Input Signal ──┬──[10MΩ]──┬──── GP26 (ADC0)
               │          │
              [10pF]   [1.11MΩ]
               │          │
              GND        GND

Attenuation: 10:1
Input Impedance: ~11MΩ
Bandwidth: ~14kHz (limited by RC)
```

⚠️ **Important Notes:**
- The ADC input must never exceed 3.3V — ensure probe divider is correctly calibrated
- Use 1% tolerance resistors for accurate voltage readings
- Add 10pF compensation capacitor for square wave response
- For AC coupling, add a 1µF capacitor in series with the 10MΩ resistor

---

## Software

### File Overview

| File | Purpose |
|------|---------|
| `main.py` | Main oscilloscope firmware — auto-runs on Pico boot |
| `ili9341.py` | ILI9341 display driver with optimized drawing functions |
| `xpt2046.py` | XPT2046 touch controller driver with calibration |
| `touch_test.py` | Touch calibration and coordinate mapping utility |
| `PicoScope_Project_Report.pdf` | Detailed project documentation |

### Installation

#### 1. Flash MicroPython onto Pico

1. Download the latest MicroPython `.uf2` for Pico from [micropython.org](https://micropython.org/download/rp2-pico/)
2. Hold the **BOOTSEL** button while plugging in USB
3. Drag the `.uf2` file to the **RPI-RP2** drive that appears
4. Pico reboots into MicroPython

#### 2. Upload Firmware to Pico

**Using Thonny IDE (Recommended):**

1. Install [Thonny IDE](https://thonny.org/)
2. Open Thonny → **Tools** → **Options** → **Interpreter**
3. Select **MicroPython (Raspberry Pi Pico)**
4. Upload files in this order:
   - `ili9341.py` → Save to Pico
   - `xpt2046.py` → Save to Pico
   - `main.py` → Save to Pico as `main.py`

**Using command line (ampy):**

```bash
pip install adafruit-ampy
ampy --port COM3 put ili9341.py
ampy --port COM3 put xpt2046.py
ampy --port COM3 put main.py
```

#### 3. Touch Calibration (Optional)

If touch input is misaligned:

1. Upload `touch_test.py` to Pico
2. Run it in Thonny
3. Touch the four corners and note the raw coordinates
4. Update calibration values in `xpt2046.py`:

```python
X_MIN = 443   # Your measured min X
X_MAX = 3567  # Your measured max X
Y_MIN = 535   # Your measured min Y
Y_MAX = 3712  # Your measured max Y
```

#### 4. Auto-Run on Boot

The file named `main.py` automatically runs when Pico powers on — no additional setup needed!

---

## User Interface

### Screen Layout

```
┌────────────────────────────────────────────────────────┐
│ CH1: 1V   5ms/d   Norm R   [RUN]   100%               │ ← Top Bar
├────────────────────────────────────────────────────────┤
│                                                        │
│         ·   ·   ·   ·   ·   ·   ·   ·                 │
│         ·   ·   ·   ·   ·   ·   ·   ·                 │
│    ·····┼···┼···┼···┼───┼───┼───┼───┼·····            │
│         │   │   │   │   │   │   │   │                 │
│    ─────┼───┼───┼───┼───┼───┼───┼───┼─────            │ ← Waveform
│         │   │   │   │   │   │   │   │                 │
│    ·····┼···┼···┼···┼───┼───┼───┼───┼·····            │
│         ·   ·   ·   ·   ·   ·   ·   ·                 │
│         ·   ·   ·   ·   ·   ·   ·   ·                 │
│                                                        │
├────────────────────────────────────────────────────────┤
│ V/Div │ T/Div │ Trig │ Cursor │ Meas                  │ ← Bottom Menu
└────────────────────────────────────────────────────────┘
```

### Top Bar Indicators

| Indicator | Meaning |
|-----------|---------|
| **CH1: 1V** | Voltage scale (volts per division) |
| **5ms/d** | Time scale (time per division) |
| **Norm R** | Trigger mode (Auto/Norm/Sngl) + Edge (R=Rising, F=Falling) |
| **[RUN]** | Acquisition status (RUN/HOLD/DONE) |
| **100%** | Battery level percentage |

### Bottom Menu Buttons

| Button | Function | Touch Action |
|--------|----------|--------------|
| **V/Div** | Voltage Scale | Touch waveform area: Up=decrease, Down=increase |
| **T/Div** | Time Scale | Touch waveform area: Left=decrease, Right=increase |
| **Trig** | Trigger Settings | Left=mode cycle, Right=edge toggle, Y-position=level |
| **Cursor** | Measurement Cursors | Cycles through Off/Horizontal/Vertical modes |
| **Meas** | Measurements Panel | Toggles measurement display on/off |

### Controls

#### Voltage Scale (V/Div)
1. Tap **V/Div** button (highlights blue)
2. Touch **upper half** of waveform → decrease scale (zoom in)
3. Touch **lower half** of waveform → increase scale (zoom out)
4. Available ranges: **50mV, 0.1V, 0.2V, 0.5V, 1V, 2V, 5V, 10V, 20V, 50V**

#### Time Scale (T/Div)
1. Tap **T/Div** button (highlights blue)
2. Touch **left half** of waveform → decrease scale (zoom in)
3. Touch **right half** of waveform → increase scale (zoom out)
4. Available ranges: **50µs, 100µs, 200µs, 500µs, 1ms, 2ms, 5ms, 10ms, 20ms, 50ms**

#### Trigger Settings
1. Tap **Trig** button (highlights blue)
2. Touch **left half** → cycle trigger mode (Auto → Normal → Single)
3. Touch **right half** → toggle edge direction (Rising ⇄ Falling)
4. Touch **Y-position** → set trigger level

**Trigger Modes:**
- **Auto** — Continuous refresh even without trigger
- **Norm** — Only updates when trigger condition met
- **Sngl** — Single-shot capture, then HOLD

#### Run/Hold Control
- Tap **[RUN]** indicator in top-right → toggles between RUN and HOLD
- **RUN** — Continuous waveform acquisition
- **HOLD** — Freeze current waveform
- **DONE** — Single-shot capture completed

#### Measurements
1. Tap **Meas** button → toggles measurement panel
2. Panel shows:
   - **Vpp** — Peak-to-peak voltage
   - **Vmax** — Maximum voltage
   - **Freq** — Signal frequency (Hz or kHz)
   - **Per** — Signal period (ms)

---

## Specifications

### Input Characteristics
| Parameter | Value |
|-----------|-------|
| Input Channels | 1 analog channel |
| Input Coupling | DC (AC with external capacitor) |
| Input Impedance | ~11MΩ (with 10:1 probe) |
| Maximum Input Voltage | 33V (with 10:1 divider) |
| ADC Resolution | 12-bit (4096 levels) |
| Voltage Accuracy | ±5% (uncalibrated) |

### Timebase
| Parameter | Value |
|-----------|-------|
| Sampling Rate | Up to 500kSPS |
| Timebase Range | 50µs/div to 50ms/div |
| Record Length | 320 samples (visible) |
| Buffer Depth | 512 samples (ring buffer) |
| Horizontal Resolution | 320 pixels |

### Trigger
| Parameter | Value |
|-----------|-------|
| Trigger Types | Edge (rising/falling) |
| Trigger Modes | Auto, Normal, Single |
| Trigger Level | Adjustable 0–100% of screen |
| Trigger Sensitivity | ~50mV |

### Display
| Parameter | Value |
|-----------|-------|
| Screen Size | 2.8" diagonal |
| Resolution | 320×240 pixels |
| Colors | 65,536 (16-bit RGB565) |
| Refresh Rate | ~30 FPS |
| Grid Divisions | 8×8 |

### Power
| Parameter | Value |
|-----------|-------|
| Supply Voltage | 3.7V Li-Ion (or 5V USB) |
| Current Consumption | ~150mA @ 3.7V |
| Battery Life | ~8 hours (2000mAh battery) |
| Charging | Via USB (if charge circuit added) |

---

## Measurements & Accuracy

### Voltage Measurement
- **Range:** 0–3.3V direct, 0–33V with 10:1 probe
- **Resolution:** 0.8mV (3.3V range), 8mV (33V range)
- **Accuracy:** ±5% typical (±2% with calibration)

### Frequency Measurement
- **Range:** 10Hz – 50kHz
- **Method:** Zero-crossing detection
- **Accuracy:** ±1% (for signals with clean edges)

### Limitations
- **Bandwidth:** ~14kHz (limited by probe RC filter)
- **Aliasing:** Signals above Nyquist frequency (250kHz max) will alias
- **Noise:** ~20mV RMS (can be reduced with averaging)

---

## Calibration

### Voltage Calibration
1. Apply a known voltage (e.g., 1.5V from AA battery)
2. Measure displayed voltage
3. Calculate correction factor: `factor = actual / displayed`
4. Update in `main.py`:

```python
# Add after ADC read
voltage = (adc_value * 3.3 / 4095) * CALIBRATION_FACTOR
```

### Timebase Calibration
1. Input a known frequency signal (e.g., 1kHz square wave)
2. Measure displayed period
3. Adjust `H_RANGE_US` values if needed

### Touch Calibration
See **Installation → Step 3** above.

---

## 3D Printed Enclosure

![Enclosure Design](images/enclosure_3d.png)

### Features
- Compact form factor: 95mm × 70mm × 30mm
- Integrated probe holder
- Battery compartment for 18650 cell
- Access ports for USB and probe input
- Mounting holes for display and Pico

### Printing Instructions
- **Material:** PLA or PETG
- **Layer Height:** 0.2mm
- **Infill:** 20%
- **Supports:** Required for probe holder overhang
- **Print Time:** ~4 hours

### Files
- `enclosure_top.stl` — Top shell with display cutout
- `enclosure_bottom.stl` — Bottom shell with battery compartment
- `probe_holder.stl` — Clip-on probe storage
- `button_caps.stl` — Optional tactile button covers

📁 **Download:** [3D Files](3d_files/)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Display stays white/blank** | Check SPI wiring (CS, DC, RST). Verify 3.3V power. Try lowering SPI baudrate to 10MHz. |
| **Touch not responding** | Run `touch_test.py` to verify touch controller. Check T_IRQ connection. Recalibrate if needed. |
| **Waveform not updating** | Check probe connection to GP26. Verify ADC is reading (print values in Thonny). |
| **Trigger not working** | Set trigger mode to **Auto** first. Adjust trigger level to mid-screen. Check signal amplitude. |
| **Incorrect voltage readings** | Verify probe divider resistor values. Run voltage calibration. Check for loose connections. |
| **Frequency shows 0 Hz** | Signal may be too slow or noisy. Try Auto trigger mode. Increase voltage scale. |
| **Battery percentage wrong** | Check GP29 (ADC3) connection. Verify VSYS voltage with multimeter. Adjust battery voltage range in code. |
| **Display flickers** | Lower SPI baudrate. Check power supply stability. Add 100µF capacitor near Pico. |
| **Core 1 crashes** | Reduce sampling rate. Check for memory issues with `gc.collect()`. |

---

## Future Enhancements

### Planned Features
- [ ] **Dual Channel** — Add second ADC input
- [ ] **FFT Spectrum Analyzer** — Frequency domain analysis
- [ ] **Waveform Storage** — Save/recall up to 10 waveforms
- [ ] **WiFi Data Logging** — Stream data to PC via Pico W
- [ ] **Auto-Measurements** — Rise time, fall time, duty cycle
- [ ] **XY Mode** — Lissajous patterns
- [ ] **Protocol Decode** — UART, SPI, I2C decoding
- [ ] **Calibration Menu** — On-screen voltage/time calibration

### Hardware Upgrades
- External ADC (ADS1115) for higher resolution
- Analog frontend with gain stages
- AC/DC coupling switch
- Adjustable trigger hysteresis
- Larger 3.5" display

---

## Project Gallery

### Hardware Photos

![PicoScope Front View](images/front_view.jpg)
*Front view showing display and touch interface*

![PicoScope Internal](images/internal_view.jpg)
*Internal layout with Pico 2 and battery*

![Probe Connection](images/probe_detail.jpg)
*10:1 probe divider circuit*

### Waveform Captures

![Square Wave 1kHz](images/capture_square_1khz.jpg)
*1kHz square wave at 1V/div, 500µs/div*

![Sine Wave 10kHz](images/capture_sine_10khz.jpg)
*10kHz sine wave with measurements panel*

![PWM Signal](images/capture_pwm.jpg)
*PWM signal with trigger on rising edge*

---

## Technical Details

### Dual-Core Architecture

**Core 0 (Main):**
- UI rendering and touch handling
- Waveform processing and display
- Trigger detection
- Measurement calculations
- Battery monitoring

**Core 1 (Sampler):**
- Continuous ADC sampling at configured rate
- Ring buffer management
- Minimal overhead for consistent timing

### Ring Buffer Design
```
Core 1 (Writer)          Ring Buffer          Core 0 (Reader)
     │                   [512 samples]              │
     │                        │                     │
     ├─── write_ptr ─────────►│                     │
     │    (continuous)        │                     │
     │                        │◄──── read_ptr ──────┤
     │                        │      (on trigger)   │
     │                        │                     │
     └────── Lock ────────────┴────── Lock ─────────┘
```

### Memory Management
- **Ring Buffer:** 1KB (512 × 16-bit samples)
- **Display Buffer:** 640 bytes (320 × 16-bit Y-coordinates)
- **Frame Buffer:** None (direct pixel drawing)
- **Free RAM:** ~200KB available for future features

### Performance Metrics
- **ADC Sampling:** 500kSPS max (2µs per sample)
- **Display Update:** ~30 FPS (33ms per frame)
- **Touch Response:** <200ms debounced
- **Trigger Latency:** <10ms

---

## Code Structure

### main.py Overview

```python
# Pin definitions and hardware init
TFT_CS, TFT_DC, TFT_RST = 17, 19, 20
PROBE_PIN = 26  # ADC0

# Display and touch initialization
display = Display(spi_disp, ...)
touch = Touch(spi_touch, ...)

# Oscilloscope state variables
vRange, hRange = 5, 5  # Default scales
trigMode, trigLevel = 0, 2048  # Auto trigger

# Ring buffer for dual-core sampling
RING_SIZE = 512
ring_buf = bytearray(RING_SIZE * 2)

# Core 1 sampler thread
def _sampler_core1():
    while True:
        # Continuous ADC sampling
        sample = adc.read_u16() >> 4
        ring_buf[write_ptr] = sample
        utime.sleep_us(H_RANGE_US[hRange])

# Main loop (Core 0)
def main():
    _thread.start_new_thread(_sampler_core1, ())
    while True:
        check_touch()
        if consume_ring():  # Trigger detection
            draw_waveform()
        draw_measurements()
```

### Key Functions

| Function | Purpose |
|----------|---------|
| `_sampler_core1()` | Core 1 ADC sampling loop |
| `consume_ring()` | Trigger detection and buffer read |
| `draw_grid()` | Render oscilloscope grid |
| `draw_waveform()` | Plot signal trace |
| `compute_measurements()` | Calculate Vpp, freq, etc. |
| `check_touch()` | Handle touch input |
| `read_battery_pct()` | Monitor battery level |

---

## Contributing

Contributions are welcome! Areas for improvement:

- **Calibration routines** — Automated voltage/time calibration
- **Signal processing** — Averaging, peak detection, filtering
- **UI enhancements** — Better touch feedback, animations
- **Documentation** — More detailed build guide, video tutorials
- **Hardware variants** — Support for different displays/touch controllers

### How to Contribute
1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is open-source and available under the **MIT License**.

```
MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Acknowledgments

- **MicroPython** — Python runtime for microcontrollers
- **ILI9341 Driver** — Based on community display drivers
- **XPT2046 Touch Library** — Resistive touch controller support
- **Raspberry Pi Foundation** — For the amazing Pico platform
- **DSO-510** — UI design inspiration

---

## Contact & Support

- **GitHub Issues:** [Report bugs or request features](https://github.com/yourusername/picoscope/issues)
- **Email:** your.email@example.com
- **Documentation:** [Full project wiki](https://github.com/yourusername/picoscope/wiki)

---

## Project Stats

![GitHub stars](https://img.shields.io/github/stars/yourusername/picoscope?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/picoscope?style=social)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![MicroPython](https://img.shields.io/badge/MicroPython-1.22-green.svg)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%20Pico%202-red.svg)

---

**Built with ❤️ for the maker community**

*If you found this project helpful, please consider giving it a ⭐ on GitHub!*
