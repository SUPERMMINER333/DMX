"""
Scene Management System
Handles saving and recalling DMX scenes
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class SceneSnapshot:
    """DMX channel values snapshot"""
    channels: Dict[int, int]  # channel: value
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "channels": {str(k): v for k, v in self.channels.items()},
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SceneSnapshot':
        """Create from dictionary"""
        return cls(
            channels={int(k): v for k, v in data["channels"].items()},
            timestamp=data.get("timestamp", time.time())
        )


@dataclass
class Scene:
    """DMX Scene with fixture states"""
    id: str
    name: str
    description: str = ""
    snapshot: Optional[SceneSnapshot] = None
    fixture_values: Dict[str, Dict[int, int]] = field(default_factory=dict)  # fixture_id: {offset: value}
    tags: List[str] = field(default_factory=list)
    fade_time: float = 0.0  # Fade time in seconds

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "snapshot": self.snapshot.to_dict() if self.snapshot else None,
            "fixture_values": {k: v for k, v in self.fixture_values.items()},
            "tags": self.tags,
            "fade_time": self.fade_time
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Scene':
        """Create from dictionary"""
        data_copy = data.copy()
        if data_copy.get("snapshot"):
            data_copy["snapshot"] = SceneSnapshot.from_dict(data_copy["snapshot"])
        return cls(**data_copy)


class SceneManager:
    """Manages DMX scenes"""

    def __init__(self):
        self.scenes: Dict[str, Scene] = {}

    def add_scene(self, scene: Scene) -> bool:
        """
        Add a scene

        Args:
            scene: Scene to add

        Returns:
            True if added, False if ID already exists
        """
        if scene.id in self.scenes:
            return False

        self.scenes[scene.id] = scene
        logger.info(f"Scene added: {scene.name}")
        return True

    def remove_scene(self, scene_id: str) -> bool:
        """
        Remove a scene

        Args:
            scene_id: Scene ID

        Returns:
            True if removed, False if not found
        """
        if scene_id in self.scenes:
            del self.scenes[scene_id]
            logger.info(f"Scene removed: {scene_id}")
            return True
        return False

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """Get scene by ID"""
        return self.scenes.get(scene_id)

    def get_all_scenes(self) -> List[Scene]:
        """Get all scenes"""
        return list(self.scenes.values())

    def get_scenes_by_tag(self, tag: str) -> List[Scene]:
        """Get scenes by tag"""
        return [s for s in self.scenes.values() if tag in s.tags]

    def capture_scene(
        self,
        scene_id: str,
        name: str,
        dmx_data: List[int],
        description: str = "",
        tags: List[str] = None
    ) -> Scene:
        """
        Capture current DMX state as a scene

        Args:
            scene_id: Unique scene ID
            name: Scene name
            dmx_data: Current DMX channel values
            description: Optional description
            tags: Optional tags

        Returns:
            Created scene
        """
        # Only store non-zero channels
        channels = {i: val for i, val in enumerate(dmx_data) if val > 0}

        snapshot = SceneSnapshot(channels=channels)

        scene = Scene(
            id=scene_id,
            name=name,
            description=description,
            snapshot=snapshot,
            tags=tags or []
        )

        self.scenes[scene_id] = scene
        logger.info(f"Scene captured: {name} ({len(channels)} active channels)")
        return scene

    def recall_scene(self, scene_id: str, dmx_controller) -> bool:
        """
        Recall a scene and apply to DMX

        Args:
            scene_id: Scene ID to recall
            dmx_controller: DMX controller instance

        Returns:
            True if successful
        """
        scene = self.get_scene(scene_id)
        if not scene or not scene.snapshot:
            logger.warning(f"Scene not found or empty: {scene_id}")
            return False

        try:
            # Apply snapshot to DMX
            for channel, value in scene.snapshot.channels.items():
                dmx_controller.set_channel(channel, value)

            logger.info(f"Scene recalled: {scene.name}")
            return True
        except Exception as e:
            logger.error(f"Error recalling scene: {e}")
            return False

    def update_scene(self, scene_id: str, **kwargs) -> bool:
        """
        Update scene properties

        Args:
            scene_id: Scene ID
            **kwargs: Properties to update

        Returns:
            True if successful
        """
        scene = self.get_scene(scene_id)
        if not scene:
            return False

        for key, value in kwargs.items():
            if hasattr(scene, key):
                setattr(scene, key, value)

        logger.info(f"Scene updated: {scene_id}")
        return True

    def to_dict(self) -> dict:
        """Export all scenes to dictionary"""
        return {
            "scenes": [s.to_dict() for s in self.scenes.values()]
        }

    def from_dict(self, data: dict):
        """Import scenes from dictionary"""
        self.scenes.clear()
        for scene_data in data.get("scenes", []):
            scene = Scene.from_dict(scene_data)
            self.scenes[scene.id] = scene
        logger.info(f"Loaded {len(self.scenes)} scenes")
