"""
Rotary Encoder Library
Handles rotary encoder inputs with button support
"""

try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    # Mock GPIO for development/testing
    class MockGPIO:
        BCM = "BCM"
        IN = "IN"
        PUD_UP = "PUD_UP"
        RISING = "RISING"
        FALLING = "FALLING"
        BOTH = "BOTH"

        def setmode(self, mode): pass
        def setup(self, pin, mode, pull_up_down=None): pass
        def add_event_detect(self, pin, edge, callback=None, bouncetime=None): pass
        def input(self, pin): return 1
        def cleanup(self): pass

    GPIO = MockGPIO()

import threading
import time


class REnc:
    """Rotary Encoder Base Class"""

    def __init__(self, pin_a, pin_b, pin_btn):
        """
        Initialize rotary encoder

        Args:
            pin_a: GPIO pin for encoder A
            pin_b: GPIO pin for encoder B
            pin_btn: GPIO pin for button
        """
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.pin_btn = pin_btn

        self.last_a = 1
        self.last_b = 1
        self.button_pressed = False
        self.button_time = 0

        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin_btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Add event detection
        GPIO.add_event_detect(self.pin_a, GPIO.BOTH, callback=self._rotation_callback, bouncetime=2)
        GPIO.add_event_detect(self.pin_btn, GPIO.BOTH, callback=self._button_callback, bouncetime=50)

    def _rotation_callback(self, channel):
        """Handle rotation events"""
        a = GPIO.input(self.pin_a)
        b = GPIO.input(self.pin_b)

        if a != self.last_a:
            if b != a:
                self.right()
            else:
                self.left()

        self.last_a = a
        self.last_b = b

    def _button_callback(self, channel):
        """Handle button events"""
        state = GPIO.input(self.pin_btn)

        if state == 0:  # Button pressed (active low)
            self.button_pressed = True
            self.button_time = time.time()
            self.pressed()
        else:  # Button released
            if self.button_pressed:
                press_duration = time.time() - self.button_time
                self.button_pressed = False
                self.released()

                # Optional: detect long press
                if press_duration > 1.0:
                    self.long_press()

    def right(self):
        """Called when encoder rotates right - override in subclass"""
        pass

    def left(self):
        """Called when encoder rotates left - override in subclass"""
        pass

    def pressed(self):
        """Called when button is pressed - override in subclass"""
        pass

    def released(self):
        """Called when button is released - override in subclass"""
        pass

    def long_press(self):
        """Called on long button press - override in subclass"""
        pass

    def cleanup(self):
        """Cleanup GPIO resources"""
        GPIO.cleanup()
