#!/usr/bin/python3

import socket
import subprocess
import sys
from os import system


s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
s.bind((socket.VMADDR_CID_ANY, 52))
s.listen()

# Send we are ready
s0 = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
s0.connect((2, 52))
s0.close()

print("MANAGER READY")

while True:
    client, addr = s.accept()
    data = client.recv(1024)
    print("CID: {} port:{} data: {}".format(addr[0], addr[1], data))


    msg = data.decode().strip()

    print('msg', [msg])
    if msg == 'halt':
        system('sync')
        client.send(b'STOP\n')
        sys.exit()
    else:
        output = subprocess.check_output(msg, stderr=subprocess.STDOUT, shell=True)
        client.send(output)

    print('...DONE')
    client.close()

