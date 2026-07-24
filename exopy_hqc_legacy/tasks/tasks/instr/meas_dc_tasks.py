# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task to measure DC properties.

"""
from time import sleep

from atom.api import Float, Int, set_default

from exopy.tasks.api import (InstrumentTask, InterfaceableTaskMixin, 
                             TaskInterface)


class MeasDCVoltageTask(InterfaceableTaskMixin, InstrumentTask):
    """Measure a dc voltage.

    Wait for any parallel operation before execution and then wait the
    specified time before perfoming the measure.

    """
    # Time to wait before the measurement.
    wait_time = Float().tag(pref=True)

    database_entries = set_default({'voltage': 1.0})

    wait = set_default({'activated': True, 'wait': ['instr']})

    def i_perform(self):
        """Wait and read the DC voltage.

        """
        sleep(self.wait_time)

        value = self.driver.read_voltage_dc()
        self.write_in_database('voltage', value)

class MeasDCCurrentTask(InstrumentTask):
    """Measure a dc voltage.

    Wait for any parallel operation before execution and then wait the
    specified time before perfoming the measure.

    """
    # Time to wait before the measurement.
    wait_time = Float().tag(pref=True)

    database_entries = set_default({'current': 1.0})

    wait = set_default({'activated': True, 'wait': ['instr']})

    def perform(self):
        """Wait and read the DC voltage.

        """
        sleep(self.wait_time)

        value = self.driver.read_current_dc()
        self.write_in_database('current', value)

class MultiDCSetChannelInterface(TaskInterface):
    """Set the specified channel.

    """
    #: Id of the channel whose central frequency should be set.
    channel = Int(1).tag(pref=True)

    def perform(self):
        """Performs the task for the specified channel.

        """
        task = self.task
        channel = self.channel
        task.driver.channel = channel
        task.i_perform()
