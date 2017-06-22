import sys, serial,time,binascii,struct

''' Basic configuration'''
COM_PORT = 'COM6'
#COM_PORT = '/dev/ttyUSB0'
BaudRate = 115200
DEBUG = True
sniffBus = True

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
    while sniffBus:
        #convert from byte to hex string
        framebuffer=ser.read(13)
        b=bin(int(binascii.hexlify(framebuffer),16))
        print b
        b = b[2:]
        #format(ord(x), 'b') for x in st
        # print framebuffer
        # print b
        # msg = canFrameDecodder(hex_to_binary(framebuffer))
        msg = canFrameDecodder(b[2:])

        #print (framebuffer[0:4])
        printMsg(msg)


def closeConn():
    ''' close the connections and exit system '''
    ser.close(0)
    sys.exit(0)


def getStandardID(frame):
    return int(frame[1:12],2)


def getStandFrameDLC(frame):
    ''' get the standard frame DLC '''
    print frame[15:19]
    print int(frame[15:19],2)
    return int(frame[15:19],2)

def getExtFrameDLC(frame):
    print frame[35:39]
    print int(frame[35:39],2)
    return int(frame[35:39],2)

def test_getFrameData():
    # standard id= 0x110 '00100010000'
    frame = b'10010001000010000000000000000000000000010101000000000000000000000000000000000000000000000000000000000000'
    print frame
    #dlc = '0001'.fromBinaryToInt()
    dlc = int('0001',2)
    data = getFrameData(frame,dlc)
    print (int(data, 2))
    # extended ID  0x60000 '00000000001100000000000000000'


def getFrameData(frame, dlc):
    # return int (frame[39:(39+(8*int(dlc,2)))],2)
    return int (frame[39:(39+(8*dlc))],2)


def canFrameDecodder(frame):
    msg = CAN_MSG()
    if isExtendedID((frame[13:14])) :
        msg.isExtended=1
        if DEBUG == True:
            print ("Extended")
        msg.frame_id =(int(getStandardID(frame))<<18)|int(frame[14:32])
        msg.frame_dlc = getStandFrameDLC(frame)

    else:
        msg.isExtended=0
        msg.frame_id = getStandardID(frame)
        msg.frame_dlc = getExtFrameDLC(frame)
    #get DLC
    msg.data = getFrameData(frame,msg.frame_dlc)
    return msg

def printMsg(msg):
    print type(msg.frame_id)
    print("ID :"),(msg.frame_id)
    print("Data :") ,binascii.hexlify(msg.data)
    print ('\n')

def isExtendedID(IDE):
    ''' Check whether the function '''
    if IDE=='1' or  IDE== 1:
        return True
    else:
        return False

def test_isExtendedID():
    ''' Unit Test for the isExtended function '''
    # case 1
    i = 0
    ans = isExtendedID(i)
    if ans == False:
        print ("Passed")


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

##
startAuth()
# test_getFrameData()
sniff()

closeConn()
