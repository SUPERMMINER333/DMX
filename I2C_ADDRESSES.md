# Hardware-Konfiguration - I2C-Adressen

## Standard-Setup (wie ursprünglich vorgesehen):

```json
{
  "oled_address": "0x3C",
  "oled_enabled": true,
  "ads1115_address": 72
}
```

**I2C-Scan ergibt:**
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- --   <- OLED Display
40: -- -- -- -- -- -- -- -- 48 -- -- -- -- -- -- --   <- ADS1115 (72 dezimal = 0x48 hex)
```

---

## Aktuelles Setup (ADS1115 auf 0x3C, kein OLED):

```json
{
  "oled_address": null,
  "oled_enabled": false,
  "ads1115_address": 60
}
```

**I2C-Scan ergibt:**
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- --   <- ADS1115 (60 dezimal = 0x3C hex)
```

**Grund:** ADS1115 auf nicht-standardmäßiger Adresse (ADDR-Pin an VDD statt GND)

---

## Alternative Setup (beide Geräte):

Wenn Sie **beide** haben möchten:

**Hardware-Änderung:** ADS1115-Adresse ändern durch ADDR-Pin:
- ADDR → GND: Adresse 0x48 (Standard)
- ADDR → VDD: Adresse 0x49
- ADDR → SDA: Adresse 0x4A
- ADDR → SCL: Adresse 0x4B

**Konfiguration:**
```json
{
  "oled_address": "0x3C",
  "oled_enabled": true,
  "ads1115_address": 72
}
```

**I2C-Scan:**
```
30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- --   <- OLED
40: -- -- -- -- -- -- -- -- 48 -- -- -- -- -- -- --   <- ADS1115
```

---

## I2C-Adressen-Tabelle

| Gerät | Standard-Adresse | Alternativ | Dezimal |
|-------|------------------|------------|---------|
| **SSD1306 OLED** | 0x3C | 0x3D | 60 / 61 |
| **SH1106 OLED** | 0x3C | 0x3D | 60 / 61 |
| **ADS1115** | 0x48 | 0x49, 0x4A, 0x4B | 72 / 73 / 74 / 75 |

---

## Adresse herausfinden

```bash
# I2C-Geräte scannen
sudo i2cdetect -y 1

# Beispiel-Ausgabe:
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- --  <- Gerät auf 0x3C
40: -- -- -- -- -- -- -- -- 48 -- -- -- -- -- -- --  <- Gerät auf 0x48
...
```

**3c (hex) = 60 (dezimal)**
**48 (hex) = 72 (dezimal)**

---

## Aktuelles System

**Ihre Konfiguration:**
- ❌ Kein OLED Display
- ✅ ADS1115 (Potis) auf I2C-Adresse **0x3C** (60 dezimal)
- ✅ 4 Potentiometer an ADS1115 (A0-A3)
- ✅ 4 Rotary Encoder auf GPIO

**settings.json ist jetzt korrekt:**
```json
{
  "oled_enabled": false,
  "ads1115_address": 60
}
```

Das System startet jetzt **ohne** OLED-Display und nutzt den ADS1115 auf 0x3C.
