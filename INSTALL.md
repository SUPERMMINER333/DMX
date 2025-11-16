# Installationsanleitung - DMX Controller

Diese Anleitung führt Sie Schritt für Schritt durch die Installation des DMX Controllers auf Ihrem Raspberry Pi 3.

## Voraussetzungen

- Raspberry Pi 3 (oder neuer) mit Raspberry Pi OS (Bullseye oder Bookworm)
- SD-Karte mit mindestens 8GB
- Internetverbindung
- SSH-Zugriff oder Monitor/Tastatur

## Schritt 1: System vorbereiten

```bash
# System aktualisieren
sudo apt-get update
sudo apt-get upgrade -y

# Benötigte System-Pakete installieren
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-setuptools \
    i2c-tools \
    git \
    bluetooth \
    bluez \
    libbluetooth-dev \
    libglib2.0-dev \
    libdbus-1-dev \
    python3-gi \
    fonts-freefont-ttf \
    fonts-dejavu-core

# Reboot empfohlen
sudo reboot
```

## Schritt 2: I2C und Serial aktivieren

```bash
# raspi-config öffnen
sudo raspi-config

# Navigieren Sie zu:
# 3 Interface Options
#   -> I2C -> Enable
#   -> Serial Port
#      -> Login shell over serial: NO
#      -> Serial port hardware: YES

# Alternativ direkt:
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_serial 2

# Reboot
sudo reboot
```

## Schritt 3: I2C-Geräte testen

```bash
# Nach dem Reboot I2C-Bus scannen
sudo i2cdetect -y 1

# Erwartetes Ergebnis (wenn Hardware angeschlossen):
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- --
# 40: -- -- -- -- -- -- -- -- 48 -- -- -- -- -- -- --
# 50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 70: -- -- -- -- -- -- -- --

# 0x3C = OLED Display
# 0x48 = ADS1115 ADC
```

## Schritt 4: Python-Pakete installieren

```bash
# In das Projektverzeichnis wechseln
cd /home/user/DMX

# Virtuelle Umgebung erstellen (optional aber empfohlen)
python3 -m venv venv
source venv/bin/activate

# Pip upgraden
pip install --upgrade pip

# Projektabhängigkeiten installieren
pip install -r requirements.txt

# Falls Fehler auftreten, einzeln installieren:
pip install pyserial
pip install RPi.GPIO
pip install Adafruit-ADS1x15
pip install adafruit-circuitpython-ads1x15
pip install luma.oled
pip install luma.core
pip install Pillow
pip install dbus-python
pip install PyGObject
pip install colorlog
```

## Schritt 5: Berechtigungen setzen

```bash
# Aktuellen Benutzer zu notwendigen Gruppen hinzufügen
sudo usermod -a -G dialout,gpio,i2c,bluetooth $USER

# GPIO-Berechtigungen (falls nötig)
sudo chown -R root:gpio /sys/class/gpio
sudo chmod -R g+rw /sys/class/gpio

# Überprüfen
groups $USER
# Sollte enthalten: dialout gpio i2c bluetooth

# WICHTIG: Ausloggen und wieder einloggen (oder reboot)
sudo reboot
```

## Schritt 6: DMX-Interface testen

```bash
# USB-DMX-Interface anschließen und Port finden
ls -l /dev/ttyUSB*
# Sollte zeigen: /dev/ttyUSB0

# Wenn nicht /dev/ttyUSB0, dann in config/settings.json anpassen

# Test-Skript
python3 << EOF
from lib.dmx import Dmx
import time

dmx = Dmx(port="/dev/ttyUSB0")
dmx.start()
dmx.set_channel(0, 255)  # Kanal 0 auf 100%
time.sleep(2)
dmx.set_channel(0, 0)    # Kanal 0 auf 0%
dmx.stop()
print("DMX Test erfolgreich!")
EOF
```

## Schritt 7: Konfiguration anpassen

```bash
# Verzeichnisse erstellen
mkdir -p config data logs

# Einstellungen anpassen (wird beim ersten Start automatisch erstellt)
# Optional: Manuell erstellen
cat > config/settings.json << 'EOF'
{
  "dmx_port": "/dev/ttyUSB0",
  "dmx_baudrate": 250000,
  "oled_address": "0x3C",
  "oled_type": "ssd1306",
  "ads1115_address": 72,
  "log_level": "INFO",
  "encoder_pins": {
    "encoder_1": {"a": 15, "b": 18, "btn": 17},
    "encoder_2": {"a": 22, "b": 23, "btn": 24},
    "encoder_3": {"a": 25, "b": 8, "btn": 7},
    "encoder_4": {"a": 12, "b": 16, "btn": 20}
  }
}
EOF
```

## Schritt 8: Erste Fixtures anlegen

```bash
# CLI-Tool starten
python3 cli_tool.py

# Im CLI:
DMX> quick_add rgbw
Fixture ID: light1
Fixture Name: Hauptlicht
Start Channel: 0

DMX> list
# Sollte das Fixture anzeigen

DMX> save
DMX> exit
```

## Schritt 9: Service einrichten (Optional)

```bash
# Service-Datei kopieren
sudo cp dmx-controller.service /etc/systemd/system/

# Pfade in Service-Datei anpassen (falls nötig)
sudo nano /etc/systemd/system/dmx-controller.service

# User/Group auf Ihren Benutzer setzen (statt 'pi')
# WorkingDirectory und ExecStart anpassen falls nötig

# Service aktivieren
sudo systemctl daemon-reload
sudo systemctl enable dmx-controller.service

# Service starten
sudo systemctl start dmx-controller.service

# Status prüfen
sudo systemctl status dmx-controller.service

# Logs ansehen
sudo journalctl -u dmx-controller.service -f
```

## Schritt 10: Test

```bash
# Manueller Test
python3 main.py

# Sie sollten sehen:
# - "DMX Controller Service v1.0" Banner
# - "DMX started on /dev/ttyUSB0"
# - "All components started successfully"
# - OLED Display zeigt "DMX Controller Ready!"

# Ctrl+C zum Beenden
```

## GPIO-Pinbelegung (BCM-Nummerierung)

### Standard-Konfiguration:

**Encoder 1:**
- Pin A: GPIO 15
- Pin B: GPIO 18
- Button: GPIO 17

**Encoder 2:**
- Pin A: GPIO 22
- Pin B: GPIO 23
- Button: GPIO 24

**Encoder 3:**
- Pin A: GPIO 25
- Pin B: GPIO 8
- Button: GPIO 7

**Encoder 4:**
- Pin A: GPIO 12
- Pin B: GPIO 16
- Button: GPIO 20

**I2C (für OLED & ADS1115):**
- SDA: GPIO 2 (Pin 3)
- SCL: GPIO 3 (Pin 5)

### Anschlussbelegung ändern

Bearbeiten Sie `config/settings.json`:

```json
{
  "encoder_pins": {
    "encoder_1": {"a": 15, "b": 18, "btn": 17},
    ...
  }
}
```

## Hardware-Verkabelung

### OLED Display (I2C)
```
OLED    ->  Raspberry Pi
VCC     ->  3.3V
GND     ->  GND
SDA     ->  GPIO 2 (SDA)
SCL     ->  GPIO 3 (SCL)
```

### ADS1115 (I2C)
```
ADS1115  ->  Raspberry Pi
VDD      ->  3.3V oder 5V
GND      ->  GND
SDA      ->  GPIO 2 (SDA)
SCL      ->  GPIO 3 (SCL)

A0-A3    ->  Potentiometer (Wiper zu ADS, Enden zu GND und 3.3V)
```

### Potentiometer
```
Poti    ->  ADS1115
Wiper   ->  A0-A3
Ende 1  ->  GND
Ende 2  ->  3.3V
```

### Rotary Encoder
```
Encoder  ->  Raspberry Pi
A        ->  GPIO (siehe Konfiguration)
B        ->  GPIO
Button   ->  GPIO
GND      ->  GND
VCC      ->  3.3V (falls benötigt)
```

## Fehlerbehebung

### I2C-Geräte werden nicht erkannt

```bash
# I2C-Module laden
sudo modprobe i2c-dev
sudo modprobe i2c-bcm2708

# In /etc/modules eintragen für automatisches Laden
echo "i2c-dev" | sudo tee -a /etc/modules
```

### Permissions-Fehler

```bash
# Neu einloggen oder:
newgrp dialout
newgrp gpio
newgrp i2c
```

### DMX funktioniert nicht

```bash
# Port prüfen
dmesg | grep ttyUSB

# Manuelle Rechte
sudo chmod 666 /dev/ttyUSB0
```

### Python-Module fehlen

```bash
# Komplett neu installieren
pip install --force-reinstall -r requirements.txt
```

## Deinstallation

```bash
# Service stoppen und deaktivieren
sudo systemctl stop dmx-controller.service
sudo systemctl disable dmx-controller.service
sudo rm /etc/systemd/system/dmx-controller.service
sudo systemctl daemon-reload

# Virtuelle Umgebung entfernen
rm -rf venv

# Projekt entfernen
cd ~
rm -rf /home/user/DMX
```

## Support

Bei Problemen:

1. **Logs prüfen**: `tail -f logs/dmx_controller.log`
2. **System-Logs**: `sudo journalctl -u dmx-controller.service -n 50`
3. **Debug-Modus**: `log_level: "DEBUG"` in `config/settings.json`

---

**Installation erfolgreich!** 🎉

Nächste Schritte:
- Fixtures über CLI hinzufügen (`python3 cli_tool.py`)
- Service starten (`sudo systemctl start dmx-controller`)
- Smartphone-App verbinden (siehe README.md BLE-Protokoll)
