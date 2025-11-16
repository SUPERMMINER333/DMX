# Smartphone App Konzept

## BLE-basierte Steuerung für Android/iOS

Die DMX-Controller-App ermöglicht die drahtlose Steuerung über Bluetooth Low Energy.

## App-Spezifikation

### Technologien

**React Native** (empfohlen für Cross-Platform):
- React Native BLE Manager
- React Native Paper (UI)
- Redux für State Management

**Alternative - Native Apps**:
- Android: Kotlin + Android BLE API
- iOS: Swift + CoreBluetooth

### Features

1. **Dashboard**
   - Schnellzugriff auf alle Fixtures
   - Aktueller Controller-Status
   - Letzte verwendete Szenen

2. **Fixture-Steuerung**
   - Liste aller Fixtures
   - Einzelne Kanäle per Slider steuern
   - Farb-Picker für RGB/RGBW
   - Preset-Farben

3. **Szenen-Management**
   - Szenen speichern
   - Szenen abrufen
   - Szenen bearbeiten/löschen

4. **Fixture-Verwaltung**
   - Neue Fixtures hinzufügen
   - Fixtures bearbeiten
   - Fixtures löschen
   - Import/Export

### UI-Mockup

```
┌─────────────────────┐
│ DMX Controller      │  <- Header
├─────────────────────┤
│ 🔗 Connected        │  <- Status
├─────────────────────┤
│                     │
│ [Fixtures] [Scenes] │  <- Tabs
│                     │
│ ┌─────────────────┐ │
│ │ RGB Light 1     │ │
│ │ Ch 0-2          │ │
│ │ R: ▓▓▓▓▓░░░ 128 │ │  <- Sliders
│ │ G: ▓▓░░░░░░  64 │ │
│ │ B: ▓▓▓▓▓▓▓▓ 255 │ │
│ └─────────────────┘ │
│                     │
│ ┌─────────────────┐ │
│ │ RGBW PAR        │ │
│ │ Ch 10-13        │ │
│ │ [Color Picker]  │ │
│ └─────────────────┘ │
│                     │
└─────────────────────┘
```

## BLE-Integration

### Verbindung herstellen

```javascript
// React Native Beispiel
import BleManager from 'react-native-ble-manager';

const SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0';
const COMMAND_UUID = '12345678-1234-5678-1234-56789abcdef5';

async function connectToController() {
  // Scan für Geräte
  const devices = await BleManager.scan([], 5);

  // Finde DMX-Controller
  const controller = devices.find(d =>
    d.name === 'DMX-Pi' || d.name === 'DMX-Controller'
  );

  if (controller) {
    await BleManager.connect(controller.id);
    return controller.id;
  }
}
```

### Befehle senden

```javascript
async function sendCommand(deviceId, command) {
  const commandJson = JSON.stringify(command);
  const data = stringToBytes(commandJson);

  await BleManager.write(
    deviceId,
    SERVICE_UUID,
    COMMAND_UUID,
    data
  );

  // Antwort lesen
  const response = await BleManager.read(
    deviceId,
    SERVICE_UUID,
    COMMAND_UUID
  );

  return JSON.parse(bytesToString(response));
}

// Beispiel: Fixtures abrufen
const fixtures = await sendCommand(deviceId, {
  action: 'list_fixtures'
});

// Beispiel: Kanal setzen
await sendCommand(deviceId, {
  action: 'set_channel',
  channel: 0,
  value: 255
});
```

### Farb-Picker Integration

```javascript
import ColorPicker from 'react-native-color-picker';

function RGBFixtureControl({ fixture, deviceId }) {
  const [color, setColor] = useState('#ff0000');

  const handleColorChange = async (newColor) => {
    setColor(newColor);

    // RGB extrahieren
    const rgb = hexToRgb(newColor);

    // An Fixture senden
    await sendCommand(deviceId, {
      action: 'set_channel',
      channel: fixture.start_channel + 0,
      value: rgb.r
    });
    await sendCommand(deviceId, {
      action: 'set_channel',
      channel: fixture.start_channel + 1,
      value: rgb.g
    });
    await sendCommand(deviceId, {
      action: 'set_channel',
      channel: fixture.start_channel + 2,
      value: rgb.b
    });
  };

  return (
    <ColorPicker
      color={color}
      onColorChange={handleColorChange}
    />
  );
}
```

## Minimal App (Python für Desktop-Test)

Für schnelle Tests kann eine einfache Python-App mit Tkinter erstellt werden:

```python
import tkinter as tk
from tkinter import ttk
import json
from bluepy import btle

class DMXControllerApp:
    def __init__(self, master):
        self.master = master
        master.title("DMX Controller")

        # Verbindungsstatus
        self.status_label = tk.Label(master, text="Nicht verbunden")
        self.status_label.pack()

        # Verbinden Button
        self.connect_button = tk.Button(
            master,
            text="Verbinden",
            command=self.connect
        )
        self.connect_button.pack()

        # Fixture Liste
        self.fixture_frame = tk.Frame(master)
        self.fixture_frame.pack()

        self.device = None
        self.cmd_char = None

    def connect(self):
        try:
            # MAC-Adresse hier eintragen
            self.device = btle.Peripheral("B8:27:EB:XX:XX:XX")

            # Characteristic finden
            cmd_uuid = "12345678-1234-5678-1234-56789abcdef5"
            chars = self.device.getCharacteristics(uuid=cmd_uuid)
            self.cmd_char = chars[0]

            self.status_label.config(text="Verbunden")
            self.load_fixtures()
        except Exception as e:
            self.status_label.config(text=f"Fehler: {e}")

    def send_command(self, command):
        if self.cmd_char:
            cmd_json = json.dumps(command)
            self.cmd_char.write(cmd_json.encode())

            response = self.cmd_char.read()
            return json.loads(response.decode())
        return None

    def load_fixtures(self):
        response = self.send_command({"action": "list_fixtures"})

        if response and response['status'] == 'success':
            for fixture in response['fixtures']:
                self.add_fixture_control(fixture)

    def add_fixture_control(self, fixture):
        frame = tk.LabelFrame(
            self.fixture_frame,
            text=fixture['name']
        )
        frame.pack(pady=5)

        # Slider für jeden Kanal
        for ch in range(fixture['num_channels']):
            channel = fixture['start_channel'] + ch

            label = tk.Label(frame, text=f"Ch {channel}:")
            label.grid(row=ch, column=0)

            slider = tk.Scale(
                frame,
                from_=0,
                to=255,
                orient=tk.HORIZONTAL,
                command=lambda v, c=channel: self.set_channel(c, int(v))
            )
            slider.grid(row=ch, column=1)

    def set_channel(self, channel, value):
        self.send_command({
            "action": "set_channel",
            "channel": channel,
            "value": value
        })

# App starten
root = tk.Tk()
app = DMXControllerApp(root)
root.mainloop()
```

## React Native App Template

### package.json

```json
{
  "name": "dmx-controller-app",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-native": "^0.72.0",
    "react-native-ble-manager": "^10.0.0",
    "react-native-paper": "^5.9.0",
    "react-native-color-picker": "^0.6.0",
    "@react-navigation/native": "^6.1.0",
    "@react-navigation/bottom-tabs": "^6.5.0",
    "redux": "^4.2.0",
    "react-redux": "^8.1.0"
  }
}
```

### App.js (Grundstruktur)

```javascript
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet } from 'react-native';
import { Button, Card, Slider } from 'react-native-paper';
import BleManager from 'react-native-ble-manager';

const SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0';
const COMMAND_UUID = '12345678-1234-5678-1234-56789abcdef5';

export default function App() {
  const [connected, setConnected] = useState(false);
  const [deviceId, setDeviceId] = useState(null);
  const [fixtures, setFixtures] = useState([]);

  useEffect(() => {
    BleManager.start({ showAlert: false });
  }, []);

  const connectToController = async () => {
    try {
      const devices = await BleManager.scan([], 5);
      const controller = devices.find(d => d.name?.includes('DMX'));

      if (controller) {
        await BleManager.connect(controller.id);
        setDeviceId(controller.id);
        setConnected(true);
        loadFixtures(controller.id);
      }
    } catch (error) {
      console.error('Connection error:', error);
    }
  };

  const loadFixtures = async (deviceId) => {
    const response = await sendCommand(deviceId, {
      action: 'list_fixtures'
    });

    if (response?.status === 'success') {
      setFixtures(response.fixtures);
    }
  };

  const sendCommand = async (deviceId, command) => {
    // Implementation siehe oben
  };

  const setChannel = async (channel, value) => {
    await sendCommand(deviceId, {
      action: 'set_channel',
      channel,
      value
    });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>DMX Controller</Text>

      {!connected ? (
        <Button onPress={connectToController}>
          Verbinden
        </Button>
      ) : (
        <FlatList
          data={fixtures}
          renderItem={({ item }) => (
            <Card style={styles.card}>
              <Card.Title title={item.name} />
              <Card.Content>
                {[...Array(item.num_channels)].map((_, i) => (
                  <View key={i}>
                    <Text>Ch {item.start_channel + i}</Text>
                    <Slider
                      minimumValue={0}
                      maximumValue={255}
                      onValueChange={(v) =>
                        setChannel(item.start_channel + i, Math.round(v))
                      }
                    />
                  </View>
                ))}
              </Card.Content>
            </Card>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  card: {
    marginBottom: 10,
  },
});
```

## Deployment

### Android
```bash
cd dmx-controller-app
npx react-native run-android
```

### iOS
```bash
cd dmx-controller-app
cd ios && pod install && cd ..
npx react-native run-ios
```

## Nächste Schritte

1. BLE-Protokoll testen (siehe README.md)
2. React Native Projekt aufsetzen
3. UI nach Mockup designen
4. BLE-Integration implementieren
5. Testing auf echter Hardware

## Alternative: Web-App

Für eine schnellere Lösung kann auch eine Web-App mit Web Bluetooth API erstellt werden:

```html
<!DOCTYPE html>
<html>
<head>
  <title>DMX Controller</title>
</head>
<body>
  <h1>DMX Controller</h1>
  <button id="connect">Verbinden</button>
  <div id="fixtures"></div>

  <script>
    const SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0';
    const COMMAND_UUID = '12345678-1234-5678-1234-56789abcdef5';

    let device, characteristic;

    document.getElementById('connect').onclick = async () => {
      device = await navigator.bluetooth.requestDevice({
        filters: [{ name: 'DMX-Controller' }],
        optionalServices: [SERVICE_UUID]
      });

      const server = await device.gatt.connect();
      const service = await server.getPrimaryService(SERVICE_UUID);
      characteristic = await service.getCharacteristic(COMMAND_UUID);

      // Fixtures laden
      await loadFixtures();
    };

    async function sendCommand(command) {
      const encoder = new TextEncoder();
      await characteristic.writeValue(
        encoder.encode(JSON.stringify(command))
      );

      const value = await characteristic.readValue();
      const decoder = new TextDecoder();
      return JSON.parse(decoder.decode(value));
    }

    async function loadFixtures() {
      const response = await sendCommand({ action: 'list_fixtures' });
      // UI rendern...
    }
  </script>
</body>
</html>
```

---

Die App ermöglicht eine komfortable Steuerung des DMX-Controllers von überall in Bluetooth-Reichweite!
