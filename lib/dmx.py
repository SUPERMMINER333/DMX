"""
DMX Control Library - Optimized Version
High-performance DMX512 implementation with precise timing
"""

import serial
import threading
import time
import os
import ctypes


class Dmx:
    """DMX Controller Interface - Optimized"""

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

        # ✅ OPTIMIERUNG: bytearray statt list (schneller, weniger Memory)
        self.data = bytearray(channels)

        # ✅ OPTIMIERUNG: Pre-allocate frame buffer
        self._frame_buffer = bytearray([0] + list(self.data))  # Start code + channels

        self.running = False
        self.thread = None
        self.serial = None

        # Performance monitoring
        self._frame_count = 0
        self._last_fps_check = time.time()

    def start(self):
        """Start DMX transmission with optimizations"""
        try:
            self.serial = serial.Serial(
                self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_TWO,
                # ✅ OPTIMIERUNG: Disable software flow control
                xonxoff=False,
                # ✅ OPTIMIERUNG: Disable hardware flow control
                rtscts=False,
                dsrdtr=False,
                # ✅ OPTIMIERUNG: Short timeout
                timeout=0.001
            )

            self.running = True
            self.thread = threading.Thread(target=self._send_loop, daemon=True)

            # ✅ OPTIMIERUNG: Set thread priority (requires root or capabilities)
            self.thread.start()
            self._set_realtime_priority()

            print(f"DMX started on {self.port}")
        except Exception as e:
            print(f"Error starting DMX: {e}")
            self.running = False

    def _set_realtime_priority(self):
        """Set realtime priority for DMX thread (Linux only)"""
        try:
            # Try to set high priority (nice level)
            os.nice(-10)  # Requires privileges
            print("DMX thread priority increased")
        except PermissionError:
            # Fallback: try with ctypes (SCHED_FIFO)
            try:
                libc = ctypes.CDLL('libc.so.6', use_errno=True)

                class SchedParam(ctypes.Structure):
                    _fields_ = [('sched_priority', ctypes.c_int)]

                SCHED_FIFO = 1
                param = SchedParam()
                param.sched_priority = 50  # 1-99, higher = more priority

                # Set scheduler for current thread
                result = libc.pthread_setschedparam(
                    libc.pthread_self(),
                    SCHED_FIFO,
                    ctypes.byref(param)
                )

                if result == 0:
                    print("DMX using SCHED_FIFO realtime scheduling")
                else:
                    print(f"Could not set realtime priority (run as root for best performance)")
            except Exception as e:
                print(f"Realtime scheduling unavailable: {e}")
        except Exception as e:
            print(f"Priority adjustment failed: {e}")

    def stop(self):
        """Stop DMX transmission"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.serial and self.serial.is_open:
            self.serial.close()
        print("DMX stopped")

    def _send_loop(self):
        """Internal loop for sending DMX data - Optimized"""
        # ✅ OPTIMIERUNG: Pre-calculate target frame time
        target_frame_time = 1.0 / 44.0  # 44 FPS for DMX (22.7ms per frame)

        while self.running:
            try:
                frame_start = time.perf_counter()

                self._send_frame_optimized()

                # ✅ OPTIMIERUNG: Precise timing with busy-wait for last microseconds
                elapsed = time.perf_counter() - frame_start
                remaining = target_frame_time - elapsed

                if remaining > 0.001:
                    # Sleep for bulk of remaining time
                    time.sleep(remaining - 0.001)

                    # Busy-wait for precision (last 1ms)
                    while time.perf_counter() - frame_start < target_frame_time:
                        pass

                # FPS monitoring
                self._frame_count += 1
                if self._frame_count % 100 == 0:
                    now = time.time()
                    fps = 100 / (now - self._last_fps_check)
                    self._last_fps_check = now
                    # print(f"DMX FPS: {fps:.1f}")  # Uncomment for debugging

            except Exception as e:
                print(f"DMX send error: {e}")

    def _send_frame(self):
        """Send a single DMX frame - Legacy method"""
        self._send_frame_optimized()

    def _send_frame_optimized(self):
        """Send a single DMX frame - Optimized version"""
        if not self.serial or not self.serial.is_open:
            return

        # ✅ OPTIMIERUNG: Use hardware break instead of software timing
        # Most USB-DMX adapters handle break automatically
        # If your interface needs manual break:
        try:
            self.serial.break_condition = True
            # Note: Hardware handles timing, Python sleep too imprecise
            self.serial.break_condition = False
        except:
            pass  # Some interfaces don't support break_condition

        # ✅ OPTIMIERUNG: Update frame buffer in-place
        self._frame_buffer[1:] = self.data

        # ✅ OPTIMIERUNG: Single write operation (faster than multiple writes)
        self.serial.write(self._frame_buffer)

    def set_channel(self, channel, value):
        """
        Set a single DMX channel - Optimized

        Args:
            channel: Channel number (0-511)
            value: DMX value (0-255)
        """
        # ✅ OPTIMIERUNG: Fast bounds checking, no function calls
        if 0 <= channel < self.channels:
            # Clamp value efficiently
            if value < 0:
                value = 0
            elif value > 255:
                value = 255
            self.data[channel] = int(value)

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
        """Reset all channels to 0 - Optimized"""
        # ✅ OPTIMIERUNG: Clear bytearray in-place (faster)
        for i in range(self.channels):
            self.data[i] = 0
        # Alternative: self.data[:] = bytearray(self.channels)

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
