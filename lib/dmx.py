"""
DMX Control Library - Working Version
Based on user's tested implementation with fcntl for precise break timing
"""

import threading
import serial
import time
import os
import fcntl


class Dmx:
    """DMX Controller - Production Version"""

    def __init__(self, port="/dev/ttyUSB0"):
        """
        Initialize DMX controller

        Args:
            port: Serial port for DMX interface (or serial.Serial object)
        """
        if isinstance(port, str):
            self.ser = serial.Serial(port)
        else:
            self.ser = port

        self.ser.baudrate = 250000
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_TWO
        self.ser.xonxoff = False

        # prepare control objects
        self.enabled = False
        self.control = threading.Condition()

        self.data = [0] * 512
        self.update = threading.Condition()

        # start the sender thread
        self.send_thread = threading.Thread(target=self.__sender)
        self.send_thread.daemon = True
        self.send_thread.start()

    def __start(self, s):
        """Internal: Start/stop DMX transmission"""
        self.control.acquire()
        self.enabled = s
        self.control.notify()
        self.control.release()

    def __sender(self):
        """Internal: DMX sender thread"""
        while True:
            self.control.acquire()
            self.control.wait_for(lambda: self.enabled)
            self.control.release()

            self.update.acquire()
            self.update.wait(0.1)

            try:
                # hacky workaround for long break using ioctl
                fcntl.ioctl(self.ser, 0x5427)  # TIOCSBRK - Set break
                time.sleep(0.0001)  # 100µs break
                fcntl.ioctl(self.ser, 0x5428)  # TIOCCBRK - Clear break

                # DMX first entry is a null byte (start code)
                self.ser.write(bytes((0,)))
                # now the channel values
                self.ser.write(bytes(self.data))
                self.ser.flush()
            except Exception as e:
                print(f"DMX send error: {e}")

            self.update.release()

    def __pre_change(self):
        """Internal: Acquire lock before changing data"""
        self.update.acquire()

    def __done_change(self):
        """Internal: Release lock and notify after changing data"""
        self.update.notify()
        self.update.release()
        time.sleep(0)  # yield

    def start(self):
        """Start DMX transmission"""
        self.__start(True)
        print(f"DMX started on {self.ser.port}")

    def stop(self):
        """Stop DMX transmission"""
        self.__start(False)
        print("DMX stopped")

    def get_data(self, channel=0, channels=1):
        """
        Get DMX data for one or more channels

        Args:
            channel: Starting channel (0-511)
            channels: Number of channels to get

        Returns:
            List of channel values
        """
        return self.data[channel:channel + channels]

    def get_channel(self, channel=0):
        """
        Get single channel value

        Args:
            channel: Channel number (0-511)

        Returns:
            Channel value (0-255)
        """
        if 0 <= channel < 512:
            return self.data[channel]
        return 0

    def set_data(self, data, channel=0):
        """
        Set DMX data

        Args:
            data: List of values or single value
            channel: Starting channel (0 = replace all data)
        """
        self.__pre_change()
        if channel == 0:
            self.data = list(data) if isinstance(data, (list, tuple)) else [data] * 512
        else:
            data_list = list(data) if isinstance(data, (list, tuple)) else [data]
            self.data = self.data[:channel] + data_list + self.data[channel + len(data_list):]
        self.__done_change()

    def reset(self):
        """Reset all channels to 0"""
        self.set_data([0] * 512)

    def set_channels(self, channels, value):
        """
        Set multiple channels to same value

        Args:
            channels: List of channel numbers
            value: Value to set (0-255)
        """
        self.__pre_change()
        for c in channels:
            if 0 <= c < 512:
                self.data[c] = max(0, min(255, int(value)))
        self.__done_change()

    def set_channel(self, channel, value):
        """
        Set single channel

        Args:
            channel: Channel number (0-511)
            value: Value (0-255)
        """
        self.set_channels([channel], value)

    def inc_channels(self, channels):
        """Increment channels by 1"""
        self.__pre_change()
        for c in channels:
            if 0 <= c < 512:
                self.data[c] = min(255, self.data[c] + 1)
        self.__done_change()

    def dec_channels(self, channels):
        """Decrement channels by 1"""
        self.__pre_change()
        for c in channels:
            if 0 <= c < 512:
                self.data[c] = max(0, self.data[c] - 1)
        self.__done_change()

    def inc_channel(self, channel):
        """Increment single channel"""
        self.inc_channels([channel])

    def dec_channel(self, channel):
        """Decrement single channel"""
        self.dec_channels([channel])

    # Add compatibility with optimized version's property
    @property
    def running(self):
        """Check if DMX is running"""
        return self.enabled
