#!/usr/bin/python3
"""Voice chat relay: takes audio from each client and sends it to the others.

Run it with `python amongUs/src/server_voice.py`, which is the launcher.

Separate from the game's own server (port 4321) and unaware of it: this one
just forwards bytes between whoever is connected on 4322.
"""

import socket
import threading

class Server:
    def __init__(self):
            self.ip = socket.gethostbyname(socket.gethostname())
            while 1:
                try:
                    #self.port = int(input('Enter port number to run on --> '))
                    self.port = 4322
                    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.s.bind((self.ip, self.port))

                    break
                except:
                    print("Couldn't bind to that port")

            self.connections = []
            self.accept_connections()

    def accept_connections(self):
        self.s.listen(100)

        print('Running on IP: '+self.ip)
        print('Running on port: '+str(self.port))
        
        while True:
            c, addr = self.s.accept()

            self.connections.append(c)

            threading.Thread(target=self.handle_client,args=(c,addr,)).start()
        
    def broadcast(self, sock, data):
        for client in self.connections:
            if client != self.s and client != sock:
                try:
                    client.send(data)
                except:
                    pass

    def handle_client(self,c,addr):
        while 1:
            try:
                data = c.recv(1024)
                self.broadcast(c, data)
            
            except socket.error:
                c.close()

# Only when run as a program: Server() binds a port and blocks in accept(), so
# importing this module used to hang whatever imported it.
if __name__ == '__main__':
    server = Server()
