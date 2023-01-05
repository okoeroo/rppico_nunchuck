import machine
import time
import math
import json


# Heavily adjusted by Oscar Koeroo

class Nunchuck(object):
    address = 0x52

    tolerance_joy_x = 15
    tolerance_joy_y = 5

    Z_BUTTON = 0b00000001
    C_BUTTON = 0b00000010

    """The Nunchuk object presents the sensor readings in a polling way.
    Based on the fact that the controller does communicate using I2C we
    cannot make it push sensor changes by using interrupts or similar
    facilities. Instead a polling mechanism is implemented, which updates
    the sensor readings based on "intent-driven" regular updates.

    If the "polling" way of updating the sensor readings is not sufficient
    a timer interrupt could be used to poll the controller. The
    corresponding update() method does not allocate memory and thereby
    could directly be used as an callback method for a timer interrupt."""

    def __init__(self, scl_pin, sda_pin, freq=100_000, nunchuck_c_z_fix_mode=False):

        ### Fixing some weird effect where the last two bits are intertwined
        self.nunchuck_c_z_fix_mode = nunchuck_c_z_fix_mode

        """Initialize the Nunchuk controller. If no polling is desired it
        can be disabled. Only one controller is possible on one I2C bus,
        because the address of the controller is fixed.
        The maximum stable I2C bus rate is 100kHz (200kHz seem to work on
        mine as well, 400kHz does not)."""

        self.i2c = machine.I2C(id=1, scl=machine.Pin(scl_pin),
                                     sda=machine.Pin(sda_pin),
                                     freq=freq)
        self.buffer = bytearray(6)
        self._joy_x_center = 0
        self._joy_y_center = 0
        self.init_nunchuck()
        time.sleep_ms(5)
        self.calibrate()

    def init_nunchuck(self):
        self.i2c.writeto(self.address, b'\x40\x00')

    def submit_data_request(self):
        self.i2c.writeto(self.address, b'\x00\x00')
        time.sleep_ms(5)

    def fetch_data(self):
        self.buffer = bytearray(6)
        self.i2c.readfrom_into(self.address, self.buffer)

    def update(self):
        """Requests a sensor readout from the controller and receives the
        six data bits afterwards."""
        self.submit_data_request()
        self.fetch_data()

    def calibrate(self):
        self.update()
        self.calibrate_joy_x_center()
        self.calibrate_joy_y_center()

    def joy_x(self):
        # values 0 - 255, with a prox 128 center
        return int(self.buffer[0])

    def joy_y(self):
        # values 0 - 255, with a prox 128 center
        return int(self.buffer[1])

    def calibrate_joy_x_center(self):
        self._joy_x_center = self.joy_x()

    def calibrate_joy_y_center(self):
        self._joy_y_center = self.joy_y()

    def joy_x_center(self):
        return self._joy_x_center

    def joy_y_center(self):
        return self._joy_y_center

    def accel_x(self):
        # returns value of x-axis accelerometer: ranges from approx 278 - 686, med 475
        return (self.buffer[2]<<2)+((self.buffer[5]>>2)&3)

    def accel_y(self):
        # returns value of y-axis accelerometer: ranges from approx 296 - 716, med 506
        return (self.buffer[3]<<2)+((self.buffer[5]>>4)&3)

    def accel_z(self):
        # returns value of z-axis accelerometer: ranges from approx 295 - 1015, med 697
        return (self.buffer[4]<<2)+((self.buffer[5]>>6)&3)


    ### The z_c_buttons() func is only used to solve the weird C/Z button bit sorting.
    #c + z = 10
    #c     = 01
    #z     = 00
    #      = 11
    def z_c_buttons(self):
        value_c = self.buffer[5] & self.C_BUTTON == self.C_BUTTON
        value_z = self.buffer[5] & self.Z_BUTTON == self.Z_BUTTON

        # Return is bool for (button C and button Z)

        if value_c and value_z:
            return False, False

        elif not value_c and value_z:
            return True, False

        elif not value_c and not value_z:
            return False, True

        elif value_c and not value_z:
            return True, True


    def z_button(self):
        if self.nunchuck_c_z_fix_mode:
            c_butt, z_butt = self.z_c_buttons()
            return z_butt
        else:
            return not (self.buffer[5] & self.Z_BUTTON == self.Z_BUTTON)

    def c_button(self):
        if self.nunchuck_c_z_fix_mode:
            c_butt, z_butt = self.z_c_buttons()
            return c_butt
        else:
            return not (self.buffer[5] & self.C_BUTTON == self.C_BUTTON)


    def joy_x_angle_percentages(self):
        offset = abs(self.joy_x() - self.joy_x_center())

        if offset < self.tolerance_joy_x:
            return 0

        if self.joy_x() > self.joy_x_center():
            return int(offset / self.joy_x_center()* 100)
        else:
            return int(-1 * offset / self.joy_x_center() * 100)

    def joy_y_angle_percentages(self):
        offset = abs(self.joy_y() - self.joy_y_center())

        if offset < self.tolerance_joy_y:
            return 0

        if self.joy_y() > self.joy_y_center():
            return int(offset / self.joy_y_center() * 100)
        else:
            return int(-1 * offset / self.joy_y_center() * 100)

    def json(self):
        self.update()
        d = {}
        d['c'] = self.c_button()
        d['z'] = self.z_button()
        d['joy'] = {}
        d['joy']['x'] = self.joy_x()
        d['joy']['y'] = self.joy_y()
        d['joy']['x_cal_center'] = self.joy_x_center()
        d['joy']['y_cal_center'] = self.joy_y_center()
        d['joy']['x_angle_perc'] = self.joy_x_angle_percentages()
        d['joy']['y_angle_perc'] = self.joy_y_angle_percentages()
        d['acc'] = {}
        d['acc']['x'] = self.accel_x()
        d['acc']['y'] = self.accel_y()
        d['acc']['z'] = self.accel_z()
        return json.dumps(d)

    def __str__(self):
        self.update()
        return " ".join([
                        f"C:{self.c_button():2}",
                        f"Z:{self.z_button():2}",
                        f"Joy:{self.joy_x():4},{self.joy_y():4}",
                        f"Accel XYZ:{self.accel_x():4},{self.accel_y():4},{self.accel_z():4}",
                        f"Joy X perc:{self.joy_x_angle_percentages():4}%",
                        f"Joy Y perc:{self.joy_y_angle_percentages():4}%"])

    def __repr__(self):
        return f"Nunchuck({self.__str__()})"


if __name__ == '__main__':
    import time
    from nunchuck import nunchuck


    nun = nunchuck.Nunchuck(15, 14, freq=100_000, nunchuck_c_z_fix_mode=True)
    print("nunchuck initialized and joy stick calibrated")


    while True:
        print(nun)
        print(nun.json())
        time.sleep(0.1)
