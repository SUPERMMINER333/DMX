"""
Fixture Profile Library
Pre-defined fixture profiles for common DMX devices
"""

from app.fixture_manager import (
    Fixture, ChannelMapping, ChannelRange, ChannelType,
    create_simple_rgb_fixture, create_rgbw_fixture
)
from typing import Dict, List


class FixtureLibrary:
    """Library of pre-defined fixture profiles"""

    def __init__(self):
        self.profiles: Dict[str, dict] = {}
        self._load_builtin_profiles()

    def _load_builtin_profiles(self):
        """Load built-in fixture profiles"""

        # ===== Generic Fixtures =====

        self.profiles["generic_rgb"] = {
            "name": "Generic RGB",
            "manufacturer": "Generic",
            "model": "RGB 3-Channel",
            "num_channels": 3,
            "mappings": [
                {"offset": 0, "type": "red", "name": "Red"},
                {"offset": 1, "type": "green", "name": "Green"},
                {"offset": 2, "type": "blue", "name": "Blue"}
            ]
        }

        self.profiles["generic_rgbw"] = {
            "name": "Generic RGBW",
            "manufacturer": "Generic",
            "model": "RGBW 4-Channel",
            "num_channels": 4,
            "mappings": [
                {"offset": 0, "type": "red", "name": "Red"},
                {"offset": 1, "type": "green", "name": "Green"},
                {"offset": 2, "type": "blue", "name": "Blue"},
                {"offset": 3, "type": "white", "name": "White"}
            ]
        }

        self.profiles["generic_dimmer"] = {
            "name": "Generic Dimmer",
            "manufacturer": "Generic",
            "model": "Single Channel Dimmer",
            "num_channels": 1,
            "mappings": [
                {"offset": 0, "type": "dimmer", "name": "Dimmer"}
            ]
        }

        # ===== PAR Cans =====

        self.profiles["par_rgbw_8ch"] = {
            "name": "PAR RGBW 8-Channel",
            "manufacturer": "Generic",
            "model": "PAR Can RGBW",
            "num_channels": 8,
            "mappings": [
                {"offset": 0, "type": "dimmer", "name": "Master Dimmer"},
                {"offset": 1, "type": "red", "name": "Red"},
                {"offset": 2, "type": "green", "name": "Green"},
                {"offset": 3, "type": "blue", "name": "Blue"},
                {"offset": 4, "type": "white", "name": "White"},
                {"offset": 5, "type": "strobe", "name": "Strobe"},
                {"offset": 6, "type": "effect", "name": "Color Macro"},
                {"offset": 7, "type": "speed", "name": "Macro Speed"}
            ]
        }

        # ===== Moving Heads =====

        self.profiles["moving_head_basic"] = {
            "name": "Moving Head Basic",
            "manufacturer": "Generic",
            "model": "Moving Head 8-Channel",
            "num_channels": 8,
            "mappings": [
                {"offset": 0, "type": "pan", "name": "Pan"},
                {"offset": 1, "type": "tilt", "name": "Tilt"},
                {"offset": 2, "type": "speed", "name": "Pan/Tilt Speed"},
                {"offset": 3, "type": "dimmer", "name": "Dimmer"},
                {"offset": 4, "type": "strobe", "name": "Strobe"},
                {
                    "offset": 5,
                    "type": "color_wheel",
                    "name": "Color Wheel",
                    "ranges": [
                        (0, 15, "Open/White", ""),
                        (16, 31, "Red", ""),
                        (32, 47, "Orange", ""),
                        (48, 63, "Yellow", ""),
                        (64, 79, "Green", ""),
                        (80, 95, "Blue", ""),
                        (96, 111, "Light Blue", ""),
                        (112, 127, "Pink", ""),
                        (128, 255, "Rainbow", "Rainbow effect")
                    ]
                },
                {
                    "offset": 6,
                    "type": "gobo",
                    "name": "Gobo Wheel",
                    "ranges": [
                        (0, 15, "Open", ""),
                        (16, 31, "Gobo 1", ""),
                        (32, 47, "Gobo 2", ""),
                        (48, 63, "Gobo 3", ""),
                        (64, 79, "Gobo 4", ""),
                        (80, 95, "Gobo 5", ""),
                        (96, 111, "Gobo 6", ""),
                        (112, 255, "Gobo Rotate", "")
                    ]
                },
                {"offset": 7, "type": "generic", "name": "Control/Reset"}
            ]
        }

        # ===== LED Bars =====

        self.profiles["led_bar_rgb"] = {
            "name": "LED Bar RGB (4 Segments)",
            "manufacturer": "Generic",
            "model": "LED Bar 12-Channel",
            "num_channels": 12,
            "mappings": [
                # Segment 1
                {"offset": 0, "type": "red", "name": "Seg1 Red"},
                {"offset": 1, "type": "green", "name": "Seg1 Green"},
                {"offset": 2, "type": "blue", "name": "Seg1 Blue"},
                # Segment 2
                {"offset": 3, "type": "red", "name": "Seg2 Red"},
                {"offset": 4, "type": "green", "name": "Seg2 Green"},
                {"offset": 5, "type": "blue", "name": "Seg2 Blue"},
                # Segment 3
                {"offset": 6, "type": "red", "name": "Seg3 Red"},
                {"offset": 7, "type": "green", "name": "Seg3 Green"},
                {"offset": 8, "type": "blue", "name": "Seg3 Blue"},
                # Segment 4
                {"offset": 9, "type": "red", "name": "Seg4 Red"},
                {"offset": 10, "type": "green", "name": "Seg4 Green"},
                {"offset": 11, "type": "blue", "name": "Seg4 Blue"}
            ]
        }

        # ===== Stroboscopes =====

        self.profiles["strobe_basic"] = {
            "name": "Strobe Basic",
            "manufacturer": "Generic",
            "model": "Strobe 2-Channel",
            "num_channels": 2,
            "mappings": [
                {"offset": 0, "type": "dimmer", "name": "Dimmer"},
                {
                    "offset": 1,
                    "type": "strobe",
                    "name": "Strobe",
                    "ranges": [
                        (0, 10, "Off", ""),
                        (11, 255, "Strobe", "Slow to Fast")
                    ]
                }
            ]
        }

        # ===== Laser =====

        self.profiles["laser_rgb"] = {
            "name": "Laser RGB",
            "manufacturer": "Generic",
            "model": "Laser RGB",
            "num_channels": 7,
            "mappings": [
                {"offset": 0, "type": "generic", "name": "Mode"},
                {"offset": 1, "type": "red", "name": "Red Pattern"},
                {"offset": 2, "type": "green", "name": "Green Pattern"},
                {"offset": 3, "type": "generic", "name": "Pattern Rotation"},
                {"offset": 4, "type": "generic", "name": "Horizontal Move"},
                {"offset": 5, "type": "generic", "name": "Vertical Move"},
                {"offset": 6, "type": "speed", "name": "Move Speed"}
            ]
        }

        # ===== Fog Machine =====

        self.profiles["fog_machine"] = {
            "name": "Fog Machine",
            "manufacturer": "Generic",
            "model": "Fog 1-Channel",
            "num_channels": 1,
            "mappings": [
                {
                    "offset": 0,
                    "type": "generic",
                    "name": "Fog Output",
                    "ranges": [
                        (0, 5, "Off", ""),
                        (6, 255, "Fog", "Low to High")
                    ]
                }
            ]
        }

    def get_profile(self, profile_id: str) -> dict:
        """Get a fixture profile"""
        return self.profiles.get(profile_id, {})

    def list_profiles(self) -> List[str]:
        """List all available profile IDs"""
        return list(self.profiles.keys())

    def search_profiles(self, keyword: str) -> List[str]:
        """
        Search profiles by keyword

        Args:
            keyword: Search term

        Returns:
            List of matching profile IDs
        """
        keyword = keyword.lower()
        matches = []

        for profile_id, profile in self.profiles.items():
            searchable = (
                profile.get("name", "").lower() +
                profile.get("manufacturer", "").lower() +
                profile.get("model", "").lower()
            )

            if keyword in searchable:
                matches.append(profile_id)

        return matches

    def create_fixture_from_profile(
        self,
        profile_id: str,
        fixture_id: str,
        name: str,
        start_channel: int
    ) -> Fixture:
        """
        Create a fixture instance from a profile

        Args:
            profile_id: Profile ID from library
            fixture_id: Unique fixture ID
            name: Fixture name
            start_channel: DMX start channel

        Returns:
            Configured Fixture instance
        """
        profile = self.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile not found: {profile_id}")

        # Create channel mappings
        mappings = []
        for m in profile.get("mappings", []):
            channel_type = ChannelType(m["type"])

            # Create ranges if specified
            ranges = []
            for r in m.get("ranges", []):
                range_obj = ChannelRange(
                    min_value=r[0],
                    max_value=r[1],
                    name=r[2],
                    description=r[3] if len(r) > 3 else ""
                )
                ranges.append(range_obj)

            mapping = ChannelMapping(
                channel_offset=m["offset"],
                channel_type=channel_type,
                name=m["name"],
                ranges=ranges,
                default_value=m.get("default_value", 0)
            )
            mappings.append(mapping)

        # Create fixture
        fixture = Fixture(
            id=fixture_id,
            name=name,
            start_channel=start_channel,
            num_channels=profile["num_channels"],
            manufacturer=profile.get("manufacturer", "Generic"),
            model=profile.get("model", "Generic"),
            channel_mappings=mappings,
            tags=[]
        )

        return fixture

    def add_custom_profile(self, profile_id: str, profile: dict):
        """
        Add a custom profile to the library

        Args:
            profile_id: Unique profile ID
            profile: Profile dictionary
        """
        self.profiles[profile_id] = profile

    def export_profiles(self) -> dict:
        """Export all profiles"""
        return {"profiles": self.profiles}

    def import_profiles(self, data: dict):
        """Import profiles from dictionary"""
        if "profiles" in data:
            self.profiles.update(data["profiles"])
