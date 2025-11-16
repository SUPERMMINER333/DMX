"""
Art-Net Protocol Implementation
DMX512 over Ethernet (Art-Net 4)

Art-Net allows sending DMX data over standard Ethernet networks,
enabling multiple universes and long-distance transmission.
"""

import socket
import struct
import threading
import time
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class ArtNetPacket:
    """Art-Net DMX packet builder"""

    # Art-Net protocol constants
    ARTNET_HEADER = b'Art-Net\x00'
    OPCODE_DMX = 0x5000  # OpDmx
    PROTOCOL_VERSION = 14  # Art-Net 4

    @staticmethod
    def create_dmx_packet(
        universe: int,
        sequence: int,
        data: bytes,
        physical: int = 0
    ) -> bytes:
        """
        Create an Art-Net DMX packet

        Args:
            universe: Universe number (0-32767)
            sequence: Sequence number (0-255, wraps around)
            data: DMX data (up to 512 bytes)
            physical: Physical port (usually 0)

        Returns:
            Complete Art-Net packet
        """
        # Ensure data is exactly 512 bytes
        dmx_data = bytes(data) + bytes(512 - len(data))

        # Build packet
        packet = bytearray()

        # Header
        packet.extend(ArtNetPacket.ARTNET_HEADER)

        # OpCode (little-endian)
        packet.extend(struct.pack('<H', ArtNetPacket.OPCODE_DMX))

        # Protocol Version (big-endian)
        packet.extend(struct.pack('>H', ArtNetPacket.PROTOCOL_VERSION))

        # Sequence
        packet.append(sequence)

        # Physical
        packet.append(physical)

        # Universe (little-endian, 15-bit)
        packet.extend(struct.pack('<H', universe & 0x7FFF))

        # Length (big-endian) - always 512 for DMX
        packet.extend(struct.pack('>H', 512))

        # DMX Data
        packet.extend(dmx_data)

        return bytes(packet)


class ArtNetSender:
    """Art-Net sender - transmits DMX data over network"""

    def __init__(
        self,
        target_ip: str = "255.255.255.255",  # Broadcast by default
        port: int = 6454,  # Standard Art-Net port
        universe: int = 0,
        fps: int = 44
    ):
        """
        Initialize Art-Net sender

        Args:
            target_ip: Target IP (use broadcast for multiple receivers)
            port: Art-Net port (default 6454)
            universe: Universe number (0-32767)
            fps: Frames per second to send
        """
        self.target_ip = target_ip
        self.port = port
        self.universe = universe
        self.fps = fps

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.data = bytearray(512)
        self.sequence = 0
        self.running = False
        self.thread: Optional[threading.Thread] = None

        logger.info(f"Art-Net sender initialized: {target_ip}:{port} Universe {universe}")

    def start(self):
        """Start Art-Net transmission"""
        if self.running:
            logger.warning("Art-Net sender already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._send_loop, daemon=True)
        self.thread.start()
        logger.info("Art-Net transmission started")

    def stop(self):
        """Stop Art-Net transmission"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("Art-Net transmission stopped")

    def _send_loop(self):
        """Main transmission loop"""
        frame_time = 1.0 / self.fps

        while self.running:
            try:
                frame_start = time.perf_counter()

                # Create and send packet
                packet = ArtNetPacket.create_dmx_packet(
                    universe=self.universe,
                    sequence=self.sequence,
                    data=self.data
                )

                self.socket.sendto(packet, (self.target_ip, self.port))

                # Increment sequence (wraps at 255)
                self.sequence = (self.sequence + 1) % 256

                # Timing
                elapsed = time.perf_counter() - frame_start
                remaining = frame_time - elapsed

                if remaining > 0:
                    time.sleep(remaining)

            except Exception as e:
                logger.error(f"Art-Net send error: {e}")

    def set_channel(self, channel: int, value: int):
        """
        Set DMX channel value

        Args:
            channel: Channel (0-511)
            value: Value (0-255)
        """
        if 0 <= channel < 512:
            self.data[channel] = max(0, min(255, value))

    def set_channels(self, start_channel: int, values: List[int]):
        """
        Set multiple channels

        Args:
            start_channel: Starting channel
            values: List of values
        """
        for i, value in enumerate(values):
            ch = start_channel + i
            if ch < 512:
                self.data[ch] = max(0, min(255, value))

    def reset(self):
        """Reset all channels to 0"""
        self.data = bytearray(512)


class ArtNetMultiverse:
    """
    Art-Net multiverse support
    Manages multiple universes
    """

    def __init__(self, target_ip: str = "255.255.255.255", fps: int = 44):
        """
        Initialize multiverse

        Args:
            target_ip: Target IP
            fps: Frames per second
        """
        self.target_ip = target_ip
        self.fps = fps
        self.universes: dict[int, ArtNetSender] = {}

    def add_universe(self, universe: int) -> ArtNetSender:
        """
        Add a universe

        Args:
            universe: Universe number

        Returns:
            ArtNetSender for this universe
        """
        if universe in self.universes:
            return self.universes[universe]

        sender = ArtNetSender(
            target_ip=self.target_ip,
            universe=universe,
            fps=self.fps
        )
        self.universes[universe] = sender

        logger.info(f"Universe {universe} added")
        return sender

    def start_all(self):
        """Start all universes"""
        for sender in self.universes.values():
            sender.start()

    def stop_all(self):
        """Stop all universes"""
        for sender in self.universes.values():
            sender.stop()

    def get_universe(self, universe: int) -> Optional[ArtNetSender]:
        """Get sender for a universe"""
        return self.universes.get(universe)

    def set_channel(self, universe: int, channel: int, value: int):
        """
        Set channel in a specific universe

        Args:
            universe: Universe number
            channel: Channel (0-511)
            value: Value (0-255)
        """
        sender = self.universes.get(universe)
        if sender:
            sender.set_channel(channel, value)
        else:
            logger.warning(f"Universe {universe} not found")


class ArtNetBridge:
    """
    Bridge between DMX controller and Art-Net
    Allows simultaneous USB-DMX and Art-Net output
    """

    def __init__(self, dmx_controller, artnet_sender: ArtNetSender):
        """
        Initialize bridge

        Args:
            dmx_controller: DMX controller instance
            artnet_sender: Art-Net sender
        """
        self.dmx_controller = dmx_controller
        self.artnet_sender = artnet_sender
        self.sync_enabled = False
        self.sync_thread: Optional[threading.Thread] = None

    def start_sync(self):
        """Start syncing DMX to Art-Net"""
        if self.sync_enabled:
            return

        self.sync_enabled = True
        self.artnet_sender.start()

        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()

        logger.info("Art-Net bridge sync started")

    def stop_sync(self):
        """Stop syncing"""
        self.sync_enabled = False
        if self.sync_thread:
            self.sync_thread.join(timeout=2)

        self.artnet_sender.stop()
        logger.info("Art-Net bridge sync stopped")

    def _sync_loop(self):
        """Sync DMX data to Art-Net"""
        while self.sync_enabled:
            try:
                if self.dmx_controller.dmx:
                    # Copy DMX data to Art-Net
                    self.artnet_sender.data[:] = self.dmx_controller.dmx.data

                time.sleep(0.01)  # 100 Hz sync rate
            except Exception as e:
                logger.error(f"Bridge sync error: {e}")


# Helper function
def discover_artnet_nodes(timeout: float = 3.0) -> List[str]:
    """
    Discover Art-Net nodes on the network (basic implementation)

    Args:
        timeout: Discovery timeout in seconds

    Returns:
        List of discovered IP addresses
    """
    # This is a simplified version
    # Full implementation would send ArtPoll and listen for ArtPollReply
    # For now, just return empty list
    logger.info("Art-Net discovery not fully implemented yet")
    return []
