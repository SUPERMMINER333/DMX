"""
OLED Display Manager
Handles rendering to OLED display
"""

try:
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    from luma.oled.device import sh1106, ssd1306
    from PIL import ImageFont, ImageDraw, Image
    LUMA_AVAILABLE = True
except ImportError:
    LUMA_AVAILABLE = False
    print("Warning: luma.oled not available, display will be mocked")

import logging

logger = logging.getLogger(__name__)


class MockDevice:
    """Mock display for testing without hardware"""
    def __init__(self):
        self.width = 128
        self.height = 64
        self.mode = "1"

    def clear(self):
        pass

    def show(self):
        pass

    def display(self, image):
        pass


class Display:
    """OLED display manager"""

    def __init__(self, device_type: str = "ssd1306", address: int = 0x3C, port: int = 1):
        """
        Initialize display

        Args:
            device_type: Display type (ssd1306 or sh1106)
            address: I2C address
            port: I2C port
        """
        self.device_type = device_type
        self.address = address
        self.port = port
        self.device = None

        try:
            if LUMA_AVAILABLE:
                serial = i2c(port=port, address=address)

                if device_type == "sh1106":
                    self.device = sh1106(serial)
                else:
                    self.device = ssd1306(serial)

                logger.info(f"Display initialized: {device_type} at 0x{address:02X}")
            else:
                self.device = MockDevice()
                logger.warning("Using mock display (luma.oled not available)")

        except Exception as e:
            logger.error(f"Error initializing display: {e}")
            self.device = MockDevice()

        # Load font
        try:
            self.font = ImageFont.truetype("FreeSans.ttf", 13)
            self.font_small = ImageFont.truetype("FreeSans.ttf", 10)
        except Exception:
            try:
                self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
                self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
            except Exception:
                logger.warning("TrueType font not found, using default")
                self.font = ImageFont.load_default()
                self.font_small = ImageFont.load_default()

    def clear(self):
        """Clear the display"""
        if self.device:
            self.device.clear()

    def draw_text(self, text: str, x: int = 0, y: int = 0, font=None):
        """
        Draw text on display

        Args:
            text: Text to draw
            x: X position
            y: Y position
            font: Font to use (default: self.font)
        """
        if not self.device:
            return

        if font is None:
            font = self.font

        with canvas(self.device) as draw:
            draw.text((x, y), text, font=font, fill="white")

    def draw_lines(self, lines: list, start_y: int = 0, font=None, line_height: int = 14):
        """
        Draw multiple lines of text

        Args:
            lines: List of text lines
            start_y: Starting Y position
            font: Font to use
            line_height: Height between lines
        """
        if not self.device:
            return

        if font is None:
            font = self.font

        with canvas(self.device) as draw:
            y = start_y
            for line in lines:
                if y < self.device.height:
                    draw.text((0, y), str(line), font=font, fill="white")
                    y += line_height

    def draw_menu(self, title: str, items: list, selected_index: int = 0):
        """
        Draw a menu with title and selectable items

        Args:
            title: Menu title
            items: List of menu items
            selected_index: Index of selected item
        """
        if not self.device:
            return

        with canvas(self.device) as draw:
            # Draw title bar
            draw.rectangle([(0, 0), (self.device.width, 14)], fill="white")
            draw.text((2, 0), title, font=self.font_small, fill="black")

            # Draw menu items
            y = 16
            visible_items = 4  # How many items fit on screen
            start_idx = max(0, selected_index - visible_items + 1)

            for i, item in enumerate(items[start_idx:start_idx + visible_items]):
                actual_idx = start_idx + i
                prefix = "> " if actual_idx == selected_index else "  "
                text = f"{prefix}{item}"

                # Truncate if too long
                if len(text) > 20:
                    text = text[:17] + "..."

                draw.text((2, y), text, font=self.font_small, fill="white")
                y += 12

    def draw_status(self, status_dict: dict):
        """
        Draw status information

        Args:
            status_dict: Dictionary of status items
        """
        if not self.device:
            return

        lines = []
        for key, value in status_dict.items():
            lines.append(f"{key}: {value}")

        self.draw_lines(lines, font=self.font_small, line_height=12)

    def draw_fixture_info(self, fixture_name: str, channels: dict):
        """
        Draw fixture information

        Args:
            fixture_name: Name of fixture
            channels: Dictionary of channel values {name: value}
        """
        if not self.device:
            return

        with canvas(self.device) as draw:
            # Title
            draw.rectangle([(0, 0), (self.device.width, 14)], fill="white")
            draw.text((2, 0), fixture_name[:18], font=self.font_small, fill="black")

            # Channels
            y = 16
            for name, value in list(channels.items())[:4]:
                bar_width = int((value / 255.0) * 100)
                draw.text((2, y), f"{name[:6]}", font=self.font_small, fill="white")
                draw.rectangle([(50, y + 2), (50 + bar_width, y + 10)], fill="white")
                draw.text((105, y), f"{value:3d}", font=self.font_small, fill="white")
                y += 12

    def show_message(self, message: str, duration: float = 2.0):
        """
        Show a temporary message

        Args:
            message: Message to display
            duration: How long to show (seconds)
        """
        if not self.device:
            return

        import time

        with canvas(self.device) as draw:
            # Center the message
            lines = message.split('\n')
            y = (self.device.height - len(lines) * 14) // 2

            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=self.font)
                text_width = bbox[2] - bbox[0]
                x = (self.device.width - text_width) // 2
                draw.text((x, y), line, font=self.font, fill="white")
                y += 14

        time.sleep(duration)
        self.clear()
