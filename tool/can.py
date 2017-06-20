import sys, serial,time,binascii

''' Basic configuration'''
COM_PORT = 'COM5'
BaudRate = 115200
DEBUG = True
sniffBus = True

#start connection
try:
    ser = serial.Serial(COM_PORT, BaudRate)
except serial.serialutil.SerialException:
    print ("not connected")

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
        framebuffer =binascii.hexlify(ser.read(13))
        canFrameDecodder(hex_to_binary(framebuffer))
        #print (framebuffer[0:4])


def closeConn():
    ''' close the connections and exit system '''
    ser.close(0)
    sys.exit(0)

def canFrameDecodder(frame):
    if isExtendedID((frame[13:14])) :
        if DEBUG == True:
            print ("Extended")
    else:
        print("not ex")

def isExtendedID(IDE):
    if IDE=='1' or  IDE== 1:
        return True
    else:
        return False

def test_canFrameDecodder():
    #case 1
    i = '00000000000001000000010110100100000011000110110000101100010011011000110010100100000'
    canFrameDecodder(i)
    i = '01110010011101100110111101110010001000000010110100100000011000110110000101100010011011000110010100100000'
    canFrameDecodder(i)



def test_isExtendedID():
    # case 1
    i = 0
    ans = isExtendedID(i)
    if ans == False:
        print ("Passed")



def byte_to_binary(n):
    return ''.join(str((n & (1 << i)) and 1) for i in reversed(range(8)))

def hex_to_binary(h):
    return ''.join(byte_to_binary(ord(b)) for b in binascii.unhexlify(h))

##
#startAuth()
test_canFrameDecodder()
#sniff()

#closeConn()
