"""Drivers for Keysight 81150A Pulse Function Generator using VISA library.

"""
import re
from textwrap import fill
from inspect import cleandoc
import numpy as np

try:
    from pyvisa import VisaTypeError
except ImportError:
    from visa import VisaTypeError


from ..driver_tools import (InstrIOError, instrument_property,
                            secure_communication)
from ..visa_tools import VisaInstrument


class Keysight81150A(VisaInstrument):
    """
    Generic driver for Keysight81150A, using the VISA library.


    Parameters
    ----------
    see the `VisaInstrument` parameters

    Attributes
    ----------
    frequency_unit : str
        Frequency unit used by the driver. The default unit is 'GHz'. Other
        valid units are : 'MHz', 'KHz', 'Hz'
    frequency : float, instrument_property
        Fixed frequency of the output signal.
    power : float, instrument_property
        Fixed power of the output signal.
    output : bool, instrument_property
        State of the output 'ON'(True)/'OFF'(False).

    Notes
    -----
    This driver has been written for the  but might work for other
    models using the same SCPI commands.

    """
    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(Keysight81150A, self).__init__(connection_info, caching_allowed,
                                         caching_permissions, auto_open)
        self.frequency_unit = 'Hz'
        self.phase_unit = 'Deg'
        self.write_termination = '\n'
        self.read_termination = '\n'

        self.freqLimits = [float(self.query(":FREQ? MIN")), float(self.query(":FREQ? MAX"))]
        self.voltageLimits = [float(self.query(":VOLT:LIM:LOW?")), float(self.query(":VOLT:LIM:HIGH?"))]
    @instrument_property
    @secure_communication()
    def frequency(self):
        """Frequency getter method
        """
        freq = self.query(':FREQuency:FIXed?')
        if freq:
            return float(freq)
        else:
            raise InstrIOError

    @frequency.setter
    @secure_communication()
    def frequency(self, value):
        """Frequency setter method
        """
        unit = self.frequency_unit
        self.write(':FREQuency:FIXed {}{}'.format(value, unit))
        result = self.query(':FREQuency:FIXed?')
        if result:
            result = float(result)
            if unit == 'GHz':
                result /= 10**9
            elif unit == 'MHz':
                result /= 10**6
            elif unit == 'KHz':
                result /= 10**3
            if abs(result - value) > 10**-12:
                mes = 'Instrument did not set correctly the frequency'
                raise InstrIOError(mes)
        else:
            raise InstrIOError('Signal generator did not return its frequency')


    @instrument_property
    @secure_communication()
    def output(self):
        """Output getter method
        """
        output = self.query(':OUTPUT?')
        if output:
            return bool(int(output))
        else:
            mes = 'PSG signal generator did not return its output'
            raise InstrIOError(mes)

    @output.setter
    @secure_communication()
    def output(self, value):
        """Output setter method
        """
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if on.match(value) or value == 1:
            self.write(':OUTPUT ON')
            if self.query(':OUTPUT?') != '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        elif off.match(value) or value == 0:
            self.write(':OUTPUT OFF')
            if self.query(':OUTPUT?') != '0':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        switch_on_off method''').format(value), 80)
            raise VisaTypeError(mess)
        
    @secure_communication()
    def open_signal_output(self, value):
        """Output setter method
        """
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if (isinstance(value, str) and on.match(value)) or value == 1:
            self.write(':OUTPUT ON')
            if self.query(':OUTPUT?') != '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        elif (isinstance(value, str) and off.match(value)) or value == 0:
            self.write(':OUTPUT OFF')
            if self.query(':OUTPUT?') != '0':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        switch_on_off method''').format(value), 80)
            raise VisaTypeError(mess)
        

    @secure_communication()
    def set_output_offset(self, value):
        """Output setter method
        """

        if not isinstance(value, (float, int)):
            raise ValueError("Invalid value type")
        max = float(self.query("VOLT:LIM:HIGH?"))
        min=  float(self.query("VOLT:LIM:LOW?"))

        if value > max or value < min:
            raise ValueError("Value outside output range")
        
        self.write("VOLT:OFFS {}".format(value))


    #@secure_communication()
    def set_ac_waveform(self, waveformFunction, 
                        freq,
                        ampl,
                        offs,
                        dutyCycle,
                        isFinite,
                        numCycles):
        '''
        Will currently ignore the existance of dutyCicle, isFinite, and numCycles
        '''

        availableFunctions = ['SIN']
        if not isinstance(waveformFunction, str):
            raise ValueError('waveFormFunction needs to be a str')
        
        if waveformFunction.upper() not in availableFunctions:
            raise ValueError(f"Provided waveform is not implemented. Implemented functions are {[func+',' for func in availableFunctions]}")
        
        if freq>self.freqLimits[1] or freq<self.freqLimits[0]:
            raise ValueError(f"Set frequency out of bounds. Use values between {self.freqLimits[0]} and {self.freqLimits[1]}")

        if np.abs(ampl) + np.abs(offs) > self.voltageLimits[1] or -np.abs(ampl) - np.abs(offs)<self.voltageLimits[0]:
            raise ValueError(f"Set total amplitude of {np.max((np.abs(ampl) + np.abs(offs),np.abs(np.abs(ampl) + np.abs(offs))))} out of bounds. Voltage limits are between {self.voltageLimits[0]} and {self.voltageLimits[1]}")

        self.write(":FUNC {}".format(waveformFunction.upper()))
        self.write(":VOLT:OFFS {}".format(offs))
        self.write(":VOLT:AMPL {}".format(ampl))



    

    @instrument_property
    @secure_communication()
    def phase(self):
        """Phase getter method
        """
        phase = self.query(':PHASe?')
        if phase:
            return float(phase)
        else:
            raise InstrIOError

    @phase.setter
    @secure_communication()
    def phase(self, value):
        """Phase setter method
        """
        pi = 3.141592653589793
        unit = self.phase_unit
        self.write(':PHAS {}{}'.format(value, unit))
        result = self.query(':PHASe?')
        if unit == 'Deg':
            value = value - (value//180)*180
        elif unit == 'Rad':
            value = value - (value//pi)*pi
        if result:
            result = float(result)
            result = result - (result//pi)*pi
            if unit == 'Deg':
                result /= pi/180
            if abs(result - value) > 10**-3:
                mes = 'Instrument did not set correctly the phase'
                raise InstrIOError(mes)
        else:
            raise InstrIOError('Signal generator did not return its phase')



