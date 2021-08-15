# SPDX-FileCopyrightText: 2021 Kevin J. Walters
# SPDX-License-Identifier: MIT

"""
Test program for Sensirion SPS30 device putting it through its paces using i2c.

SPS30 running 2.2 firmware appears to take around one second to change into the
requested mode for data type. Any read in that time will be in the previous format
causing bad data or CRC errors!

Reminder: SPS30 interface select pin needs to be connected to ground for i2c mode.
"""

# pylint: disable=unused-import
import time
import board
import busio
from adafruit_sps30.i2c import SPS30_I2C

DELAYS = (5.0, 2.0, 1.0, 0.1, 0.0, 0.0)
DEF_READS = len(DELAYS)
PM_PREFIXES = ("pm10", "pm25", "pm40", "pm100")
TEST_VERSION = "1.2"


def some_reads(sps, num=DEF_READS):
    """Read and print out some values from the sensor which could be
    integers or floating-point values."""

    output_header = True
    last_idx = min(len(DELAYS), num) - 1
    for idx in range(last_idx + 1):
        data = sps.read()
        if output_header:
            print("PM1\tPM2.5\tPM4\tPM10")
            output_header = False
        # print(data)
        print("{}\t{}\t{}\t{}".format(*[data[pm + " standard"] for pm in PM_PREFIXES]))
        if idx != last_idx:
            time.sleep(DELAYS[idx])

    # Just for last value
    print("ALL for last read")
    for field in sps.FIELD_NAMES:
        print("{:s}: {}".format(field, data[field]))


print()
print("Reminder: tps units are different between integer and floating-point modes")
# Bogus data / bogus CRC errors for around one second after mode change are
# inhibited by default mode_change_delay=1.5 in SPS30_I2C constructor
# measured at 0.98 seconds, 1.5 is more conservative value
print()

# To allow a human to grab the serial console
# after a power up to capture the data
print("Sleeping for 20 seconds")
time.sleep(20)

# SPS30 works up to 100kHz
print("BEGIN TEST sps30_test version", TEST_VERSION)
i2c = busio.I2C(board.SCL, board.SDA, frequency=100_000)
print("Creating SPS30_I2C defaults")
sps30_int = SPS30_I2C(i2c, fp_mode=False)
fw_ver = sps30_int.firmware_version
print("Firmware version: {:d}.{:d}".format(fw_ver[0], fw_ver[1]))
print("Six reads in integer mode")
some_reads(sps30_int)
del sps30_int


print("Creating SPS30_I2C fp_mode=True")
sps30_fp = SPS30_I2C(i2c, fp_mode=True)
print("Six reads in default floating-point mode")

start_t = time.monotonic()
readstart_t = start_t
fails = 0
exception = None
for attempts in range(30):
    try:
        readstart_t = time.monotonic()
        some_reads(sps30_fp)
        break
    except RuntimeError as ex:
        exception = ex
        fails += 1
    time.sleep(0.050)
if fails:
    print("Number of exceptions:", fails)
    print("Last exception:", repr(exception))
    print("Time to good read:", readstart_t - start_t)

print("Stop and wait 10 seconds")
sps30_fp.stop()
print("Start and wait for data to become available")
sps30_fp.start()
start_t = time.monotonic()
while True:
    now_t = time.monotonic()
    got_data = sps30_fp.data_available
    if got_data or now_t - start_t > 30.0:
        break
print("Time since start: ", now_t - start_t)
print("Data available:", got_data)
print("Six more reads")
some_reads(sps30_fp)

print("Reset (goes to idle mode)")
sps30_fp.reset()
print("Start")
sps30_fp.start()
print("Six reads after reset+start")
some_reads(sps30_fp)

print("Stop / Sleep / 10 second pause / Wake-up / Start")
sps30_fp.stop()
sps30_fp.sleep()
time.sleep(5)
got_data = False
try:
    got_data = sps30_fp.data_available
    if got_data:
        print("Data available during sleep mode: BAD BAD BAD!")
except OSError:
    # this seems to happen in sleep mode
    # OSError: [Errno 19] Unsupported operation
    pass
time.sleep(5)
sps30_fp.wakeup()  # transitions back to "Idle" mode
sps30_fp.start()  # needed to return to "Measurement" mode
print("Six reads after wakeup and start")
some_reads(sps30_fp)
print("Six more reads after wakeup and start")
some_reads(sps30_fp)

# data sheet implies this takes 10 seconds but more like 14
print("Fan clean (the speed up is audible)")
sps30_fp.clean(wait=4)
for _ in range(2 * (10 - 4 + 15)):
    cleaning = bool(sps30_fp.read_status_register() & sps30_fp.STATUS_FAN_CLEANING)
    print("c" if cleaning else ".", end="")
    if not cleaning:
        break
    time.sleep(0.5)
print()
print("Six reads after clean")
some_reads(sps30_fp)

print("END TEST")
time.sleep(6)
