# DMX Controller für Raspberry Pi 3

Vollständiges DMX-Steuerungssystem mit OLED-Display, Potentiometern, Rotary Encodern und Bluetooth-Steuerung.

## Features

### Hardware-Integration
- ✅ **DMX-Steuerung** über USB-DMX-Interface
- ✅ **4 Potentiometer** über ADS1115 ADC
- ✅ **4 Rotary Encoder** mit Buttons
- ✅ **OLED Display** (SSD1306/SH1106) für Menüs und Status

### Steuerung & Effekte
- ✅ **Fixture-Management** mit flexiblem Channel-Mapping
- ✅ **Szenen-System** zum Speichern und Abrufen
- ✅ **Chase-Effekte** (Strobe, Running Light, Color Fade, etc.)
- ✅ **Art-Net Support** (DMX über Ethernet, mehrere Universen)
- ✅ **Fixture-Profil-Bibliothek** (9+ vordefinierte Geräte)

### Schnittstellen
- ✅ **Web-Interface** mit RESTful API (Flask)
- ✅ **Bluetooth LE** für Smartphone-Steuerung
- ✅ **CLI-Tool** zur Konfiguration
- ✅ **JSON-Persistenz** für alle Einstellungen
- ✅ **Systemd Service** für automatischen Start

## Hardware-Anforderungen

- Raspberry Pi 3 (oder neuer)
- 4x Potentiometer (10kΩ)
- 4x Rotary Encoder mit Taster
- ADS1115 ADC-Modul (I2C)
- OLED Display (SSD1306 oder SH1106, I2C)
- USB-DMX-Interface
- DMX-Lampen/Fixtures

## Installation

### 1. Abhängigkeiten installieren

```bash
# System-Pakete
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev i2c-tools \
    libglib2.0-dev libdbus-1-dev bluetooth bluez python3-gi \
    fonts-freefont-ttf

# I2C aktivieren
sudo raspi-config
# -> Interface Options -> I2C -> Enable

# Python-Pakete
cd /home/user/DMX
pip3 install -r requirements.txt
```

### 2. GPIO-Pins konfigurieren

Bearbeiten Sie `config/settings.json` und passen Sie die Encoder-Pins an:

```json
{
  "encoder_pins": {
    "encoder_1": {"a": 15, "b": 18, "btn": 17},
    "encoder_2": {"a": 22, "b": 23, "btn": 24},
    "encoder_3": {"a": 25, "b": 8, "btn": 7},
    "encoder_4": {"a": 12, "b": 16, "btn": 20}
  }
}
```

### 3. DMX-Interface einrichten

Verbinden Sie Ihr USB-DMX-Interface und prüfen Sie den Port:

```bash
ls -l /dev/ttyUSB*
# Sollte /dev/ttyUSB0 zeigen
```

### 4. Berechtigungen setzen

```bash
# Benutzer zu dialout-Gruppe hinzufügen (für Serial/DMX)
sudo usermod -a -G dialout $USER

# Benutzer zu gpio/i2c-Gruppen hinzufügen
sudo usermod -a -G gpio,i2c $USER

# Neustart erforderlich
sudo reboot
```

## Verwendung

### CLI-Tool für Fixture-Verwaltung

```bash
# CLI-Tool starten
python3 cli_tool.py

# Befehle:
DMX> help              # Hilfe anzeigen
DMX> list              # Alle Fixtures auflisten
DMX> show <id>         # Fixture-Details anzeigen
DMX> add               # Neues Fixture hinzufügen
DMX> quick_add rgb     # Schnell RGB-Fixture hinzufügen
DMX> remove <id>       # Fixture entfernen
DMX> save              # Speichern
DMX> conflicts         # Channel-Konflikte prüfen
DMX> export <datei>    # Nach JSON exportieren
DMX> import <datei>    # Von JSON importieren
DMX> exit              # Beenden
```

### Haupt-Service starten

```bash
# Manuell starten
python3 main.py

# Als systemd Service
sudo cp dmx-controller.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dmx-controller.service
sudo systemctl start dmx-controller.service

# Status prüfen
sudo systemctl status dmx-controller.service

# Logs ansehen
sudo journalctl -u dmx-controller.service -f
```

### Fixture-Beispiele

#### RGB-Fixture hinzufügen

```python
from app.fixture_manager import create_simple_rgb_fixture, FixtureManager

manager = FixtureManager()
fixture = create_simple_rgb_fixture(
    fixture_id="rgb1",
    name="RGB Scheinwerfer",
    start_channel=0
)
manager.add_fixture(fixture)
```

#### RGBW-Fixture mit CLI

```bash
DMX> quick_add rgbw
Fixture ID: stage_light_1
Fixture Name: Bühne Links
Start Channel: 0
Fixture 'Bühne Links' added successfully!
```

#### Fixture mit Color Wheel und Value-Ranges

```python
from app.fixture_manager import create_fixture_with_color_wheel

color_ranges = [
    (0, 50, "Blau", "Blaues Licht"),
    (51, 100, "Rot", "Rotes Licht"),
    (101, 150, "Grün", "Grünes Licht"),
    (151, 200, "Gelb", "Gelbes Licht"),
    (201, 255, "Weiß", "Weißes Licht")
]

fixture = create_fixture_with_color_wheel(
    fixture_id="colorwheel1",
    name="Moving Head",
    start_channel=10,
    color_ranges=color_ranges
)
```

## Steuerungsmodi

Das System hat 4 Steuerungsmodi:

1. **DIRECT** - Potis steuern direkt DMX-Kanäle
2. **FIXTURE** - Potis steuern ausgewähltes Fixture
3. **SCENE** - Szenen abrufen und speichern
4. **MENU** - OLED-Menü-Navigation

Modus wechseln: Langer Druck auf Encoder 4

## OLED-Menü

Navigation:
- **Encoder 1**: Menü hoch/runter
- **Encoder 1 drücken**: Auswählen
- **Encoder 4 lang**: Zurück zum Hauptmenü

Menüstruktur:
```
Main Menu
├── Fixtures (Fixture auswählen)
├── Scenes
│   ├── Recall Scene
│   ├── Capture Current
│   └── Blackout
├── Settings
│   ├── Save Config
│   ├── Load Config
│   ├── Backup
│   └── Control Mode
└── Status
```

## Bluetooth-Steuerung

### BLE-Protokoll

Service UUID: `12345678-1234-5678-1234-56789abcdef0`

Befehle werden als JSON gesendet:

```json
{
  "action": "set_channel",
  "channel": 0,
  "value": 255
}
```

### Verfügbare Aktionen

```javascript
// Fixtures auflisten
{"action": "list_fixtures"}

// Fixture hinzufügen
{
  "action": "add_fixture",
  "fixture": {
    "id": "new_light",
    "name": "Neue Lampe",
    "start_channel": 10,
    "num_channels": 4
  }
}

// Kanal setzen
{"action": "set_channel", "channel": 0, "value": 255}

// Szene abrufen
{"action": "recall_scene", "scene_id": "scene1"}

// Szene speichern
{
  "action": "capture_scene",
  "scene_id": "new_scene",
  "scene_name": "Blaue Stimmung"
}

// Status abrufen
{"action": "get_status"}
```

### Beispiel Python BLE-Client

```python
# Benötigt: pip install bluepy

import json
from bluepy import btle

# Verbinden (MAC-Adresse des Pi ermitteln mit: hcitool dev)
device = btle.Peripheral("B8:27:EB:XX:XX:XX")

# Command Characteristic
cmd_uuid = "12345678-1234-5678-1234-56789abcdef5"
cmd_char = device.getCharacteristics(uuid=cmd_uuid)[0]

# Befehl senden
command = {"action": "list_fixtures"}
cmd_char.write(json.dumps(command).encode())

# Antwort lesen
response = json.loads(cmd_char.read().decode())
print(response)
```

## Konfigurationsdateien

```
config/
├── fixtures.json   # Gespeicherte Fixtures
├── scenes.json     # Gespeicherte Szenen
├── settings.json   # Systemeinstellungen
└── backups/        # Automatische Backups
```

### fixtures.json Beispiel

```json
{
  "fixtures": [
    {
      "id": "rgb1",
      "name": "RGB Scheinwerfer",
      "start_channel": 0,
      "num_channels": 3,
      "manufacturer": "Generic",
      "model": "RGB",
      "channel_mappings": [
        {
          "channel_offset": 0,
          "channel_type": "red",
          "name": "Red",
          "ranges": [],
          "default_value": 0
        }
      ],
      "tags": ["stage"]
    }
  ]
}
```

## Testen ohne Hardware

Das System kann auch ohne echte Hardware getestet werden:

```bash
# Mock-Modus (automatisch wenn Hardware fehlt)
python3 main.py

# Logs zeigen:
# "Warning: ADS1115 not available, using mock"
# "Warning: luma.oled not available, display will be mocked"
# "Warning: Using mock BLE server"
```

## Projektstruktur

```
DMX/
├── lib/                    # Hardware-Bibliotheken
│   ├── dmx.py             # DMX-Steuerung
│   ├── renc.py            # Rotary Encoder
│   └── poti.py            # Potentiometer
├── app/                    # Anwendungslogik
│   ├── fixture_manager.py # Fixture-Verwaltung
│   ├── scene_manager.py   # Szenen-Verwaltung
│   ├── storage.py         # Persistenz
│   └── controller.py      # Haupt-Controller
├── ui/                     # User Interface
│   ├── display.py         # OLED-Display
│   └── oled_menu.py       # Menü-System
├── ble/                    # Bluetooth
│   └── server.py          # BLE GATT Server
├── cli/                    # Command Line Interface
│   └── fixture_cli.py     # Fixture-CLI
├── config/                 # Konfiguration
├── logs/                   # Log-Dateien
├── main.py                # Haupt-Service
├── cli_tool.py            # CLI-Einstieg
├── example_integration.py # Integration-Beispiel
├── requirements.txt       # Python-Abhängigkeiten
└── README.md             # Diese Datei
```

## Entwicklung & Debugging

### Logging

Log-Dateien befinden sich in `logs/dmx_controller.log`

```bash
# Live-Logs
tail -f logs/dmx_controller.log

# Debug-Level in settings.json ändern:
{
  "log_level": "DEBUG"
}
```

### Tests

```bash
# Pytest installieren
pip3 install pytest

# Tests ausführen (wenn vorhanden)
pytest tests/
```

## Fehlerbehebung

### Problem: DMX sendet nicht

```bash
# Port prüfen
ls -l /dev/ttyUSB0

# Berechtigungen prüfen
groups $USER  # sollte 'dialout' enthalten

# Manuell testen
python3 -c "from lib.dmx import Dmx; d=Dmx(); d.start(); d.set_channel(0,255); import time; time.sleep(2)"
```

### Problem: OLED zeigt nichts

```bash
# I2C-Geräte scannen
sudo i2cdetect -y 1

# Sollte 0x3C zeigen (OLED)
# Sollte 0x48 zeigen (ADS1115)
```

### Problem: BLE funktioniert nicht

```bash
# Bluetooth-Status
sudo systemctl status bluetooth

# Bluetooth neu starten
sudo systemctl restart bluetooth

# D-Bus prüfen
sudo systemctl status dbus
```

## Sicherheitshinweise

⚠️ **WICHTIG**: DMX-Geräte können hohe Spannungen führen!

- Niemals DMX-Kabel bei eingeschalteten Geräten ziehen
- Immer korrekte DMX-Terminierung verwenden
- Keine Standard-Audiokabel für DMX verwenden
- Bei professionellem Einsatz: Elektriker konsultieren

## Lizenz & Support

Dieses Projekt ist Open Source. Bei Fragen oder Problemen:

1. Logs prüfen: `logs/dmx_controller.log`
2. GitHub Issues verwenden
3. Dokumentation lesen

## Roadmap

Geplante Features:
- [ ] Web-Interface
- [ ] Smartphone-App (React Native)
- [ ] Chase-Effekte
- [ ] DMX-Input (Feedback von Fixtures)
- [ ] Art-Net Support
- [ ] Fixture-Profil-Bibliothek

---

**Version**: 1.0.0
**Autor**: DMX Controller Team
**Datum**: 2025-11-16
