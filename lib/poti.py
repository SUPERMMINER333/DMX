"""
Potentiometer Library
Reads analog values from ADS1115 ADC
"""

import time


class Poti:
    """Potentiometer Handler using ADS1115"""

    def __init__(self, ads, smoothing=5):
        """
        Initialize potentiometer reader

        Args:
            ads: ADS1115 instance
            smoothing: Number of samples for smoothing (default 5)
        """
        self.ads = ads
        self.smoothing = smoothing
        self.history = [[] for _ in range(4)]
        self.last_values = [0, 0, 0, 0]

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
        Read and smooth ADC value, convert to DMX range (0-255)

        Args:
            channel: ADC channel (0-3)

        Returns:
            DMX value (0-255)
        """
        raw = self.read(channel)

        # Add to history for smoothing
        self.history[channel].append(raw)
        if len(self.history[channel]) > self.smoothing:
            self.history[channel].pop(0)

        # Calculate average
        if self.history[channel]:
            avg = sum(self.history[channel]) / len(self.history[channel])
        else:
            avg = raw

        # Convert to 0-255 range (assuming ADS1115 returns 0-4095 for 12-bit)
        dmx_value = int((avg / 4095.0) * 255)
        dmx_value = max(0, min(255, dmx_value))

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
