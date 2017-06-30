import struct
import array

__author__ = 'MoatazFarid'

DEBUG = True

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
        print "DEBUG --> DLC and RTR Byte : " ,b
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
    print out
    return out

# if __name__ == '__main__':
    # print ""
    #testing encode id
    #UCAN_encode_id(92,0)
    #testing encode data
    #UCAN_encode_data('ff00ff01020304',7)
