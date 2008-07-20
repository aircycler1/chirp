#!/usr/bin/python

import chirp_common
import errors
import util
import icf

import ic2200_ll

class IC2200Radio(chirp_common.IcomMmapRadio):
    _model = "\x26\x98\x00\x01"
    _memsize = 6848
    _endframe = "Icom Inc\x2eD8"

    _memories = []

    _ranges = [(0x0000, 0x1340, 32),
               (0x1340, 0x1360, 16),
               (0x1360, 0x136B,  8),

               (0x1370, 0x1380, 16),
               (0x1380, 0x15E0, 32),
               (0x15E0, 0x1600, 16),
               (0x1600, 0x1640, 32),
               (0x1640, 0x1660, 16),
               (0x1660, 0x1680, 32),

               (0x16E0, 0x1860, 32),

               (0x1880, 0x1AB0, 32),

               (0x1AB8, 0x1AC0,  8),
               ]

    foo = [
               (0x1A80, 0x2B18, 32),
               (0x2B18, 0x2B20,  8),
               (0x2B20, 0x2BE0, 32),
               (0x2BE0, 0x2BF4, 20),
               (0x2BF4, 0x2C00, 12),
               (0x2C00, 0x2DE0, 32),
               (0x2DE0, 0x2DF4, 20),
               (0x2DF4, 0x2E00, 12),
               (0x2E00, 0x2E20, 32),

               (0x2F00, 0x3070, 32),

               (0x30D0, 0x30E0, 16),
               (0x30E0, 0x3160, 32),
               (0x3160, 0x3180, 16),
               (0x3180, 0x32A0, 32),
               (0x31A0, 0x31B0, 16),

               (0x3220, 0x3240, 32),
               (0x3240, 0x3260, 16),
               (0x3260, 0x3560, 32),
               (0x3560, 0x3580, 16),
               (0x3580, 0x3720, 32),
               (0x3720, 0x3780,  8),

               (0x3798, 0x37A0,  8),
               (0x37A0, 0x37B0, 16),
               (0x37B0, 0x37B1,  1),

               (0x37D8, 0x37E0,  8),
               (0x37E0, 0x3898, 32),
               (0x3898, 0x389A,  2),

               (0x38A8, 0x38C0, 16)]

    def process_mmap(self):
        self._memories = ic2200_ll.parse_map_for_memory(self._mmap)

    def get_memory(self, number, vfo=None):
        if not self._mmap:
            self.sync_in()

        try:
            return self._memories[number]
        except IndexError:
            raise errors.InvalidMemoryLocation("Location is empty")

    def get_memories(self, vfo=None):
        if not self._mmap:
            self.sync_in()

        return self._memories

    def set_memory(self, memory):
        if not self._mmap:
            self.sync_in()

        self._mmap = ic2200_ll.set_memory(self._mmap, memory)

    def sync_in(self):
        self._mmap = icf.clone_from_radio(self)
        self.process_mmap()
    
    def sync_out(self):
        return icf.clone_to_radio(self)