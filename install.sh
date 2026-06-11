#!/bin/bash

R='\033[1;31m'
G='\033[1;32m'
Y='\033[1;33m'
B='\033[1;34m'
C='\033[1;36m'
D='\033[0m'

echo -e ""
echo -e "  ${R}╔═══════════════════════════════════════════════╗${D}"
echo -e "  ${R}║           ${G}ESPX${R} - ESP32 WiFi Auditor            ║${D}"
echo -e "  ${R}║       ${Y}Author: Adhithya J (AdhiHub)${R}          ║${D}"
echo -e "  ${R}╚═══════════════════════════════════════════════╝${D}"
echo -e ""

if [ "$(id -u)" != "0" ]; then
    echo -e "  ${Y}[!] This script requires root privileges${D}"
    echo -e "  ${Y}[!] Re-running with sudo...${D}\n"
    exec sudo bash "$0" "$@"
    exit 1
fi

echo -e "  ${C}[*] Installing ESPX...${D}\n"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/usr/share/espX"
LINK_PATH="/usr/local/bin/espX"

if [ -d "$INSTALL_DIR" ]; then
    echo -e "  ${Y}[*] Removing old installation...${D}"
    rm -rf "$INSTALL_DIR"
fi

echo -e "  ${G}[+] Creating installation directory...${D}"
mkdir -p "$INSTALL_DIR"

echo -e "  ${G}[+] Installing Python dependencies...${D}"
pip3 install pyserial 2>/dev/null || pip install pyserial 2>/dev/null

echo -e "  ${G}[+] Copying files...${D}"
cp "$SCRIPT_DIR/espX.py" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/espX.py"

echo -e "  ${G}[+] Creating symlink...${D}"
ln -sf "$INSTALL_DIR/espX.py" "$LINK_PATH"
chmod +x "$LINK_PATH"

echo -e ""
echo -e "  ${G}╔═══════════════════════════════════════════════╗${D}"
echo -e "  ${G}║             Installation Complete!            ║${D}"
echo -e "  ${G}╚═══════════════════════════════════════════════╝${D}"
echo -e ""
echo -e "  ${C}Usage:${D}"
echo -e "  ${G}espX${D}"
echo -e ""
echo -e "  ${Y}Example:${D}"
echo -e "  ${G}espX                                 # Interactive mode${D}"
echo -e "  ${G}espX -p COM12                        # Specify ESP32 port${D}"
echo -e "  ${G}espX -p /dev/ttyUSB0 scan            # Scan networks${D}"
echo -e "  ${G}espX crack capture.pcap              # Crack handshake${D}"
echo -e ""
echo -e "  ${Y}Dependencies:${D}"
echo -e "  ${G}esptool.py   - Flash firmware (pip install esptool)${D}"
echo -e "  ${G}hashcat      - Crack handshakes${D}"
echo -e ""
echo -e "  ${R}╔═══════════════════════════════════════════════╗${D}"
echo -e "  ${R}║  Use at your own risk, developer assumes      ║${D}"
echo -e "  ${R}║  NO liability. For educational purposes only.  ║${D}"
echo -e "  ${R}╚═══════════════════════════════════════════════╝${D}"
echo -e ""
