import time
import xbee
from machine import Pin

#time.sleep(1)   #Let XBee power up completely

#------------Pin definitions------------
serData = Pin("P2", Pin.OUT, value=0)           #MSB
clk = Pin("P1", Pin.OUT, value=0)
latch = Pin("P0", Pin.OUT, value=0)
#dataD = Pin("D3", Pin.OUT, value=0)           #LSB
inhibitRel = Pin("D4", Pin.OUT, value=0)      #Disables selection buttons on machine
startRel = Pin("D7", Pin.OUT, value=0)        #Starts selection motor
cancel = Pin("D2", Pin.OUT, value=0)          #Energize to pick a B-side
power = Pin("D0", Pin.OUT, value=0)          #Energize to pick a A-side
sel_done = Pin("D8", Pin.IN, Pin.PULL_UP)
num_let = Pin("D9", Pin.IN, Pin.PULL_UP)
#one_latch = Pin("D5", Pin.OUT, value=0)       #Latches the ones place of the internal 7-segment display
#ten_latch = Pin("D9", Pin.OUT, value=0)       #Latches the tens place of the internal 7-segment display
decoder_en = Pin("D5", Pin.OUT, value=0)      #Enables the 1 of 10 decoder_en
ready2xfer = Pin("D3", Pin.IN, Pin.PULL_UP)
endOfRecord = Pin("D6", Pin.IN, Pin.PULL_UP)
ok2xfer = Pin("D1", Pin.OUT, value=0)

shiftRegData = [0,0,0,0,0,0,0,0]


def display(tens, ones, SRData):
    #print(type(SRData))
    binary = "{:04b}".format(ones)
    SRData[0] = int(binary[3])
    SRData[1] = int(binary[2])
    SRData[2] = int(binary[1])
    SRData[3] = int(binary[0])
    SRData[6] = 1
    shiftOut(SRData)
    SRData[6] = 0
    shiftOut(SRData)
    #time.sleep(2)
    binary = "{:04b}".format(tens)
    SRData[0] = int(binary[3])
    SRData[1] = int(binary[2])
    SRData[2] = int(binary[1])
    SRData[3] = int(binary[0])
    SRData[7] = 1
    shiftOut(SRData)
    SRData[7] = 0
    shiftOut(SRData)
    return SRData

def selection(side, number, letter, SRData):
    decoder_en.value(0)
    binary = "{:04b}".format(number)
    SRData[0] = int(binary[3])
    SRData[1] = int(binary[2])
    SRData[2] = int(binary[1])
    SRData[3] = int(binary[0])
    shiftOut(SRData)
    decoder_en.value(1)
    inhibitRel.value(1)
    if (side == 0):
        SRData[4] = 1
        SRData[5] = 0
    else:
        SRData[4] = 0
        SRData[5] = 1
    shiftOut(SRData)
    binary = "{:04b}".format(letter)
    SRData[0] = int(binary[3])
    SRData[1] = int(binary[2])
    SRData[2] = int(binary[1])
    SRData[3] = int(binary[0])
    shiftOut(SRData, False)
    startRel.value(1)
    time.sleep(.1)
    decoder_en.value(1)
    for i in range(0, 2000):
        if (num_let.value() == 1):
            break
        time.sleep_ms(1)
    if (i >= 1999):
        SRData = finish_selection("RE1", SRData)
        return SRData
        #return "RE1"
    #decoder_en.value(0)
    # binary = "{:04b}".format(letter)
    # SRData[0] = int(binary[3])
    # SRData[1] = int(binary[2])
    # SRData[2] = int(binary[1])
    # SRData[3] = int(binary[0])
    # shiftOut(SRData)
    #decoder_en.value(1)
    latch.value(1)
    latch.value(0)
    for i in range(0, 350):
        if (sel_done.value() == 0):
            break
        time.sleep_ms(1)
    if (i >= 349):
        SRData = finish_selection("RE2", SRData)
        return SRData
        #return "RE2"
    time.sleep(.5)
    SRData = finish_selection("RE0", SRData)
    return SRData
    #return "RE0"

def finish_selection(reply, SRData):
        decoder_en.value(0)
        SRData[4] = 0
        SRData[5] = 0
        shiftOut(SRData)
        time.sleep(.1)
        startRel.value(0)
        inhibitRel.value(0)
        try:
            xbee.transmit(18, bytes(reply, "utf-8"))
        except:
            pass
        return SRData

def recordReady():
    ok2xfer.value(1)
    try:
        xbee.transmit(18, bytes("ST0", "utf-8"))
    except OSError as e:
        print("OSERROR RECIEVED:", e)
        recordPlay()
    global gotReply
    gotReply = True
    return
    # start = time.ticks_ms()
    # while (time.ticks_diff(time.ticks_ms(), start)) < 5000:
    #     data = xbee.receive()
    #     if(not(data == None)):
    #         #print(data)
    #         data = data['payload']
    #         #print(data)
    #         if data == b'OK':
    #             #print("Data was good!")
    #             global gotReply
    #             #global shiftRegData
    #             #shiftRegData = display(10, 10, shiftRegData)
    #             gotReply = True
    #             return
    # recordPlay()
    # return
    #global gotReply
    #gotReply = True
    # try:
    #     xbee.transmit(18, bytes([35, 0, 1]))
    # except:
    #     pass
    #time.sleep(3)
def recordPlay():
    ok2xfer.value(0)
    # try:
    #     xbee.transmit(18, bytes([35, 0, 2]))
    # except:
    #     pass
    while ready2xfer.value() == 0 or endOfRecord.value() == 0:
        time.sleep_ms(1)
    return

def recordEnd ():
    try:
        xbee.transmit(18, bytes("ST1", "utf-8"))
    except:
        pass

def shiftOut(data, latch_data=True):
    for i in range(8):
        clk.value(0)
        serData.value(data[i])
        # if data[i] == 0:
        #     serData.value(1)
        # else:
        #     serData.value(0)
        clk.value(1)
    clk.value(0)
    if latch_data == True:
        latch.value(1)
        latch.value(0)
    return

def command(command):
    if command == 0:
        cancel.value(1)
        time.sleep(1.5)
        cancel.value(0)
    elif command == 1:
        power.value(0)
    elif command == 2:
        power.value(1)
    elif command == 3:
        global playing
        global gotReply
        if playing == True:
            try:
                xbee.transmit(18, bytes("RE6", "utf-8"))
            except:
                pass
            return
        else:
            recordPlay()
            playing = True
            gotReply = False

    try:
        xbee.transmit(18, bytes("RE5", "utf-8"))
    except:
        pass
    return

time.sleep(2)
shiftRegData = display(14, 10, shiftRegData)
playing = False
gotReply = False
# time.sleep(2)
# inhibitRel.value(1)
# startRel.value(1)

#print(type(shiftRegData))
while True:
    time.sleep(.01)
    if (ready2xfer.value() == 0) and (gotReply == False):
        recordReady()
    if (endOfRecord.value() == 0) and (playing == True):
        recordEnd()
        playing = False
    data = xbee.receive()
    if(not(data == None)):
        data = data['payload']
        if data[0] == 9:
            display(10, data[2], shiftRegData)
            command(data[2])
        elif data == b'OK':
            gotReply = True
        else:
            #print(data, len(data))
            (side, number, letter) = (data[0], data[1], data[2])
            #print(type(side), side, number, letter)
            #print(type(shiftRegData))
            display(number, letter, shiftRegData)
            reply = selection(side, number, letter, shiftRegData)
            #finish_selection(reply, shiftRegData)
