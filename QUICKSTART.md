# DMX Controller - Quick Start Guide

Schnellstart in 5 Minuten (ohne Hardware-Test)

## 1. System vorbereiten (einmalig)

```bash
# I2C und Serial aktivieren
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_serial 2

# Pakete installieren
sudo apt-get update
sudo apt-get install -y python3 python3-pip i2c-tools

# Python-Abhängigkeiten
pip3 install -r requirements.txt

# Berechtigungen
sudo usermod -a -G dialout,gpio,i2c $USER

# Reboot
sudo reboot
```

## 2. Erste Fixtures anlegen

```bash
cd /home/user/DMX

# CLI starten
python3 cli_tool.py

# Im CLI:
DMX> quick_add rgbw
Fixture ID: light1
Fixture Name: Hauptlicht
Start Channel: 0

DMX> quick_add rgb
Fixture ID: light2
Fixture Name: Hintergrund
Start Channel: 10

DMX> list
DMX> save
DMX> exit
```

## 3. Controller starten

```bash
# Manuell testen
python3 main.py

# Als Service
sudo cp dmx-controller.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start dmx-controller.service
sudo systemctl status dmx-controller.service
```

## 4. Testen

### DMX testen
```python
python3 -c "
from lib.dmx import Dmx
import time

dmx = Dmx('/dev/ttyUSB0')
dmx.start()
dmx.set_channel(0, 255)  # Kanal 0 auf max
time.sleep(2)
dmx.set_channel(0, 0)    # Kanal 0 auf 0
dmx.stop()
print('DMX OK!')
"
```

### I2C testen
```bash
sudo i2cdetect -y 1
# Sollte 0x3C (OLED) und 0x48 (ADS1115) zeigen
```

## 5. Hardware anschließen

### OLED (I2C)
```
OLED  ->  Pi
VCC   ->  3.3V
GND   ->  GND
SDA   ->  GPIO 2
SCL   ->  GPIO 3
```

### ADS1115 (I2C)
```
ADS   ->  Pi
VDD   ->  3.3V
GND   ->  GND
SDA   ->  GPIO 2
SCL   ->  GPIO 3
```

### Potis
```
Poti    ->  ADS1115
Wiper   ->  A0, A1, A2, A3
Links   ->  GND
Rechts  ->  3.3V
```

## Fertig! 🎉

**Service läuft jetzt automatisch beim Boot**

### Nächste Schritte:

- **Fixtures verwalten**: `python3 cli_tool.py`
- **Logs ansehen**: `tail -f logs/dmx_controller.log`
- **Status prüfen**: `sudo systemctl status dmx-controller`
- **Smartphone-App**: Siehe `SMARTPHONE_APP.md`

### Häufige Befehle:

```bash
# Service starten/stoppen
sudo systemctl start dmx-controller
sudo systemctl stop dmx-controller
sudo systemctl restart dmx-controller

# Logs
sudo journalctl -u dmx-controller -f

# Fixtures verwalten
python3 cli_tool.py
```

### Tastatur-Shortcuts (CLI):

- `list` - Fixtures auflisten
- `show <id>` - Details anzeigen
- `quick_add rgb|rgbw` - Schnell hinzufügen
- `save` - Speichern
- `exit` - Beenden

---

**Bei Problemen**: Siehe `README.md` oder `INSTALL.md`
