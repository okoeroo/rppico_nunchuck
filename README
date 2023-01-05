# Raspberry Pico Nintendo Nunchuck library.

It reads on I2C all data from the nunchuck and presents it in an object with properties.

## Example
```python
import time
from nunchuck import nunchuck


nun = nunchuck.Nunchuck(15, 14, freq=100_000, nunchuck_c_z_fix_mode=True)
print("nunchuck initialized and joy stick calibrated")


while True:
    print(nun)
    print(nun.json())
    time.sleep(0.1)
```
