# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Drivers for KeysightKeysight AP SignalGenerator using VISA library.

"""
import re
from textwrap import fill
from inspect import cleandoc

try:
    from pyvisa import VisaTypeError
except ImportError:
    from visa import VisaTypeError


from ..driver_tools import (InstrIOError, instrument_property,
                            secure_communication)
from ..visa_tools import VisaInstrument


class KeysightAP50X2A_002(VisaInstrument):
    """
    Generic driver for Keysight AP Signal Generators,
    using the VISA library.

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
    """
    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(KeysightAP50X2A_002, self).__init__(connection_info,
                                      caching_allowed,
                                      caching_permissions,
                                      auto_open)
        self.write_termination = '\n'
        self.read_termination = '\n'
        self.frequency_unit = 'GHz'
        self.phase_unit = 'Deg'
        self.pulsedict={
            "PulseGen": "INT",
            "Ext": "EXT",
            "Random": "NOPE"}
        self.active_channel = 0
# The next line sets the timeout before reconnection to 0. This is available
# since firmware version 0.4.106 and avoids the Keysight AP generator to freeze
# upon unproperly closed connections (for instance if exopy crashes)
# no need to turn the generator OFF and ON with this line
# here if the explanation from the support team at Keysight AP:
# I added a reconnect timeout option. It allows to reconnect to an
# inactive link that has never been closed. The timeout defines how long
# the user must wait until the link is considered inactive and reconnect is
# enabled. The default timeout is infinite, meaning no reconnect possible at
# all so it behaves like earlier firmare. In this application the timeout can
# be set to zero so reconnect is always possible immediately.
#
# The command is "SYST:COMM:VXI:RTMO <x>", where "<x>" is the reconnect timeout
# in seconds or "INF" for infinite. If they need to reuse to an unclosed link,
# they should always send "SYST:COMM:VXI:RTMO 0" immediately after opening a
# connection.
        self.write("SYST:COMM:VXI:RTMO 0")

    @instrument_property
    def channel(self):
        """Currently selected channel

        """
        return self.active_channel

    @channel.setter
    def channel(self, channel):
        """Driver level channel choice

        """
        if channel not in [1,2]:
            msg = 'AP_50X2A_002 can only use channel 1 or 2, not {}'
            raise InstrIOError(msg.format(channel))
        self.active_channel = channel

    @instrument_property
    @secure_communication()
    def frequency(self):
        """Frequency of the output signal.

        """
        freq = self.query('SOUR{}:FREQ?'.format(self.active_channel))
        if freq:
            return float(freq)
        else:
            raise InstrIOError

    @frequency.setter
    @secure_communication()
    def frequency(self, value):
        """Frequency setter method.

        """
        unit = self.frequency_unit
        self.write('SOUR{}:FREQ {}{}'.format(self.active_channel, value, unit))
        result = self.query('SOUR{}:FREQ?'.format(self.active_channel))
        if result:
            result = float(result)
            if unit == 'GHz':
                result /= 1e9
            elif unit == 'MHz':
                result /= 1e6
            elif unit == 'KHz':
                result /= 1e3
            if abs(result - value) > 1e-12:
                mes = 'Instrument did not set correctly the frequency.'
                raise InstrIOError(mes)

    @instrument_property
    @secure_communication()
    def power(self):
        """Power of the output signal.

        """
        power = self.query('SOUR{}:POWER?')
        if power:
            return float(power)
        else:
            raise InstrIOError

    @power.setter
    @secure_communication()
    def power(self, value):
        """Power setter method.

        """
        self.write('SOUR{}:POWER {}'.format(self.active_channel,value))
        result = float(self.query('SOUR{}:POWER?'.format(self.active_channel)))
        if abs(result - value) > 1e-4:
            raise InstrIOError('Instrument did not set correctly the power')

    @instrument_property
    @secure_communication()
    def output(self):
        """Output state of the source.

        """
        output = self.query('OUTP{}?'.format(self.active_channel))
        if output:
            return bool(int(output))
        else:
            mes = 'Keysight AP signal generator did not return its output'
            raise InstrIOError(mes)

    @output.setter
    @secure_communication()
    def output(self, value):
        """Output setter method.

        """
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if on.match(value) or value == 1:
            self.write('OUTP{} ON'.format(self.active_channel))
            if self.query('OUTP{}?'.format(self.active_channel)) != '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        elif off.match(value) or value == 0:
            self.write('OUTP{} OFF'.format(self.active_channel))
            if self.query('OUTP{}?'.format(self.active_channel)) != '0':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        switch_on_off method''').format(value), 80)
            raise VisaTypeError(mess)

    @instrument_property
    @secure_communication()
    def phase(self):
        """Phase getter method
        """
        phase = self.query('SOUR{}:PHASe?'.format(self.active_channel))
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
        self.write('SOUR{}:PHAS {}{}'.format(self.active_channel, value, unit))
        result = self.query('SOUR{}:PHASe?'.format(self.active_channel))
        if result:
            result = float(result)
            if unit == 'Deg':
                result /= pi/180
            if abs(result - value) > 10**-3:
                mes = 'Instrument did not set correctly the phase'
                raise InstrIOError(mes)
        else:
            raise InstrIOError('PSG signal generator did not return its phase')

    @instrument_property
    @secure_communication()
    def pm_state(self):
        """Pulse modulation getter method

        """
        pm_state = self.query('SOUR{}:PULM:STATE?'.format(self.active_channel))
        if pm_state:
            return bool(pm_state)
        else:
            mes = 'Keysight AP signal generator did not return its pulse modulation state'
            raise InstrIOError(mes)

    @pm_state.setter
    @secure_communication()
    def pm_state(self, value):
        """Pulse modulation setter method.

        """
        # TODO: write checks
        self.write('SOUR{}:PULM:POLarity NORMal'.format(self.active_channel))
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if on.match(value) or value == 1:
            self.write('SOUR{}:PULM:STATE ON'.format(self.active_channel))
            if self.query('SOUR{}:PULM:STATE?'.format(self.active_channel)) != '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation state'''))
        elif off.match(value) or value == 0:
            self.write('SOUR{}:PULM:STATE OFF'.format(self.active_channel))
            if self.query('SOUR{}:PULM:STATE?'.format(self.active_channel)) != '0':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation state'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        switch_on_off method''').format(value), 80)
            raise VisaTypeError(mess)

    @instrument_property
    @secure_communication()
    def pm_source(self):
        """Pulse modulation getter method

        """
        source = self.query('SOUR{}:PULM:SOURce?'.format(self.active_channel))
        if source:
            return source # EXT, INT or RAND
        else:
            mes = 'Signal generator did not return the pulse modulation source'
            raise InstrIOError(mes)

    @pm_source.setter
    @secure_communication()
    def pm_source(self, value):
        """Pulse modulation setter method.

        """
        # TODO: write checks
        self.write('SOUR{}:PULM:POLarity NORMal'.format(self.active_channel))
        source=self.pulsedict[value]
        if source in ['EXT','INT']:
            self.write('SOUR{}:PULM:SOURce '.format(self.active_channel) + source)
        elif source not in ['EXT','INT']:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        pulse modulation method''').format(value), 80)
            raise VisaTypeError(mess)
        newvalue = self.query('SOUR{}:PULM:SOURce?'.format(self.active_channel))
        if '.' in newvalue:
            newvalue = newvalue[:-1]
        if source != newvalue:
            raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation source'''))

    @instrument_property
    @secure_communication()
    def pulse_width(self):
        """Pulse width of the output signal.

        """
        width = self.query('SOUR{}:PULM:INT:PWIDTh?'.format(self.active_channel))
        if width:
            return float(width)
        else:
            raise InstrIOError('Instrument did not return the pulse width')

    @pulse_width.setter
    @secure_communication()
    def pulse_width(self, value):
        """Pulse width setter method.

        """
        self.write('SOUR{}:PULM:INT:PWIDTh {}'.format(self.active_channel,value))
        result = self.query('SOUR{}:PULM:INT:PWIDTh?'.format(self.active_channel))
        if result:
            if abs(float(result) - value) > 1e-9:
                raise InstrIOError('Instrument did not set correctly the pulse width')
        else:
            raise InstrIOError('Instrument did not return the pulse width')

    @instrument_property
    @secure_communication()
    def pulse_period(self):
        """Pulse period of the output signal.

        """
        period = self.query('SOUR{}:PULM:INT:PERiod?'.format(self.active_channel))
        if period:
            return float(period)
        else:
            raise InstrIOError('Instrument did not return the pulse period')

    @pulse_period.setter
    @secure_communication()
    def pulse_period(self, value):
        """Pulse period setter method.

        """
        self.write('SOUR{}:PULM:INT:PERiod {}'.format(self.active_channel,value))
        result = self.query('SOUR{}:PULM:INT:PERiod?'.format(self.active_channel))
        if result:
            if abs(float(result) - value) > 1e-9:
                raise InstrIOError('Instrument did not set correctly the pulse period')
        else:
            raise InstrIOError('Instrument did not return the pulse period')

    @instrument_property
    @secure_communication()
    def video_state(self):
        """For compatibility

        """
        chan = self.query('SOUR{}:PULM:OUTPut:VIDeo:SOURce?'.format(self.active_channel))
        if chan:
            return (int(chan) == self.active_channel)
        else:
            mes = 'Signal generator did not return its pulse modulation state'
            raise InstrIOError(mes)

    @video_state.setter
    @secure_communication()
    def video_state(self, value):
        """Pulse modulation setter method.

        """
        # TODO: write checks
        self.write('SOUR{}:PULM:OUTPut:VIDeo:POLarity NORMal'.format(self.active_channel))
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if on.match(value) or value == 1:
            self.write('SOUR{}:PULM:OUTPut:VIDeo:SOURce {}'.format(self.active_channel,self.active_channel))
            if int(self.query('SOUR{}:PULM:OUTPut:VIDeo:SOURce?'.format(self.active_channel))) != self.active_channel:
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation video output'''))
            self.write('LFO:SOUR PULM')
            if self.query('LFO:SOUR?') != 'PULM':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation video output on TRIG OUT'''))
            self.write('LFO:STAT 1')
            if self.query('LFO:STAT?') != '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation video output on TRIG OUT'''))
        elif off.match(value) or value == 0:
            self.write('SOUR{}:PULM:OUTPut:VIDeo:SOURce {}'.format(self.active_channel,self.active_channel))
            if self.query('SOUR{}:PULM:OUTPut:VIDeo:SOURce?'.format(self.active_channel)) != self.active_channel:
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation video output'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        switch_on_off method''').format(value), 80)
            raise VisaTypeError(mess)
