
# Python's random number generator's stability across Python versions
# is complicated.
# Different versions will produce different results.
# It's easier right now to just have our own random number generator
# that's not as good, but is definitely stable between machines.

# At the moment this is unimplemented

class Random(object):
    def seed(self, s):
        pass

    def shuffle(self, x):
        # TODO
        pass
