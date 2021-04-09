#!/usr/bin/python3

import socket
import subprocess
import sys
from os import system
from io import StringIO
from contextlib import redirect_stdout

s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
s.bind((socket.VMADDR_CID_ANY, 52))
s.listen()

# Send we are ready
s0 = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
s0.connect((2, 52))
s0.close()

print("INIT1 READY")

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
    elif msg.startswith('!'):
        # Shell
        msg = msg[1:]
        try:
            output = subprocess.check_output(msg, stderr=subprocess.STDOUT, shell=True)
            client.send(output)
        except subprocess.CalledProcessError as error:
            client.send(str(error).encode() + b'\n' + error.output)
    else:
        # Python
        try:
            with StringIO() as buf, redirect_stdout(buf):
                # Execute in the same process, saves ~20ms than a subprocess
                exec(msg)
                output = buf.getvalue().encode()
            client.send(output)
        except Exception as error:
            client.send(str(error).encode())

    print('...DONE')
    client.close()
