"""CD Chat server program."""
import logging
import selectors
import socket
from .protocol import CDProto

logging.basicConfig(filename="server.log", level=logging.DEBUG)


class Server:
    """Chat Server process."""

    def __init__(self):
        """Start the server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = ("localhost", 4023)
        self.server_socket.bind(self.address)
        print("[SERVER] Server is up and running")
        logging.debug('[SERVER] Starting')
        self.server_socket.listen()
        self.conns_names = {}
        self.list_users = {}
        self.sel = selectors.DefaultSelector()
        self.sel.register(self.server_socket, selectors.EVENT_READ, self.accept)

    def loop(self):
        """Loop indefinetely."""
        print(f"[SERVER] Listening on {self.address[0]}:{self.address[1]}")
        while True:
            events = self.sel.select()
            for key, _ in events:
                callback = key.data
                callback(key.fileobj)

    def accept(self, server_socket):
        conn, addr = server_socket.accept()  # Should be ready
        print(f"[SERVER] Accepted client {addr[0]}:{addr[1]}")
        logging.debug('[SERVER] Accepted client %s:%s', addr[0], addr[1])
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn):
        message = CDProto.recv_msg(conn)
        if message:
            logging.debug('[SERVER] Received %s', message)
            if message.command == "register":
                print(f"[SERVER] {message.user} has joined the server")
                self.conns_names[conn] = message.user
                self.list_users[conn] = [None] 
            elif message.command == "join":
                active_channels = self.list_users.get(conn)
                if active_channels == [None]:
                    self.list_users[conn] = [message.channel]
                else:
                    active_channels.append(message.channel)
                print(f"[SERVER] User {self.conns_names[conn]} joined the channel{self.list_users[conn][0]}")
            elif message.command == "message":
                message_content = message.message
                channel = message.channel
                print(f"[SERVER] {self.conns_names[conn]}({channel}): {message.message}")
                send_msg = (f"\n{self.conns_names[conn]}: {message_content}")
                msg_obj = CDProto.message(send_msg, channel)
                logging.debug('received "%s' , msg_obj.__repr__)
                for connection, list_channel in self.list_users.items(): 
                    if (connection != conn and channel in list_channel):
                        CDProto.send_msg(connection,msg_obj)
        else:
            try:
                print(f"[SERVER] User {self.conns_names[conn]} has left the server")
                logging.debug('[SERVER] Client %s left', self.conns_names[conn] )
                del self.conns_names[conn]   
            except KeyError as e:
                if (len(self.conns_names)==1):
                    self.conns_names={}
            self.sel.unregister(conn)
