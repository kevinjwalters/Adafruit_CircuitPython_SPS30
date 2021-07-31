# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-FileCopyrightText: 2021 Kevin J. Walters
# SPDX-License-Identifier: MIT

"""
Example program for Sensirion SPS30 using i2c.

Reminder: SPS30 interface select pin needs to be connected to ground for i2c mode.
"""

# pylint: disable=unused-import
import time
import board
import busio
from adafruit_sps30.i2c import SPS30_I2C

# SPS30 works up to 100kHz
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
sps30 = SPS30_I2C(i2c, fp_mode=False)

print("Found SPS30 sensor, reading data...")

while True:
    time.sleep(1)

    try:
        aqdata = sps30.read()
        # print(aqdata)
    except RuntimeError as ex:
        print("Unable to read from sensor, retrying..." + str(ex))
        continue

    print()
    print("Concentration Units (standard)")
    print("---------------------------------------")
    print(
        "PM 1.0: {}\tPM2.5: {}\tPM10: {}".format(
            aqdata["pm10 standard"], aqdata["pm25 standard"], aqdata["pm100 standard"]
        )
    )
    print("Concentration Units (number count)")
    print("---------------------------------------")
    print("Particles 0.3-0.5um  / cm3:", aqdata["particles 05um"])
    print("Particles 0.3-1.0um  / cm3:", aqdata["particles 10um"])
    print("Particles 0.3-2.5um  / cm3:", aqdata["particles 25um"])
    print("Particles 0.3-4.0um  / cm3:", aqdata["particles 40um"])
    print("Particles 0.3-10.0um / cm3:", aqdata["particles 100um"])
    print("---------------------------------------")
