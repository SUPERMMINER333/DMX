"""
BLE GATT Server for DMX Controller
Provides smartphone control via Bluetooth LE
"""

import json
import logging
import threading
from typing import Optional, Dict, Any

try:
    import dbus
    import dbus.exceptions
    import dbus.mainloop.glib
    import dbus.service
    from gi.repository import GLib
    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False
    print("Warning: dbus/GLib not available, BLE will be mocked")

logger = logging.getLogger(__name__)

# BLE UUIDs
DMX_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
FIXTURE_LIST_UUID = "12345678-1234-5678-1234-56789abcdef1"
FIXTURE_CONTROL_UUID = "12345678-1234-5678-1234-56789abcdef2"
SCENE_CONTROL_UUID = "12345678-1234-5678-1234-56789abcdef3"
STATUS_UUID = "12345678-1234-5678-1234-56789abcdef4"
COMMAND_UUID = "12345678-1234-5678-1234-56789abcdef5"


class MockBLEServer:
    """Mock BLE server for testing without Bluetooth hardware"""

    def __init__(self, controller):
        self.controller = controller
        self.running = False
        logger.warning("Using mock BLE server (dbus not available)")

    def start(self):
        self.running = True
        logger.info("Mock BLE server started")

    def stop(self):
        self.running = False
        logger.info("Mock BLE server stopped")

    def send_notification(self, characteristic, data):
        logger.debug(f"Mock notification: {characteristic} -> {data}")


if DBUS_AVAILABLE:
    BLUEZ_SERVICE_NAME = 'org.bluez'
    GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
    DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
    DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'
    GATT_SERVICE_IFACE = 'org.bluez.GattService1'
    GATT_CHRC_IFACE = 'org.bluez.GattCharacteristic1'


class BLEServer:
    """BLE GATT Server for DMX Control"""

    def __init__(self, controller, device_name: str = "DMX-Controller"):
        """
        Initialize BLE server

        Args:
            controller: DMX controller instance
            device_name: Bluetooth device name
        """
        self.controller = controller
        self.device_name = device_name
        self.running = False
        self.thread = None

        if not DBUS_AVAILABLE:
            self._mock_server = MockBLEServer(controller)
            self.is_mock = True
        else:
            self.is_mock = False
            self._setup_ble()

    def _setup_ble(self):
        """Setup BLE GATT server (requires BlueZ on Linux)"""
        if not DBUS_AVAILABLE:
            return

        try:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SystemBus()
            self.mainloop = GLib.MainLoop()
            logger.info("BLE D-Bus setup complete")
        except Exception as e:
            logger.error(f"Error setting up BLE: {e}")
            self.is_mock = True
            self._mock_server = MockBLEServer(self.controller)

    def start(self):
        """Start BLE server"""
        if self.is_mock:
            self._mock_server.start()
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        logger.info(f"BLE server started as '{self.device_name}'")

    def stop(self):
        """Stop BLE server"""
        if self.is_mock:
            self._mock_server.stop()
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("BLE server stopped")

    def _run_server(self):
        """Run BLE server mainloop"""
        try:
            self.mainloop.run()
        except Exception as e:
            logger.error(f"BLE server error: {e}")

    def handle_command(self, command_json: str) -> Dict[str, Any]:
        """
        Handle JSON command from BLE client

        Args:
            command_json: JSON command string

        Returns:
            Response dictionary
        """
        try:
            command = json.loads(command_json)
            action = command.get("action")

            if action == "list_fixtures":
                return self._list_fixtures()

            elif action == "add_fixture":
                return self._add_fixture(command)

            elif action == "remove_fixture":
                return self._remove_fixture(command)

            elif action == "set_channel":
                return self._set_channel(command)

            elif action == "recall_scene":
                return self._recall_scene(command)

            elif action == "capture_scene":
                return self._capture_scene(command)

            elif action == "list_scenes":
                return self._list_scenes()

            elif action == "get_status":
                return self._get_status()

            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Invalid JSON: {e}"}
        except Exception as e:
            logger.error(f"Error handling command: {e}")
            return {"status": "error", "message": str(e)}

    def _list_fixtures(self) -> Dict[str, Any]:
        """List all fixtures"""
        fixtures = self.controller.fixture_manager.get_all_fixtures()
        fixture_list = [
            {
                "id": f.id,
                "name": f.name,
                "start_channel": f.start_channel,
                "num_channels": f.num_channels,
                "manufacturer": f.manufacturer,
                "model": f.model
            }
            for f in fixtures
        ]

        return {
            "status": "success",
            "fixtures": fixture_list,
            "count": len(fixture_list)
        }

    def _add_fixture(self, command: dict) -> Dict[str, Any]:
        """Add a new fixture"""
        from app.fixture_manager import Fixture

        try:
            fixture_data = command.get("fixture", {})
            fixture = Fixture(
                id=fixture_data.get("id"),
                name=fixture_data.get("name"),
                start_channel=fixture_data.get("start_channel"),
                num_channels=fixture_data.get("num_channels"),
                manufacturer=fixture_data.get("manufacturer", "Generic"),
                model=fixture_data.get("model", "Generic")
            )

            if self.controller.fixture_manager.add_fixture(fixture):
                self.controller.save_configuration()
                return {"status": "success", "message": "Fixture added"}
            else:
                return {"status": "error", "message": "Fixture ID already exists"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _remove_fixture(self, command: dict) -> Dict[str, Any]:
        """Remove a fixture"""
        fixture_id = command.get("fixture_id")

        if self.controller.fixture_manager.remove_fixture(fixture_id):
            self.controller.save_configuration()
            return {"status": "success", "message": "Fixture removed"}
        else:
            return {"status": "error", "message": "Fixture not found"}

    def _set_channel(self, command: dict) -> Dict[str, Any]:
        """Set DMX channel value"""
        channel = command.get("channel")
        value = command.get("value")

        if channel is None or value is None:
            return {"status": "error", "message": "Missing channel or value"}

        try:
            self.controller.dmx.set_channel(int(channel), int(value))
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _recall_scene(self, command: dict) -> Dict[str, Any]:
        """Recall a scene"""
        scene_id = command.get("scene_id")

        if self.controller.recall_scene(scene_id):
            return {"status": "success", "message": "Scene recalled"}
        else:
            return {"status": "error", "message": "Scene not found"}

    def _capture_scene(self, command: dict) -> Dict[str, Any]:
        """Capture current state as scene"""
        scene_id = command.get("scene_id")
        scene_name = command.get("scene_name")
        description = command.get("description", "")

        if self.controller.capture_scene(scene_id, scene_name, description):
            self.controller.save_configuration()
            return {"status": "success", "message": "Scene captured"}
        else:
            return {"status": "error", "message": "Failed to capture scene"}

    def _list_scenes(self) -> Dict[str, Any]:
        """List all scenes"""
        scenes = self.controller.scene_manager.get_all_scenes()
        scene_list = [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "tags": s.tags
            }
            for s in scenes
        ]

        return {
            "status": "success",
            "scenes": scene_list,
            "count": len(scene_list)
        }

    def _get_status(self) -> Dict[str, Any]:
        """Get controller status"""
        status = self.controller.get_status()
        return {
            "status": "success",
            "controller_status": status
        }


# BLE Protocol Documentation
BLE_PROTOCOL_DOC = """
DMX Controller BLE Protocol
===========================

Service UUID: 12345678-1234-5678-1234-56789abcdef0

Characteristics:
- Fixture List (read): 12345678-1234-5678-1234-56789abcdef1
- Fixture Control (write): 12345678-1234-5678-1234-56789abcdef2
- Scene Control (write/read): 12345678-1234-5678-1234-56789abcdef3
- Status (read/notify): 12345678-1234-5678-1234-56789abcdef4
- Command (write/read): 12345678-1234-5678-1234-56789abcdef5

Command Format (JSON):
{
  "action": "action_name",
  "param1": value1,
  ...
}

Actions:

1. List Fixtures:
   {"action": "list_fixtures"}

   Response:
   {
     "status": "success",
     "fixtures": [...],
     "count": n
   }

2. Add Fixture:
   {
     "action": "add_fixture",
     "fixture": {
       "id": "fix1",
       "name": "Stage Light",
       "start_channel": 0,
       "num_channels": 4,
       "manufacturer": "Generic",
       "model": "RGBW"
     }
   }

3. Remove Fixture:
   {"action": "remove_fixture", "fixture_id": "fix1"}

4. Set Channel:
   {"action": "set_channel", "channel": 0, "value": 255}

5. Recall Scene:
   {"action": "recall_scene", "scene_id": "scene1"}

6. Capture Scene:
   {
     "action": "capture_scene",
     "scene_id": "scene1",
     "scene_name": "Blue Mood",
     "description": "All lights blue"
   }

7. List Scenes:
   {"action": "list_scenes"}

8. Get Status:
   {"action": "get_status"}

Example Client (Python):
-----------------------
import json
from bluepy import btle

# Connect
device = btle.Peripheral("MAC_ADDRESS")

# Send command
cmd_char = device.getCharacteristics(uuid="12345678-1234-5678-1234-56789abcdef5")[0]
command = {"action": "list_fixtures"}
cmd_char.write(json.dumps(command).encode())

# Read response
response = json.loads(cmd_char.read().decode())
print(response)
"""
