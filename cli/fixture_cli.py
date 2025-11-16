"""
Fixture Management CLI
Interactive command-line tool for managing DMX fixtures
"""

import cmd
import json
import sys
from typing import Optional
from app.fixture_manager import (
    FixtureManager, Fixture, ChannelMapping, ChannelRange, ChannelType,
    create_simple_rgb_fixture, create_rgbw_fixture, create_fixture_with_color_wheel
)
from app.storage import Storage


class FixtureCLI(cmd.Cmd):
    """Interactive CLI for fixture management"""

    intro = """
╔══════════════════════════════════════════╗
║   DMX Controller - Fixture Manager CLI   ║
╚══════════════════════════════════════════╝

Type 'help' or '?' to list commands.
Type 'help <command>' for detailed help.
"""
    prompt = "DMX> "

    def __init__(self):
        super().__init__()
        self.fixture_manager = FixtureManager()
        self.storage = Storage()
        self.load_fixtures()

    def load_fixtures(self):
        """Load fixtures from storage"""
        data = self.storage.load_fixtures()
        if data:
            self.fixture_manager.from_dict(data)
            print(f"Loaded {len(self.fixture_manager.fixtures)} fixtures")

    def save_fixtures(self):
        """Save fixtures to storage"""
        self.storage.save_fixtures(self.fixture_manager.to_dict())
        print("Fixtures saved")

    # ===== Fixture Commands =====

    def do_list(self, arg):
        """List all fixtures"""
        fixtures = self.fixture_manager.get_all_fixtures()

        if not fixtures:
            print("No fixtures configured")
            return

        print("\n" + "=" * 80)
        print(f"{'ID':<15} {'Name':<20} {'Start Ch':<10} {'Channels':<10} {'Model':<15}")
        print("=" * 80)

        for fixture in fixtures:
            print(f"{fixture.id:<15} {fixture.name:<20} {fixture.start_channel:<10} "
                  f"{fixture.num_channels:<10} {fixture.manufacturer}/{fixture.model:<15}")

        print("=" * 80)
        print(f"Total: {len(fixtures)} fixtures\n")

    def do_show(self, arg):
        """
        Show detailed information about a fixture
        Usage: show <fixture_id>
        """
        if not arg:
            print("Usage: show <fixture_id>")
            return

        fixture = self.fixture_manager.get_fixture(arg)
        if not fixture:
            print(f"Fixture not found: {arg}")
            return

        print("\n" + "=" * 60)
        print(f"Fixture: {fixture.name}")
        print("=" * 60)
        print(f"ID:           {fixture.id}")
        print(f"Manufacturer: {fixture.manufacturer}")
        print(f"Model:        {fixture.model}")
        print(f"Start Ch:     {fixture.start_channel}")
        print(f"Channels:     {fixture.num_channels}")
        print(f"Tags:         {', '.join(fixture.tags) if fixture.tags else 'None'}")

        if fixture.channel_mappings:
            print("\nChannel Mappings:")
            print("-" * 60)
            for mapping in fixture.channel_mappings:
                ch = fixture.get_dmx_channel(mapping.channel_offset)
                print(f"  Ch {ch} (Offset {mapping.channel_offset}): {mapping.name} [{mapping.channel_type.value}]")

                if mapping.ranges:
                    print(f"    Ranges:")
                    for r in mapping.ranges:
                        print(f"      {r.min_value:3d}-{r.max_value:3d}: {r.name} ({r.description})")

        print("=" * 60 + "\n")

    def do_add(self, arg):
        """
        Add a new fixture
        Usage: add
        """
        print("\n=== Add New Fixture ===\n")

        fixture_id = input("Fixture ID (unique): ").strip()
        if not fixture_id:
            print("ID cannot be empty")
            return

        if self.fixture_manager.get_fixture(fixture_id):
            print(f"Fixture ID already exists: {fixture_id}")
            return

        name = input("Fixture Name: ").strip()
        manufacturer = input("Manufacturer [Generic]: ").strip() or "Generic"
        model = input("Model [Generic]: ").strip() or "Generic"

        try:
            start_channel = int(input("Start Channel (0-511): ").strip())
            num_channels = int(input("Number of Channels: ").strip())
        except ValueError:
            print("Invalid channel number")
            return

        # Create fixture
        fixture = Fixture(
            id=fixture_id,
            name=name,
            start_channel=start_channel,
            num_channels=num_channels,
            manufacturer=manufacturer,
            model=model
        )

        # Ask about channel mappings
        add_mappings = input("\nAdd channel mappings? (y/n) [n]: ").strip().lower() == 'y'

        if add_mappings:
            self._add_channel_mappings(fixture)

        # Add fixture
        try:
            if self.fixture_manager.add_fixture(fixture):
                print(f"\nFixture '{name}' added successfully!")
                self.save_fixtures()
            else:
                print("Failed to add fixture")
        except Exception as e:
            print(f"Error: {e}")

    def _add_channel_mappings(self, fixture: Fixture):
        """Helper to add channel mappings interactively"""
        print("\n=== Channel Mappings ===")
        print("Available types: dimmer, red, green, blue, white, amber, uv, strobe, speed, pan, tilt, color_wheel, gobo, effect, generic")

        for offset in range(fixture.num_channels):
            print(f"\nChannel {offset} (DMX {fixture.get_dmx_channel(offset)}):")

            name = input(f"  Name [Channel {offset}]: ").strip() or f"Channel {offset}"
            type_str = input(f"  Type [generic]: ").strip() or "generic"

            try:
                channel_type = ChannelType(type_str)
            except ValueError:
                print(f"  Invalid type, using 'generic'")
                channel_type = ChannelType.GENERIC

            default_value = int(input(f"  Default value [0]: ").strip() or "0")

            mapping = ChannelMapping(
                channel_offset=offset,
                channel_type=channel_type,
                name=name,
                default_value=default_value
            )

            # Ask about ranges
            add_ranges = input("  Add value ranges? (y/n) [n]: ").strip().lower() == 'y'
            if add_ranges:
                self._add_ranges(mapping)

            fixture.channel_mappings.append(mapping)

    def _add_ranges(self, mapping: ChannelMapping):
        """Helper to add value ranges"""
        print("  Adding ranges (enter empty name to finish):")

        while True:
            range_name = input("    Range name: ").strip()
            if not range_name:
                break

            try:
                min_val = int(input("    Min value (0-255): ").strip())
                max_val = int(input("    Max value (0-255): ").strip())
                description = input("    Description: ").strip()

                range_obj = ChannelRange(min_val, max_val, range_name, description)
                mapping.ranges.append(range_obj)
                print(f"    Added range: {range_name} ({min_val}-{max_val})")
            except ValueError:
                print("    Invalid value, range not added")

    def do_remove(self, arg):
        """
        Remove a fixture
        Usage: remove <fixture_id>
        """
        if not arg:
            print("Usage: remove <fixture_id>")
            return

        fixture = self.fixture_manager.get_fixture(arg)
        if not fixture:
            print(f"Fixture not found: {arg}")
            return

        confirm = input(f"Remove fixture '{fixture.name}'? (yes/no): ").strip().lower()
        if confirm == 'yes':
            if self.fixture_manager.remove_fixture(arg):
                print(f"Fixture '{fixture.name}' removed")
                self.save_fixtures()
        else:
            print("Cancelled")

    def do_quick_add(self, arg):
        """
        Quick add common fixture types
        Usage: quick_add <type>
        Types: rgb, rgbw, colorwheel
        """
        if not arg:
            print("Usage: quick_add <type>")
            print("Types: rgb, rgbw, colorwheel")
            return

        fixture_type = arg.strip().lower()
        fixture_id = input("Fixture ID: ").strip()
        name = input("Fixture Name: ").strip()

        try:
            start_channel = int(input("Start Channel: ").strip())
        except ValueError:
            print("Invalid channel")
            return

        if fixture_type == "rgb":
            fixture = create_simple_rgb_fixture(fixture_id, name, start_channel)
        elif fixture_type == "rgbw":
            fixture = create_rgbw_fixture(fixture_id, name, start_channel)
        elif fixture_type == "colorwheel":
            # Default color wheel ranges
            ranges = [
                (0, 50, "Blue", "Blue color"),
                (51, 100, "Red", "Red color"),
                (101, 150, "Green", "Green color"),
                (151, 200, "Yellow", "Yellow color"),
                (201, 255, "White", "White color")
            ]
            fixture = create_fixture_with_color_wheel(fixture_id, name, start_channel, ranges)
        else:
            print(f"Unknown fixture type: {fixture_type}")
            return

        try:
            if self.fixture_manager.add_fixture(fixture):
                print(f"Fixture '{name}' added successfully!")
                self.save_fixtures()
        except Exception as e:
            print(f"Error: {e}")

    # ===== Storage Commands =====

    def do_save(self, arg):
        """Save fixtures to disk"""
        self.save_fixtures()

    def do_load(self, arg):
        """Reload fixtures from disk"""
        self.load_fixtures()

    def do_export(self, arg):
        """
        Export fixtures to JSON file
        Usage: export <filename>
        """
        if not arg:
            print("Usage: export <filename>")
            return

        try:
            data = self.fixture_manager.to_dict()
            with open(arg, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Fixtures exported to {arg}")
        except Exception as e:
            print(f"Error exporting: {e}")

    def do_import(self, arg):
        """
        Import fixtures from JSON file
        Usage: import <filename>
        """
        if not arg:
            print("Usage: import <filename>")
            return

        try:
            with open(arg, 'r') as f:
                data = json.load(f)
            self.fixture_manager.from_dict(data)
            print(f"Fixtures imported from {arg}")
            self.save_fixtures()
        except Exception as e:
            print(f"Error importing: {e}")

    # ===== Utility Commands =====

    def do_conflicts(self, arg):
        """Check for channel conflicts between fixtures"""
        fixtures = self.fixture_manager.get_all_fixtures()
        conflicts_found = False

        print("\nChecking for channel conflicts...")

        for fixture in fixtures:
            conflicts = self.fixture_manager.check_channel_conflicts(fixture, exclude_id=fixture.id)
            if conflicts:
                conflicts_found = True
                print(f"\n⚠ {fixture.name} (Ch {fixture.start_channel}-{fixture.start_channel + fixture.num_channels - 1})")
                print(f"  Conflicts with:")
                for conflict_id in conflicts:
                    conflict = self.fixture_manager.get_fixture(conflict_id)
                    if conflict:
                        print(f"    - {conflict.name} (Ch {conflict.start_channel}-{conflict.start_channel + conflict.num_channels - 1})")

        if not conflicts_found:
            print("✓ No conflicts found")

    def do_exit(self, arg):
        """Exit the program"""
        print("Goodbye!")
        return True

    def do_quit(self, arg):
        """Exit the program"""
        return self.do_exit(arg)

    def do_EOF(self, arg):
        """Handle Ctrl+D"""
        print()
        return self.do_exit(arg)


def main():
    """Main entry point for CLI tool"""
    try:
        cli = FixtureCLI()
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
