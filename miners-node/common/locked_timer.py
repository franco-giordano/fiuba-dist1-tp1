from threading import Lock, Timer
import logging

class LockedTimer:
    def __init__(self, length, func):
        self.timer = None
        self.seconds_length = length
        self.lock = Lock()
        self.func_to_exec = func
    
    def restart(self):
        self.destroy()

        with self.lock as lck:
            self.timer = Timer(self.seconds_length, self.func_to_exec)
            self.timer.start()
            logging.info(f"TIMER: Set new timer for dispatch, triggering in {self.seconds_length} seconds.")

    def destroy(self):
        with self.lock as lck:
            if self.timer:
                self.timer.cancel()
                logging.info(f"TIMER: Cancelled previous running timer.")

            self.timer = None
