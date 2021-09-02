from digi.xbee.devices import Raw802Device, RemoteRaw802Device, XBeeDevice
from digi.xbee.models.address import XBee16BitAddress
from digi.xbee.exception import TransmitException, TimeoutException
from time import strftime, localtime, sleep, time
import queue
import threading
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from Jukebox import jukebox
import sqlite3


#Initialize display based on ADAFruit tutorial
i2c = busio.I2C(SCL, SDA)
disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
disp.fill(0)
disp.show()
width = disp.width
height = disp.height
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)
draw.rectangle((0, 0, width, height), outline=0, fill=0)
padding = -2
top = padding
bottom = height - padding
x = 0
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 10)


PORT = "/dev/ttyAMA1"
BAUD = 9600
POWER_ON = bytes([9, 2, 2])
POWER_OFF = bytes([9, 1, 1])
#MM1 = XBee16BitAddress.from_hex_string("0018")
#MM6 = XBee16BitAddress.from_hex_string("0017")
#TI2 = XBee16BitAddress.from_hex_string("0010")


#device = Raw802Device(PORT, BAUD)
device = XBeeDevice(PORT, BAUD)
device.open()
print("XBee with address", device.get_16bit_addr(), "opened on port",PORT)
#jukebox = RemoteRaw802Device(device, XBee16BitAddress.from_hex_string("0017"))
#MM1 = RemoteRaw802Device(device, x16bit_addr=XBee16BitAddress.from_hex_string("0018"))
#device.send_data(MM1, bytes([0, 5, 3]))

xbee_net = device.get_network()
MM1_XBee = xbee_net.discover_device("MM1")
MM5_XBee = xbee_net.discover_device("MM5")
MM6_XBee = xbee_net.discover_device("MM6")
TI2_XBee = xbee_net.discover_device("TI-2")
jukeboxes = {}
if MM1_XBee != None:
    MM1 = jukebox("MM1", MM1_XBee)
    jukeboxes["MM1"] = MM1
    print("MM1 connected")
if MM5_XBee != None:
    MM5 = jukebox("MM5", MM5_XBee)
    jukeboxes["MM5"] = MM5
    print("MM5 connected")
if MM6_XBee != None:
    MM6 = jukebox("MM6", MM6_XBee)
    jukeboxes["MM6"] = MM6
    print("MM6 connected")
if TI2_XBee != None:
    TI2 = jukebox("TI2", TI2_XBee)
    jukeboxes["TI2"] = TI2
    print("TI2 connected")
#jukeboxes = {"MM6":MM6, "MM1":MM1, "TI2":TI2}
playing = False
playQueue = []
# for jukebox in jukeboxes:
#     device.send_data(jukeboxes[jukebox], POWER_ON)
#     sleep(1)
# device.send_data(MM1, POWER_ON)
# sleep(2)
# device.send_data(MM6, POWER_ON)
# sleep(1)
# device.send_data(TI2, POWER_ON)

#sleep(5)
#device.send_data_broadcast(POWER_OFF)
# device.close()
def read_kbd_input(inputQueue):
    print('Ready for keyboard input:')
    while (True):
        input_str = input()
        inputQueue.put(input_str)
        #print("Data added to queue:", input_str)

def scan_DB(inputQueue):
    connection = sqlite3.connect('/var/databases/Jukebox/jukebox.db')
    cursor = connection.cursor()
    timeSinceCheck = time()
    while(True):
        if(time() - timeSinceCheck) > 2:
            cursor.execute("SELECT code FROM selection")
            selection = cursor.fetchone()
            timeSinceCheck = time()

def xbee_recieve_callback(packet):
    packetQueue.append(packet)

def update_screen():
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw.text((x, top + 0), "MM1: " + MM1._status, font=font, fill=255)
    draw.text((x, top + 8), "MM5: " + MM5._status, font=font, fill=255)
    draw.text((x, top + 16), "MM6: " + MM6._status, font=font, fill=255)
    draw.text((x, top + 24), "TI2: " + TI2._status, font=font, fill=255)
    disp.image(image)
    disp.show()

def update_database():
    connection = sqlite3.connect('/var/databases/Jukebox/jukebox.db')
    cursor = connection.cursor()
    cursor.execute("UPDATE jukeboxes SET status = ? WHERE id = ?", (MM1._status, MM1._id))
    cursor.execute("UPDATE jukeboxes SET status = ? WHERE id = ?", (MM5._status, MM5._id))
    cursor.execute("UPDATE jukeboxes SET status = ? WHERE id = ?", (MM6._status, MM6._id))
    cursor.execute("UPDATE jukeboxes SET status = ? WHERE id = ?", (TI2._status, TI2._id))
    connection.commit()
    connection.close()


def play_next(queue):
    print(queue)
    machine2play = queue.pop(0)
    jukeboxes[machine2play].send_command("PLAY", device)
    jukeboxes[machine2play].status("PLAYING")
    update_screen()
    update_database()
    return
    #device.send_data(jukeboxes[machine2play], bytes([9, 3, 3]))
    start = time()
    while (time()-start) < 10:
        for i in range(len(packetQueue)):
            print(packetQueue[i].data, packetQueue[i].remote_device.get_16bit_addr())
            if packetQueue[i].data == b'RE5' and packetQueue[i].remote_device.get_16bit_addr() == jukeboxes[machine2play].get_16bit_addr():
                print("Playing song on", machine2play)
                packetQueue.pop(i)
                return
    print("NO JUKEBOX RESPONSE")
    return
        # data = device.read_data()
        # if data != None:
        #     if data.data == b'RE5' and data.remote_device.get_16bit_addr() == jukeboxes[machine2play].get_16bit_addr():
        #         print("Playing song on", machine2play)
        #         break
        #     elif data.data == b'ST0':
        #         machine_ready(queue, data)
        #     else:
        #         print("INVALID RESPONSE:", data.data)

def machine_ready(queue, data):
    for machine in jukeboxes:
        if jukeboxes[machine]._address == data.remote_device.get_16bit_addr():
            #device.send_data(jukeboxes[machine], "OK")
            queue.append(machine)
            print(machine, "waiting to play")
            jukeboxes[machine].status("WAITING")
            update_screen()
            update_database()
            break
    return

print("ready")
print(MM1._address)
#def main():
EXIT_COMMAND = "exit"
inputQueue = queue.Queue()

inputThread = threading.Thread(target=read_kbd_input, args=(inputQueue,), daemon=True)
inputThread.start()

DBinputThread = threading.Thread(target=scan_DB, args=(inputQueue,), daemon=True)
DBinputThread.start()

packetQueue = []
device.add_data_received_callback(xbee_recieve_callback)

update_screen()
update_database()
# sleep(2)
# draw.rectangle((0, 16, 128, 24), outline=0, fill=0)
# draw.text((x, top + 16), "MM6: PLAYING", font=font, fill=255)
# disp.image(image)
# disp.show()

while True:
    if (inputQueue.qsize() > 0):
        input_str = inputQueue.get()
        print("input_str = {}".format(input_str))

        if (input_str == EXIT_COMMAND):
            print("Exiting program")
            device.close()
            break
        # Insert your code here to do whatever you want with the input_str.
        elif input_str.lower() == "off":
            device.send_data_broadcast(POWER_OFF)
        elif input_str.lower() == "on":
            MM1.send_command("ON", device)
            # device.send_data(MM1, POWER_ON)
            sleep(1)
            MM5.send_command("ON", device)
            # device.send_data(MM5, POWER_ON)
            sleep(1)
            MM6.send_command("ON", device)
            # device.send_data(MM6, POWER_ON)
            sleep(1)
            TI2.send_command("ON", device)
            # device.send_data(TI2, POWER_ON)
        elif input_str.lower() == "cancel":
            device.send_data_broadcast(bytes([9, 0, 0]))

        elif input_str == "packet":
            for packet in packetQueue:
                print(packet.data, packet.remote_device.get_16bit_addr())

        elif input_str == "playing":
            print(playQueue)

        elif input_str == "play":
            device.send_data_broadcast(bytes([9, 3, 3]))

        else:
            selection = [int(x) for x in input_str]     #Makes a list of the individual digits
            if selection[0] >= 6:
                selection[0] = selection[0] % 2
                TI2.select(selection, device)
            elif selection[0] >= 4:
                selection[0] = selection[0] % 2
                MM6.select(selection, device)
            elif selection[0] >= 2:
                selection[0] = selection[0] % 2
                MM5.select(selection, device)
            elif selection[0] >= 0:
                selection[0] = selection[0] % 2
                MM1.select(selection, device)
        #print(input_str)

    # The rest of your program goes here.

    #data = device.read_data()
    for packet in packetQueue:
        if packet.data == b'ST0':
            packetQueue.remove(packet)
            machine_ready(playQueue, packet)

        # if data.remote_device.get_16bit_addr() == MM6.get_16bit_addr() and data.data == b'ST0':
        #     device.send_data(MM6, "OK")
        #     playQueue.append("MM6")
        # elif data.remote_device.get_16bit_addr() == MM1.get_16bit_addr() and data.data == b'ST0':
        #     device.send_data(MM1, "OK")
        #     playQueue.append("MM1")
        elif packet.data == b'ST1':
            print("Song ended")
            playing = False
            for machine in jukeboxes:
                if jukeboxes[machine]._address == packet.remote_device.get_16bit_addr():
                    jukeboxes[machine].status("IDLE")
                    update_screen()
                    update_database()
                    break
            packetQueue.remove(packet)

        elif packet.data == b'RE0' or packet.data == b'RE5':
            packetQueue.remove(packet)
            #print("MM6 found record, waiting ten seconds to play")
            #sleep(10)
            #device.send_data(MM6, bytes([9, 3, 3]))
            #print("Playing song")
    if playing == False and len(playQueue) > 0:
        play_next(playQueue)
        playing = True

        #print(data.remote_device.get_16bit_addr())
        #print(data.data)
        #print(data.remote_device.get_16bit_addr() == MM6.get_16bit_addr())
#     selection = input("Enter three digit song code: ")
#     (JB, number, letter) = (int(selection[0]), int(selection[1]), int(selection[2]))
#     if JB < 2:
#         try:
#             device.send_data_16(MM6, bytes([JB,number,letter]))
#         except TransmitException:
#             print("Jukebox not responding.")
#     elif JB < 4:
#         JB -= 2
#         try:
#             device.send_data_16(TI2, bytes([JB,number,letter]))
#         except TransmitException:
#             print("Jukebox not responding.")
#     else:
#         Jukebox.select(9,0,0)
#     try:
#         reply = device.read_data(3).timestamp#.decode('utf-8')
#         reply = "Response received at " + strftime("%H", localtime(reply)) + ":" + strftime("%M", localtime(reply))
#     except TimeoutException:
#         reply = ""
#     print(reply)
#if (__name__ == '__main__'):
#    main()
