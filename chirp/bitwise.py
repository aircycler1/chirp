#!/usr/bin/python
#
# Copyright 2010 Dan Smith <dsmith@danplanet.com>
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

# Language:
#
# Example definitions:
#
#  u8   foo;     /* Unsigned 8-bit value                    */
#  u16  foo;     /* Unsigned 16-bit value                   */
#  u24  foo;     /* Unsigned 24-bit value                   */
#  u32  foo;     /* Unsigned 32-bit value                   */
#  char foo;     /* Character (single-byte                  */
#  lbcd foo;     /* BCD-encoded byte (LE)                   */
#  bbcd foo;     /* BCD-encoded byte (BE)                   */
#  char foo[8];  /* 8-char array                            */
#  struct {                                                 
#   u8 foo;                                                 
#   u16 bar;                                                
#  } baz;        /* Structure with u8 and u16               */
#
# Example directives:
# 
# #seekto 0x1AB; /* Set the data offset to 0x1AB            */
# #seek 4;       /* Set the data offset += 4                */
# #printoffset "foobar" /* Echo the live data offset,
#                          prefixed by string while parsing */
#
# Usage:
#
# Create a data definition in a string, and pass it and the data
# to parse to the parse() function.  The result is a structure with 
# dict-like objects for structures, indexed by name, and lists of
# objects for arrays.  The actual data elements can be interpreted
# as integers directly (for int types) and the following helper
# functions will facilitate composing or decomposing array types:
#
# bcd_to_int()
# int_to_bcd()
# get_string()
# set_string()
#
# Discrete types can be set using their "_" property as so:
#
# obj["mystruct"]["mybyte"]._ = 123
#

import struct
from chirp import bitwise_grammar
from chirp.memmap import MemoryMap

def bits_between(start, end):
    bits = (1 << (end - start )) - 1
    return bits << start

def pp(structure, level=0):
    for i in structure:
        if isinstance(i, list):
            pp(i, level+2)
        elif isinstance(i, tuple):
            if isinstance(i[1], str):
                print "%s%s: %s" % (" " * level, i[0], i[1])
            else:
                print "%s%s:" % (" " * level, i[0])
                pp(i, level+2)
        elif isinstance(i, str):
            print "%s%s" % (" " * level, i)

def array_copy(dst, src):
    """Copy an array src into DataElement array dst"""
    if len(dst) != len(src):
        raise Exception("Arrays differ in size")

    for i in range(0, len(dst)):
        dst[i].set_value(src[i])

def bcd_to_int(bcd_array):
    """Convert an array of bcdDataElement like \x12\x34 into an int like 1234"""
    value = 0
    for bcd in bcd_array:
        a, b = bcd.get_value()
        value = (value * 100) + (a * 10) + b
    return value
        
def int_to_bcd(bcd_array, value):
    """Convert an int like 1234 into bcdDataElements like "\x12\x34" """
    for i in reversed(range(0, len(bcd_array))):
        bcd_array[i].set_value(value % 100)
        value /= 100

def get_string(char_array):
    """Convert an array of charDataElements into a string"""
    return "".join([x.get_value() for x in char_array])

def set_string(char_array, string):
    """Set an array of charDataElements from a string"""
    array_copy(char_array, list(string))

class DataElement:
    _size = 1

    def __init__(self, data, offset, count=1):
        self._data = data
        self._offset = offset
        self._count = count

    def size(self):
        return self._size * 8

    def _get_value(self, data):
        raise Exception("Not implemented")

    def get_value(self):
        return self._get_value(self._data[self._offset:self._offset+self._size])

    def set_value(self, value):
        raise Exception("Not implemented")

class arrayDataElement(DataElement):
    def __init__(self):
        self.__items = []

    def append(self, item):
        self.__items.append(item)

    def get_value(self):
        return list(self.__items)

    def __setitem__(self, index, val):
        self.__items[index].set_value(val)

    def __getitem__(self, index):
        return self.__items[index]

    def __len__(self):
        return len(self.__items)

class intDataElement(DataElement):
    def __int__(self):
        return self.get_value()

    def __trunc__(self):
        return self.get_value()

    def __abs__(self):
        return abs(self.get_value())

    def __mod__(self, val):
        return self.get_value() % val

    def __mul__(self, val):
        return self.get_value() * val

    def __div__(self, val):
        return self.get_value() / val

    def __add__(self, val):
        return self.get_value() + val

    def __sub__(self, val):
        return self.get_value() - val

    def __or__(self, val):
        return self.get_value() | val

    def __and__(self, val):
        return self.get_value() & val

    def __radd__(self, val):
        return val + self.get_value()

    def __rsub__(self, val):
        return val - self.get_value()

    def __rmul__(self, val):
        return val * self.get_value()

    def __rdiv__(self, val):
        return val / self.get_value()

    def __rand__(self, val):
        return val & self.get_value()

    def __ror__(self, val):
        return val | self.get_value()

    def __rmod__(self, val):
        return val % self.get_value()

    def __lshift__(self, val):
        return self.get_value() << val

    def __rshift__(self, val):
        return self.get_value() >> val

    def __iadd__(self, val):
        self.set_value(self.get_value() + val)
        return self

    def __isub__(self, val):
        self.set_value(self.get_value() - val)
        return self

    def __imul__(self, val):
        self.set_value(self.get_value() * val)
        return self

    def __idiv__(self, val):
        self.set_value(self.get_value() / val)
        return self

    def __imod__(self, val):
        self.set_value(self.get_value() % val)
        return self

    def __iand__(self, val):
        self.set_value(self.get_value() & val)
        return self

    def __ior__(self, val):
        self.set_value(self.get_value() | val)
        return self

    def __index__(self):
        return abs(self)

    def __eq__(self, val):
        return self.get_value() == val

    def __ne__(self, val):
        return self.get_value() != val

    def __lt__(self, val):
        return self.get_value() < val

    def __le__(self, val):
        return self.get_value() <= val

    def __gt__(self, val):
        return self.get_value() > val

    def __ge__(self, val):
        return self.get_value() >= val

    def __nonzero__(self):
        return self.get_value() != 0

class u8DataElement(intDataElement):
    _size = 1

    def _get_value(self, data):
        return ord(data)

    def set_value(self, value):
        self._data[self._offset] = (value & 0xFF)

class u16DataElement(intDataElement):
    _size = 2

    def _get_value(self, data):
        return struct.unpack(">H", data)[0]

    def set_value(self, value):
        self._data[self._offset] = struct.pack(">H", value)

class u24DataElement(intDataElement):
    _size = 3

    def _get_value(self, data):
        return struct.unpack(">I", "\x00" + data)[0]

    def set_value(self, value):
        self._data[self._offset] = struct.pack(">I", value)[1:]

class u32DataElement(intDataElement):
    _size = 4

    def _get_value(self, data):
        return struct.unpack(">I", data)[0]

    def set_value(self, value):
        self._data[self._offset] = struct.pack(">I", value)

class charDataElement(DataElement):
    _size = 1

    def _get_value(self, data):
        return data

    def set_value(self, value):
        self._data[self._offset] = value

class bcdDataElement(DataElement):
    pass

class lbcdDataElement(bcdDataElement):
    _size = 1

    def _get_value(self, data):
        a = (ord(data) & 0xF0) >> 4
        b = ord(data) & 0x0F
        return (b, a)

    def set_value(self, value):
        value = int("%02i" % value, 16)
        value = ((value & 0x0F) << 4) | ((value & 0xF0) >> 4)
        self._data[self._offset] = value

class bbcdDataElement(bcdDataElement):
    _size = 1

    def _get_value(self, data):
        a = (ord(data) & 0xF0) >> 4
        b = ord(data) & 0x0F
        return (a, b)

    def set_value(self, value):
        self._data[self._offset] = int("%02i" % value, 16)

class bitDataElement(intDataElement):
    _nbits = 0
    _shift = 0
    _subgen = None

    def get_value(self):
        data = self._subgen(self._data, self._offset).get_value()
        mask = bits_between(self._shift-self._nbits, self._shift)
        val = data & mask

        #print "start: %i bits: %i" % (self._shift, self._nbits)
        #print "data:  %04x" % data
        #print "mask:  %04x" % mask
        #print " val:  %04x" % val

        val >>= (self._shift - self._nbits)
        return val

    def set_value(self, value):
        mask = bits_between(self._shift-self._nbits, self._shift)
        data = self._subgen(self._data, self._offset).get_value()
        data &= ~mask

        #print "data: %04x" % data
        #print "mask: %04x" % mask
        #print "valu: %04x" % value

        value = ((value << (self._shift-self._nbits)) & mask) | data
        self._subgen(self._data, self._offset).set_value(value)
        
    def size(self):
        return self._nbits

class structDataElement(DataElement):
    def __init__(self, *args, **kwargs):
        self._generators = {}
        self._count = 1
        DataElement.__init__(self, *args, **kwargs)
        self.__init = True

    def _value(self, data, generators):
        result = {}
        for name, gen in generators.items():
            result[name] = gen.get_value(data)
        return result

    def get_value(self):
        result = []
        for i in range(0, self._count):
            result.append(self._value(self._data, self._generators[i]))

        if self._count == 1:
            return result[0]
        else:
            return result

    def __getitem__(self, key):
        return self._generators[key]

    def __setitem__(self, key, value):
        if key in self._generators:
            self._generators[key].set_value(value)
        else:
            self._generators[key] = value

    def __getattr__(self, name):
        return self._generators[name]

    def __setattr__(self, name, value):
        if not self.__dict__.has_key("_structDataElement__init"):
            self.__dict__[name] = value
        else:
            self.__dict__["_generators"][name].set_value(value)

    def size(self):
        size = 0
        for gen in self._generators.values():
            if not isinstance(gen, list):
                gen = [gen]

            i = 0
            for el in gen:
                i += 1
                size += el.size()
        return size

class Processor:

    _types = {
        "u8"   : u8DataElement,
        "u16"  : u16DataElement,
        "u24"  : u24DataElement,
        "u32"  : u32DataElement,
        "char" : charDataElement,
        "lbcd" : lbcdDataElement,
        "bbcd" : bbcdDataElement,
        }

    def __init__(self, data, offset):
        self._data = data
        self._offset = offset
        self._obj = None

    def do_symbol(self, symdef, gen):
        name = symdef[1]
        self._generators[name] = gen

    def do_bitfield(self, dtype, bitfield):
        bytes = self._types[dtype](self._data, 0).size() / 8
        bitsleft = bytes * 8

        for _bitdef, defn in bitfield:
            name = defn[0][1]
            bits = int(defn[1][1])
            if bitsleft < 0:
                raise ParseError("Invalid bitfield spec")

            class bitDE(bitDataElement):
                _nbits = bits
                _shift = bitsleft
                _subgen = self._types[dtype]
            
            self._generators[name] = bitDE(self._data, self._offset)
            bitsleft -= bits

        if bitsleft:
            print "WARNING: %i trailing bits unaccounted for in %s" % (bitsleft,
                                                                       bitfield)

        return bytes

    def parse_defn(self, defn):
        dtype = defn[0]

        if defn[1][0] == "bitfield":
            size = self.do_bitfield(dtype, defn[1][1])
            count = 1
            self._offset += size
        else:
            if defn[1][0] == "array":
                sym = defn[1][1][0]
                count = int(defn[1][1][1][1])
            else:
                count = 1
                sym = defn[1]

            name = sym[1]
            res = arrayDataElement()
            size = 0
            for i in range(0, count):
                gen = self._types[dtype](self._data, self._offset)
                res.append(gen)
                self._offset += (gen.size() / 8)

            if count == 1:
                self._generators[name] = res[0]
            else:
                self._generators[name] = res

    def parse_struct(self, struct):
        block = struct[:-1]
        deftype = struct[-1]
        if deftype[0] == "array":
            name = deftype[1][0][1]
            count = int(deftype[1][1][1])
        elif deftype[0] == "symbol":
            name = deftype[0][1]
            count = 1

        result = arrayDataElement()
        for i in range(0, count):
            element = structDataElement(self._offset, count)
            result.append(element)
            tmp = self._generators
            self._generators = element
            self.parse_block(block)
            self._generators = tmp

        if count == 1:
            self._generators[name] = result[0]
        else:
            self._generators[name] = result

    def parse_directive(self, directive):
        name = directive[0][0]
        if name == "seekto":
            offset = directive[0][1][0][1]
            if offset.startswith("0x"):
                offset = int(offset[2:], 16)
            else:
                offset = int(offset)
            print "NOTICE: Setting offset to %i (0x%X)" % (offset, offset)
            self._offset = offset
        elif name == "seek":
            offset = int(directive[0][1][0][1])
            self._offset += offset
        elif name == "printoffset":
            string = directive[0][1][0][1]
            print "%s: %i (0x%08X)" % (string[1:-1], self._offset, self._offset)

    def parse_block(self, lang):
        for t, d in lang:
            #print t
            if t == "struct":
                self.parse_struct(d)
            elif t == "definition":
                self.parse_defn(d)
            elif t == "directive":
                self.parse_directive(d)
        

    def parse(self, lang):
        self._generators = structDataElement(self._data, self._offset)
        self.parse_block(lang[0])
        return self._generators


def parse(spec, data, offset=0):
    ast = bitwise_grammar.parse(spec)
    p = Processor(data, offset)
    return p.parse(ast)

if __name__ == "__main__":
    test = """
    struct {
      u16 bar;
      u16 baz;
      u8 one;
      u8 upper:2,
         twobit:1,
         onebit:1,
         lower:4;
      u8 array[3];
      char str[3];
      bbcd bcdL[2];
    } foo[2];
    u8 tail;
    """
    data = "\xfe\x10\x00\x08\xFF\x23\x01\x02\x03abc\x34\x89"
    data = (data * 2) + "\x12"
    data = MemoryMap(data)
    
    ast = bitwise_grammar.parse(test)

    # Just for testing, pretty-print the tree
    pp(ast)
    
    # Mess with it a little
    p = Processor(data, 0)
    obj = p.parse(ast)
    print "Object: %s" % obj
    print obj["foo"][0]["bcdL"]
    print obj["tail"]
    print obj["foo"][0]["bar"]
    obj["foo"][0]["bar"].set_value(255 << 8)
    obj["foo"][0]["twobit"].set_value(0)
    obj["foo"][0]["onebit"].set_value(1)
    print "%i" % int(obj["foo"][0]["bar"])

    for i in  obj["foo"][0]["array"]:
        print int(i)
    obj["foo"][0]["array"][1].set_value(255)

    for i in obj["foo"][0]["bcdL"]:
        print i.get_value()

    int_to_bcd(obj["foo"][0]["bcdL"], 1234)
    print bcd_to_int(obj["foo"][0]["bcdL"])

    set_string(obj["foo"][0]["str"], "xyz")
    print get_string(obj["foo"][0]["str"])

    print repr(data.get_packed())