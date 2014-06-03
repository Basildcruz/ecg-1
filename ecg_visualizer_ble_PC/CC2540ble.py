import serial
import os
import binascii
import time


class BTDongle():
    def __init__(self, port=None, readResponseTimeOut=20):
        ''' Example port='/dev/ttyACM0'. notifyCB is called when a notification arrives. readResponseTimeOut in seconds '''
        
        self.readResponseTimeOut = readResponseTimeOut
        self.bt = self.__initSerial(port)
        self.bt.flush()
        self.bt.flushInput()

        if not self.__GAPDevInit():
            raise Exception('GAPDeviceInit() failed')

    def discover(self):
        ''' returns a list of BLE devices discovered '''
        return self.__GAPDevDiscoveryRequest()

    def link(self, dev):
        ''' establish a link to 'dev'. 'dev' is a list of 6 8-bit integers describing the MAC address
            example: self.link([1,2,3,4,5,6])
            Returns True on Success and False on Failure
        '''
        gapLinkRequestDump = ''' 01 09 FE 09 00 00 00 ''' #73 A9 B3 EB D7 90 '''
        for i in dev:
            gapLinkRequestDump += ' '+"{:02x}".format(i)
        self.bt.write(self.__dumpToStr(gapLinkRequestDump))
        for evt in self.__eventWaiter():
            if evt['event'] == int('0x0605', 16):
                return evt['status'] == 0
        return False

    def enableNotifications(self, handle):
        ''' enable notifications. example handle = '0x002F' '''
        gattWriteCharValDump = ''' 01 92 FD 06 00 00 '''
        gattWriteCharValDump += ' ' + handle[4:] + ' ' + handle[2:4]+ ' '
        gattWriteCharValDump += '''  01 00 '''
        self.bt.write(self.__dumpToStr(gattWriteCharValDump))
        for evt in self.__eventWaiter():
            if evt['event'] == int('0x0513', 16):
                return evt['status'] == 0
        return False

    def pollNotifications(self):
        ''' poll notifications '''
        for evt in self.__eventWaiter():
            if evt['event'] == int('0x051B', 16):
                #ATT_HandleValueNotification Event
                if evt['status'] == 0:
                    yield evt['data'][5:]

    def __GAPDevDiscoveryRequest(self):
        ''' Issue a device discovery request. Returns False on failure. Otherwise a list of devices '''
        gapDevDiscoveryRequestDump = '''01 04 FE 03 03 01 00'''
        self.bt.write(self.__dumpToStr(gapDevDiscoveryRequestDump))
        devs = []
        for evt in self.__eventWaiter():
            if evt['event'] == int('0x0601', 16):
                # device discovery done
                return devs
            if evt['event'] == int('0x060D', 16):
                # GAP_DeviceInformation
                if evt['data'][0] == 4: 
                    addr = evt['data'][2:8]
                    devs.append(addr)
        return False


    def __GAPDevInit(self, mode='central'):
        ''' currently mode is ignored. Always BTDongle takes central role. Returns True on sucess, False on failure '''
        gapInitCommandDump = ''' 01 00 FE 26 08 05 00 00 00 00 00 00 00 00 00 00 
                                 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 
                                 00 00 00 00 00 00 01 00 00 00 '''
        self.bt.write(self.__dumpToStr(gapInitCommandDump))
        done = self.__waitForEvent('0x0600')
        return done['status'] == 0
    
    def __waitForEvent(self, eventCodeInHex):
        ''' Wait for event to occur. 
            example: self.__waitForEvent('0x0600') for GAPInitDone(). 
            Returns None on timeout, otherwise with packet '''
        for evt in self.__eventWaiter():
            if evt['event'] == int(eventCodeInHex, 16):
                return evt

    def __eventWaiter(self):
        ''' Wait for events '''
        while True:
            resp = self.__readResponse()
            if not resp:
                return 
            packet = self.__parseResponse(resp)
            yield packet

    def __parseResponse(self, resp):
        ''' parses response '''
        packet = {'event':None, 'status': None, 'data':None}
        packet['event'] = resp['data'][0] + resp['data'][1] * 256
        packet['status'] = resp['data'][2]
        packet['data'] = resp['data'][3:]
        return packet

    def __readResponse(self):
        ''' can read only event responses '''
        packet = {'eventCode': None, 'data': [], 'datadump': "" }
        cnt = 0
        maxlen = 255
        datalen = 0

        t1 = time.time()
        while True:
            if (time.time() - t1) > self.readResponseTimeOut:
                return None
            x = self.bt.read()
            for i in x:
                c = binascii.b2a_hex(i)
                num = int(c, 16)
                if cnt == 0 and num != 4:
                    print "Dont know how to handle this"
                if cnt == 1:
                    packet['eventCode'] = c
                if cnt == 2:
                    maxlen = num
                packet['datadump'] += ' ' + c

                if cnt >= 3:
                    datalen += 1
                    packet['data'].append(num)
                cnt += 1
                if datalen >= maxlen:
                    break
            if datalen >= maxlen:
                break
        
        return packet

    def __dumpToStr(self, dumpStr):
        return ''.join([binascii.a2b_hex(i) for i in dumpStr.split()])

    def __initSerial(self, port=None):
        if port:
            ser = serial.Serial(port, 115200, timeout=0)
        else:
            if os.name == 'posix':
                ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0)
            else:
                ser = serial.Serial('COM4', 115200, timeout=0)
        return ser

