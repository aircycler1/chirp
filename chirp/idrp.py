#!/usr/bin/python
#
# Copyright 2008 Dan Smith <dsmith@danplanet.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import struct
import serial

from chirp import chirp_common, errors
from chirp.memmap import MemoryMap
from chirp import util

DEBUG_IDRP = False

def parse_frames(buf):
    frames = []

    while "\xfe\xfe" in buf:
        try:
            start = buf.index("\xfe\xfe")
            end = buf[start:].index("\xfd") + start + 1
        except Exception:
            print "Unable to parse frames"
            break

        frames.append(buf[start:end])
        buf = buf[end:]

    return frames

def send(pipe, buffer):
    pipe.write("\xfe\xfe%s\xfd" % buffer)
    pipe.flush()

    data = ""
    while True:
        buf = pipe.read(4096)
        if not buf:
            break

        data += buf
        if DEBUG_IDRP:
            print "Got: \n%s" % util.hexprint(buf)

    return parse_frames(data)

def send_magic(pipe):
    send(pipe, ("\xfe" * 15) + "\x01\x7f\x19")

def drain(pipe):
    while True:
        buf = pipe.read(4096)
        if not buf:
            break

def set_freq(pipe, freq):
    freq *= 10000

    freqbcd = util.bcd_encode(int(freq), bigendian=False, width=7)
    buf = "\x01\x7f\x05\x00" + freqbcd

    drain(pipe)
    send_magic(pipe)
    resp = send(pipe, buf)
    for frame in resp:
        if len(frame) == 6:
            if frame[4] == "\xfb":
                return True

    raise errors.InvalidDataError("Repeater reported error")
    
def get_freq(pipe):
    buf = "\x01\x7f\x1a\x09"

    drain(pipe)
    send_magic(pipe)
    resp = send(pipe, buf)

    for frame in resp:
        if frame[4] == "\x03":
            els = frame[6:10]

            freq = int("%02x%02x%02x%02x" % (ord(els[3]),
                                             ord(els[2]),
                                             ord(els[1]),
                                             ord(els[0])))
            freq = freq / 10000.0
            if DEBUG_IDRP:
                print "Freq: %f" % freq
            return freq

    raise errors.InvalidDataError("No frequency frame received")

RP_IMMUTABLE = ["number", "skip", "bank", "extd_number", "name", "rtone",
                "ctone", "dtcs", "tmode", "dtcs_polarity", "skip", "duplex",
                "offset", "mode", "tuning_step", "bank_index"]

class IcomRepeater(chirp_common.IcomRadio):
    pass

class IDRPx000V(IcomRepeater):
    BAUD_RATE = 19200
    mem_upper_limit = 0
        
    def get_memory(self, number):
        if number != 0:
            raise errors.InvalidMemoryLocation("Repeaters have only one slot")

        mem = chirp_common.Memory()
        mem.number = 0
        mem.freq = get_freq(self.pipe)
        mem.name = "TX/RX"
        mem.mode = "DV"
        mem.offset = 0.0
        mem.immutable = RP_IMMUTABLE

        return mem

    def set_memory(self, mem):
        if mem.number != 0:
            raise errors.InvalidMemoryLocation("Repeaters have only one slot")

        set_freq(self.pipe, mem.freq)

    def get_banks(self):
        return []

if __name__ == "__main__":
    pipe = serial.Serial(port="/dev/icom", baudrate=19200, timeout=0.5)
    #set_freq(pipe, 439.920)
    get_freq(pipe)