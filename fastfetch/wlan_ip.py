#!/data/data/com.termux/files/usr/bin/python3
import fcntl
import socket
import struct

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = socket.inet_ntoa(
        fcntl.ioctl(s.fileno(), 0x8915, struct.pack("256s", b"wlan0"))[20:24]
    )
    print("wlan0: " + ip)
except Exception:
    print("wlan0: sin conexion")
