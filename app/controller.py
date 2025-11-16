"""
Main DMX Controller
Coordinates all components: DMX, fixtures, encoders, potentiometers, OLED
"""

import time
import logging
from typing import Optional, Dict, List
from lib import dmx as dmx_lib
from lib import renc
from lib.poti import Poti
from app.fixture_manager import FixtureManager, Fixture
from app.scene_manager import SceneManager
from app.storage import Storage

logger = logging.getLogger(__name__)


class ControlMode:
    """Control modes for the controller"""
    DIRECT = "direct"  # Direct potentiometer control
    FIXTURE = "fixture"  # Fixture-based control
    SCENE = "scene"  # Scene recall
    MENU = "menu"  # Menu navigation


class DMXController:
    """Main DMX controller coordinating all components"""

    def __init__(self, settings: dict):
        """
        Initialize controller

        Args:
            settings: Configuration settings
        """
        self.settings = settings
        self.running = False

        # Initialize components
        self.dmx: Optional[dmx_lib.Dmx] = None
        self.fixture_manager = FixtureManager()
        self.scene_manager = SceneManager()
        self.storage = Storage()

        # Control state
        self.mode = ControlMode.DIRECT
        self.selected_fixture: Optional[Fixture] = None
        self.selected_scene_id: Optional[str] = None

        # Potentiometer mapping (poti index -> DMX channel or fixture channel)
        self.poti_mapping: Dict[int, int] = {0: 0, 1: 3, 2: 1, 3: 2}

        # Encoder assignments
        self.encoder_functions = {
            0: "menu_navigate",  # Navigate menu
            1: "fixture_select",  # Select fixture
            2: "channel_adjust",  # Adjust channel value
            3: "mode_select"  # Select control mode
        }

        logger.info("DMX Controller initialized")

    def start(self):
        """Start the controller"""
        try:
            # Initialize DMX
            dmx_port = self.settings.get("dmx_port", "/dev/ttyUSB0")
            dmx_baudrate = self.settings.get("dmx_baudrate", 250000)

            self.dmx = dmx_lib.Dmx(port=dmx_port, baudrate=dmx_baudrate)
            self.dmx.start()
            logger.info(f"DMX started on {dmx_port}")

            # Load fixtures and scenes
            self.load_configuration()

            self.running = True
            logger.info("Controller started")

        except Exception as e:
            logger.error(f"Error starting controller: {e}")
            raise

    def stop(self):
        """Stop the controller"""
        self.running = False

        if self.dmx:
            self.dmx.stop()

        logger.info("Controller stopped")

    def load_configuration(self):
        """Load fixtures and scenes from storage"""
        try:
            # Load fixtures
            fixture_data = self.storage.load_fixtures()
            if fixture_data:
                self.fixture_manager.from_dict(fixture_data)
                logger.info(f"Loaded {len(self.fixture_manager.fixtures)} fixtures")

            # Load scenes
            scene_data = self.storage.load_scenes()
            if scene_data:
                self.scene_manager.from_dict(scene_data)
                logger.info(f"Loaded {len(self.scene_manager.scenes)} scenes")

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")

    def save_configuration(self):
        """Save fixtures and scenes to storage"""
        try:
            self.storage.save_fixtures(self.fixture_manager.to_dict())
            self.storage.save_scenes(self.scene_manager.to_dict())
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def set_poti_mapping(self, poti_index: int, channel: int):
        """
        Set potentiometer to DMX channel mapping

        Args:
            poti_index: Potentiometer index (0-3)
            channel: DMX channel to control
        """
        if 0 <= poti_index <= 3:
            self.poti_mapping[poti_index] = channel
            logger.debug(f"Poti {poti_index} -> Channel {channel}")

    def update_from_potis(self, poti: Poti):
        """
        Update DMX channels from potentiometer values

        Args:
            poti: Potentiometer instance
        """
        if not self.dmx:
            return

        for poti_idx in range(4):
            value = poti.read_all(poti_idx)
            channel = self.poti_mapping.get(poti_idx, poti_idx)

            if self.mode == ControlMode.DIRECT:
                # Direct DMX channel control
                self.dmx.set_data(value, channel)

            elif self.mode == ControlMode.FIXTURE and self.selected_fixture:
                # Control selected fixture's channels
                if poti_idx < self.selected_fixture.num_channels:
                    dmx_channel = self.selected_fixture.get_dmx_channel(poti_idx)
                    self.dmx.set_channel(dmx_channel, value)

    def select_fixture(self, fixture_id: str) -> bool:
        """
        Select a fixture for control

        Args:
            fixture_id: Fixture ID

        Returns:
            True if successful
        """
        fixture = self.fixture_manager.get_fixture(fixture_id)
        if fixture:
            self.selected_fixture = fixture
            self.mode = ControlMode.FIXTURE
            logger.info(f"Selected fixture: {fixture.name}")
            return True
        return False

    def next_fixture(self):
        """Select next fixture in list"""
        fixtures = self.fixture_manager.get_all_fixtures()
        if not fixtures:
            return

        if self.selected_fixture:
            try:
                current_idx = fixtures.index(self.selected_fixture)
                next_idx = (current_idx + 1) % len(fixtures)
                self.selected_fixture = fixtures[next_idx]
            except ValueError:
                self.selected_fixture = fixtures[0]
        else:
            self.selected_fixture = fixtures[0]

        logger.info(f"Selected fixture: {self.selected_fixture.name}")

    def previous_fixture(self):
        """Select previous fixture in list"""
        fixtures = self.fixture_manager.get_all_fixtures()
        if not fixtures:
            return

        if self.selected_fixture:
            try:
                current_idx = fixtures.index(self.selected_fixture)
                prev_idx = (current_idx - 1) % len(fixtures)
                self.selected_fixture = fixtures[prev_idx]
            except ValueError:
                self.selected_fixture = fixtures[-1]
        else:
            self.selected_fixture = fixtures[-1]

        logger.info(f"Selected fixture: {self.selected_fixture.name}")

    def recall_scene(self, scene_id: str) -> bool:
        """
        Recall a scene

        Args:
            scene_id: Scene ID

        Returns:
            True if successful
        """
        if self.scene_manager.recall_scene(scene_id, self.dmx):
            self.selected_scene_id = scene_id
            return True
        return False

    def capture_scene(self, scene_id: str, name: str, description: str = "") -> bool:
        """
        Capture current state as a scene

        Args:
            scene_id: Unique scene ID
            name: Scene name
            description: Optional description

        Returns:
            True if successful
        """
        if not self.dmx:
            return False

        try:
            self.scene_manager.capture_scene(
                scene_id=scene_id,
                name=name,
                dmx_data=self.dmx.data,
                description=description
            )
            return True
        except Exception as e:
            logger.error(f"Error capturing scene: {e}")
            return False

    def blackout(self):
        """Set all channels to 0"""
        if self.dmx:
            self.dmx.reset()
            logger.info("Blackout")

    def set_mode(self, mode: str):
        """
        Set control mode

        Args:
            mode: Control mode (ControlMode constant)
        """
        self.mode = mode
        logger.info(f"Mode changed to: {mode}")

    def get_status(self) -> dict:
        """
        Get current controller status

        Returns:
            Status dictionary
        """
        return {
            "running": self.running,
            "mode": self.mode,
            "fixtures_count": len(self.fixture_manager.fixtures),
            "scenes_count": len(self.scene_manager.scenes),
            "selected_fixture": self.selected_fixture.name if self.selected_fixture else None,
            "selected_scene": self.selected_scene_id,
            "dmx_connected": self.dmx is not None and self.dmx.running
        }


class EncoderController(renc.REnc):
    """Rotary encoder integrated with DMX controller"""

    def __init__(self, pin_a: int, pin_b: int, pin_btn: int, dmx_controller: DMXController, encoder_id: int):
        """
        Initialize encoder controller

        Args:
            pin_a: GPIO pin A
            pin_b: GPIO pin B
            pin_btn: GPIO pin for button
            dmx_controller: Main DMX controller
            encoder_id: Encoder ID (0-3)
        """
        super().__init__(pin_a, pin_b, pin_btn)
        self.controller = dmx_controller
        self.encoder_id = encoder_id
        self.function = dmx_controller.encoder_functions.get(encoder_id, "generic")

    def right(self):
        """Handle right rotation"""
        if self.function == "fixture_select":
            self.controller.next_fixture()
        elif self.function == "channel_adjust" and self.controller.dmx:
            self.controller.dmx.inc_channel(2)
        elif self.function == "menu_navigate":
            # Menu navigation handled by OLED menu system
            pass

        logger.debug(f"Encoder {self.encoder_id} right")

    def left(self):
        """Handle left rotation"""
        if self.function == "fixture_select":
            self.controller.previous_fixture()
        elif self.function == "channel_adjust" and self.controller.dmx:
            self.controller.dmx.dec_channel(2)
        elif self.function == "menu_navigate":
            # Menu navigation handled by OLED menu system
            pass

        logger.debug(f"Encoder {self.encoder_id} left")

    def pressed(self):
        """Handle button press"""
        logger.debug(f"Encoder {self.encoder_id} pressed")

    def released(self):
        """Handle button release"""
        if self.function == "channel_adjust" and self.controller.dmx:
            self.controller.dmx.set_channel(0, 0)

        logger.debug(f"Encoder {self.encoder_id} released")

    def long_press(self):
        """Handle long button press"""
        if self.function == "mode_select":
            # Cycle through modes
            modes = [ControlMode.DIRECT, ControlMode.FIXTURE, ControlMode.SCENE, ControlMode.MENU]
            try:
                current_idx = modes.index(self.controller.mode)
                next_idx = (current_idx + 1) % len(modes)
                self.controller.set_mode(modes[next_idx])
            except ValueError:
                self.controller.set_mode(ControlMode.DIRECT)

        logger.debug(f"Encoder {self.encoder_id} long press")
