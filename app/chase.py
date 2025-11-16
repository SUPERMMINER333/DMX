"""
Chase Effects System
Create dynamic lighting effects and chasers
"""

import time
import threading
import logging
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ChaseDirection(Enum):
    """Direction of chase playback"""
    FORWARD = "forward"
    BACKWARD = "backward"
    BOUNCE = "bounce"
    RANDOM = "random"


@dataclass
class ChaseStep:
    """Single step in a chase"""
    scene_id: Optional[str] = None  # Scene to recall
    channel_values: Dict[int, int] = field(default_factory=dict)  # Or direct channel values
    fade_time: float = 0.0  # Fade time in seconds
    hold_time: float = 1.0  # How long to hold this step


@dataclass
class Chase:
    """Chase/Effect definition"""
    id: str
    name: str
    steps: List[ChaseStep] = field(default_factory=list)
    speed: float = 1.0  # Speed multiplier (1.0 = normal)
    direction: ChaseDirection = ChaseDirection.FORWARD
    loop: bool = True
    enabled: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "steps": [
                {
                    "scene_id": step.scene_id,
                    "channel_values": step.channel_values,
                    "fade_time": step.fade_time,
                    "hold_time": step.hold_time
                }
                for step in self.steps
            ],
            "speed": self.speed,
            "direction": self.direction.value,
            "loop": self.loop,
            "enabled": self.enabled
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Chase':
        """Create from dictionary"""
        steps = [
            ChaseStep(
                scene_id=s.get("scene_id"),
                channel_values=s.get("channel_values", {}),
                fade_time=s.get("fade_time", 0.0),
                hold_time=s.get("hold_time", 1.0)
            )
            for s in data.get("steps", [])
        ]

        return cls(
            id=data["id"],
            name=data["name"],
            steps=steps,
            speed=data.get("speed", 1.0),
            direction=ChaseDirection(data.get("direction", "forward")),
            loop=data.get("loop", True),
            enabled=data.get("enabled", False)
        )


class ChaseEngine:
    """Chase playback engine"""

    def __init__(self, dmx_controller, scene_manager):
        """
        Initialize chase engine

        Args:
            dmx_controller: DMX controller instance
            scene_manager: Scene manager instance
        """
        self.dmx_controller = dmx_controller
        self.scene_manager = scene_manager
        self.chases: Dict[str, Chase] = {}
        self.running_chases: Dict[str, threading.Thread] = {}
        self.stop_flags: Dict[str, threading.Event] = {}

    def add_chase(self, chase: Chase) -> bool:
        """
        Add a chase

        Args:
            chase: Chase to add

        Returns:
            True if added
        """
        if chase.id in self.chases:
            return False

        self.chases[chase.id] = chase
        logger.info(f"Chase added: {chase.name}")
        return True

    def remove_chase(self, chase_id: str) -> bool:
        """Remove a chase"""
        if chase_id in self.chases:
            self.stop_chase(chase_id)
            del self.chases[chase_id]
            logger.info(f"Chase removed: {chase_id}")
            return True
        return False

    def start_chase(self, chase_id: str) -> bool:
        """
        Start a chase

        Args:
            chase_id: Chase ID to start

        Returns:
            True if started
        """
        chase = self.chases.get(chase_id)
        if not chase:
            logger.warning(f"Chase not found: {chase_id}")
            return False

        if chase_id in self.running_chases:
            logger.warning(f"Chase already running: {chase_id}")
            return False

        # Create stop flag
        stop_flag = threading.Event()
        self.stop_flags[chase_id] = stop_flag

        # Start playback thread
        thread = threading.Thread(
            target=self._playback_loop,
            args=(chase, stop_flag),
            daemon=True
        )
        thread.start()
        self.running_chases[chase_id] = thread

        chase.enabled = True
        logger.info(f"Chase started: {chase.name}")
        return True

    def stop_chase(self, chase_id: str) -> bool:
        """Stop a chase"""
        if chase_id not in self.running_chases:
            return False

        # Signal stop
        self.stop_flags[chase_id].set()

        # Wait for thread
        self.running_chases[chase_id].join(timeout=2)

        # Cleanup
        del self.running_chases[chase_id]
        del self.stop_flags[chase_id]

        chase = self.chases.get(chase_id)
        if chase:
            chase.enabled = False

        logger.info(f"Chase stopped: {chase_id}")
        return True

    def stop_all_chases(self):
        """Stop all running chases"""
        for chase_id in list(self.running_chases.keys()):
            self.stop_chase(chase_id)

    def _playback_loop(self, chase: Chase, stop_flag: threading.Event):
        """
        Playback loop for a chase

        Args:
            chase: Chase to play
            stop_flag: Event to signal stop
        """
        step_index = 0
        direction = 1 if chase.direction == ChaseDirection.FORWARD else -1

        while not stop_flag.is_set():
            try:
                # Get current step
                if not chase.steps:
                    break

                step = chase.steps[step_index]

                # Apply step
                self._apply_step(step, chase)

                # Hold
                hold_time = step.hold_time / chase.speed
                if stop_flag.wait(timeout=hold_time):
                    break  # Stop requested

                # Next step
                if chase.direction == ChaseDirection.RANDOM:
                    import random
                    step_index = random.randint(0, len(chase.steps) - 1)

                elif chase.direction == ChaseDirection.BOUNCE:
                    step_index += direction
                    if step_index >= len(chase.steps) or step_index < 0:
                        direction *= -1
                        step_index += direction * 2
                        step_index = max(0, min(len(chase.steps) - 1, step_index))

                else:
                    step_index += direction
                    if chase.loop:
                        step_index = step_index % len(chase.steps)
                    else:
                        if step_index >= len(chase.steps) or step_index < 0:
                            break  # Chase finished

            except Exception as e:
                logger.error(f"Error in chase playback: {e}")
                break

        logger.debug(f"Chase playback ended: {chase.name}")

    def _apply_step(self, step: ChaseStep, chase: Chase):
        """
        Apply a chase step

        Args:
            step: Step to apply
            chase: Parent chase
        """
        # If scene_id is set, recall scene
        if step.scene_id:
            self.scene_manager.recall_scene(step.scene_id, self.dmx_controller.dmx)

        # Apply direct channel values
        if step.channel_values and self.dmx_controller.dmx:
            for channel, value in step.channel_values.items():
                # TODO: Implement fading if fade_time > 0
                self.dmx_controller.dmx.set_channel(channel, value)

    def get_running_chases(self) -> List[str]:
        """Get list of currently running chase IDs"""
        return list(self.running_chases.keys())

    def to_dict(self) -> dict:
        """Export all chases"""
        return {
            "chases": [chase.to_dict() for chase in self.chases.values()]
        }

    def from_dict(self, data: dict):
        """Import chases"""
        self.stop_all_chases()
        self.chases.clear()

        for chase_data in data.get("chases", []):
            chase = Chase.from_dict(chase_data)
            self.chases[chase.id] = chase

        logger.info(f"Loaded {len(self.chases)} chases")


# Helper functions for creating common chases

def create_color_fade_chase(
    chase_id: str,
    name: str,
    fixture_start_channel: int,
    colors: List[tuple],  # [(R, G, B), ...]
    hold_time: float = 1.0
) -> Chase:
    """
    Create a color fade chase for RGB fixtures

    Args:
        chase_id: Unique ID
        name: Chase name
        fixture_start_channel: Start channel of RGB fixture
        colors: List of RGB tuples
        hold_time: Time per color

    Returns:
        Configured chase
    """
    steps = []
    for r, g, b in colors:
        step = ChaseStep(
            channel_values={
                fixture_start_channel: r,
                fixture_start_channel + 1: g,
                fixture_start_channel + 2: b
            },
            fade_time=0.5,
            hold_time=hold_time
        )
        steps.append(step)

    return Chase(id=chase_id, name=name, steps=steps, loop=True)


def create_strobe_chase(
    chase_id: str,
    name: str,
    channels: List[int],
    speed: float = 0.1
) -> Chase:
    """
    Create a strobe effect

    Args:
        chase_id: Unique ID
        name: Chase name
        channels: Channels to strobe
        speed: Strobe speed

    Returns:
        Strobe chase
    """
    steps = [
        ChaseStep(
            channel_values={ch: 255 for ch in channels},
            hold_time=speed
        ),
        ChaseStep(
            channel_values={ch: 0 for ch in channels},
            hold_time=speed
        )
    ]

    return Chase(id=chase_id, name=name, steps=steps, loop=True, speed=1.0)


def create_running_light_chase(
    chase_id: str,
    name: str,
    channels: List[int],
    hold_time: float = 0.2
) -> Chase:
    """
    Create a running light effect

    Args:
        chase_id: Unique ID
        name: Chase name
        channels: Channels for running light
        hold_time: Time per step

    Returns:
        Running light chase
    """
    steps = []
    for i, channel in enumerate(channels):
        step = ChaseStep(
            channel_values={
                channels[j]: 255 if j == i else 0
                for j in range(len(channels))
            },
            hold_time=hold_time
        )
        steps.append(step)

    return Chase(id=chase_id, name=name, steps=steps, loop=True)
