import logging
import usb1

req_id = 64

POS_MIN = -100
POS_MAX = 100

logger = logging.getLogger( "sr.servo" )

class Servo(object):
    "A servo board"
    def __init__(self, path, busnum, devnum, serialnum = None):
        self.serialnum = serialnum

        self.ctx = usb1.USBContext()
        self.handle = None
        for dev in self.ctx.getDeviceList():
            if dev.getBusNumber() == busnum and dev.getDeviceAddress() == devnum:
                self.handle = dev.open()

        if self.handle is None:
            raise Exception("Failed to find servo board even though it was enumerated")

        self._positions = [0] * 12
        self.init_board()

    def init_board(self):
        self.handle.controlWrite(0, req_id, 0, 12, "")
        try:
            for i in range(12):
                self[i] = 0
        except:
            raise Exception("Failed to initialise servo board. Have you connected its 12V input to the power board?")

    def close(self):
        self.handle.close()

    def __getitem__(self, index):
        return self._positions[index]

    def __setitem__(self, index, value):
        if not 0 <= index < 12:
            raise IndexError('servo index {0} out of range'.format(index))
        # Limit the value to within the valid range
        value = int(value)
        if value > POS_MAX:
            value = POS_MAX
        elif value < POS_MIN:
            value = POS_MIN
        self.handle.controlWrite(0, req_id, value, index, "")
        self._positions[index] = value

    def __repr__(self):
        return "Servo( serialnum = \"{0}\" )".format( self.serialnum )
