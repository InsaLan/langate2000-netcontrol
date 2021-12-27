from threading import Thread

class WrappedThread(Thread):
    """
    This is a wrapper class on Thread that
    propagates any exception rose on the thread
    to the caller thread. This allows to propagate
    exceptions that occured on the server to the
    pytest context.
    """

    def run(self):
        self.exc = None
        try:
            self.ret = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self.exc = e

    def join(self, timeout=None):
        super().join(timeout)
        if self.exc:
            raise self.exc

        return self.ret
