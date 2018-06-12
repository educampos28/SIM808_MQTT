"""
Using SIM808 in non-transparent mode
"""

from time import sleep

######################################################################################################################
CONNECT =    1   #Client request to connect to Server                Client          Server
CONNACK =    2   #Connect Acknowledgment                             Server/Client   Server/Client
PUBLISH =    3   #Publish message                                    Server/Client   Server/Client
PUBACK  =    4   #Publish Acknowledgment                             Server/Client   Server/Client
PUBREC  =    5   #Publish Received (assured delivery part 1)         Server/Client   Server/Client
PUBREL  =    6   #Publish Release (assured delivery part 2)          Server/Client   Server/Client
PUBCOMP =    7   #Publish Complete (assured delivery part 3)         Server/Client   Server/Client
SUBSCRIBE=   8   #Client Subscribe request                           Client          Server
SUBACK   =   9   #Subscribe Acknowledgment                           Server          Client
UNSUBSCRIBE= 10  #Client Unsubscribe request                         Client          Server
UNSUBACK   = 11  #Unsubscribe Acknowledgment                         Server          Client
PINGREQ    = 12  #PING Request                                       Client          Server
PINGRESP   = 13  #PING Response                                      Server          Client
DISCONNECT = 14  #Client is Disconnecting                            Client          Server

# QoS value bit 2 bit 1 Description
#   0       0       0   At most once    Fire and Forget         <=1
#   1       0       1   At least once   Acknowledged delivery   >=1
#   2       1       0   Exactly once    Assured delivery        =1
#   3       1       1   Reserved
DUP_Mask    =     8   # Duplicate delivery   Only for QoS>0
QoS_Mask    =     6   # Quality of Service
QoS_Scale   =     2   # (()&QoS)/QoS_Scale
RETAIN_Mask =     1   # RETAIN flag

User_Name_Flag_Mask =  128
Password_Flag_Mask  = 64
Will_Retain_Mask    = 32
Will_QoS_Mask       = 24
Will_QoS_Scale      = 8
Will_Flag_Mask      = 4
Clean_Session_Mask  = 2

class MQTT:
    
    Modem = None
    Connected = False
    _ProtocolVersion = 3
    _KeepAliveTimeOut = 6000
    
    def __init__(self,Modem):
        self.Modem = Modem
        

    #https://public.dhe.ibm.com/software/dw/webservices/ws-mqtt/mqtt-v3r1.html#connect
    def connect(self,ClientIdentifier, UserNameFlag, PasswordFlag, UserName, Password, CleanSession, WillFlag, WillQoS, WillRetain, WillTopic, WillMessage):
        
        Fixed_Head = chr(CONNECT * 16)
        
        #Variable header
        ProtocolName = "MQIsdp"  
              
        localLength = 2 + len(ProtocolName) + 4  + 2 + len(ClientIdentifier);
        if (WillFlag != 0):
            localLength = localLength + 2 + len(WillTopic) + 2 + len(WillMessage);

        if (UserNameFlag != 0):
            localLength = localLength + 2 + len(UserName);
        
            if (PasswordFlag != 0):
                localLength = localLength + 2 + len(Password);

        
        msg = Fixed_Head
        msg = msg + self._Encode_Length(localLength)
        msg = msg + self._Encode_UTFString(ProtocolName)
        msg = msg + chr(self._ProtocolVersion)
        msg = msg + chr(UserNameFlag * User_Name_Flag_Mask + PasswordFlag * Password_Flag_Mask + WillRetain * Will_Retain_Mask + WillQoS * Will_QoS_Scale + WillFlag * Will_Flag_Mask + CleanSession * Clean_Session_Mask)
        msg = msg + chr(self._KeepAliveTimeOut/256)
        msg = msg + chr(self._KeepAliveTimeOut % 256)
        msg = msg + self._Encode_UTFString(ClientIdentifier)
        
        if (WillFlag != 0):
            msg = msg + WillTopic
            msg = msg + WillMessage
        
        if (UserNameFlag != 0):
            msg = msg + UserName

            if (PasswordFlag != 0):
                msg = msg + Password
 
        rs_msg = self.Modem.Send_TCP(msg,len(msg))
        
        if rs_msg[0] == chr(CONNACK*16) and rs_msg[2] == chr(0):
            print('MQTT broker connected')
            self.Connected = True
        else:
            print('MQTT broker not connected')
            self.Connected = False  
            
        return self.Connected            
        
        
    def publish(self,DUP, Qos, RETAIN, MessageID, Topic, Message):

        #=========================================================================
        # DUP       :This flag is set when the client or server attempts to re-deliver a PUBLISH message
        #           :This applies to messages where the value of QoS is greater than zero (0)
        #           :Possible values (0,1)
        #           :Default value 0
        # QoS       :Quality of Service
        #           :This flag indicates the level of assurance for delivery of a PUBLISH message
        #           :Possible values (0,1,2)
        #           :Default value 0
        # RETAIN    :if the Retain flag is set (1), the server should hold on to the message after it has been delivered to the current subscribers.
        #           :When a new subscription is established on a topic, the last retained message on that topic is sent to the subscriber
        #           :Possible values (0,1)
        #           :Default value 0
        # Message ID:The Message Identifier (Message ID) field
        #           :Used only in messages where the QoS levels greater than 0
        # Topic     :Publishing topic
        # Message   :Publishing Message
        #=========================================================================
    
        
        Fixed_Head = chr(PUBLISH * 16 + DUP * DUP_Mask + Qos * QoS_Scale + RETAIN)
        localLength = (2 + len(Topic));
        if (Qos > 0):
            localLength = localLength +2;
            
        localLength = localLength +  len(Message);
        
        msg = Fixed_Head
        msg = msg + self._Encode_Length(localLength);
        msg = msg + self._Encode_UTFString(Topic);
        if (Qos > 0):
            msg = msg + chr(MessageID / 256);
            msg = msg + chr(MessageID % 256);
            
        msg = msg + Message
            
        rs_msg = self.Modem.Send_TCP(msg,len(msg))
        
        if rs_msg[0] == chr(PUBACK*16) and rs_msg[1] == chr(2):
            print('publish success')
            return True
        else:
            print('publish fail')
            return False   
    
    def ping(self):
        
        msg = chr(PINGREQ * 16)
        msg = msg + self._Encode_Length(0);    
        
        rs_msg = self.Modem.Send_TCP(msg,len(msg))
        
        if rs_msg[0] == chr(PINGRESP*16) and rs_msg[1] == chr(0):
            print('ping success')
            return True
        else:
            print('ping fail')
            return False 
        
    def _Encode_Length(self , _len):
        length_flag = False;
        msg =''
        while (length_flag == False):
            if ((_len / 128) > 0):
                msg = msg + chr(_len % 128 + 128);
                _len = _len / 128;
            else:
                length_flag = True;
                msg = msg + chr(_len);
        return msg

    def _Encode_UTFString(self , string):
        localLength = len(string);
        msg = chr(localLength / 256);
        msg = msg + chr(localLength % 256);
        return  msg + string;
    
class TCP_IP:    
    
    Serial = None
    IP = None
    Connected = False
    Sock_Open = False
    Server_ip = None
    Server_port= None 
    
    def __init__(self,serial):
        self.Serial=serial
        

    def Init(self):
        
        try:
            
            #Firstly, before any TCP/UDP related operation is set up, 
            #the module should be connected to GSM or GPRS network
            replystr=('AT+CPIN?\r\r\n','#','\r\n','OK\r\n')        
            rs_msg = self.sendATretrieve('AT+CPIN?\r\n',replystr,0)
            if rs_msg <> '+CPIN: READY\r\n':
                print(rs_msg)
                assert False
            
            #received signal strength
            replystr=('AT+CSQ\r\r\n','*','\r\n','OK\r\n') 
            assert self.sendATreply('AT+CSQ\r\n',replystr,0) 
            
            #the registration of the ME.
            replystr=('AT+CREG?\r\r\n','+CREG: 0,1\r\n','\r\n','OK\r\n') 
            assert self.sendATreply('AT+CREG?\r\n',replystr,0)
    
            #GPRS Service status
            replystr=('AT+CGATT?\r\r\n','+CGATT: 1\r\n','\r\n','OK\r\n') 
            assert self.sendATreply('AT+CGATT?\r\n',replystr,0)
            
        except:
            print ('Fail to Initialize the GRPS modem')
            return False
        
        return True        
        
    def sendATreply(self, command, replystr, waitms): 
        # use * within replystr as wildcard
        
        ReplyFlag = True
        
        while self.Serial.in_waiting>0:
            self.Serial.flushInput()
            sleep(0.1) 
        
        self.Serial.write(command)
        sleep(waitms)
        for item in replystr:
            in_msg = self.Serial.readline()
            ReplyFlag = ReplyFlag and ((in_msg== item) or (item=='*'))  
    
        return ReplyFlag # True: Success / False: Fail
    
    def sendATretrieve(self, command, replystr, waitms): 
        # use * within replystr as wildcard
        
        ReplyFlag = True
        
        while self.Serial.in_waiting>0:
            self.Serial.flushInput()
            sleep(0.1)        
        
        self.Serial.write(command)
        sleep(0.1)
        for item in replystr:
            in_msg = self.Serial.readline()
            if (item == '#'):
                out_msg = in_msg
            else:
                ReplyFlag = ReplyFlag and ((in_msg== item) or (item=='*'))  
                
        if (not ReplyFlag):
            out_msg = "ERROR\r\n"
    
        return out_msg
    
    def Connect_GPRS(self):
        
        while not self.Init():
            print ('Try again in 10 seconds')
            sleep(10)
            print ('Trying now')
    

        #Verify the actual status
        replystr=('AT+CIPSTATUS\r\r\n','OK\r\n','\r\n','#') 
        rs_msg = self.sendATretrieve('AT+CIPSTATUS\r\n',replystr,0)
        
        if rs_msg == 'STATE: IP INITIAL\r\n':
            # Open a GPRS Connection
            try: 
                #Single Connection
                replystr=('AT+CIPMUX=0\r\r\n','OK\r\n') 
                assert self.sendATreply('AT+CIPMUX=0\r\n',replystr,0)
                
                #Non-transparent mode
                replystr=('AT+CIPMODE=0\r\r\n','OK\r\n') 
                assert self.sendATreply('AT+CIPMODE=0\r\n',replystr,0)
                
                #Start gprs connection 
                #Start task and set APN.
                replystr=('AT+CSTT="zap.vivo.com.br","vivo","vivo"\r\r\n','OK\r\n') 
                assert self.sendATreply('AT+CSTT="zap.vivo.com.br","vivo","vivo"\r\n',replystr,0)
                
                #Bring up wireless connection
                replystr=('AT+CIICR\r\r\n','OK\r\n') 
                assert self.sendATreply('AT+CIICR\r\n',replystr,0)
                
            
            except:
                print('GPRS Fail')       
            
        elif rs_msg == 'STATE: TCP CLOSED\r\n':
            pass
        
        elif rs_msg == 'STATE: CONNECT OK\r\n':
            pass
        
        elif rs_msg == 'STATE: TCP CONNECTING\r\n':
            pass
        
        else:
            #TODO -- Include others msg assessment
            print("GPRS Connection - Please include an assessment to the msg " + rs_msg)
            return False
            
        
        #Get local IP address
        replystr=('AT+CIFSR\r\r\n','#') 
        self.IP = self.sendATretrieve('AT+CIFSR\r\n',replystr,0)
        
        if (self.IP=='ERROR\r\n'):
            print(self.IP)
            return False
        else:
            self.Connected = True
            print(self.IP)
            return True
            
    def Close_All(self):
        
        #Deactivate the PDP context and close all connections
        sleep(0.5)
        self.Serial.flushInput()
        replystr=('AT+CIPSHUT\r\r\n','SHUT OK\r\n')
        try:
            assert self.sendATreply('AT+CIPSHUT\r\n',replystr,0)
        except:
            print('Diconnection Fail')
        
        self.Connected = False 
        
    def Service_Reconnect(self):
        
        self.Service_Connect(self.Server_ip,self.Server_port)
    
    def Service_Connect(self,IP,PORT):
        #Connect to a server
        
        connetion_flag = False
        
        self.Server_ip = IP
        self.Server_port= PORT        
        
                
        #Retrieve the actual TCP/IP status
        replystr=('AT+CIPSTATUS\r\r\n','OK\r\n','\r\n','#') 
        rs_msg = self.sendATretrieve('AT+CIPSTATUS\r\n',replystr,0)  
        
        while True:      
            if rs_msg == 'STATE: IP INITIAL\r\n':
                #something happend and GPRS connection had been lost 
                self.Connect_GPRS()
                
            elif rs_msg == 'STATE: TCP CLOSED\r\n':
                #Start up the connection
                payload ='"TCP","'+ IP + '","' + PORT +'"'        
                replystr=('AT+CIPSTART=' + payload + ' \r\r\n','OK\r\n')             

                #Start up the connection
                if not self.sendATreply('AT+CIPSTART='+ payload +' \r\n',replystr,0):
                    print('Some problem with the AT+CIPSTART command')
                    sleep(10)                        

                    
                #Retrieve againg the actual TCP/IP status   
                replystr=('AT+CIPSTATUS\r\r\n','OK\r\n','\r\n','#') 
                rs_msg = self.sendATretrieve('AT+CIPSTATUS\r\n',replystr,0)
                    
            elif rs_msg == 'STATE: TCP CONNECTING\r\n':
                #Waiting establish the connection
                sleep(10)
                #Retrieve againg the actual TCP/IP status
                replystr=('AT+CIPSTATUS\r\r\n','OK\r\n','\r\n','#') 
                rs_msg = self.sendATretrieve('AT+CIPSTATUS\r\n',replystr,0)
                print(rs_msg[:-2] + ' IP:' +self.Server_ip + ' Port:' +self.Server_port )
                
            elif rs_msg == 'STATE: CONNECT OK\r\n':
                print(rs_msg[:-2] + ' IP:' +self.Server_ip + ' Port:' +self.Server_port )
                connetion_flag = True
                break
                
            else:
                print("Include a msg assessment to:" + rs_msg )
                connetion_flag = False
                break
                
        return connetion_flag
    
    def Send_TCP(self,msg,length):
        
        replystr=('AT+CIPSTATUS\r\r\n','OK\r\n','\r\n', '#')
        rs_msg = self.sendATretrieve('AT+CIPSTATUS\r\n',replystr,0) 
        
        while True:
            if rs_msg == 'STATE: TCP CLOSED\r\n':
                #Connection has been lost. Reopen the connection
                self.Service_Reconnect()
                rs_msg = self.sendATretrieve('AT+CIPSTATUS\r\n',replystr,0) 
                
            elif rs_msg == 'STATE: CONNECT OK\r\n':
                break
            
            else:
                print('Something wrong happend at Send_TCP: ' + rs_msg)
                rs_msg = self.sendATretrieve('AT+CIPSTATUS\r\n',replystr,0) 
                
                
        replystr=('AT+CIPSEND='+ str(length) +'\r\r\n','#') 
        rs_msg = self.sendATretrieve('AT+CIPSEND='+ str(length)+'\r\n',replystr,1)
        

        if (rs_msg == '> '):
            self.Serial.write(msg)
            sleep(2)              
        else:
            print('There are some wrong with the AT+CIPSEND command: ' + rs_msg)
            assert False
            
        while (True):
            in_msg = self.Serial.readline()
            if (in_msg == 'SEND OK\r\n'):
                sleep(5)
                rs_msg = self.Serial.readline()
                break
            
            elif (in_msg == 'SEND FAIL\r\n'):
                rs_msg = 'SEND FAIL'
                print("Fail to send the msg to MQTT server")
                break
            
            elif in_msg[:-2] == msg: 
                pass
            
            elif in_msg == msg: 
                pass
            
            elif in_msg <> '':
                print("Not trated message:" + in_msg)
                
            elif in_msg == '':
                rs_msg = 'FAIL'
                break
            
                       
        
        return rs_msg

            
        
    
