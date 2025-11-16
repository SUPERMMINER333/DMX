# DMX Controller - Projektstruktur

Vollständige Übersicht über die Projekt-Architektur

## Verzeichnisstruktur

```
DMX/
│
├── 📁 lib/                         # Hardware-Bibliotheken
│   ├── __init__.py
│   ├── dmx.py                      # DMX-Steuerung (USB-DMX-Interface)
│   ├── renc.py                     # Rotary Encoder Handler
│   └── poti.py                     # Potentiometer Reader (ADS1115)
│
├── 📁 app/                         # Anwendungslogik
│   ├── __init__.py
│   ├── fixture_manager.py          # Fixture/Lampen-Verwaltung
│   │   └── Classes:
│   │       ├── Fixture             # Lampen-Definition
│   │       ├── ChannelMapping      # Kanal-Konfiguration
│   │       ├── ChannelRange        # Wert-Bereiche
│   │       └── FixtureManager      # Verwaltung
│   │
│   ├── scene_manager.py            # Szenen-System
│   │   └── Classes:
│   │       ├── Scene               # Szene
│   │       ├── SceneSnapshot       # DMX-Snapshot
│   │       └── SceneManager        # Verwaltung
│   │
│   ├── storage.py                  # Persistenz (JSON)
│   │   └── Class: Storage          # Save/Load
│   │
│   └── controller.py               # Haupt-Controller
│       └── Classes:
│           ├── DMXController       # Koordiniert alles
│           ├── EncoderController   # Encoder-Integration
│           └── ControlMode         # Modi (Direct/Fixture/Scene/Menu)
│
├── 📁 ui/                          # User Interface
│   ├── __init__.py
│   ├── display.py                  # OLED-Display-Manager
│   │   └── Class: Display          # Rendering
│   │
│   └── oled_menu.py                # Menü-System
│       └── Classes:
│           ├── MenuItem            # Menü-Eintrag
│           ├── Menu                # Menü
│           └── MenuSystem          # Komplettes System
│
├── 📁 ble/                         # Bluetooth LE
│   ├── __init__.py
│   └── server.py                   # BLE GATT Server
│       └── Classes:
│           ├── BLEServer           # Server
│           └── MockBLEServer       # Test-Mock
│
├── 📁 cli/                         # Command Line Interface
│   ├── __init__.py
│   └── fixture_cli.py              # Interaktive CLI
│       └── Class: FixtureCLI       # cmd-basierte CLI
│
├── 📁 config/                      # Konfigurationsdateien
│   ├── settings.json               # System-Einstellungen
│   ├── fixtures.json               # Gespeicherte Fixtures
│   ├── scenes.json                 # Gespeicherte Szenen
│   ├── fixtures_example.json       # Beispiel-Fixtures
│   └── backups/                    # Auto-Backups
│
├── 📁 logs/                        # Log-Dateien
│   └── dmx_controller.log          # Haupt-Log
│
├── 📁 data/                        # Laufzeit-Daten
│
├── 📄 main.py                      # 🚀 Haupt-Service
├── 📄 cli_tool.py                  # 🔧 CLI-Tool Einstieg
├── 📄 example_integration.py       # 📝 Integrations-Beispiel
│
├── 📄 requirements.txt             # Python-Abhängigkeiten
├── 📄 dmx-controller.service       # Systemd Service-Datei
│
├── 📄 README.md                    # 📖 Haupt-Dokumentation
├── 📄 INSTALL.md                   # 📖 Installations-Anleitung
├── 📄 QUICKSTART.md                # 📖 Schnellstart
├── 📄 SMARTPHONE_APP.md            # 📖 App-Konzept
├── 📄 PROJECT_STRUCTURE.md         # 📖 Diese Datei
│
└── 📄 .gitignore                   # Git-Ignore
```

## Komponenten-Übersicht

### 1. Hardware-Layer (`lib/`)

**Zweck**: Direkte Hardware-Kommunikation

| Modul | Beschreibung | Hardware |
|-------|--------------|----------|
| `dmx.py` | DMX512-Steuerung | USB-DMX-Interface |
| `renc.py` | Rotary Encoder | 4x Encoder mit Buttons |
| `poti.py` | Potentiometer | ADS1115 ADC |

**Abhängigkeiten**:
- `pyserial` (DMX)
- `RPi.GPIO` (Encoder)
- `Adafruit-ADS1x15` (Potis)

### 2. Anwendungs-Layer (`app/`)

**Zweck**: Business Logic, keine direkte Hardware

| Modul | Klassen | Zweck |
|-------|---------|-------|
| `fixture_manager.py` | Fixture, FixtureManager | Lampen-Verwaltung |
| `scene_manager.py` | Scene, SceneManager | Szenen-System |
| `storage.py` | Storage | JSON-Persistenz |
| `controller.py` | DMXController | Koordination |

**Datenfluss**:
```
Hardware -> Controller -> FixtureManager -> DMX
                       -> SceneManager
                       -> Storage
```

### 3. UI-Layer (`ui/`)

**Zweck**: Benutzerschnittstelle (OLED)

| Modul | Klassen | Zweck |
|-------|---------|-------|
| `display.py` | Display | OLED-Rendering |
| `oled_menu.py` | Menu, MenuSystem | Navigation |

**Abhängigkeiten**:
- `luma.oled` (Display)
- `Pillow` (Grafik)

### 4. Kommunikations-Layer (`ble/`, `cli/`)

**Zweck**: Externe Schnittstellen

| Modul | Protokoll | Client |
|-------|-----------|--------|
| `ble/server.py` | BLE GATT | Smartphone |
| `cli/fixture_cli.py` | Terminal | CLI |

## Datenmodell

### Fixture (Lampe)

```python
{
  "id": "unique_id",
  "name": "Lampen-Name",
  "start_channel": 0,      # DMX-Startadresse
  "num_channels": 4,       # Anzahl Kanäle
  "manufacturer": "...",
  "model": "...",
  "channel_mappings": [    # Kanal-Konfiguration
    {
      "channel_offset": 0,
      "channel_type": "red",
      "name": "Rot",
      "ranges": [          # Optional: Wert-Bereiche
        {
          "min_value": 0,
          "max_value": 50,
          "name": "Blau",
          "description": "..."
        }
      ],
      "default_value": 0
    }
  ],
  "tags": ["stage", "rgb"]
}
```

### Scene (Szene)

```python
{
  "id": "scene_id",
  "name": "Szenen-Name",
  "description": "...",
  "snapshot": {
    "channels": {
      "0": 255,
      "1": 128,
      # nur nicht-null Kanäle
    },
    "timestamp": 1234567890.0
  },
  "fixture_values": {
    "fixture_id": {
      "0": 255,  # Offset -> Wert
      "1": 128
    }
  },
  "tags": ["blue", "mood"],
  "fade_time": 1.0
}
```

## Kontrollfluss

### Start-Sequenz

```
1. main.py startet
2. DMXService.__init__()
   ├─ Storage lädt settings.json
   ├─ Logging wird konfiguriert
   └─ Signal-Handler registriert

3. DMXService.start()
   ├─ DMXController erstellt
   │  ├─ DMX-Interface startet
   │  ├─ FixtureManager lädt fixtures.json
   │  └─ SceneManager lädt scenes.json
   │
   ├─ Display initialisiert (I2C)
   ├─ MenuSystem erstellt
   ├─ ADS1115 + Poti initialisiert
   ├─ Rotary Encoders setup
   └─ BLE Server startet

4. _main_loop() läuft
   ├─ Potis lesen (50ms)
   ├─ DMX aktualisieren
   └─ Display updaten (1s)
```

### Potentiometer -> DMX

```
1. Poti.read_all(channel)
   └─ ADS1115.readADCSingleEnded()
   └─ Smoothing (Mittelwert)
   └─ Umrechnung zu 0-255

2. DMXController.update_from_potis()
   └─ Für jeden Poti (0-3):
      ├─ Wert lesen
      └─ Mode-abhängig:
         ├─ DIRECT: DMX-Kanal direkt setzen
         ├─ FIXTURE: Fixture-Kanal setzen
         └─ SCENE: Ignorieren

3. Dmx.set_channel(channel, value)
   └─ self.data[channel] = value
   └─ _send_frame() (in Thread)
      └─ Serial Write
```

### Encoder -> Menu

```
1. REnc._rotation_callback()
   └─ GPIO Interrupt
   └─ EncoderController.right/left()
      └─ MenuSystem.navigate_up/down()
         └─ Display.draw_menu()

2. REnc._button_callback()
   └─ EncoderController.pressed()
      └─ MenuSystem.select_item()
         └─ MenuItem.execute()
            └─ Action oder Submenu
```

### BLE Command

```
1. BLE Client schreibt JSON
   └─ BLEServer.handle_command()
      └─ JSON parsen
      └─ Action auswählen:
         ├─ list_fixtures -> FixtureManager
         ├─ add_fixture -> FixtureManager.add()
         ├─ set_channel -> DMX.set_channel()
         ├─ recall_scene -> SceneManager.recall()
         └─ ...
      └─ Response als JSON
```

## Steuerungsmodi

| Modus | Potis steuern | Encoder-Funktion |
|-------|---------------|------------------|
| **DIRECT** | Direkt DMX-Kanäle 0-3 | Menu-Navigation |
| **FIXTURE** | Ausgewähltes Fixture | Fixture wählen |
| **SCENE** | Inaktiv | Szene wählen |
| **MENU** | Inaktiv | Menu-Navigation |

Modus wechseln: Encoder 4 lang drücken

## Konfigurations-Flow

### Fixture hinzufügen (CLI)

```
1. cli_tool.py starten
2. FixtureCLI.do_add()
   ├─ Benutzereingaben sammeln
   ├─ Fixture-Objekt erstellen
   ├─ Optional: Channel-Mappings
   ├─ FixtureManager.add_fixture()
   └─ Storage.save_fixtures()
3. Fixture verfügbar in main.py
```

### Szene speichern (OLED)

```
1. Menu: Scenes -> Capture Current
2. MenuSystem._capture_scene_wizard()
   └─ SceneManager.capture_scene()
      ├─ DMX.data kopieren
      ├─ Scene-Objekt erstellen
      └─ Storage.save_scenes()
```

## Persistenz

**Format**: JSON
**Location**: `config/`

| Datei | Inhalt | Aktualisiert |
|-------|--------|--------------|
| `settings.json` | System-Einstellungen | Selten |
| `fixtures.json` | Alle Fixtures | Bei Add/Remove |
| `scenes.json` | Alle Szenen | Bei Capture/Delete |

**Backup**: Automatisch bei `Storage.backup()`
→ `config/backups/dmx_backup_YYYYMMDD_HHMMSS.json`

## Logging

**Location**: `logs/dmx_controller.log`

**Levels**:
- `DEBUG`: Detaillierte Infos (Encoder-Events, ADC-Werte)
- `INFO`: Normale Operationen (Start, Fixture geladen)
- `WARNING`: Warnings (Hardware fehlt, Mock verwendet)
- `ERROR`: Fehler (DMX-Fehler, BLE-Problem)
- `CRITICAL`: Kritische Fehler (Service-Crash)

**Konfiguration**: `settings.json` → `"log_level": "INFO"`

## Threading

| Thread | Zweck | Interval |
|--------|-------|----------|
| DMX Send Loop | DMX-Frames senden | 1ms |
| BLE Mainloop | BLE GATT Server | Event-based |
| Main Loop | Potis lesen, Display | 50ms |

## Sicherheit

**Mock-Mode**: Automatisch wenn Hardware fehlt
- Kein Crash bei fehlender Hardware
- Entwicklung ohne Pi möglich
- Logs warnen vor Mock-Verwendung

**Fehlerbehandlung**:
- Try/Catch in allen Hardware-Calls
- Graceful degradation
- Signal-Handler für sauberes Shutdown

## Erweiterbarkeit

### Neue Fixture-Typen

```python
# In fixture_manager.py
def create_my_custom_fixture(id, name, start_ch):
    mappings = [...]
    return Fixture(id, name, start_ch, ...)
```

### Neue Menu-Items

```python
# In oled_menu.py -> MenuSystem.build_menus()
menu.add_item("Neue Funktion", action=my_function)
```

### Neue BLE-Aktionen

```python
# In ble/server.py -> BLEServer.handle_command()
elif action == "my_action":
    return self._my_action(command)
```

## Performance

**Ziel-Latenz**:
- DMX Update: < 1ms
- Poti → DMX: < 100ms
- Encoder → Display: < 50ms
- BLE Command: < 200ms

**Ressourcen** (Pi 3):
- RAM: ~100MB
- CPU: ~5-10%
- DMX Refresh: ~40 FPS

---

**Projekt-Version**: 1.0.0
**Letzte Änderung**: 2025-11-16
