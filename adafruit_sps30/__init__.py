# SPDX-FileCopyrightText: 2021 Kevin J. Walters
#
# SPDX-License-Identifier: MIT
"""
`adafruit_sps30`
================================================================================

Helper library for the Sensirion SPS30 particulate matter sensor


* Author(s): Kevin J. Walters

Implementation Notes
--------------------

**Hardware:**

* `Sensirion SPS30 <https://www.sensirion.com/en/environmental-sensors/particulate-matter-sensors-pm25/>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases


 * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
 * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""


__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SPS30.git"


class SPS30:
    """
    Super-class for Sensirion SPS30 particulate matter sensor.
    .. note::
        * Subclasses must implement _read_into_buffer and _read_parse_data
        * The dictionary returned by read will be changed by the next read.
        * The units for particles values are number per cubic centimetre (not ppm).
        * The units for Typical Particle Size (tps) are nm for integer
          and um for floating-point.
        * Field names follow the standard set by the adafruit_pm25 library
          omitting the decimal point in the numerical values, e.g.
          PM2.5 standard is represented by "pm25" and "25um",
          PM10 standard is represented by "pm100" and "100um".
    """

    FIELD_NAMES = (
        "pm10 standard",
        "pm25 standard",
        "pm40 standard",
        "pm100 standard",
        "particles 05um",
        "particles 10um",
        "particles 25um",
        "particles 40um",
        "particles 100um",
        "tps",
    )

    DEFAULT_RETRIES = 2

    # SPS30 min firmware version in comments if not V1.0
    _CMD_START_MEASUREMENT = 0x0010
    _CMD_STOP_MEASUREMENT = 0x0104
    _CMD_READ_DATA_READY_FLAG = 0x0202
    _CMD_READ_MEASURED_VALUES = 0x0300
    _CMD_SLEEP = 0x1001  # V2.0
    _CMD_WAKEUP = 0x1103  # V2.0
    _CMD_START_FAN_CLEANING = 0x5607
    _CMD_RW_AUTO_CLEANING_INTERVAL = 0x8004
    _CMD_READ_PRODUCT_TYPE = 0xD002
    _CMD_READ_SERIAL_NUMBER = 0xD033
    _CMD_READ_VERSION = 0xD100
    _CMD_READ_DEVICE_STATUS_REG = 0xD206  # V2.2
    _CMD_CLEAR_DEVICE_STATUS_REG = 0xD210  # V2.0
    _CMD_SOFT_RESET = 0xD304

    # mask values for read_status_register()
    STATUS_FAN_ERROR = 1 << 4
    STATUS_LASER_ERROR = 1 << 5
    STATUS_FAN_CLEANING = 1 << 19  # undocumented
    STATUS_FAN_SPEED_WARNING = 1 << 21

    # time in seconds for clean operation to complete
    FAN_CLEAN_TIME = 15

    _WRONG_CLASS_TXT = "Object must be instantiated as an SPS30_I2C or SPS30_UART"

    def __init__(self):
        if type(self) == SPS30:  # pylint: disable=unidiomatic-typecheck
            raise TypeError(self._WRONG_CLASS_TXT)

        self.aqi_reading = {k: None for k in self.FIELD_NAMES}

    def _read_into_buffer(self):
        """Low level buffer filling function, to be overridden"""
        raise NotImplementedError(self._WRONG_CLASS_TXT)

    def _read_parse_data(self, output):
        """Low level buffer parsing function, to be overridden"""
        raise NotImplementedError(self._WRONG_CLASS_TXT)

    def read(self):
        """Read any available data from the air quality sensor and
        return a dictionary with available particulate/quality data"""
        self._read_into_buffer()
        self._read_parse_data(self.aqi_reading)
        return self.aqi_reading
