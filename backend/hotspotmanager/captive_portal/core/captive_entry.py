from .start import startcaptive
from .stop import stopcaptive


class Captive:
    def __init__(self):
        pass

    def start(self):
        return startcaptive.start()

    def stop(self):
        return stopcaptive.stop()

    def status(self):
        ...

    def monitor(self):
        ...

    def check(self):
        ...

    def test(self):
        ...

    def debug(self):
        ...

    def reset(self):
        ...

    @property
    def properties(self):
        ...
