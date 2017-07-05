import struct
import array
try:
    import sys,serial,time,binascii ,array,struct
    from docopt import docopt
except:
    print 'Import Errors!!'

__author__ = 'MoatazFarid'

DEBUG = False

class CAN_MSG:
    ''' CAN MSG structure '''
    frame_id = 1 # int
    isExtended = 0 # bool
    frame_dlc=8 #integer
    data=None #long
    RTR=0#bool


def UCAN_encode_id(frame_id, isExtended):
    b= struct.pack('=BBBB',((frame_id<<1) | (isExtended & 1)),(frame_id>>8),(frame_id>>8),(frame_id>>8)) #it is inserted into 4 bytes
    if DEBUG==True :
        print "DEBUG --> DLC and RTR Byte : " ,int(b)
    return b

def UCAN_encode_dlc(frame_dlc,RTR):
    b = struct.pack('=B',((frame_dlc)|((RTR & 0x01)<< 7) ) )
    if DEBUG==True :
        print "DEBUG --> DLC and RTR Byte : " ,b
    return b

def UCAN_encode_data(data,frame_dlc):
    b=array.array('b')
    # for i in range(frame_dlc):
    #     struct.pack_into('=B',b,i,hex(int(data[(i*2):(i*2)+2],16)))

    if frame_dlc == 1:
        b=struct.pack('=B',int(data[0:2],16))
    elif frame_dlc ==2:
        b=struct.pack('=BB',int(data[0:2],16),int(data[2:4],16))
    elif frame_dlc ==3:
        b=struct.pack('=BBB',int(data[0:2],16),int(data[2:4],16),int(data[4:6],16))
    elif frame_dlc ==4:
        b=struct.pack('=BBBB',int(data[0:2],16),int(data[2:4],16),int(data[4:6],16),int(data[6:8],16))
    elif frame_dlc ==5:
        b=struct.pack('=BBBBB',int(data[0:2],16),int(data[2:4],16),int(data[4:6],16),int(data[6:8],16),int(data[8:10],16))
    elif frame_dlc ==6:
        b=struct.pack('=BBBBBB',int(data[0:2],16),int(data[2:4],16),int(data[4:6],16),int(data[6:8],16),int(data[8:10],16),int(data[10:12],16))
    elif frame_dlc ==7:
        b=struct.pack('=BBBBBBB',int(data[0:2],16),int(data[2:4],16),int(data[4:6],16),int(data[6:8],16),int(data[8:10],16),int(data[10:12],16),int(data[12:14],16))
    elif frame_dlc ==8:
        b=struct.pack('=BBBBBBBB',int(data[0:2],16),int(data[2:4],16),int(data[4:6],16),int(data[6:8],16),int(data[8:10],16),int(data[10:12],16),int(data[12:14],16),int(data[14:16],16))
    else:
        b=struct.pack('=B','')
    if DEBUG==True :
        print "DEBUG --> Data : " ,b #, struct.unpack('=BBBBBBB',b) #that test if dlc = 7
    return b

def UCAN_encode_message(msg):
    '''
    This function encodes the can msg and returns byte array
    input is CAN_MSG
    '''
    ID = UCAN_encode_id(msg.frame_id,msg.isExtended)
    DLC = UCAN_encode_dlc(msg.frame_dlc,msg.RTR)
    DATA = UCAN_encode_data(msg.data,msg.frame_dlc)

    a=struct.unpack('=4B',ID)
    b=struct.unpack('=B',DLC)
    c=struct.unpack('=%uB'%msg.frame_dlc,DATA)
    d=()
    for i in range(8-msg.frame_dlc):
        l = list(d)
        l.append(0)
        d= tuple(l)
    out = array.array('B',list(a+b+c+d))
    if DEBUG==True :
        print "DEBUG --> Msg Array",out
    return out

def UCAN_decode_message(buffer):
    msg = CAN_MSG
    RX_bytes = array.array('B',buffer)
    RXID = (int(str((RX_bytes[0])),16) & 0xFE)+ int(str((RX_bytes[1])),16)+int(str((RX_bytes[2])),16)+int(str((RX_bytes[3])),16)
    RXID >>= 1
    msg.frame_id = RXID

    dlc = int(str(RX_bytes[4]),16) & 0xF
    msg.frame_dlc = int(str(dlc),16)

    data=[]
    #check if RTR or not
    if (RX_bytes[4] & 0x80) != 0 :
        #RTR
        msg.RTR = 1
    else:
        msg.RTR = 0
        for i in range(8):
            if i < dlc:
                data.append(int(str(RX_bytes[i]),16))
            data.append('00')
        msg.data = ''.join(str(data))
    return msg



# def UCAN_startConn():
#     ''' This function handle the Authentication with the usb to CAN '''
#     if DEBUG==True :
#         print ("Start initialization")
#     ser.setDTR(True);
#     time.sleep(2)
#     ser.write(bytearray([105, 115, 85, 50, 67]))
#     if DEBUG==True :
#         print ("Start reading")
#     ans = ser.read(2)
#     if DEBUG==True :
#         print (ans)
#         print ("reading finished")
#         print ("recieved YI ")
#
#     ser.write(bytearray([12]))

# def UCAN_closeConn():
#     ''' close the connections and exit system '''
#     ser.close()
#     sys.exit(0)

# def UCAN_read_msg():
#     framebuffer=ser.read(13).encode("hex")
#     if DEBUG==True :
#         print "DEBUG-> SERIAL is ",framebuffer
#     # bin(int(framebuffer,16)) #converted into binary
#     msg = canFrameDecodder(framebuffer)

# if __name__ == '__main__':
    # print ""
    #testing encode id
    #UCAN_encode_id(92,0)
    #testing encode data
    #UCAN_encode_data('ff00ff01020304',7)
