'''
    CAN Bus Vulnerability tool
    This tool is part of Automotive IDPS and Cyber Security Vulnerability tool Graduation Project
Usage:
    app.py sniff [--port=COM6] [--baudrate=115200] [--d] [--conf=path]
    app.py spoof [( <target_ecu_name> <msg_name> <signal_name> <new_val> )][--port=COM6] [--baudrate=115200] [--d] [--conf=path]
Options:
    --port=COM6         Select the port we connected our UCAN on default is COM6
    --baudrate=115200   Select the BaudRate we use default is 115200
    --d                 Debug mode
    --conf=path         Path of the xml config file default is conf.xml file name in same directory of the script
'''
from _ctypes import sizeof

try:
    import sys,serial,time,binascii,UCAN
    from docopt import docopt
except:
    print 'Import Errors!!'

''' Basic configuration'''
COM_PORT = 'COM6'
#COM_PORT = '/dev/ttyUSB0'
BaudRate = 115200
DEBUG = False

''' Global Variables'''
sniffed_Msgs=[]

#start connection
try:
    ser = serial.Serial(COM_PORT, BaudRate)
except serial.serialutil.SerialException:
    print '====================================================='
    print ("Not connected")
    print '====================================================='
    exit(0)


#starting
class CAN_MSG:
    ''' CAN MSG structure '''
    frame_id = 0x00
    isExtended = 0
    frame_dlc=8
    data=None


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

def printMsg(msg):
    ''' Print the sniffed msg '''
    # print type(msg.frame_id)
    if idExists(msg):
        # print "found"
        pass
        # print(chr(27) + "[2J") #clear screen
    else:
        sniffed_Msgs.append(msg)
        print("ID :"),(msg.frame_id),"  ||  DLC:",msg.frame_dlc,"   ||  Data:",msg.data ,'\n'

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

################# encoding a frame to send data #################
def encodeID(frame_id,isExtended):
    # bytearr = bytearray()
    # if isExtendedID(frame_id) :
    b=bytearray()
    if isExtended :#is extended
        # print "hh"
        b.append((frame_id<<1) | 1)
        # print b
    else:
        b.extend(hex(frame_id<<1 & 0xFE))
    #adding byte0 to the byte array
    # bytearr = bytearray()
    for i in range(3):
        # bytearr.append(frame_id>>8)
        # b[i+1] = frame_id>>8
        b.extend(hex(frame_id>>8))
        # print( b)
    return bytearray([b[0],b[1],b[2],b[3]])

def test_encodeID():
    frame_id = 0x18
    isExtended = 0
    print encodeID(frame_id,isExtended)

#ERRRRRRRRRRORR
def encodeDLC(frame_dlc):
    # print frame_dlc , type(frame_dlc) #frame_dlc is int number
    b = bytearray()
    b.extend(hex(frame_dlc))
    if DEBUG==True :
        print "DEBUG --> encoded DLC bytearray is " , b
    return b

def test_encodeDLC():
    dlc=2
    p= encodeDLC(dlc)
    print(p)

def encodeData(data,dlc):
    b=bytearray()
    # print(type(dlc)),type(data)
    data = str(data)
    for i in range(dlc):
        ld = str(data[(i*2):(i*2)+2])
        if ld=="":
            ld='00'
        ld = hex(int(ld,16))
        b.extend(ld)
    if DEBUG==True :
        print "DEBUG --> encoded Data bytearray is " , b #printing the data in  the array
    return b

def encodeCANFrame(msg):
    msgByteArray=bytearray()
    id = encodeID(msg.frame_id,msg.isExtended)
    # print "-id is :",id
    dlc = encodeDLC(msg.frame_dlc)
    # print "-dlc is ",(dlc)
    data = encodeData(msg.data,msg.frame_dlc)
    # print "-data is ",(data)
    # writing to serial
    msgByteArray = id[:]+ dlc[:]+ data[:]
    if DEBUG==True :
        print "DEBUG --> encoded msg bytearray is " , msgByteArray
    return msgByteArray
    # ser.write(msgByteArray)

def sendTestFrame():
    msg = CAN_MSG
    msg.data=0x1
    msg.frame_dlc=8
    msg.isExtended = 0
    msg.frame_id =0x62
    bArr = encodeCANFrame(msg)
    if DEBUG==True :
        print "before sending ",bArr,type(bArr),len(bArr)
        # bArr.replace(b'0x',b'')
        for ss in bArr:
            print ss
        # print(bArr)
    ser.write(bArr)

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

if __name__ == '__main__':
    # arguments = docopt(__doc__)
    # # start authentication
    startAuth()
    # #getting args values Todo : cont. handling args when we need it
    # if len(arguments['--port']) != 0: #set the com port
    #     COM_PORT = arguments['--port'][0]
    # if arguments['--d'] == True: #enable Debug mode
    #     DEBUG=True
    # if len(arguments['--baudrate']) != 0: #set baudrate
    #     BaudRate = int(arguments['--baudrate'][0])
    # if arguments['sniff'] == True:
    #     if DEBUG==True :
    #         print "DEBUG --> Starting Sniffing commmand"
    #     sniff()
    #close connection with the serial port
    # sniff()
    # sendTestFrame()
    msg=UCAN.CAN_MSG
    msg.frame_id=98
    msg.frame_dlc=1
    msg.data='01'
    ser.write(UCAN.UCAN_encode_message(msg))
    closeConn()
