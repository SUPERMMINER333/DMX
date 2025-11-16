"""
Fixture (Lamp) Management System
Handles DMX fixtures with channel mapping and range-based sub-features
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class ChannelType(Enum):
    """Types of DMX channels"""
    DIMMER = "dimmer"
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    WHITE = "white"
    AMBER = "amber"
    UV = "uv"
    STROBE = "strobe"
    SPEED = "speed"
    PAN = "pan"
    TILT = "tilt"
    COLOR_WHEEL = "color_wheel"
    GOBO = "gobo"
    EFFECT = "effect"
    GENERIC = "generic"


@dataclass
class ChannelRange:
    """Defines a value range with specific meaning"""
    min_value: int  # 0-255
    max_value: int  # 0-255
    name: str
    description: str = ""

    def contains(self, value: int) -> bool:
        """Check if value is in this range"""
        return self.min_value <= value <= self.max_value

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "min_value": self.min_value,
            "max_value": self.max_value,
            "name": self.name,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ChannelRange':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ChannelMapping:
    """DMX channel configuration with optional range mapping"""
    channel_offset: int  # Offset from fixture start channel
    channel_type: ChannelType
    name: str
    ranges: List[ChannelRange] = field(default_factory=list)
    default_value: int = 0

    def get_range_for_value(self, value: int) -> Optional[ChannelRange]:
        """Get the range that contains this value"""
        for r in self.ranges:
            if r.contains(value):
                return r
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "channel_offset": self.channel_offset,
            "channel_type": self.channel_type.value,
            "name": self.name,
            "ranges": [r.to_dict() for r in self.ranges],
            "default_value": self.default_value
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ChannelMapping':
        """Create from dictionary"""
        data_copy = data.copy()
        data_copy["channel_type"] = ChannelType(data_copy["channel_type"])
        data_copy["ranges"] = [ChannelRange.from_dict(r) for r in data_copy.get("ranges", [])]
        return cls(**data_copy)


@dataclass
class Fixture:
    """DMX Fixture (Lamp) definition"""
    id: str
    name: str
    start_channel: int  # DMX start address (0-511)
    num_channels: int
    manufacturer: str = "Generic"
    model: str = "Generic"
    channel_mappings: List[ChannelMapping] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def get_dmx_channel(self, offset: int) -> int:
        """Get absolute DMX channel from offset"""
        return self.start_channel + offset

    def get_mapping(self, offset: int) -> Optional[ChannelMapping]:
        """Get channel mapping by offset"""
        for mapping in self.channel_mappings:
            if mapping.channel_offset == offset:
                return mapping
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "start_channel": self.start_channel,
            "num_channels": self.num_channels,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "channel_mappings": [m.to_dict() for m in self.channel_mappings],
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Fixture':
        """Create from dictionary"""
        data_copy = data.copy()
        data_copy["channel_mappings"] = [
            ChannelMapping.from_dict(m) for m in data_copy.get("channel_mappings", [])
        ]
        return cls(**data_copy)


class FixtureManager:
    """Manages all DMX fixtures"""

    def __init__(self):
        self.fixtures: Dict[str, Fixture] = {}

    def add_fixture(self, fixture: Fixture) -> bool:
        """
        Add a fixture

        Args:
            fixture: Fixture to add

        Returns:
            True if added, False if ID already exists
        """
        if fixture.id in self.fixtures:
            return False

        # Validate channel range
        if fixture.start_channel < 0 or fixture.start_channel > 511:
            raise ValueError(f"Invalid start channel: {fixture.start_channel}")

        if fixture.start_channel + fixture.num_channels > 512:
            raise ValueError(f"Fixture extends beyond DMX universe (512 channels)")

        self.fixtures[fixture.id] = fixture
        return True

    def remove_fixture(self, fixture_id: str) -> bool:
        """
        Remove a fixture

        Args:
            fixture_id: ID of fixture to remove

        Returns:
            True if removed, False if not found
        """
        if fixture_id in self.fixtures:
            del self.fixtures[fixture_id]
            return True
        return False

    def get_fixture(self, fixture_id: str) -> Optional[Fixture]:
        """Get fixture by ID"""
        return self.fixtures.get(fixture_id)

    def get_all_fixtures(self) -> List[Fixture]:
        """Get all fixtures"""
        return list(self.fixtures.values())

    def get_fixtures_by_tag(self, tag: str) -> List[Fixture]:
        """Get all fixtures with a specific tag"""
        return [f for f in self.fixtures.values() if tag in f.tags]

    def update_fixture(self, fixture_id: str, **kwargs) -> bool:
        """
        Update fixture properties

        Args:
            fixture_id: ID of fixture to update
            **kwargs: Properties to update

        Returns:
            True if updated, False if not found
        """
        fixture = self.get_fixture(fixture_id)
        if not fixture:
            return False

        for key, value in kwargs.items():
            if hasattr(fixture, key):
                setattr(fixture, key, value)

        return True

    def check_channel_conflicts(self, fixture: Fixture, exclude_id: Optional[str] = None) -> List[str]:
        """
        Check if fixture's channels conflict with existing fixtures

        Args:
            fixture: Fixture to check
            exclude_id: Fixture ID to exclude from check (for updates)

        Returns:
            List of conflicting fixture IDs
        """
        conflicts = []
        fixture_range = range(fixture.start_channel, fixture.start_channel + fixture.num_channels)

        for existing in self.fixtures.values():
            if exclude_id and existing.id == exclude_id:
                continue

            existing_range = range(existing.start_channel, existing.start_channel + existing.num_channels)

            # Check for overlap
            if any(ch in existing_range for ch in fixture_range):
                conflicts.append(existing.id)

        return conflicts

    def to_dict(self) -> dict:
        """Export all fixtures to dictionary"""
        return {
            "fixtures": [f.to_dict() for f in self.fixtures.values()]
        }

    def from_dict(self, data: dict):
        """Import fixtures from dictionary"""
        self.fixtures.clear()
        for fixture_data in data.get("fixtures", []):
            fixture = Fixture.from_dict(fixture_data)
            self.fixtures[fixture.id] = fixture


def create_simple_rgb_fixture(fixture_id: str, name: str, start_channel: int) -> Fixture:
    """
    Helper to create a simple RGB fixture

    Args:
        fixture_id: Unique ID
        name: Fixture name
        start_channel: DMX start address

    Returns:
        Configured RGB fixture
    """
    mappings = [
        ChannelMapping(0, ChannelType.RED, "Red", default_value=0),
        ChannelMapping(1, ChannelType.GREEN, "Green", default_value=0),
        ChannelMapping(2, ChannelType.BLUE, "Blue", default_value=0),
    ]

    return Fixture(
        id=fixture_id,
        name=name,
        start_channel=start_channel,
        num_channels=3,
        manufacturer="Generic",
        model="RGB",
        channel_mappings=mappings
    )


def create_rgbw_fixture(fixture_id: str, name: str, start_channel: int) -> Fixture:
    """
    Helper to create an RGBW fixture

    Args:
        fixture_id: Unique ID
        name: Fixture name
        start_channel: DMX start address

    Returns:
        Configured RGBW fixture
    """
    mappings = [
        ChannelMapping(0, ChannelType.RED, "Red", default_value=0),
        ChannelMapping(1, ChannelType.BLUE, "Blue", default_value=0),
        ChannelMapping(2, ChannelType.GREEN, "Green", default_value=0),
        ChannelMapping(3, ChannelType.WHITE, "White", default_value=0),
    ]

    return Fixture(
        id=fixture_id,
        name=name,
        start_channel=start_channel,
        num_channels=4,
        manufacturer="Generic",
        model="RGBW",
        channel_mappings=mappings
    )


def create_fixture_with_color_wheel(
    fixture_id: str,
    name: str,
    start_channel: int,
    color_ranges: List[tuple]
) -> Fixture:
    """
    Create a fixture with a color wheel channel that has value ranges

    Args:
        fixture_id: Unique ID
        name: Fixture name
        start_channel: DMX start address
        color_ranges: List of (min, max, color_name, description) tuples

    Returns:
        Configured fixture with color wheel
    """
    ranges = [
        ChannelRange(min_val, max_val, color, desc)
        for min_val, max_val, color, desc in color_ranges
    ]

    mappings = [
        ChannelMapping(
            0,
            ChannelType.COLOR_WHEEL,
            "Color Wheel",
            ranges=ranges,
            default_value=0
        )
    ]

    return Fixture(
        id=fixture_id,
        name=name,
        start_channel=start_channel,
        num_channels=1,
        manufacturer="Generic",
        model="ColorWheel",
        channel_mappings=mappings
    )
