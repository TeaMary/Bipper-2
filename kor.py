import serial
import serial.tools.list_ports as sp
import math
import numpy as np
import struct
from matplotlib import pyplot as plt
import time

class LCcali:
    lx=[]
    ly=[]

    def connect(comport,baudrate):
        open_com=serial.Serial(comport,baudrate)
        open_com.isOpen()
        return open_com
        
    def scan(serial):
        open_com=serial
        value=bytearray([int('a5',16),int('60',16)])
        open_com.write(value)
        return open_com
    def receive(serial):
        read_data = serial.read(6000)
        #n=read_data.count(b"\xaa\x55") 
        n = 10    
        while(n>0):
            print(n)
            #a=read_data.find(b"\xaa\x55")
            a = 0
            read_data=read_data[a:]
            lsn = read_data[3]
            n=n-1
            #print(n)
            if(lsn!=1):
                print('lsn:',lsn)
                fsa1= read_data[4]
                fsa2= read_data[5]
                lsa1= read_data[6]
                lsa2= read_data[7]
                start_angle=(fsa2*64.0 + fsa1/4.0)/32.0
                end_angle=(lsa2*64.0 + lsa1/4.0)/32.0
                print(start_angle,end_angle)
                
                
                for i in range(1,lsn):
                    if(end_angle - start_angle<0):
                        lsn_angle=((end_angle+360.0-start_angle)/(lsn-1))*i+start_angle
                        
                        if(lsn_angle > 360.0):
                            lsn_angle=lsn_angle-360.0
                    else:
                        lsn_angle=((end_angle-start_angle)/(lsn-1))*i+start_angle

                    lsn_distance = (read_data[8+2*i+1]*64.0 + read_data[8+2*i]/4.0)
                    if(int(lsn_distance)==0):
                        lsn_angle = lsn_angle
                    else:
                        lsn_angle=lsn_angle+math.atan2(21.8*((155.3-lsn_distance)),155.3*lsn_distance)*180/math.pi
                        print(math.atan(21.8*((155.3-lsn_distance)/155.3*lsn_distance))*180/math.pi)
                        print(lsn_angle)
                    lidar_x=lsn_distance*math.cos(lsn_angle*(math.pi/180))
                    lidar_y=lsn_distance*math.sin(lsn_angle*(math.pi/180))
                    LCcali.lx.append(lidar_x)
                    LCcali.ly.append(lidar_y)
        return LCcali.lx, LCcali.ly

    def plot(lidar_x,lidar_y):
        plt.cla()
        plt.ylim(-9000,9000)
        plt.xlim(-9000,9000)
        plt.scatter(lidar_x,lidar_y)


open_com=LCcali.connect('/dev/ttyUSB0',128000)
open_com=LCcali.scan(open_com)
fig, ax = plt.subplots()
for i in range(50):
    lx,ly=LCcali.receive(open_com)

    


LCcali.plot(ly,lx)

plt.xlabel(lx)
plt.ylabel(ly)
fig.savefig('lidar_gr4.png')
open_com.close()
