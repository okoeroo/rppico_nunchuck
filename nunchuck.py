import machine
import time
import utime

# Heavily adjusted by Oscar Koeroo

class Nunchuck(object):
    """The Nunchuk object presents the sensor readings in a polling way.
    Based on the fact that the controller does communicate using I2C we
    cannot make it push sensor changes by using interrupts or similar
    facilities. Instead a polling mechanism is implemented, which updates
    the sensor readings based on "intent-driven" regular updates.

    If the "polling" way of updating the sensor readings is not sufficient
    a timer interrupt could be used to poll the controller. The
    corresponding update() method does not allocate memory and thereby
    could directly be used as an callback method for a timer interrupt."""

    def __init__(self, scl_pin, sda_pin, freq=10000):
        """Initialize the Nunchuk controller. If no polling is desired it
        can be disabled. Only one controller is possible on one I2C bus,
        because the address of the controller is fixed.
        The maximum stable I2C bus rate is 100kHz (200kHz seem to work on
        mine as well, 400kHz does not)."""
        
        self.i2c = machine.I2C(id=1, scl=machine.Pin(scl_pin),
                                     sda=machine.Pin(sda_pin),
                                     freq=freq)
        self.address = 0x52
        self.buffer = bytearray(6)
        self.init_nunchuck()
        
    def init_nunchuck(self):
        self.i2c.writeto(self.address, b'\x40\x00')
    
    def submit_data_request(self):
        self.i2c.writeto(self.address, b'\x00\x00')
        
    def fetch_data(self):
        self.buffer = bytearray(6)
        self.i2c.readfrom_into(self.address, self.buffer)
        
    def update(self):
        """Requests a sensor readout from the controller and receives the
        six data bits afterwards."""
        self.submit_data_request()
        self.fetch_data()
        
    def joy_x(self):
        return int(self.buffer[0])

    def joy_y(self):
        return int(self.buffer[1])
    
    def accel_x(self):
        # returns value of x-axis accelerometer: ranges from approx 278 - 686, med 475
        return (self.buffer[2]<<2)+((self.buffer[5]>>2)&3)
    
    def accel_y(self):
        # returns value of y-axis accelerometer: ranges from approx 296 - 716, med 506
        return (self.buffer[3]<<2)+((self.buffer[5]>>4)&3)
    
    def accel_z(self):
        # returns value of z-axis accelerometer: ranges from approx 295 - 1015, med 697
        return (self.buffer[4]<<2)+((self.buffer[5]>>6)&3)

    def z_button(self):
        return not (self.buffer[5] & 0x01) == 0x01

    def c_button(self):
        return not (self.buffer[5] & 0x02) == 0x02
    