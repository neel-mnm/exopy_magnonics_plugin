# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2022 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Drivers for Magnet-Physik probe system using VISA library.
"""

from inspect import cleandoc

import logging

from ..driver_tools import (InstrIOError, secure_communication)
from ..visa_tools import VisaInstrument


class MP_FH55(VisaInstrument):
    """Driver for a Magnet_Physik Model FH55 gaussmeter, using the VISA library.
    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of the
    driver_tools package for more details about writing instruments drivers.
    Parameters
    ----------
    see the `VisaInstrument` parameters in the `driver_tools` module
    Methods
    -------
    read_temperature()
        Return the temperature measured by the instrument
    read_field()
        Return the magnetic field measured by the instrument
    Notes
    -----

    """

    log_prefix= 'MP FH55 Driver: '

    # define Ranges that are available (probe-specific)
    # the Magnet-Physik HS-TGB5-104020 probe has a range from 3mT to 3T
    # RANGE_30uT = 1
    # RANGE_300uT = 2
    RANGE_3mT = '3'
    RANGE_30mT = '4'
    RANGE_300mT = '5'
    RANGE_3T = '6'
    # RANGE_30T = 7

    baudrate = 19200
    flowcontrol = 0
    parity = 0
    databits = 8
    stopbits = 10

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(MP_FH55,self).__init__(connection_info,
                                    caching_allowed,
                                    caching_permissions,
                                    auto_open)
        log = logging.getLogger(__name__)
        msg = ('Init with parameters {}')
        log.info(self.log_prefix+msg.format(str(connection_info)))
        try:
            br = connection_info['baudrate']
            self.set_baudrate(int(br))
            fc = connection_info['flowcontrol']
            self.set_flowcontrol(int(fc))
            pr = connection_info['parity']
            self.set_parity(int(pr))
            db = connection_info['databits']
            self.set_databits(int(db))
            sb = connection_info['stopbits']
            self.set_stopbits(int(sb))       
        except KeyError:
            raise InstrIOError(cleandoc('''All connection parameters need to 
                                be specified in instrument settings panel 
                                to ensure smooth connection'''))
        

        #self.update_connection_parameters()


        if self.query('#CFIELD 1')!="CFIELD 1":
            raise InstrIOError(cleandoc('''FH55 instrument did not set correctly
                    the field correction mode'''))
        if self.query('#CTEMP 1')!="CTEMP 1":
            raise InstrIOError(cleandoc('''FH55 instrument did not set correctly
                    the temperature correction mode'''))
        if self.query('#UNIT 0')!="UNIT 0":
            raise InstrIOError(cleandoc('''FH55 instrument did not set correctly
                    the field unit to Tesla'''))
        if self.query('#TEMP 1')!='TEMP 1':
            raise InstrIOError(cleandoc('''FH55 instrument did not set correctly
                    the temp unit to Celsius'''))

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`.
        """
        super(MP_FH55, self).open_connection(**para)
        self.write_termination = '\r'
        self.read_termination = '\r\n'

    def reopen_connection(self,**para):
        """Reopen the connection and set up the parameters.

        """
        self.update_connection_parameters()

    def update_connection_parameters(self):
        super(MP_FH55, self).close_connection()
        self.open_connection(baud_rate=self.baudrate,
                                          flow_control=self.flowcontrol,
                                          parity=self.parity,
                                          data_bits=self.databits,
                                          stop_bits=self.stopbits)

    def set_baudrate(self,value):
        self.baudrate = value

    def set_flowcontrol(self,value):
        self.flowcontrol = value

    def set_parity(self,value):
        self.parity = value

    def set_databits(self,value):
        self.databits = value

    def set_stopbits(self,value):
        self.stopbits = value

    def set_maxcurr(self,value):
        self.maxcurr = value   

    @secure_communication()
    def setup_dc(self):
        if self.query('#MODE 0')!='MODE 0':
            raise InstrIOError(cleandoc('''FH55 instrument did not set correctly
                    the DC mode'''))
        if self.query('#RANGE '+self.RANGE_3T)!="RANGE "+self.RANGE_3T:
            raise InstrIOError(cleandoc('''FH55 instrument did not set correctly
                    the 3T range for DC'''))

    @secure_communication()
    def setup_ac(self,filterLP,filterWB):
        if filterLP:
            if self.query('#FILTER 1')!="FILTER 1":
                raise InstrIOError(cleandoc('''FH55 instrument did not set correctly
                        the filter mode'''))
        elif filterWB:
            raise ValueError(cleandoc('''FH55 instrument does not have a
                    the WB filter mode'''))
        if self.query('#MODE 1')!="MODE 1":
            raise InstrIOError(cleandoc('''FH55 instrument did not set correctly
                    the AC mode'''))
        if self.query('#RANGE '+self.RANGE_3mT)!="RANGE "+self.RANGE_3mT:
            raise InstrIOError(cleandoc('''FH55 instrument did not set correctly
                    the 3mT range for AC'''))

    @secure_communication()
    def read_temperature(self):
        """
        Return the temperature for the probe measured by the instrument
        """
        value = self.query('?TEMP')
        numb,unit = value.split()
        if unit=='C':
            return float(numb)
        else:
            raise InstrIOError(cleandoc('''FH55 instrument did not set correctly
                    the temp unit to Celsius'''))

    @secure_communication()
    def read_field(self):
        """
        Return the field for the probe measured by the instrument
        """
        value = self.query('?MEAS')
        numb,unit = value.split()
        if 'T' in unit:
            # convert value based on unit reading
            if 'k' in unit:
                return float(numb)*1e3
            elif 'm' in unit:
                return float(numb)/1e3
            elif 'u' in unit:
                return float(numb)/1e6
            elif 'unit'=='T':
                return float(numb)
            else:
                raise InstrIOError(cleandoc('''FH55 instrument did communicate
                    an allowed field unit'''))
        else:
            raise InstrIOError(cleandoc('''FH55 instrument did not set correctly
                    the field unit to Tesla'''))

    @secure_communication()
    def read_freq(self):
        """
        Return the field for the probe measured by the instrument
        """        
        return 0.0
