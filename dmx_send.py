#!/usr/bin/env python3
"""
DMX Send CLI Tool
Direktes Senden von DMX-Werten ohne main.py zu starten
"""

import sys
import time
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from lib import dmx as dmx_lib


def send_channel(port, channel, value, duration=None):
    """
    Sende Wert an einen DMX-Kanal

    Args:
        port: DMX USB-Port
        channel: DMX-Kanal (1-512)
        value: Wert (0-255)
        duration: Optional - halte Wert für X Sekunden
    """
    if not (1 <= channel <= 512):
        print(f"✗ Fehler: Kanal muss zwischen 1 und 512 liegen")
        return False

    if not (0 <= value <= 255):
        print(f"✗ Fehler: Wert muss zwischen 0 und 255 liegen")
        return False

    try:
        dmx = dmx_lib.Dmx(port=port)
        dmx.start()

        dmx.set_channel(channel, value)
        print(f"✓ Kanal {channel} -> {value}")

        if duration:
            print(f"  Halte für {duration}s...")
            time.sleep(duration)
            dmx.set_channel(channel, 0)
            print(f"✓ Kanal {channel} -> 0")

        dmx.stop()
        return True

    except Exception as e:
        print(f"✗ Fehler: {e}")
        return False


def send_multiple(port, channels, duration=None):
    """
    Sende Werte an mehrere Kanäle

    Args:
        port: DMX USB-Port
        channels: Liste von (Kanal, Wert) Tupeln
        duration: Optional - halte Werte für X Sekunden
    """
    try:
        dmx = dmx_lib.Dmx(port=port)
        dmx.start()

        for channel, value in channels:
            if not (1 <= channel <= 512):
                print(f"✗ Warnung: Kanal {channel} übersprungen (außerhalb Bereich)")
                continue
            if not (0 <= value <= 255):
                print(f"✗ Warnung: Wert {value} für Kanal {channel} übersprungen (außerhalb Bereich)")
                continue

            dmx.set_channel(channel, value)
            print(f"✓ Kanal {channel} -> {value}")

        if duration:
            print(f"\n  Halte für {duration}s...")
            time.sleep(duration)

            # Reset zu 0
            for channel, _ in channels:
                if 1 <= channel <= 512:
                    dmx.set_channel(channel, 0)
            print("✓ Alle Kanäle -> 0")

        dmx.stop()
        return True

    except Exception as e:
        print(f"✗ Fehler: {e}")
        return False


def send_fade(port, channel, start, end, duration=2.0, steps=50):
    """
    Fade einen Kanal von start zu end

    Args:
        port: DMX USB-Port
        channel: DMX-Kanal (1-512)
        start: Start-Wert (0-255)
        end: End-Wert (0-255)
        duration: Fade-Dauer in Sekunden
        steps: Anzahl Schritte
    """
    if not (1 <= channel <= 512):
        print(f"✗ Fehler: Kanal muss zwischen 1 und 512 liegen")
        return False

    if not (0 <= start <= 255) or not (0 <= end <= 255):
        print(f"✗ Fehler: Werte müssen zwischen 0 und 255 liegen")
        return False

    try:
        dmx = dmx_lib.Dmx(port=port)
        dmx.start()

        step_delay = duration / steps
        step_size = (end - start) / steps

        print(f"✓ Fade Kanal {channel}: {start} -> {end} ({duration}s)")

        for i in range(steps + 1):
            value = int(start + (step_size * i))
            dmx.set_channel(channel, value)
            time.sleep(step_delay)

        print(f"✓ Fade abgeschlossen")

        dmx.stop()
        return True

    except Exception as e:
        print(f"✗ Fehler: {e}")
        return False


def send_rgb(port, start_channel, red, green, blue, duration=None):
    """
    Sende RGB-Werte an 3 aufeinanderfolgende Kanäle

    Args:
        port: DMX USB-Port
        start_channel: Start-Kanal für RGB (1-510)
        red: Rot-Wert (0-255)
        green: Grün-Wert (0-255)
        blue: Blau-Wert (0-255)
        duration: Optional - halte Werte für X Sekunden
    """
    if not (1 <= start_channel <= 510):
        print(f"✗ Fehler: Start-Kanal muss zwischen 1 und 510 liegen")
        return False

    if not all(0 <= v <= 255 for v in [red, green, blue]):
        print(f"✗ Fehler: RGB-Werte müssen zwischen 0 und 255 liegen")
        return False

    channels = [
        (start_channel, red),
        (start_channel + 1, green),
        (start_channel + 2, blue)
    ]

    print(f"✓ RGB Kanal {start_channel}-{start_channel+2}: R={red} G={green} B={blue}")
    return send_multiple(port, channels, duration)


def blackout(port):
    """
    Setze alle Kanäle auf 0

    Args:
        port: DMX USB-Port
    """
    try:
        dmx = dmx_lib.Dmx(port=port)
        dmx.start()

        dmx.reset()
        print("✓ Blackout (alle Kanäle auf 0)")

        dmx.stop()
        return True

    except Exception as e:
        print(f"✗ Fehler: {e}")
        return False


def interactive_mode(port):
    """
    Interaktiver Modus zum Senden von DMX-Werten

    Args:
        port: DMX USB-Port
    """
    print("\n" + "="*50)
    print("  DMX Send - Interaktiver Modus")
    print("="*50)
    print("\nBefehle:")
    print("  set <kanal> <wert>        - Setze Kanal auf Wert")
    print("  fade <kanal> <start> <end> <dauer> - Fade Kanal")
    print("  rgb <start_kanal> <r> <g> <b> - Setze RGB-Werte")
    print("  blackout                  - Alle Kanäle auf 0")
    print("  quit                      - Beenden\n")

    try:
        dmx = dmx_lib.Dmx(port=port)
        dmx.start()
        print(f"✓ DMX gestartet auf {port}\n")

        while True:
            try:
                cmd = input("dmx> ").strip().split()

                if not cmd:
                    continue

                if cmd[0] == "quit":
                    break

                elif cmd[0] == "set" and len(cmd) == 3:
                    channel = int(cmd[1])
                    value = int(cmd[2])
                    if 1 <= channel <= 512 and 0 <= value <= 255:
                        dmx.set_channel(channel, value)
                        print(f"✓ Kanal {channel} -> {value}")
                    else:
                        print("✗ Ungültiger Kanal oder Wert")

                elif cmd[0] == "fade" and len(cmd) == 5:
                    channel = int(cmd[1])
                    start = int(cmd[2])
                    end = int(cmd[3])
                    duration = float(cmd[4])

                    if not (1 <= channel <= 512):
                        print("✗ Ungültiger Kanal")
                        continue
                    if not (0 <= start <= 255) or not (0 <= end <= 255):
                        print("✗ Ungültige Werte")
                        continue

                    steps = 50
                    step_delay = duration / steps
                    step_size = (end - start) / steps

                    for i in range(steps + 1):
                        value = int(start + (step_size * i))
                        dmx.set_channel(channel, value)
                        time.sleep(step_delay)

                    print(f"✓ Fade abgeschlossen")

                elif cmd[0] == "rgb" and len(cmd) == 5:
                    start_ch = int(cmd[1])
                    r = int(cmd[2])
                    g = int(cmd[3])
                    b = int(cmd[4])

                    if not (1 <= start_ch <= 510):
                        print("✗ Ungültiger Start-Kanal")
                        continue
                    if not all(0 <= v <= 255 for v in [r, g, b]):
                        print("✗ Ungültige RGB-Werte")
                        continue

                    dmx.set_channel(start_ch, r)
                    dmx.set_channel(start_ch + 1, g)
                    dmx.set_channel(start_ch + 2, b)
                    print(f"✓ RGB: R={r} G={g} B={b}")

                elif cmd[0] == "blackout":
                    dmx.reset()
                    print("✓ Blackout")

                else:
                    print("✗ Unbekannter Befehl oder falsche Anzahl Parameter")

            except ValueError:
                print("✗ Ungültige Parameter")
            except KeyboardInterrupt:
                print("\n")
                break

        dmx.reset()
        dmx.stop()
        print("\n✓ DMX gestoppt")

    except Exception as e:
        print(f"✗ Fehler: {e}")
        return False

    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="DMX Send CLI - Direktes Senden von DMX-Werten",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Kanal 1 auf 255 setzen
  %(prog)s channel 1 255

  # Kanal 1 auf 255 für 5 Sekunden
  %(prog)s channel 1 255 --duration 5

  # Fade Kanal 1 von 0 auf 255 in 3 Sekunden
  %(prog)s fade 1 0 255 --duration 3

  # RGB-Werte setzen (Kanal 1-3: R=255, G=128, B=64)
  %(prog)s rgb 1 255 128 64

  # Mehrere Kanäle setzen
  %(prog)s multi 1:255 2:128 3:64

  # Blackout (alle Kanäle auf 0)
  %(prog)s blackout

  # Interaktiver Modus
  %(prog)s interactive
        """
    )

    parser.add_argument(
        "--port",
        default="/dev/ttyUSB0",
        help="DMX USB-Port (default: /dev/ttyUSB0)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Befehl")

    # channel command
    channel_parser = subparsers.add_parser("channel", help="Sende Wert an Kanal")
    channel_parser.add_argument("channel", type=int, help="DMX-Kanal (1-512)")
    channel_parser.add_argument("value", type=int, help="Wert (0-255)")
    channel_parser.add_argument("--duration", type=float, help="Halte Wert für X Sekunden")

    # fade command
    fade_parser = subparsers.add_parser("fade", help="Fade einen Kanal")
    fade_parser.add_argument("channel", type=int, help="DMX-Kanal (1-512)")
    fade_parser.add_argument("start", type=int, help="Start-Wert (0-255)")
    fade_parser.add_argument("end", type=int, help="End-Wert (0-255)")
    fade_parser.add_argument("--duration", type=float, default=2.0, help="Fade-Dauer in Sekunden (default: 2.0)")
    fade_parser.add_argument("--steps", type=int, default=50, help="Anzahl Schritte (default: 50)")

    # rgb command
    rgb_parser = subparsers.add_parser("rgb", help="Sende RGB-Werte")
    rgb_parser.add_argument("start_channel", type=int, help="Start-Kanal (1-510)")
    rgb_parser.add_argument("red", type=int, help="Rot-Wert (0-255)")
    rgb_parser.add_argument("green", type=int, help="Grün-Wert (0-255)")
    rgb_parser.add_argument("blue", type=int, help="Blau-Wert (0-255)")
    rgb_parser.add_argument("--duration", type=float, help="Halte Werte für X Sekunden")

    # multi command
    multi_parser = subparsers.add_parser("multi", help="Sende Werte an mehrere Kanäle")
    multi_parser.add_argument("channels", nargs="+", help="Kanal:Wert Paare (z.B. 1:255 2:128)")
    multi_parser.add_argument("--duration", type=float, help="Halte Werte für X Sekunden")

    # blackout command
    subparsers.add_parser("blackout", help="Alle Kanäle auf 0")

    # interactive command
    subparsers.add_parser("interactive", help="Interaktiver Modus")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Führe Befehl aus
    try:
        if args.command == "channel":
            success = send_channel(args.port, args.channel, args.value, args.duration)

        elif args.command == "fade":
            success = send_fade(args.port, args.channel, args.start, args.end,
                              args.duration, args.steps)

        elif args.command == "rgb":
            success = send_rgb(args.port, args.start_channel, args.red,
                             args.green, args.blue, args.duration)

        elif args.command == "multi":
            # Parse channel:value pairs
            channels = []
            for pair in args.channels:
                try:
                    ch, val = pair.split(":")
                    channels.append((int(ch), int(val)))
                except ValueError:
                    print(f"✗ Ungültiges Format: {pair} (erwartet: kanal:wert)")
                    return 1

            success = send_multiple(args.port, channels, args.duration)

        elif args.command == "blackout":
            success = blackout(args.port)

        elif args.command == "interactive":
            success = interactive_mode(args.port)

        else:
            print(f"✗ Unbekannter Befehl: {args.command}")
            return 1

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n✗ Abgebrochen")
        return 1


if __name__ == "__main__":
    sys.exit(main())
