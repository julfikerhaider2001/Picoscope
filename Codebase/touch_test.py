from machine import Pin, SPI
from xpt2046 import Touch
import utime

spi_touch = SPI(1, baudrate=1_000_000,
                sck=Pin(10), mosi=Pin(11), miso=Pin(12))

touch = Touch(spi_touch,
              cs=Pin(9, Pin.OUT),
              irq=Pin(13, Pin.IN))

print("Touch coordinate mapping test")
print("Touch each button area and corners")
print("-" * 40)

while True:
    pt = touch.get_touch()
    if pt:
        raw_x, raw_y = pt
        print(f"X: {raw_x:3d}  Y: {raw_y:3d}  |  ", end="")
        
        # Test different mapping possibilities
        # Your display is rotated 90°, so we need to remap
        
        # Try swapping X and Y
        swap_x = raw_y
        swap_y = 319 - raw_x  # Invert X when swapped
        
        print(f"Remapped: X={swap_x:3d} Y={swap_y:3d}  ->  ", end="")
        
        if swap_y < 25:
            if swap_x > 276:
                print("TOP BAR (Run/Hold)")
            else:
                print("TOP BAR")
        elif swap_y >= 201:
            if swap_x < 64:
                print("V/Div BUTTON")
            elif swap_x < 128:
                print("T/Div BUTTON")
            elif swap_x < 192:
                print("Trig BUTTON")
            elif swap_x < 256:
                print("Cursor BUTTON")
            else:
                print("Measure BUTTON")
        else:
            print("WAVEFORM")
    
    utime.sleep_ms(100)