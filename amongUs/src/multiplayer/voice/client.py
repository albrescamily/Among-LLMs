#!/usr/bin/python3
"""Voice chat client: microphone out, everyone else's voices in.

Run it with `python amongUs/src/voice.py`, which is the launcher for this.

Independent of the game's own connection -- it has its own server on its own
port, and the game neither knows nor cares whether it is running.
"""

import socket
import threading
import pyaudio

class Client:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        while 1:
            try:
                self.target_ip = input('Enter IP address of server --> ')
                self.target_port = 4322

                self.s.connect((self.target_ip, self.target_port))

                break
            except:
                print("Couldn't connect to server")

        chunk_size = 1024 # 512
        audio_format = pyaudio.paInt16
        channels = 1
        rate = 20000

        # initialise microphone recording
        self.p = pyaudio.PyAudio()
        self.playing_stream = self.p.open(format=audio_format, channels=channels, rate=rate, output=True, frames_per_buffer=chunk_size)
        self.recording_stream = self.p.open(format=audio_format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk_size)
        
        print("Connected to Server")

        # start threads
        receive_thread = threading.Thread(target=self.receive_server_data).start()
        self.send_data_to_server()

    def receive_server_data(self):
        while True:
            try:
                data = self.s.recv(1024)
                self.playing_stream.write(data)
            except:
                pass


    def send_data_to_server(self):
        while True:
            try:
                data = self.recording_stream.read(1024)
                self.s.sendall(data)
            except:
                pass

# Only when run as a program: Client() prompts for an address and then never
# returns, so importing this module used to hang whatever imported it.
if __name__ == '__main__':
    client = Client()
