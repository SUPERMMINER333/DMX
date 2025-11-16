"""
Potentiometer Library - Optimized
Reads analog values from ADS1115 ADC with efficient smoothing
"""

import time
from collections import deque


class Poti:
    """Potentiometer Handler using ADS1115 - Optimized"""

    def __init__(self, ads, smoothing=5):
        """
        Initialize potentiometer reader

        Args:
            ads: ADS1115 instance
            smoothing: Number of samples for smoothing (default 5)
        """
        self.ads = ads
        self.smoothing = smoothing

        # ✅ OPTIMIERUNG: deque statt list (schnellere append/pop)
        self.history = [deque(maxlen=smoothing) for _ in range(4)]

        # ✅ OPTIMIERUNG: bytearray für Werte
        self.last_values = bytearray([0, 0, 0, 0])

        # Cache für letzten Raw-Wert (Noise-Reduktion)
        self._last_raw = [0, 0, 0, 0]
        self._noise_threshold = 10  # ADC-Rauschen ignorieren

    def read(self, channel):
        """
        Read raw value from ADC channel

        Args:
            channel: ADC channel (0-3)

        Returns:
            Raw ADC value
        """
        try:
            value = self.ads.readADCSingleEnded(channel)
            return value
        except Exception as e:
            print(f"Error reading ADC channel {channel}: {e}")
            return 0

    def read_all(self, channel):
        """
        Read and smooth ADC value, convert to DMX range (0-255) - Optimized

        Args:
            channel: ADC channel (0-3)

        Returns:
            DMX value (0-255)
        """
        raw = self.read(channel)

        # ✅ OPTIMIERUNG: Noise filtering - ignore small changes
        if abs(raw - self._last_raw[channel]) < self._noise_threshold:
            return self.last_values[channel]

        self._last_raw[channel] = raw

        # ✅ OPTIMIERUNG: deque auto-manages size
        self.history[channel].append(raw)

        # ✅ OPTIMIERUNG: Fast average without intermediate list
        avg = sum(self.history[channel]) / len(self.history[channel])

        # ✅ OPTIMIERUNG: Fast conversion with precalculated constant
        # avg / 4095 * 255 = avg * 0.0622659...
        dmx_value = int((avg * 255) / 4095)

        # ✅ OPTIMIERUNG: Fast clamping
        if dmx_value < 0:
            dmx_value = 0
        elif dmx_value > 255:
            dmx_value = 255

        self.last_values[channel] = dmx_value
        return dmx_value

    def read_all_channels(self):
        """
        Read all 4 channels

        Returns:
            List of 4 DMX values
        """
        return [self.read_all(i) for i in range(4)]

    def get_last_value(self, channel):
        """
        Get last read value without reading ADC

        Args:
            channel: Channel number (0-3)

        Returns:
            Last DMX value
        """
        if 0 <= channel < 4:
            return self.last_values[channel]
        return 0
