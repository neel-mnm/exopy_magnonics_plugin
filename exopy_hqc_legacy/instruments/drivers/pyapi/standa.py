#Driver for Standa rotation stage using the newer and less confusing (fuck Dlls) python wrapper.
#Written by Niccolo' Davitti



import pathlib
import os
import time
import libximc.highlevel as ximc

import logging

from inspect import cleandoc

from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property)

from ..pyapi_tools import (BaseInstrument,PyAPIInstrument)


class Standa_8MR151_30_MEn1(BaseInstrument):
    _instance = None
    log_prefix = "Standa control driver"
    
    def __init__(self, connection_info, caching_allowed=True, caching_permissions={}, auto_open=True):
        super().__init__(connection_info, caching_allowed, caching_permissions, auto_open)
        self.info = connection_info
        if auto_open:
            props = self.get_props(connection_info)
            self.setup_instr(props)

    def list_instr(self):
        res = ximc.enumerate_devices(ximc.EnumerateFlags.ENUMERATE_NETWORK | ximc.EnumerateFlags.ENUMERATE_PROBE)
        return res

    def get_props(self, dev_serial_id):
        devices = self.list_instr()
        correctDevice = [dev for dev in devices if int(dev["device_serial"])==int(dev_serial_id["instr_id"])]
        return correctDevice[0]
    
    def setup_instr(self, props):
        device_uri = props["uri"]
        self.axis = ximc.Axis(device_uri)
        self.axis.open_device()
        deg_per_step = 0.0005
        engine_settings = self.axis.get_engine_settings()
        self.axis.set_calb(deg_per_step, engine_settings.MicrostepMode)



    def get_present_abs_angle(self):
        return self.axis.get_position_calb().Position
    
    def setZero(self):
        self.axis.command_zero()

    def move_motor_abs(self, finalAngle):
        self.axis.command_move_calb(finalAngle)
        self.axis.command_wait_for_stop(100)

    def move_motor_rel(self, relAngle):
        self.axis.command_movr_calb(relAngle)
        self.axis.command_wait_for_stop(100)

    def close_connection(self):
        self.axis.close_device()