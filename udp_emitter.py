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

def from_controller_state_to_dict(pControllerState):
    # docs: https://github.com/ValveSoftware/openvr/wiki/IVRSystem::GetControllerState
    d = {}
    d['unPacketNum'] = pControllerState.unPacketNum
    # on trigger .y is always 0.0 says the docs
    d['trigger'] = pControllerState.rAxis[1].x
    # 0.0 on trigger is fully released
    # -1.0 to 1.0 on joystick and trackpads
    d['trackpad_x'] = pControllerState.rAxis[0].x
    d['trackpad_y'] = pControllerState.rAxis[0].y
    # These are published and always 0.0
    # for i in range(2, 5):
    #     d['unknowns_' + str(i) + '_x'] = pControllerState.rAxis[i].x
    #     d['unknowns_' + str(i) + '_y'] = pControllerState.rAxis[i].y
    d['ulButtonPressed'] = pControllerState.ulButtonPressed
    d['ulButtonTouched'] = pControllerState.ulButtonTouched
    # To make easier to understand what is going on
    # Second bit marks menu button
    d['menu_button'] = bool(pControllerState.ulButtonPressed >> 1 & 1)
    # 32 bit marks trackpad
    d['trackpad_pressed'] = bool(pControllerState.ulButtonPressed >> 32 & 1)
    d['trackpad_touched'] = bool(pControllerState.ulButtonTouched >> 32 & 1)
    # third bit marks grip button
    d['grip_button'] = bool(pControllerState.ulButtonPressed >> 2 & 1)
    # System button can't be read, if you press it
    # the controllers stop reporting
    return d

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
            print(v.devices.keys())


            strData = ""

            devicename = "tracker_1"
            if(devicename in v.devices):
                trackerData = v.devices[devicename].get_pose_euler()
                strData += devicename + "_POSE " + ','.join(str(i) for i in trackerData) + "|"
            
            devicename = "controller_1"
            if(devicename in v.devices):
            #     print ("==========")
            #     print(v.devices['controller_1'].vr.getControllerState(0)[1])
            #     print(from_controller_state_to_dict(v.devices['controller_1'].vr.getControllerState(0)[1]))
                trackerData = v.devices[devicename].get_pose_euler()
                strData += devicename + "_POSE " + ','.join(str(i) for i in trackerData)
            #     #v.vr.triggerHapticPulse(handset.index,0,pulse)
            #     res, controllerState = v.vr.getControllerState(0)
            #     for i in controllerState.rAxis:
            #         print(i.x, i.y)
            #     print("controllerstate =>")
            #     print(from_controller_state_to_dict(controllerState))
            #     print(controllerState.ulButtonPressed)
            #     print(controllerState.ulButtonTouched)
            
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


