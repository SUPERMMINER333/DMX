"""
DMX Control Library
This is a placeholder for the existing DMX library.
The actual implementation should be provided by the user.
"""

import serial
import threading
import time


class Dmx:
    """DMX Controller Interface"""

    def __init__(self, port="/dev/ttyUSB0", baudrate=250000, channels=512):
        """
        Initialize DMX controller

        Args:
            port: Serial port for DMX interface
            baudrate: DMX baudrate (default 250000)
            channels: Number of DMX channels (default 512)
        """
        self.port = port
        self.baudrate = baudrate
        self.channels = channels
        self.data = [0] * channels
        self.running = False
        self.thread = None
        self.serial = None

    def start(self):
        """Start DMX transmission"""
        try:
            self.serial = serial.Serial(
                self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_TWO
            )
            self.running = True
            self.thread = threading.Thread(target=self._send_loop, daemon=True)
            self.thread.start()
            print(f"DMX started on {self.port}")
        except Exception as e:
            print(f"Error starting DMX: {e}")
            self.running = False

    def stop(self):
        """Stop DMX transmission"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.serial and self.serial.is_open:
            self.serial.close()
        print("DMX stopped")

    def _send_loop(self):
        """Internal loop for sending DMX data"""
        while self.running:
            try:
                self._send_frame()
                time.sleep(0.001)  # ~1ms delay between frames
            except Exception as e:
                print(f"DMX send error: {e}")

    def _send_frame(self):
        """Send a single DMX frame"""
        if not self.serial or not self.serial.is_open:
            return

        # Send break
        self.serial.break_condition = True
        time.sleep(0.0001)  # 100us break
        self.serial.break_condition = False

        # Send start code
        self.serial.write(bytes([0]))

        # Send channel data
        self.serial.write(bytes(self.data))

    def set_channel(self, channel, value):
        """
        Set a single DMX channel

        Args:
            channel: Channel number (0-511)
            value: DMX value (0-255)
        """
        if 0 <= channel < self.channels:
            self.data[channel] = max(0, min(255, int(value)))

    def set_channels(self, channels, value):
        """
        Set multiple DMX channels to the same value

        Args:
            channels: List of channel numbers
            value: DMX value (0-255)
        """
        for ch in channels:
            self.set_channel(ch, value)

    def set_data(self, value, channel):
        """
        Alternative method to set channel (compatible with existing code)

        Args:
            value: DMX value (0-255)
            channel: Channel number (0-511)
        """
        self.set_channel(channel, value)

    def inc_channel(self, channel, step=1):
        """
        Increment channel value

        Args:
            channel: Channel number
            step: Increment step (default 1)
        """
        if 0 <= channel < self.channels:
            self.data[channel] = min(255, self.data[channel] + step)

    def dec_channel(self, channel, step=1):
        """
        Decrement channel value

        Args:
            channel: Channel number
            step: Decrement step (default 1)
        """
        if 0 <= channel < self.channels:
            self.data[channel] = max(0, self.data[channel] - step)

    def reset(self):
        """Reset all channels to 0"""
        self.data = [0] * self.channels

    def get_channel(self, channel):
        """
        Get current value of a channel

        Args:
            channel: Channel number

        Returns:
            Current DMX value (0-255)
        """
        if 0 <= channel < self.channels:
            return self.data[channel]
        return 0
