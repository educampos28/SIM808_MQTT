#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pydevd


from SIM808 import SIM808

#Raspberry Serial Connection
import serial
Serial_Port='/dev/ttyS0'
Serial = serial.Serial(port=Serial_Port, baudrate=9600, bytesize=serial.EIGHTBITS, 
               parity=serial.PARITY_NONE, 
               stopbits=serial.STOPBITS_ONE, timeout=10, 
               xonxoff=False, rtscts=False, 
               writeTimeout=None, dsrdtr=True, 
               interCharTimeout=None)


if __name__ == "__main__":
    
    pydevd.settrace("192.168.0.14", port=5678,stdoutToServer=True, stderrToServer=True)
    
    Modem = SIM808.TCP_IP(Serial)
    
    MQTT = SIM808.MQTT(Modem)
    
    try:
        #Open a GRPS Network
        Modem.Connect()
        
        #MQTT host and port
        Modem.Service_Connect('179.190.169.78','1883')
        
        MQTT.connect("qwertyuiopzzbr", 0, 0, "", "", 1, 0, 0, 0, "", "")
        
        msg_ID=1
        MQTT.publish(0, 0, 0, msg_ID, "Teste", "Hello");
        
        while(True):
            pass
        
        
    except KeyboardInterrupt:
        print "Program finished\n"
        Modem.Close_All()
    
    except:
        Modem.Close_All()
        
