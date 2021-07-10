# SPDX-FileCopyrightText: 2021 Kevin J. Walters
#
# SPDX-License-Identifier: MIT
"""
`adafruit_sps30.i2c`
================================================================================

Helper library for the Sensirion SPS30 particulate matter sensor using i2c interface.


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

import time
from struct import unpack_from

import adafruit_bus_device.i2c_device as i2c_device

from . import SPS30


__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SPS30.git"


SPS30_DEFAULT_ADDR = 0x69


class SPS30_I2C(SPS30):
    """
    CircuitPython helper class for using the Sensirion SPS30 particulate matter sensor
    over the i2c interface.

    :param ~busio.I2C i2c_bus: The I2C bus the SCD30 is connected to.
    :param int address: The I2C device address for the sensor. Default is :const:`0x69`

    **Quickstart: Importing and using the SCD30**

        Here is an example of using the :class:`SPS30` class.
        First you will need to import the libraries to use the sensor

        .. code-block:: python

            import board
            from adafruit_sps30.i2c import SPS30_I2C

        Once this is done you can define your `board.I2C` object and define your sensor object
        using the i2c bus.
        The SPS30 i2c mode is selected by grounding its interface select pin.

        .. code-block:: python

            i2c = board.I2C()   # uses board.SCL and board.SDA
            sps = SPS30_I2C(i2c)

        Now you have access to the air quality data using the class function
        `adafruit_sps30.SPS30.read`

        .. code-block:: python

            aqdata = sps.read()

    """

    def __init__(
        self,
        i2c_bus,
        address=SPS30_DEFAULT_ADDR,
        *,
        auto_start=True,
        fp_mode=False,  # fp_mode selection is buggy, end 30 bytes are 0xff
        delays=True
    ):
        super().__init__()
        self._buffer = bytearray(60)  # 10*(4+2)
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)
        self._cmd_buffer = bytearray(2 + 6)

        self._fp_mode = None
        self._m_size = None
        self._m_total_size = None
        self._m_fmt = None
        self._delays = delays
        self._set_fp_mode_fields(fp_mode)

        if auto_start:
            self.start(fp_mode)

        self.firmware_version = self.read_firmware_version()

    def start(self, use_floating_point=None, *, stop_first=True):
        """Send start command to the SPS30.
        This will already have been called by constructor
        if auto_start is left to default value.
        if stop_first is True (default value) a stop will be send first.
        A stop is required if the device has previously been started
        with a different use_floating_point mode.
        """
        if stop_first:
            self.stop()
        request_fp = self._fp_mode if use_floating_point is None else use_floating_point
        output_format = 0x0300 if request_fp else 0x0500
        self._sps30_command(self._CMD_START_MEASUREMENT, arguments=(output_format,))
        self._set_fp_mode_fields(request_fp)
        # Data sheet states command execution time < 20ms
        if self._delays:
            time.sleep(0.020)

    def stop(self):
        """Send stop command to SPS30."""
        self._sps30_command(self._CMD_STOP_MEASUREMENT)
        # Data sheet states command execution time < 20ms
        if self._delays:
            time.sleep(0.020)

    def reset(self):
        """Perform a soft reset on the SPS30, restoring default values"""
        self._sps30_command(self._CMD_SOFT_RESET)
        # Data sheet states command execution time < 100ms
        if self._delays:
            time.sleep(0.100)

    def read_firmware_version(self):
        """Read firmware version returning as two element tuple."""
        self._sps30_command(self._CMD_READ_VERSION, rx_size=3)
        self._buffer_check(3)
        return (self._buffer[0], self._buffer[1])

    def read_status_register(self):
        """Read 32bit status register."""
        # The datasheet does not indicate a delay is required between write
        # and read but the Sensirion library does this for some reason
        # https://github.com/Sensirion/embedded-sps/blob/master/sps30-i2c/sps30.c
        # https://github.com/Sensirion/arduino-sps/blob/master/sps30.cpp
        self._sps30_command(self._CMD_READ_DEVICE_STATUS_REG, rx_size=6, delay=0.005)
        self._buffer_check(6)
        self._scrunch_buffer(6)
        return unpack_from(">I", self._buffer)[0]

    def data_available(self):
        """Boolean indicating if data is available or None for invalid response."""
        self._sps30_command(self._CMD_DATA_READY, rx_size=3)
        self._buffer_check(3)
        ready = None
        if self._buffer[1] == 0x00:
            ready = False
        elif self._buffer[1] == 0x01:
            ready = True

        return ready

    def _set_fp_mode_fields(self, use_floating_point):
        self._fp_mode = use_floating_point
        self._m_size = 6 if self._fp_mode else 3
        self._m_total_size = len(self.FIELD_NAMES) * self._m_size
        self._m_parse_size = len(self.FIELD_NAMES) * (self._m_size * 2 // 3)
        self._m_fmt = ">" + ("f" if self._fp_mode else "H") * len(self.FIELD_NAMES)

    def _sps30_command(
        self,
        command,
        arguments=None,
        *,
        rx_size=0,
        retry=SPS30.DEFAULT_RETRIES,
        delay=0
    ):
        """Set rx_size to None to read arbitrary amount of data up to max of _buffer size"""
        self._cmd_buffer[0] = (command >> 8) & 0xFF
        self._cmd_buffer[1] = command & 0xFF
        tx_size = 2

        # Add arguments if any
        if arguments is not None:
            for arg in arguments:
                self._cmd_buffer[tx_size] = (arg >> 8) & 0xFF
                tx_size += 1
                self._cmd_buffer[tx_size] = arg & 0xFF
                tx_size += 1
                self._cmd_buffer[tx_size] = self._crc8(
                    self._cmd_buffer, start=tx_size - 2, end=tx_size
                )
                tx_size += 1

        # The write_then_readinto method cannot be used as the SPS30
        # does not like it based on real tests using self._CMD_READ_VERSION
        # This is probably due to lack of support for i2c repeated start
        with self.i2c_device as i2c:
            i2c.write(self._cmd_buffer, end=tx_size)
            if delay:
                time.sleep(delay)
            if rx_size != 0:
                i2c.readinto(self._buffer, end=rx_size)

        if retry:
            pass  # implement retries with appropriate exception handling

    def _read_into_buffer(self):
        data_len = self._m_total_size
        self._sps30_command(self._CMD_READ_MEASURED_VALUES, rx_size=data_len)
        self._buffer_check(data_len)

    def _scrunch_buffer(self, raw_data_len):
        """Move all the data from 0:raw_data_len to one contiguous sequence at
        the start of the buffer.
        This will overwrite some of the interleaved crcs."""
        dst_idx = 2
        for src_idx in range(3, raw_data_len, 3):
            self._buffer[dst_idx : dst_idx + 2] = self._buffer[src_idx : src_idx + 2]
            dst_idx += 2

    def _read_parse_data(self, output):
        self._scrunch_buffer(self._m_total_size)

        # buffer will be longer than the data hence the use of unpack_from
        for key, val in zip(self.FIELD_NAMES, unpack_from(self._m_fmt, self._buffer)):
            output[key] = val

    def _buffer_check(self, raw_data_len):
        if raw_data_len % 3 != 0:
            raise RuntimeError("Data length not a multiple of three")

        for st_chunk in range(0, raw_data_len, 3):
            if self._buffer[st_chunk + 2] != self._crc8(
                self._buffer, st_chunk, st_chunk + 2
            ):
                raise RuntimeError("CRC mismatch in data at offset " + str(st_chunk))

    @staticmethod
    def _crc8(buffer, start=None, end=None):
        crc = 0xFF
        for idx in range(
            0 if start is None else start, len(buffer) if end is None else end
        ):
            crc ^= buffer[idx]
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        return crc & 0xFF  # return the bottom 8 bits
