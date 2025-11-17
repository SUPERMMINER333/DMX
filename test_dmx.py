#!/usr/bin/env python3
"""
DMX Test-Skript
Ermöglicht Testen einzelner Komponenten ohne main.py zu starten
"""

import sys
import time
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from lib import dmx as dmx_lib
from lib.poti import Poti
from lib.renc import REnc
from app.fixture_manager import FixtureManager, Fixture, ChannelMapping
from app.scene_manager import SceneManager
from app.storage import Storage


def test_dmx(port="/dev/ttyUSB0", duration=5):
    """
    Test DMX-Ausgabe

    Args:
        port: DMX USB-Port
        duration: Test-Dauer in Sekunden
    """
    print(f"\n=== DMX Test ===")
    print(f"Port: {port}")
    print(f"Dauer: {duration}s\n")

    try:
        dmx = dmx_lib.Dmx(port=port)
        dmx.start()
        print("✓ DMX gestartet")

        # Test: Alle Kanäle auf 0
        dmx.reset()
        print("✓ Reset (alle Kanäle auf 0)")
        time.sleep(1)

        # Test: Kanal 1 auf 255
        dmx.set_channel(1, 255)
        print("✓ Kanal 1 -> 255")
        time.sleep(1)

        # Test: Kanäle 1-4 Fade
        print("✓ Fade Kanäle 1-4...")
        for i in range(0, 256, 5):
            dmx.set_channel(1, i)
            dmx.set_channel(2, i)
            dmx.set_channel(3, i)
            dmx.set_channel(4, i)
            time.sleep(0.02)

        time.sleep(duration - 3)

        # Cleanup
        dmx.reset()
        dmx.stop()
        print("✓ DMX gestoppt\n")

    except Exception as e:
        print(f"✗ Fehler: {e}\n")
        return False

    return True


def test_storage():
    """Test Storage-System"""
    print("\n=== Storage Test ===\n")

    try:
        storage = Storage()
        print(f"✓ Storage initialisiert: {storage.config_dir}")

        # Test Settings laden
        settings = storage.load_settings()
        print(f"✓ Settings geladen: {len(settings)} Einträge")
        print(f"  - DMX Port: {settings.get('dmx_port')}")
        print(f"  - OLED: {settings.get('oled_address')}")

        # Test Fixtures laden
        fixtures_data = storage.load_fixtures()
        print(f"✓ Fixtures geladen: {len(fixtures_data.get('fixtures', []))} Fixtures")

        # Test Scenes laden
        scenes_data = storage.load_scenes()
        print(f"✓ Scenes geladen: {len(scenes_data.get('scenes', []))} Scenes")

        print()

    except Exception as e:
        print(f"✗ Fehler: {e}\n")
        return False

    return True


def test_fixture_manager():
    """Test Fixture Manager"""
    print("\n=== Fixture Manager Test ===\n")

    try:
        manager = FixtureManager()
        print("✓ FixtureManager initialisiert")

        # Test: Fixture hinzufügen
        fixture = Fixture(
            fixture_id="test_rgb",
            name="Test RGB LED",
            start_channel=1,
            num_channels=3,
            channel_mappings=[
                ChannelMapping(0, "Red", 1),
                ChannelMapping(1, "Green", 2),
                ChannelMapping(2, "Blue", 3)
            ]
        )

        manager.add_fixture(fixture)
        print(f"✓ Fixture hinzugefügt: {fixture.name}")

        # Test: Fixture abrufen
        retrieved = manager.get_fixture("test_rgb")
        print(f"✓ Fixture abgerufen: {retrieved.name}")

        # Test: Alle Fixtures
        all_fixtures = manager.get_all_fixtures()
        print(f"✓ Alle Fixtures: {len(all_fixtures)}")

        # Test: Konflikt-Erkennung
        conflicts = manager.find_conflicts()
        print(f"✓ Konflikte: {len(conflicts)}")

        print()

    except Exception as e:
        print(f"✗ Fehler: {e}\n")
        return False

    return True


def test_scene_manager():
    """Test Scene Manager"""
    print("\n=== Scene Manager Test ===\n")

    try:
        manager = SceneManager()
        print("✓ SceneManager initialisiert")

        # Test: Scene erstellen
        test_data = [0] * 512
        test_data[0] = 255  # Kanal 1
        test_data[1] = 128  # Kanal 2
        test_data[2] = 64   # Kanal 3

        manager.capture_scene(
            scene_id="test_scene",
            name="Test Scene",
            dmx_data=test_data,
            description="Test-Beschreibung"
        )
        print("✓ Scene erstellt: Test Scene")

        # Test: Scene abrufen
        scene = manager.get_scene("test_scene")
        print(f"✓ Scene abgerufen: {scene.name}")
        print(f"  - Kanäle: {len([v for v in scene.dmx_values if v > 0])} aktiv")

        # Test: Alle Scenes
        all_scenes = manager.get_all_scenes()
        print(f"✓ Alle Scenes: {len(all_scenes)}")

        print()

    except Exception as e:
        print(f"✗ Fehler: {e}\n")
        return False

    return True


def test_all():
    """Führe alle Tests aus"""
    print("\n" + "="*50)
    print("  DMX Controller - Test Suite")
    print("="*50)

    results = {
        "Storage": test_storage(),
        "Fixture Manager": test_fixture_manager(),
        "Scene Manager": test_scene_manager()
    }

    # DMX Test optional (erfordert Hardware)
    if input("\nDMX Hardware-Test durchführen? (j/n): ").lower() == 'j':
        port = input("DMX Port [/dev/ttyUSB0]: ").strip() or "/dev/ttyUSB0"
        results["DMX Hardware"] = test_dmx(port=port)

    # Zusammenfassung
    print("\n" + "="*50)
    print("  Test-Ergebnisse")
    print("="*50)

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:20s} {status}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nGesamt: {passed}/{total} Tests erfolgreich")
    print("="*50 + "\n")

    return all(results.values())


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="DMX Controller Test-Skript"
    )

    parser.add_argument(
        "test",
        nargs="?",
        choices=["all", "dmx", "storage", "fixtures", "scenes"],
        default="all",
        help="Test zum Ausführen (default: all)"
    )

    parser.add_argument(
        "--port",
        default="/dev/ttyUSB0",
        help="DMX USB-Port (default: /dev/ttyUSB0)"
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=5,
        help="DMX Test-Dauer in Sekunden (default: 5)"
    )

    args = parser.parse_args()

    # Führe gewählten Test aus
    if args.test == "all":
        success = test_all()
    elif args.test == "dmx":
        success = test_dmx(port=args.port, duration=args.duration)
    elif args.test == "storage":
        success = test_storage()
    elif args.test == "fixtures":
        success = test_fixture_manager()
    elif args.test == "scenes":
        success = test_scene_manager()
    else:
        print(f"Unbekannter Test: {args.test}")
        return 1

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
