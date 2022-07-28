"""CD Chat client program"""
import fcntl
import logging
import os
import selectors
import sys
import socket
from time import time
from .protocol import CDProto, TextMessage

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)


class Client:
    """Chat Client process."""

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        self.name = name
        self.channel = None
        self.CDProto = CDProto()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = ('localhost', 4023)
        self.sel = selectors.DefaultSelector()

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        self.client_socket.connect(self.address)
        self.sel.register(self.client_socket, selectors.EVENT_READ, self.read)
        print(f"[CLIENT {self.name.upper()}] Connecting to {self.address[0]}:{self.address[1]}")
        self.CDProto.send_msg(self.client_socket, self.CDProto.register(self.name))

    def read(self, client_socket):
        new_msg = self.CDProto.recv_msg(client_socket)
        if type(new_msg) is TextMessage:
            print(new_msg.message)
            logging.debug(f"[CLIENT {self.name.upper()}] Received %s", new_msg)

    def get_kb_data(self, stdin):
        input_msg = stdin.read().rstrip()
        if input_msg != "":
            if input_msg[:5] == "/exit":
                self.sel.unregister(self.client_socket)
                self.client_socket.close()
                logging.debug(f'[CLIENT {self.name.upper()}] Client {self.name} left')
                sys.exit(f"Goodbye {self.name}!")
            elif input_msg[:5] == "/join":
                if len(input_msg[6:]) > 1:
                    self.channel = input_msg[5:]
                    sent_msg = self.CDProto.join(self.channel)
                    self.CDProto.send_msg(self.client_socket, sent_msg)
                    logging.debug(f'[CLIENT {self.name.upper()}] Sent {sent_msg}')
                else:
                    print("[ERROR] Invalid channel!")
            else:
                msg = self.CDProto.message(input_msg, self.channel)
                self.CDProto.send_msg(self.client_socket, msg)
                logging.debug(f"[CLIENT {self.name.upper()}] Sent %s", msg)

    def loop(self):
        """Loop indefinetely."""
        print(f"[CLIENT {self.name.upper()}] Connected successfully")
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)
        self.sel.register(sys.stdin, selectors.EVENT_READ, self.get_kb_data)
        while True: 
            sys.stdout.write("Write: ")
            sys.stdout.flush()
            for key, _ in self.sel.select():
                callback = key.data
                callback(key.fileobj)
        
