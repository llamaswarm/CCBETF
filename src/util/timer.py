from datetime import datetime

class Timer(object):

    def __init__(self, name = None):
        self.name = name or 'Timer'

    def __enter__(self):
        self.start = datetime.now()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = datetime.now()
        delta = self.end - self.start
        print '%s: finished in %i days %i second %i microseconds' \
            % (self.name, delta.days, delta.seconds, delta.microseconds)