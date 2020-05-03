# Copyright Robert Spanton 2014
import json, sys, optparse, time, os, glob
import logging
import motor, power, ruggeduino, vision, servo
import pyudev

logger = logging.getLogger( "sr.robot" )

def setup_logging():
    "Apply default settings for logging"
    # (We do this by default so that our users
    # don't have to worry about logging normally)

    logger.setLevel( logging.INFO )

    h = logging.StreamHandler( sys.stdout )
    h.setLevel( logging.INFO )

    fmt = logging.Formatter( "%(message)s" )
    h.setFormatter(fmt)

    logger.addHandler(h)

class NoCameraPresent(Exception):
    "Camera not connected."

    def __str__(self):
        return "No camera found."

class AlreadyInitialised(Exception):
    "The robot has been initialised twice"
    def __str__(self):
        return "Robot object can only be initialised once."

class UnavailableAfterInit(Exception):
    "The called function is unavailable after init()"
    def __str__(self):
        return "The called function is unavailable after init()"

def pre_init(f):
    "Decorator for functions that may only be called before init()"

    def g(self, *args, **kw):
        if self._initialised:
            raise UnavailableAfterInit()

        return f(self, *args, **kw)

    return g

class Robot(object):
    """Class for initialising and accessing robot hardware"""
    SYSLOCK_PATH = "/tmp/robot-object-lock"

    def __init__( self,
                  quiet = False,
                  init = True,
                  config_logging = True ):
        if config_logging:
            setup_logging()

        self._initialised = False
        self._quiet = quiet

        # TODO: Re-enable the lock after mangling herdsman etc to support it
        # self._acquire_syslock()

        self._parse_cmdline()

        self._ruggeduino_id_handlers = {}
        self._ruggeduino_fwver_handlers = { "SRduino": ruggeduino.Ruggeduino }

        if init:
            self.init()
            self.wait_start()

    @classmethod
    def setup(cls, quiet = False, config_logging = True ):
        if config_logging:
            setup_logging()

        logger.debug( "Robot.setup( quiet = %s )", str(quiet) )
        return cls( init = False,
                    quiet = quiet,
                    # Logging is already configured
                    config_logging = False )

    def init(self):
        "Find and initialise hardware"
        if self._initialised:
            raise AlreadyInitialised()

        logger.info( "Initialising hardware." )
        self._init_devs()
        self._init_vision()

        if not self._quiet:
            self._dump_devs()

        self._initialised = True

    def _acquire_syslock(self):
        try:
            # Create the file
            self._syslock = os.open( self.SYSLOCK_PATH,
                                     os.O_CREAT | os.O_EXCL )
        except OSError:
            raise Exception( "Robot lock could not be acquired. Have you created more than one Robot() object?" )

    def _dump_devs(self):
        "Write a list of relevant devices out to the log"
        logger.info( "Found the following devices:" )

        self._dump_power()
        self._dump_usbdev_dict( self.motors, "Motors" )
        self._dump_usbdev_dict( self.servos, "Servos" )
        self._dump_usbdev_dict( self.ruggeduinos, "Ruggeduinos" )
        self._dump_webcam()

    def _dump_webcam(self):
        "Write information about the webcam to stdout"

        if not hasattr(self, "vision"):
            "No webcam"
            return

        # For now, just display the fact we have a webcam
        logger.info( " - Webcam" )

    def _dump_power(self):
        "Write information about the power board to stdout"
        if self.power is None:
            "No power board!"
            return

        logger.info( " - {0}".format(self.power) )

    def _dump_usbdev_dict(self, devdict, name ):
        "Write the contents of a device dict to stdout"

        if len(devdict) == 0:
            return

        logger.info( " - %s:", name )

        for key, motor in devdict.iteritems():
            if not isinstance( key, int ):
                continue

            logger.info( "    %(index)s: %(motor)s",
                         { "index": key,
                           "motor": motor } )

    def _parse_cmdline(self):
        "Parse the command line arguments"
        parser = optparse.OptionParser()

        parser.add_option( "--usbkey", type="string", dest="usbkey",
                           help="The path of the (non-volatile) user USB key" )

        parser.add_option( "--startfifo", type="string", dest="startfifo",
                           help="The path of the fifo which start information will be received through" )
        (options, args) = parser.parse_args()

        self.usbkey = options.usbkey
        self.startfifo = options.startfifo

    def wait_start(self):
        "Wait for the start signal to happen"
        logger.info( "Waiting for start signal." )

        f = open( self.startfifo, "r" )
        d = f.read()
        f.close()

        j = json.loads(d)

        for prop in ["zone", "mode", "arena"]:
            if prop not in j:
                raise Exception( "'{}' must be in startup info".format(prop) )
            setattr(self, prop, j[prop])

        if self.mode not in ["comp", "dev"]:
            raise Exception( "mode of '%s' is not supported -- must be 'comp' or 'dev'" % self.mode )
        if self.zone < 0 or self.zone > 3:
            raise Exception( "zone must be in range 0-3 inclusive -- value of %i is invalid" % self.zone )
        if self.arena not in ["A", "B"]:
            raise Exception( "arena must be A or B")

    @pre_init
    def ruggeduino_set_handler_by_id( self, r_id, handler ):
        logger.debug( "Ruggeduino handler set for ID '%s'", r_id )
        self._ruggeduino_id_handlers[ r_id ] = handler

    @pre_init
    def ruggeduino_set_handler_by_fwver( self, fwver, handler ):
        logger.debug( "Ruggeduino handler set for firmware version '%s'", fwver )
        self._ruggeduino_fwver_handlers[ fwver ] = handler

    @pre_init
    def ruggeduino_ignore_id( self, r_id ):
        "Ignore the Ruggeduino with the given ID"
        logger.debug( "Ruggeduino ID '%s' set to be ignored", r_id )
        self.ruggeduino_set_handler_by_id( r_id, ruggeduino.IgnoredRuggeduino )

    def _init_devs(self):
        "Initialise the attributes for accessing devices"

        # Power board
        self._init_power()
        # Motor boards
        self._init_motors()
        # Servo boards
        self._init_servos()
        # Ruggeduinos
        self._init_ruggeduinos()

    def _init_power(self):
        boards = self._init_usb_devices("Power_board_v4", power.Power)
        if len(boards):
            self.power = boards[0]

            # Bring the rails up
            # In the future we will do something more complicated here
            for x in range(6):
                self.power.output[x] = True

        else:
            self.power = None

    def _init_motors(self):
        self.motors = self._init_usb_devices("MCV4B", motor.Motor, subsystem="tty")

    def _init_servos(self):
        self.servos = self._init_usb_devices("Servo_Board_v4", servo.Servo)

    def _init_ruggeduinos(self):
        self.ruggeduinos = {}

        for n, dev in enumerate( self._list_usb_devices( "Ruggeduino", subsystem="tty" ) ):
            handler = None

            snum = dev["ID_SERIAL_SHORT"]
            if snum in self._ruggeduino_id_handlers:
                handler = self._ruggeduino_id_handlers[snum]

            else:
                # There's no ID-specific handler, so we can query it for
                # its firmware version.
                r = ruggeduino.RuggeduinoCmdBase( dev.device_node )
                ver = r.firmware_version_read()
                genre = ver.split(":")[0]

                if genre in self._ruggeduino_fwver_handlers:
                    handler = self._ruggeduino_fwver_handlers[genre]

            if handler is None:
                raise Exception( "No handler found for ruggeduino: serial {0}, firmware '{1}'".format( snum, genre ) )

            srdev = handler( dev.device_node, snum )
            self.ruggeduinos[n] = srdev
            self.ruggeduinos[snum] = srdev

    def _list_usb_devices(self, model, subsystem=None):
        "Create a sorted list of USB devices of the given type"
        def _udev_compare_serial(x, y):
            """Compare two udev serial numbers"""
            return cmp(x["ID_SERIAL_SHORT"],
                       y["ID_SERIAL_SHORT"])

        udev = pyudev.Context()
        devs = list(udev.list_devices( ID_MODEL = model, subsystem=subsystem ))
        # Sort by serial number
        devs.sort( cmp = _udev_compare_serial )
        return devs

    def _init_usb_devices(self, model, ctor, subsystem=None):
        devs = self._list_usb_devices( model, subsystem )

        # Devices stored in a dictionary
        # Each device appears twice in this dictionary:
        #  1. Under its serial number
        #  2. Under an integer key.  Integers assigned by ordering
        #     boards by serial number.
        srdevs = {}

        n = 0
        for dev in devs:
            serialnum = dev["ID_SERIAL_SHORT"]

            if "BUSNUM" in dev:
                srdev = ctor( dev.device_node,
                              busnum = int(dev["BUSNUM"]),
                              devnum = int(dev["DEVNUM"]),
                              serialnum = serialnum )
            else:
                srdev = ctor( dev.device_node,
                              busnum = None,
                              devnum = None,
                              serialnum = serialnum )

            srdevs[n] = srdev
            srdevs[ serialnum ] = srdev
            n += 1

        return srdevs

    def _init_vision(self):
        udev = pyudev.Context()
        cams = list(udev.list_devices( subsystem="video4linux",
                                       # For now, find devices that use this driver
                                       ID_USB_DRIVER="uvcvideo" ))

        if len(cams) == 0:
            "Camera isn't connected."
            return

        camdev = cams[0].device_node

        # Find libkoki.so:
        libpath = None
        if "LD_LIBRARY_PATH" in os.environ:
            for d in os.environ["LD_LIBRARY_PATH"].split(":"):
                l = glob.glob( "%s/libkoki.so*" % os.path.abspath( d ) )

                if len(l):
                    libpath = os.path.abspath(d)
                    break

        if libpath == None:
            v = vision.Vision(camdev, "/usr/lib")
        else:
            v = vision.Vision(camdev, libpath)

        self.vision = v

    def see(self, res = (800,600), stats = False):
        if not hasattr( self, "vision" ):
            raise NoCameraPresent()

        return self.vision.see( res = res,
                                mode = self.mode,
                                arena = self.arena,
                                stats = stats )
