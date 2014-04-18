#!/usr/bin/env python
import hashlib
# Python's random number generator's stability across Python versions
# is complicated.
# Different versions will produce different results.
# It's easier right now to just have our own random number generator
# that's not as good, but is definitely stable between machines.

class Random(object):
    def __init__(self):
        self.state = 0

    def seed(self, s):
        assert isinstance(s, str)

        h = hashlib.md5()
        h.update(s)

        self.state = int(h.hexdigest(),16) & 0xffffffff

    def rand_bit(self):
        bit = self.state & 1

        nb = 0
        for n in [20,25,30,31]:
            nb ^= (self.state >> n) & 1

        self.state <<= 1
        self.state |= nb

        return bit

    def rand_bits(self, n):
        v = 0
        for i in range(n):
            v <<= 1
            v |= self.rand_bit()
        return v

    def random(self):
        return self.rand_bits(32) / float(1<<32)

    def shuffle(self, x):
        "Based on python's shuffle function"

        for i in reversed(xrange(1, len(x))):
            # pick an element in x[:i+1] with which to exchange x[i]
            j = int(self.random() * (i+1))
            x[i], x[j] = x[j], x[i]

if __name__ == "__main__":
    R = Random()
    R.seed("hello".encode("utf-8"))
    for n in range(10):
        print R.random()
