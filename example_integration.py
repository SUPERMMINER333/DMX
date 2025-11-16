#!/usr/bin/env python3
"""
Example Integration with Existing Code
Shows how to use the existing code snippet with the new system
"""

import ADS1115
import time
from lib import dmx as lib
from lib import renc as renc
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106, ssd1306
from PIL import ImageFont, ImageDraw, Image
from lib.poti import Poti as poti


class REncCtrl(renc.REnc):
    """
    Rotary Encoder Controller (from original code)
    This is your existing implementation
    """
    def __init__(self, pin_a, pin_b, pin_btn, dmx):
        super().__init__(pin_a, pin_b, pin_btn)
        self.dmx = dmx

    def right(self):
        print("right")
        self.dmx.inc_channel(2)
        print("inc")

    def left(self):
        print("left")
        self.dmx.dec_channel(2)

    def pressed(self):
        print("pressed")

    def released(self):
        print("released")
        self.dmx.set_channel(0, 0)


def run_original_code():
    """
    Run the original code exactly as provided
    This demonstrates compatibility with the existing DMX library
    """
    ads = ADS1115.ADS1115()

    serial = i2c(port=1, address=0x3C)
    device = ssd1306(serial)

    oled_font = ImageFont.truetype("FreeSans.ttf", 13)

    dmx = lib.Dmx(port="/dev/ttyUSB0")
    dmx.start()

    dmx.reset()
    dmx.set_channels([0], 255)

    re = REncCtrl(15, 18, 17, dmx)

    po = poti(ads)

    # Channel mapping
    # 0: rechts
    # 1: rechts mitte
    # 2: links
    # 3: links mitte

    # ch0:red
    # ch1:blue
    # ch2:green
    # ch3:white
    dic = {0: 0, 1: 3, 2: 1, 3: 2}

    while True:
        for i in range(4):
            dmx.set_data(po.read_all(i), dic[i])


def run_with_new_system():
    """
    Run using the new fixture management system
    This shows how to use fixtures instead of manual channel mapping
    """
    from app.controller import DMXController
    from app.fixture_manager import create_rgbw_fixture
    from app.storage import Storage

    # Load settings
    storage = Storage()
    settings = storage.load_settings()

    # Create controller
    controller = DMXController(settings)

    # Add an RGBW fixture
    fixture = create_rgbw_fixture(
        fixture_id="main_light",
        name="Main Stage Light",
        start_channel=0  # Starts at channel 0
    )

    controller.fixture_manager.add_fixture(fixture)
    controller.save_configuration()

    # Start DMX
    controller.start()

    # Select the fixture for control
    controller.select_fixture("main_light")

    # Setup hardware
    ads = ADS1115.ADS1115()
    po = poti(ads)

    # Main loop - potis control the selected fixture
    try:
        while True:
            controller.update_from_potis(po)
            time.sleep(0.05)
    except KeyboardInterrupt:
        controller.stop()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--original":
        print("Running original code...")
        run_original_code()
    else:
        print("Running with new fixture system...")
        print("Use --original flag to run original code")
        run_with_new_system()
