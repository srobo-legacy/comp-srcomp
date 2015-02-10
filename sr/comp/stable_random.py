from __future__ import print_function
import hashlib
import random
# Python's random number generator's stability across Python versions
# is complicated.
# Different versions will produce different results.
# It's easier right now to just have our own random number generator
# that's not as good, but is definitely stable between machines.


class Random(random.Random):
    def __init__(self):
        self.state = 0

    def seed(self, s):
        h = hashlib.md5()
        h.update(s)

        self.state = int(h.hexdigest(), 16) & 0xffffffff

    def getstate(self):
        return self.state

    def setstate(self, state):
        self.state = state

    def _rand_bit(self):
        bit = self.state & 1

        nb = 0
        for n in (20, 25, 30, 31):
            nb ^= (self.state >> n) & 1

        self.state <<= 1
        self.state |= nb

        return bit

    def getrandbits(self, n):
        v = 0
        for i in range(n):
            v <<= 1
            v |= self._rand_bit()
        return v

    def random(self):
        return self.getrandbits(32) / float(1 << 32)


def _demo():
    R = Random()
    R.seed("hello".encode("utf-8"))
    for n in range(10):
        print(R.random())

if __name__ == "__main__":
    _demo()
