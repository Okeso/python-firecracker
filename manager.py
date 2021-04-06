#!/usr/bin/python3

import socket

s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
s.bind((socket.VMADDR_CID_ANY, 52))
s.listen()

while True:
    client, addr = s.accept()
    data = client.recv(1024)
    print("CID: {} port:{} data: {}".format(addr[0], addr[1], data))
    client.send(b'YOLO\n')
    client.close()

