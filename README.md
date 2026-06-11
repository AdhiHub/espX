# ESPX - ESP32 WiFi Auditor

[![Python](https://img.shields.io/badge/python-3.8+-red?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-ESP32-red?style=for-the-badge&logo=espressif&logoColor=white)](https://www.espressif.com/)
[![License](https://img.shields.io/badge/license-MIT-red?style=for-the-badge)](LICENSE)

**ESPX** is a Python-based WiFi auditing companion for ESP32. It turns your ESP32 into a portable WiFi reconnaissance tool — scan networks, deauth clients, flood beacons, capture handshakes, and crack passwords — all from one CLI.

```
╔══════════════════════════════════════════╗
║   ESPX - ESP32 WiFi Auditor  v1.0.0     ║
║   Author: Adhithya J (AdhiHub)          ║
╚══════════════════════════════════════════╝
```

---

## Features

| Feature | Description |
|---------|-------------|
| **WiFi Scan** | Scan visible access points via ESP32 radio |
| **Network List** | Display SSID, BSSID, channel, signal, encryption |
| **Target Select** | Choose target network for attacks |
| **Deauth Flood** | Disconnect clients from target AP |
| **Beacon Flood** | Spam fake access points (probe beacon frames) |
| **Handshake Crack** | Crack WPA/WPA2 captured handshakes |
| **Marauder Flash** | Auto-flash Marauder firmware to ESP32 |
| **Manual Mode** | Enter networks manually (no ESP32 needed) |

---

## Installation

### One-Liner Install

```bash
curl -fsSL https://raw.githubusercontent.com/AdhiHub/espX/main/install.sh | sudo bash
```

### Manual Install

```bash
git clone https://github.com/AdhiHub/espX.git
cd espX
pip install pyserial
chmod +x espX.py
sudo ln -sf $(pwd)/espX.py /usr/local/bin/espX
```

### Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| `pyserial` | Serial communication with ESP32 | `pip install pyserial` |
| `esptool` | Flash firmware to ESP32 | `pip install esptool` |
| `hashcat` | GPU-accelerated handshake cracking | `apt install hashcat` |

---

## Usage

### Interactive Mode

```bash
espX
```

```
     ███████╗███████╗██████╗ ██╗  ██╗
     ██╔════╝██╔════╝██╔══██╗╚██╗██╔╝
     █████╗  ███████╗██████╔╝ ╚███╔╝
     ██╔══╝  ╚════██║██╔═══╝  ██╔██╗
     ███████╗███████║██║     ██╔╝ ██╗
     ╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝

espX > help

   ESPX Commands
  ==================================================
  scan          Scan WiFi networks via ESP32
  list          List scanned networks
  target        Select a target network
  flash         Flash Marauder firmware to ESP32
  deauth        Deauth target network
  flood         Rapid deauth flood (100 packets)
  beacon        Start beacon flood (fake AP spam)
  crack         Crack captured handshake
  info          Show target info
  manual        Manual network entry
  exit          Exit ESPX
```

### CLI Mode

```bash
# Scan networks and exit
espX -p COM12 scan

# Crack a captured handshake
espX crack capture.pcap

# Flash Marauder firmware
espX -p COM12 flash
```

---

## Workflow

### 1. Connect ESP32
Plug in your ESP32 via USB. ESPX auto-detects it:

```
[12:34:56] ESP32 detected on COM12
[12:34:58] Connected to COM12 @ 115200 baud
```

### 2. Scan Networks
```
espX > scan

  SSID                      BSSID              CH   RSSI  ENC
  ----------------------------------------------------------------
  HomeNetwork               aa:bb:cc:dd:ee:ff   1    -45   WPA2
  NeighborWiFi              aa:bb:cc:11:22:33   6    -67   WPA3
  Guest                     aa:bb:cc:99:88:77   11   -72   OPEN
```

### 3. Select Target
```
espX > target

   Available Networks:
  ==================================================
  [1] HomeNetwork          aa:bb:cc:dd:ee:ff
  [2] NeighborWiFi         aa:bb:cc:11:22:33
  [3] Guest                aa:bb:cc:99:88:77

Select target [#]: 1
[12:35:10] Target set: HomeNetwork (aa:bb:cc:dd:ee:ff)
```

### 4. Deauth Clients
```
espX [HomeNetwork] > deauth
[12:35:15] Sending 5 deauth packets to HomeNetwork...
[12:35:15] Deauth complete
```

### 5. Flood (Mass Deauth)
```
espX [HomeNetwork] > flood
[12:35:20] Sending 50 deauth packets to HomeNetwork...
  Deauth packets sent: 50/50
[12:35:22] Deauth complete
```

### 6. Crack Handshake
```
espX > crack
  Method - hashcat/hc (default) or python/py:
Running: hashcat -m 22000 handshake.hccapx /usr/share/wordlists/rockyou.txt --force -O
```

---

## ESP32 Setup

### Flash Marauder Firmware
From inside ESPX:
```
espX > flash
[12:34:50] Flashing Marauder firmware to ESP32...
```

Or manually:
```bash
esptool.py --port COM12 --baud 115200 write_flash --flash_mode dio --flash_size detect 0x1000 ESP32Marauder.bin
```

### Supported ESP32 Boards
- ESP32 DevKit V1 (CP2102)
- ESP32 DevKit V4 (CP2102)
- ESP32-WROOM-32
- ESP32-S (CH340)
- ESP32-C3
- Any board with USB-to-UART bridge

---

## Cracking Methods

### Hashcat (Recommended)
```bash
espX crack capture.pcap
# Converts to hashcat 22000 format and cracks with rockyou
```

### Manual Hashcat
```bash
hcxpcapngtool capture.pcap -o handshake.hccapx
hashcat -m 22000 handshake.hccapx /usr/share/wordlists/rockyou.txt
```

### Python (Built-in)
ESPX includes a PBKDF2-based WPA2 cracker (slow but no deps):
```
Method - hashcat/hc (default) or python/py: py
Wordlist path (default: rockyou.txt):
```

---

## Architecture

```
┌───────────────────────────────────────────────────┐
│                   Your PC                          │
│  ┌─────────────────────────────────────────────┐  │
│  │               ESPX (Python)                  │  │
│  │  ┌─────────┐  ┌──────────┐  ┌────────────┐  │  │
│  │  │ Scanner │  │ Cracker  │  │ Serial I/O │  │  │
│  │  └────┬────┘  └────┬─────┘  └──────┬─────┘  │  │
│  └───────┼────────────┼───────────────┼────────┘  │
│          │            │               │            │
│          │            │         ╔═════╧══════╗     │
│          │            │         ║ USB Serial ║     │
│          │            │         ╚═════╤══════╝     │
└──────────┼────────────┼───────────────┼────────────┘
           │            │               │
      ┌────┴────────────┴───────────────┴────┐
      │            ESP32 (Marauder)           │
      │  ┌────────┐ ┌────────┐ ┌──────────┐  │
      │  │ 2.4GHz │ │ Packet │ │ Deauth   │  │
      │  │ Radio  │ │ Inject │ │ Engine   │  │
      │  └────────┘ └────────┘ └──────────┘  │
      └───────────────────────────────────────┘
                      │
            ┌─────────┴──────────┐
            │   Target WiFi AP    │
            │   (192.168.1.1)     │
            └────────────────────┘
```

---

## FAQ

**Q: Do I need an ESP32 to use ESPX?**  
A: No. Manual mode lets you enter networks and plan attacks manually. Scanning and deauth require the ESP32.

**Q: What firmware does the ESP32 need?**  
A: Marauder firmware is recommended. ESPX can auto-flash it via the `flash` command.

**Q: Can ESPX crack WPA3?**  
A: No. ESPX currently targets WPA/WPA2 (PSK) networks only.

**Q: How fast is the built-in Python cracker?**  
A: ~500-2000 passwords/sec. For serious cracking, use hashcat (millions/sec with GPU).

**Q: Does this work on Windows?**  
A: ESPX runs on any OS with Python 3, but the installer script is Linux-only. On Windows, run `python espX.py` directly.

**Q: Deauth not working?**  
A: Make sure your ESP32 has Marauder firmware flashed and the target is on 2.4GHz (ESP32 doesn't support 5GHz).

---

## Legal

```
  ╔═══════════════════════════════════════════════╗
  ║  Use at your own risk, developer assumes      ║
  ║  NO liability. For educational purposes only.  ║
  ╚═══════════════════════════════════════════════╝
```

This tool is for authorized security testing and educational purposes only. Unauthorized deauth attacks and network intrusion are illegal in most jurisdictions. The developer is not responsible for any misuse.

---

**Author:** Adhithya J (AdhiHub)  
**License:** MIT
