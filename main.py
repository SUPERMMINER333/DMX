#!/usr/bin/env python3
"""
DMX Controller Main Service
Integrates all components: DMX, fixtures, encoders, potis, OLED, BLE
"""

import time
import signal
import logging
import sys
from pathlib import Path

# Mock hardware imports for when not on Raspberry Pi
try:
    import ADS1115
    ADS_AVAILABLE = True
except ImportError:
    ADS_AVAILABLE = False
    print("Warning: ADS1115 not available, using mock")

    class MockADS:
        """Mock ADS1115 for testing"""
        def readADCSingleEnded(self, channel):
            return 2048  # Mid-range value

    class MockADSModule:
        @staticmethod
        def ADS1115():
            return MockADS()

    ADS1115 = MockADSModule()

from lib.poti import Poti
from app.controller import DMXController, EncoderController
from app.storage import Storage
from ui.display import Display
from ui.oled_menu import MenuSystem
from ble.server import BLEServer


# Configure logging
def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    log_dir = Path("/home/user/DMX/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "dmx_controller.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )


logger = logging.getLogger(__name__)


class DMXService:
    """Main DMX Controller Service"""

    def __init__(self):
        """Initialize the service"""
        self.running = False
        self.storage = Storage()
        self.settings = self.storage.load_settings()

        # Setup logging
        setup_logging(self.settings.get("log_level", "INFO"))

        # Components
        self.controller = None
        self.display = None
        self.menu_system = None
        self.ble_server = None
        self.poti = None
        self.encoders = []

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("DMX Service initialized")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)

    def start(self):
        """Start all components"""
        try:
            logger.info("Starting DMX Controller Service...")

            # Initialize DMX controller
            self.controller = DMXController(self.settings)
            self.controller.start()

            # Initialize OLED display
            oled_type = self.settings.get("oled_type", "ssd1306")
            oled_addr = int(self.settings.get("oled_address", "0x3C"), 16)

            self.display = Display(device_type=oled_type, address=oled_addr)
            self.display.show_message("DMX Controller\nStarting...")

            # Initialize menu system
            self.menu_system = MenuSystem(self.display, self.controller)

            # Initialize ADS1115 and potentiometers
            if ADS_AVAILABLE:
                ads = ADS1115.ADS1115()
            else:
                ads = ADS1115.ADS1115()  # Mock

            self.poti = Poti(ads)

            # Initialize rotary encoders
            self._setup_encoders()

            # Initialize BLE server
            self.ble_server = BLEServer(self.controller, device_name="DMX-Pi")
            self.ble_server.start()

            self.running = True

            # Display startup info
            self.display.show_message("DMX Controller\nReady!", 2.0)
            self.menu_system.render()

            logger.info("All components started successfully")

            # Run main loop
            self._main_loop()

        except Exception as e:
            logger.error(f"Error starting service: {e}", exc_info=True)
            self.stop()
            raise

    def _setup_encoders(self):
        """Setup rotary encoders"""
        encoder_pins = self.settings.get("encoder_pins", {})

        for encoder_id, pins in encoder_pins.items():
            try:
                encoder = EncoderController(
                    pin_a=pins["a"],
                    pin_b=pins["b"],
                    pin_btn=pins["btn"],
                    dmx_controller=self.controller,
                    encoder_id=int(encoder_id.split("_")[1]) - 1  # Extract ID number
                )
                self.encoders.append(encoder)
                logger.info(f"Encoder {encoder_id} initialized on pins A:{pins['a']}, B:{pins['b']}, BTN:{pins['btn']}")
            except Exception as e:
                logger.warning(f"Could not initialize encoder {encoder_id}: {e}")

    def _main_loop(self):
        """Main service loop - Optimized"""
        logger.info("Entering main loop")

        # ✅ OPTIMIERUNG: Faster update rate (20ms = 50 Hz)
        update_interval = 0.020  # 20ms instead of 50ms
        display_update_counter = 0
        display_update_interval = 50  # Update display every 50 iterations (1 second)

        # ✅ OPTIMIERUNG: Use perf_counter for precise timing
        last_update = time.perf_counter()

        try:
            while self.running:
                loop_start = time.perf_counter()

                # Update DMX from potentiometers
                if self.poti and self.controller.dmx:
                    self.controller.update_from_potis(self.poti)

                # Update display periodically
                display_update_counter += 1
                if display_update_counter >= display_update_interval:
                    display_update_counter = 0
                    self._update_display()

                # ✅ OPTIMIERUNG: Precise sleep with busy-wait
                elapsed = time.perf_counter() - loop_start
                remaining = update_interval - elapsed

                if remaining > 0.002:
                    time.sleep(remaining - 0.001)  # Sleep most of the time

                # Busy-wait for precision (last 1-2ms)
                while time.perf_counter() - loop_start < update_interval:
                    pass

        except KeyboardInterrupt:
            logger.info("Service interrupted by user")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.stop()

    def _update_display(self):
        """Update display with current status"""
        try:
            if self.controller.mode == "menu":
                # Menu mode - menu system handles display
                pass
            elif self.controller.mode == "fixture" and self.controller.selected_fixture:
                # Show selected fixture info
                fixture = self.controller.selected_fixture
                channels = {}

                for i, mapping in enumerate(fixture.channel_mappings[:4]):
                    dmx_ch = fixture.get_dmx_channel(mapping.channel_offset)
                    value = self.controller.dmx.get_channel(dmx_ch) if self.controller.dmx else 0
                    channels[mapping.name] = value

                self.display.draw_fixture_info(fixture.name, channels)
            else:
                # Show general status
                status = {
                    "Mode": self.controller.mode,
                    "Fixtures": len(self.controller.fixture_manager.fixtures),
                    "Scenes": len(self.controller.scene_manager.scenes),
                    "DMX": "Connected" if self.controller.dmx and self.controller.dmx.running else "Disconnected"
                }
                self.display.draw_status(status)

        except Exception as e:
            logger.error(f"Error updating display: {e}")

    def stop(self):
        """Stop all components"""
        logger.info("Stopping DMX Controller Service...")
        self.running = False

        # Save configuration
        if self.controller:
            self.controller.save_configuration()

        # Stop BLE server
        if self.ble_server:
            self.ble_server.stop()

        # Stop DMX controller
        if self.controller:
            self.controller.stop()

        # Cleanup encoders
        for encoder in self.encoders:
            try:
                encoder.cleanup()
            except:
                pass

        # Clear display
        if self.display:
            self.display.show_message("Shutdown", 1.0)
            self.display.clear()

        logger.info("DMX Service stopped")


def main():
    """Main entry point"""
    print("""
    ╔════════════════════════════════════════╗
    ║     DMX Controller Service v1.0        ║
    ║     Raspberry Pi DMX Control System    ║
    ╚════════════════════════════════════════╝
    """)

    service = DMXService()

    try:
        service.start()
    except KeyboardInterrupt:
        print("\nService interrupted")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
