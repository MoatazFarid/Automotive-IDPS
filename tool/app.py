'''
    CAN Bus Vulnerability tool
    This tool is part of Automotive IDPS and Cyber Security Vulnerability tool Graduation Project
Usage:
    app.py sniff [--port=COM6] [--baudrate=115200] [--d] [--conf=path] [--out] [( [--BL] [--v] --case=name )]
    app.py spoof [( <target_ecu_name> <msg_name> <signal_name> <new_val> )][--port=COM6] [--baudrate=115200] [--d] [--conf=path]
Options:
    --port=COM6         Select the port we connected our UCAN on default is COM6
    --baudrate=115200   Select the BaudRate we use default is 115200
    --d                 Debug mode
    --conf=path         Path of the xml config file default is conf.xml file name in same directory of the script
    --out               output the log of the sniffing to log.txt file
    --BL                calculate the busload and insert it into external file
    --v                 visualise the outputs
    --case=name         name the case which is used as Busload file name
'''
import datetime
import thread

try:
    import sys,serial,time,binascii,UCAN,sched
    from docopt import docopt
    import matplotlib.pyplot as plt
    import csv
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
    data=None #long
    RTR=0#bool


''' Global Variables'''
sniffed_Msgs=[]
LOG = None
MSG_COUNTER = 0
MSG_LATEST_COUNT=0 #used in bus load
MSG_TEMP=0 #used in bus load function
RATE=0 #used in bus load function
CASENAME =""


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
    Lamb_ONOFF.frame_id = int('0x62',16)
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

## Bus load calculations
def calc_BusLoad():
    global MSG_TEMP
    global MSG_COUNTER
    global MSG_LATEST_COUNT
    MSG_TEMP=MSG_COUNTER-MSG_LATEST_COUNT
    MSG_LATEST_COUNT=MSG_COUNTER
    RATE=(MSG_TEMP/3906)*100
    print('calc bus load hh')
    file=open("dd.txt","a+")
    file.write(str(RATE)+"\n")
    file.close()
    s.enter(1,1,calc_BusLoad,())

#start connection
try:
    ser = serial.Serial(COM_PORT, BaudRate)
except serial.serialutil.SerialException:
    print '====================================================='
    print ("Not connected")
    print '====================================================='
    exit(0)


def startAuth():
    ''' This function handle the Authentication with the usb to CAN '''
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


def sniff():
    ''' start sniffing over the CAN bus  '''
    # print(chr(27) + "[2J") #clear screen
    print "++++++++= Start Sniffing CAN Bus =++++++++"
    while True:
        #convert from byte to hex string
        framebuffer=ser.read(13).encode("hex")
        if DEBUG==True :
            print "DEBUG-> SERIAL is ",framebuffer
        # bin(int(framebuffer,16)) #converted into binary
        msg = canFrameDecodder(framebuffer)
        printMsg(msg)

def closeConn():
    ''' close the connections and exit system '''
    ser.close()
    sys.exit(0)


def getFrameData(frame, dlc):
    if DEBUG==True :
        print "DEBUG --> getFrameData-> dlc is ",dlc
    data = frame[12:12+(2*dlc)]
    if DEBUG==True :
        print "DEBUG --> Data is ",data
    return data

def getFrameDLC(frame):
    dlc = int(frame[10:12],16) & 0x0F
    if DEBUG==True :
        print "DEBUG --> DLC is ",dlc,type(dlc)
    return dlc

def canFrameDecodder(frame):
    msg = CAN_MSG()
    msg.frame_id = getStandardID(frame)
    msg.frame_dlc = getFrameDLC(frame)
    msg.data = getFrameData(frame,msg.frame_dlc)
    return msg

def getStandardID(frame):
    ''' encode the standard it '''
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
    file = open(fileName,'a')
    file.write(log)
    file.close()

def printMsg(msg):
    ''' Print the sniffed msg '''
    global MSG_COUNTER
    log = str((MSG_COUNTER))+'  @  '+datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')+("    ||  ID :")+str(msg.frame_id)+"  ||  DLC:"+str(msg.frame_dlc)+"   ||  Data:"+str(msg.data) +'\n'
    MSG_COUNTER +=1
    if LOG != None:
        sendToLog(log,LOG)
    if idExists(msg):
        # print "found"
        pass
        # print(chr(27) + "[2J") #clear screen
    else:
        sniffed_Msgs.append(msg)
        print log

def idExists(msg):
    ''' This function is used to check if the recieved msg has been seen before or not , it is used in the printMsg function '''
    for s in sniffed_Msgs:
        if (s.frame_id == msg.frame_id) and (s.data==msg.data):
            return True
    return False

def isExtendedID(IDE):
    ''' Check whether the function '''
    if IDE=='1' or  IDE== 1:
        return True
    else:
        return False


def sendTestFrame():
    msg=UCAN.CAN_MSG
    msg.frame_id=98
    msg.frame_dlc=1
    msg.data='01'
    ser.write(UCAN.UCAN_encode_message(msg))

def test_canFrameDecodder():
    #case 1
    i = '00000000000001000000010110100100000011000110110000101100010011011000110010100100000'
    canFrameDecodder(i)
    i = '01110010011101100110111101110010001000000010110100100000011000110110000101100010011011000110010100100000'
    canFrameDecodder(i)

def byte_to_binary(n):
    return ''.join(str((n & (1 << i)) and 1) for i in reversed(range(8)))

def hex_to_binary(h):
    return ''.join(byte_to_binary(ord(b)) for b in binascii.unhexlify(h))


def visualise_busLoad():
    print( 'visualize bus load entered ')
    x = []
    with open('dd.txt','r') as csvfile:
        plots = csv.reader(csvfile, delimiter=',')
        for row in plots:
            x.append(int(row[0]))


    plt.plot(x, label='Bus Load')
    plt.xlabel('x')

    plt.title(CASENAME)
    plt.legend()
    plt.show()

def start_visaliseBusLoad():
    s.enter(20,2,visualise_busLoad,())

def start_busload_calc():
    oldtime = time.time()
    # check
    while True:
        if time.time() - oldtime > 59:
            calc_BusLoad()
            oldtime=time.time()


if __name__ == '__main__':
    arguments = docopt(__doc__)
    # start authentication
    startAuth()
    #getting args values Todo : cont. handling args when we need it
    if len(arguments['--port']) != 0: #set the com port
        COM_PORT = arguments['--port'][0]
    if arguments['--d'] == True: #enable Debug mode
        DEBUG=True
    if len(arguments['--baudrate']) != 0: #set baudrate
        BaudRate = int(arguments['--baudrate'][0])
    if arguments['--out'] == True:
        if DEBUG==True :
            print "DEBUG --> Log file output is enabled "
        LOG = 'log.txt'
    if arguments['--v'] == True:
        if DEBUG==True :
            print "DEBUG --> visualise the bus load is enabled which will visaulise after 60 second"
        try:
            thread.start_new_thread(start_visaliseBusLoad,())
        except:
            print("can't start" ),"visualise_busLoad"
    if arguments['--BL'] == True:
        if DEBUG==True :
            print "DEBUG --> calcaulate the busload per second is enabled "
        # s.enter(1,1,calc_BusLoad,())
        # calc_BusLoad()
        try:
            thread.start_new_thread(start_busload_calc,())
        except:
            print 'can not start bus load calc thread'
    if len(arguments['--case']) !=0:
        if DEBUG==True :
            print "DEBUG --> case name is ",str(arguments['--case'][0])
        CASENAME = str(arguments['--case'][0])
    if arguments['sniff'] == True:
        if DEBUG==True :
            print "DEBUG --> Starting Sniffing commmand"
        try:
            # thread.start_new_thread(sniff,())
            sniff()
        except:
            print('can not start sniff thread ')
    #close connection with the serial port
    # sniff()
    # sendTestFrame()
    closeConn()
