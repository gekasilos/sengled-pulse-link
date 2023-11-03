import serial
import re
import binascii
from serial.tools.list_ports import comports

DEFAULT_BAUDRATE = 115200
DEFAULT_PORT = '/dev/ttyUSB0'

class ReadLine:
    def __init__(self, s):
        self.buf = bytearray()
        self.s = s

    def readline(self):
        while True:
            i = max(1, min(2048, self.s.in_waiting))
            data = self.s.read(i)
            i = data.find(b"~")
            if i >= 0:
                r = self.buf + data[:i]
                self.buf[0:] = data[i+1:]
                return r
            else:
                self.buf.extend(data)

ser = serial.Serial(DEFAULT_PORT, DEFAULT_BAUDRATE)
rl = ReadLine(ser)

naming = {
    "feffffff": "bluetooth",
    "ffffffff": "gateway",
    "00000000": "memory",
    "b6fe0100": "AD:0001FEB6",
    "56000200": "AD:00020056",
    "0d0a5353": "service1",
    "3d30300d": "service2",
    "c06c0900": "gw sn"
}

processnames = {
    "00000000": "bluetooth params ?",
    "00000100": "manager lamps",
    "00000200": "get saved data",
    "00000b00": "set light memory",
    "00000c00": "get light memory",
    "01000000": "set light on/off",
    "01000100": "change light",
    "01000300": "get light",
    "02000000": "change l/l+r/r volume",
    "02000100": "set EQ",
    "02000200": "set volume on/off",
    "02000300": "change cpu volume",
    "02000400": "get volume",
    "04000000": "get gateway serial",
    "04000100": "pair mode?",
    "04000200": "NONE",
    "04000600": "set source",
    "04000700": "get source",
}

eqlist = {
    "fa": "normal",
    "fb": "pop",
    "fc": "jazz",
    "fd": "classic",
    "fe": "rock",
    "ff": "movie"
}

while True:
    message = binascii.hexlify(rl.readline()).decode('utf-8')
    startremoved = re.sub(r"^7e", "", message)
    cleared = re.sub(r"00$", "", startremoved)
    if cleared:
        sender = cleared[0:8]
        reciever = cleared[8:16]
        process = cleared[16:24]
        message = re.sub(r"007e$", "", cleared[24:])
        original = cleared[24:]
        try:
            prefix = str(message[:4])
            part_1 = message[4:6]
            part_2 = message[6:8]
            part_3 = message[8:10]
            if process == '01000100' and reciever == 'ffffffff': #change light
                if part_2 != '64':
                    message = 'light: ' + str(int(part_1, 16)) + '% '
                else:
                    message = 'apply change'
            elif process == '01000100':
                message = 'light: ' + str(int(part_2, 16)) + '% '

            if process == '01000000' and reciever == 'ffffffff': #set light on/off
                if part_3 == 'f8':
                    message = 'light on'
                else:
                    message = 'light off'

            if process == '01000000' and not reciever == 'ffffffff':  # set light on/off
                if part_1 == '00':
                    message = 'light on'
                else:
                    message = 'light off'

            if process == '02000100':
                message = eqlist[part_2]

            if process == '02000000':
                if part_1 == '00':
                    message = 'right'
                elif part_1 == '01':
                    message = 'left'
                else:
                    message = 'left+right'

            if process == '02000200':
                if part_1 == '01':
                    message = 'volume off'
                else:
                    message = 'volume on'

            if process == '04000600':
                if part_1 == '00':
                    message = '3.5mm'
                else:
                    message = 'bluetooth'

            if process == '02000300':
                if part_2 == 'ff':
                    message = "volume: " + str(int(part_1, 16)) + ' %'

            if process == '00000b00':
                if part_1 == '00':
                    message = 'light saved memory disabled'
                else:
                    message = 'light memory enabled'

            if process == '00000200':
                bulb_count = message[1:8]
                separator = message[8:16]
                bulbs_sn = message[16:80] # because in docs max 8 lamps , 8*8=64 + 16
                spacedata = message[80:128]
                bulbs = [bulbs_sn[i:i+8] for i in range(0, len(bulbs_sn), 8)]
                bulb_c = str(int(bulb_count[4:5]) - 1)
                message = 'Total bulbs: ' + bulb_c + '; '
                for bulb in bulbs:
                    if bulb != '00000000':
                        message = message + 'bulb id: ' + bulb + '; '


            print(f"{naming[sender]} to {naming[reciever]} \t\t| process: {processnames[process]} \t\t| message: {message}")
            #print(f"from: {naming[sender]} | to: {naming[reciever]} | process: {processnames[process]} | message: {original}\n")
        except:
            print(f"{sender} | {reciever} | {process} | {message}")
