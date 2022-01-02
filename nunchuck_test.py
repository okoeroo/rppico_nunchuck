import machine
import utime

import nunchuck


nun = nunchuck.Nunchuck(15, 14, 10000)
print("nunchuck initialized")

while True:
    nun.update()
    print(nun.z_button(),
          nun.c_button(),
          nun.joy_x(), nun.joy_y(),
          nun.accel_x(), nun.accel_y(),
          nun.accel_z(), nun.buffer)
    
    utime.sleep(0.5)
