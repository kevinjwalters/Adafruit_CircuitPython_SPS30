# SPDX-FileCopyrightText: 2021 Kevin J. Walters
#
# SPDX-License-Identifier: MIT
"""
`adafruit_sps30.uart`
================================================================================

Helper library for the Sensirion SPS30 particulate matter sensor using UART interface.


* Author(s): Kevin J. Walters

Implementation Notes
--------------------

**Hardware:**

* `Sensirion SPS30
   <https://www.sensirion.com/en/environmental-sensors/particulate-matter-sensors-pm25/>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases


 * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
 * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SPS30.git"


class SPS30_UART:
    """
    CircuitPython helper class for using the Sensirion SPS30 particulate matter sensor
    over UART interface.

    :param ~busio.UART uart: The `busio.UART` object to use.

    **Quickstart: Importing and using the SPS30**

        Here is an example of using the :class:`SPS30` class.
        First you will need to import the libraries to use the sensor

        .. code-block:: python

            import time
            import board
            from adafruit_sps30.i2c import SPS30_I2C

            i2c = board.I2C()   # uses board.SCL and board.SDA
            sps = SPS30_I2C(i2c)

            while True:
                aqdata = sps.read()
                print("PM2.5: {:d}".format(aqdata["pm25 standard"]))
                time.sleep(1)

    """

    # pylint: disable=too-few-public-methods
    def __init__(self, uart):

        super().__init__()
        # TODO CHECK THIS IS BIG ENOUGH IF STORING HEADERS/FRAME CHECKSUMS IN HERE
        self._buffer = bytearray(40)  # 10*4

        self._uart = uart
        raise NotImplementedError("Not yet implemented...")

    def _read_into_buffer(self):
        """Low level buffer filling function, to be overridden"""
        raise NotImplementedError("Not yet implemented...")

    def _read_parse_data(self, output):
        """Low level buffer parsing function, to be overridden"""
        raise NotImplementedError("Not yet implemented...")
