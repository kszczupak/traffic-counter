from queue import Queue


class ClosableQueue(Queue):
    CLOSE_SIGNAL = object()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.closed = False

    def close(self):
        self.closed = True
        self.put(self.CLOSE_SIGNAL)

    def __iter__(self):
        while True:
            item = self.get()
            try:
                if item is self.CLOSE_SIGNAL:
                    return

                yield item
            finally:
                self.task_done()
