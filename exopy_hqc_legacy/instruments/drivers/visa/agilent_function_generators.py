"""Drivers for Keysight 81150A Pulse Function Generator using VISA library.

"""
import re
from textwrap import fill
from inspect import cleandoc
import numpy as np
from time import sleep

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
        if value is True or (isinstance(value, str) and on.match(value)) or value == 1:
            self.write(':OUTP ON')
            if self.query(':OUTP?') != '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        elif value is False or (isinstance(value, str) and off.match(value)) or value == 0:
            self.write(':OUTP OFF')
            if self.query(':OUTP?') != '0':
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

    @secure_communication()
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

        availableFunctions = ['SIN', 'DC', 'SQU']
        requested_waveform = waveformFunction

        if not isinstance(requested_waveform, str):
            raise ValueError('waveFormFunction needs to be a str')

        if freq == 0.0 or ampl == 0.0:
            requested_waveform = "DC"
        
        if requested_waveform.upper() not in availableFunctions:
            raise ValueError(f"Provided waveform is not implemented. Implemented functions are {[func for func in availableFunctions]}")
        
        if (freq>self.freqLimits[1] or freq<self.freqLimits[0]) and requested_waveform.upper!="DC":
            raise ValueError(f"Set frequency out of bounds. Use values between {self.freqLimits[0]} and {self.freqLimits[1]}")

        rounded_ampl = np.round(ampl,3)
        rounded_offs = np.round(offs,3)
        if (   ( np.abs(rounded_ampl) + np.abs(rounded_offs)) > self.voltageLimits[1] 
            or (-np.abs(rounded_ampl) - np.abs(rounded_offs)) < self.voltageLimits[0]  ):
            raise ValueError(f"Set total amplitude of {np.abs(rounded_ampl) + np.abs(rounded_offs)} out of bounds. Voltage limits are between {self.voltageLimits[0]} and {self.voltageLimits[1]}")

        if requested_waveform=="DC":
            self.write(":FUNC {}".format(requested_waveform.upper()))
            if self.query(":FUNC?") != "DC":
                raise InstrIOError("Keysight 81150A function generator did not set correctly the mode")        
        else:
            self.write(":FUNC {}".format(requested_waveform.upper()))
            if self.query(":FUNC?") != requested_waveform.upper():
                raise InstrIOError("Keysight 81150A function generator did not set correctly the mode")
            self.write(":FREQ {}".format(freq))
            if float(self.query(":FREQ?")) != freq:
                raise InstrIOError("Keysight 81150A function generator did not set correctly the frequency")
            self.write(":VOLT:AMPL {}".format(rounded_ampl))
            if float(self.query(":VOLT:AMPL?")) != rounded_ampl:
                raise InstrIOError("Keysight 81150A function generator did not set correctly the amplitude")
        self.write(":VOLT:OFFS {}".format(rounded_offs))
        if float(self.query(":VOLT:OFFS?")) != rounded_offs:
                raise InstrIOError("Keysight 81150A function generator did not set correctly the offset")

        
class Agilent33120A(VisaInstrument):
    """
    Generic driver for Agilent33120A, using the VISA library.


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

        super(Agilent33120A, self).__init__(connection_info, caching_allowed,
                                         caching_permissions, auto_open)
        self.frequency_unit = 'Hz'
        self.phase_unit = 'Deg'
        self.write_termination = '\n'
        self.read_termination = '\n'
        self.availableFunctions = ['SIN','SQU','DC']

        self.write("SOUR:VOLT:UNIT VPP")
        self.freqLimits = [float(self.query("FREQ? MIN")), float(self.query("FREQ? MAX"))]
        if self.query("SOUR:FUNC:SHAP?")=="DC":
            self.voltageLimits = [float(self.query("SOUR:VOLT:OFFS? MIN")), float(self.query("SOUR:VOLT:OFFS? MAX"))]
        elif self.query("SOUR:FUNC:SHAP?") in ["SIN","SQU"]:
            self.voltageLimits = [-float(self.query("SOUR:VOLT:OFFS? MAX"))-float(self.query("SOUR:VOLT:AMPL? MAX")),
                                   float(self.query("SOUR:VOLT:OFFS? MAX"))+float(self.query("SOUR:VOLT:AMPL? MAX"))]
        else:
            raise ValueError(f"Present waveform not supported. Manually change to one of {[func for func in self.availableFunctions]}")

    @secure_communication()
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

        if not isinstance(waveformFunction, str):
            raise ValueError('waveFormFunction needs to be a str')
        
        if waveformFunction.upper() not in self.availableFunctions:
            raise ValueError(f"Provided waveform is not implemented. Implemented functions are {[func for func in self.availableFunctions]}")
        
        if (freq>self.freqLimits[1] or freq<self.freqLimits[0]) and waveformFunction.upper()!="DC":
            raise ValueError(f"Set frequency out of bounds. Use values between {self.freqLimits[0]} and {self.freqLimits[1]}")

        rounded_ampl = np.round(np.abs(ampl/2),3)
        rounded_offs = np.round(offs/2,3)

        if ampl == 0.0 or waveformFunction.upper()=="DC":
            self.write("SOUR:FUNC:SHAP DC")

            if self.query("SOUR:FUNC:SHAP?")!="DC":
                raise InstrIOError("Agilent 33120A function generator did not set correctly the mode")           
            if (rounded_offs < self.voltageLimits[0]) or (rounded_offs > self.voltageLimits[1]):
                raise ValueError(f"Offset amplitude of {rounded_offs} V out of bounds. DC offset limits are between {self.voltageLimits[0]} and {self.voltageLimits[1]}")
            self.write("SOUR:VOLT:OFFS {}".format(rounded_offs))
            if np.round(float(self.query("SOUR:VOLT:OFFS?")),4)!=rounded_offs:
                raise InstrIOError("Agilent 33120A function generator did not set correctly the DC offset")
        else:
            self.write("SOUR:FUNC:SHAP {}".format(waveformFunction.upper()))

            if self.query("SOUR:FUNC:SHAP?")!=waveformFunction.upper():
                raise InstrIOError("Agilent 33120A function generator did not set correctly the waveform type")
            self.write("SOUR:FREQ {}".format(freq))
            if np.round(float(self.query("SOUR:FREQ?")),3)!=np.round(freq,3):
                raise InstrIOError("Agilent 33120A function generator did not set correctly the frequency")

            if (   ( np.abs(rounded_ampl) + np.abs(rounded_offs)) > self.voltageLimits[1] 
                or (-np.abs(rounded_ampl) - np.abs(rounded_offs)) < self.voltageLimits[0]  ):
                raise ValueError(f"Set total amplitude of {np.abs(rounded_ampl) + np.abs(rounded_offs)} out of bounds. Voltage limits are between {self.voltageLimits[0]} and {self.voltageLimits[1]}")
            min_ampl = float(self.query("SOUR:VOLT:AMPL? MIN"))
            if np.abs(rounded_ampl)<min_ampl:
                raise ValueError(f"Set amplitude of {np.abs(rounded_ampl)} out of bounds. Min voltage amplitude is between {min_ampl}")

            present_offs = float(self.query("SOUR:VOLT:OFFS?"))

            present_ampl = float(self.query("SOUR:VOLT:AMPL?"))

            if np.abs(rounded_offs)<np.abs(present_offs):
                self.write("SOUR:VOLT:OFFS {}".format(rounded_offs))
                sleep(0.02)
                self.write("SOUR:VOLT:AMPL {}".format(rounded_ampl))
            elif rounded_ampl<present_ampl:
                self.write("SOUR:VOLT:AMPL {}".format(rounded_ampl))
                sleep(0.02)
                self.write("SOUR:VOLT:OFFS {}".format(rounded_offs))
            else:
                self.write("SOUR:VOLT:OFFS {}".format(rounded_offs))
                sleep(0.02)
                self.write("SOUR:VOLT:AMPL {}".format(rounded_ampl))

            if np.round(float(self.query("SOUR:VOLT:OFFS?")),4)!=rounded_offs:
                raise InstrIOError("Agilent 33120A function generator did not set correctly the offset")
            if np.round(float(self.query("SOUR:VOLT:AMPL?")),4)!=rounded_ampl:
                raise InstrIOError("Agilent 33120A function generator did not set correctly the amplitude")
