#/usr/bin/python
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

import gtk
import gobject

import threading

from chirp import errors

class ShiftDialog(gtk.Dialog):
    def __init__(self, rthread, parent=None):
        gtk.Dialog.__init__(self,
                            title="Shift",
                            buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_OK))

        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)

        self.rthread = rthread

        self.__prog = gtk.ProgressBar()
        self.__prog.show()

        self.__labl = gtk.Label("")
        self.__labl.show()

        self.vbox.pack_start(self.__prog, 1, 1, 1)
        self.vbox.pack_start(self.__labl, 0, 0, 0)

        self.thread = None

        self.set_response_sensitive(gtk.RESPONSE_OK, False)

    def _status(self, msg, prog):
        self.__labl.set_text(msg)
        self.__prog.set_fraction(prog)

    def status(self, msg, prog):
        gobject.idle_add(self._status, msg, prog)

    def _shift_memories(self, delta, memories):
        count = 0.0
        for i in memories:
            src = i.number
            dst = src + delta

            print "Moving %i to %i" % (src, dst)
            self.status("Moving %i to %i" % (src, dst), count / len(memories))

            i.number = dst
            self.rthread.radio.set_memory(i)
            count += 1.0

        return int(count)

    def _get_mems_until_hole(self, start):
        mems = []

        pos = start
        while True:
            self.status("Looking for a free spot (%i)" % pos, 0)
            try:
                mem = self.rthread.radio.get_memory(pos)
            except errors.InvalidMemoryLocation:
                break

            mems.append(mem)
            pos += 1

        print "Found a hole: %i" % pos

        return mems

    def _insert_hole(self, start):
        mems = self._get_mems_until_hole(start)
        mems.reverse()
        if mems:
            return self._shift_memories(1, mems)
        else:
            print "No memory list?"
            return 0

    def _delete_hole(self, start):
        mems = self._get_mems_until_hole(start+1)
        if mems:
            count = self._shift_memories(-1, mems)
            self.rthread.radio.erase_memory(count+start)
            return count
        else:
            print "No memory list?"
            return 0

    def finished(self):
        gobject.idle_add(self.set_response_sensitive, gtk.RESPONSE_OK, True)

    def threadfn(self, newhole, func):
        self.status("Waiting for radio to become available", 0)
        self.rthread.lock()

        count = func(newhole)

        self.rthread.unlock()
        self.status("Moved %i memories" % count, 1)

        self.finished()

    def insert(self, newhole):
        self.thread = threading.Thread(target=self.threadfn,
                                       args=(newhole,self._insert_hole))
        self.thread.start()
        gtk.Dialog.run(self)

    def delete(self, newhole):
        self.thread = threading.Thread(target=self.threadfn,
                                       args=(newhole,self._delete_hole))
        self.thread.start()
        gtk.Dialog.run(self)