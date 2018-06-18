import triad_openvr
import time
import sys
import struct
import asyncore
from socket import *
import threading
import os


TRACKER_BROADCAST_PORT = 8053

DESKTOP_IP          = '192.168.1.133'
DESKTOP_LISTEN_PORT = 8059

class Server(asyncore.dispatcher_with_send): 
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        self.create_socket(AF_INET, SOCK_DGRAM)
        self.bind((DESKTOP_IP, DESKTOP_LISTEN_PORT))
        self.buffer = ''
        self.recvData = ''

    def handle_close(self):
        self.close()

    def handle_read(self):
        try: 
            print (self.recv(8192)) #8192 is buffer size, not port
            # self.buffer ='a'
        except e:
            print(e)

    def handle_write(self):
        if self.buffer != '':
            sent = self.sendto(self.buffer,('192.168.1.154',8054)) ## RECEIVING ON PORT 8054
            self.buffer = self.buffer[sent:]



def main(): 
    loop_thread = threading.Thread(target=asyncore.loop, name="Asyncore Loop", daemon=True)

    The_Server = Server()


    loop_thread.start() 

    cs = socket(AF_INET, SOCK_DGRAM)
    cs.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    cs.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

    server_address = ('255.255.255.255', TRACKER_BROADCAST_PORT) 

    v = triad_openvr.triad_openvr()
    v.print_discovered_objects()

    if len(sys.argv) == 1:
        # interval = 1/50
        interval = 1/250
    elif len(sys.argv) == 2:
        interval = 1/float(sys.argv[1])
    else:
        print("Invalid number of arguments")
        interval = False
        
    if interval:
        print("hi") 
        while(True):
            start = time.time()
            txt = ""
            data = v.devices["tracker_1"].get_pose_quaternion()
            # byteData = bytes(data, "utf-8")
            strData = ','.join(str(i) for i in data)
            # strData = str(data[4])
            # strData =  strData[:strData.find(".")]
            print(strData)
            
            byteData = bytes(strData, "utf-8")
            cs.sendto(byteData , server_address)
            

            print("\r" + txt, end="")
            sleep_time = interval-(time.time()-start)
            if sleep_time>0:
                time.sleep(sleep_time)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Stopping tracking!")
        sys.exit(0)
    except Exception as e:
        print(str(e))
        if(str(e) == 'tracker_1'):
            print("Tracker is not being tracked!")
        else:
            print("other exception:", e)


