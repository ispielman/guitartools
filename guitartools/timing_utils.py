# -*- coding: utf-8 -*-
"""
Created on Sun May 24 22:08:53 2015

This file provides tools for better locking of timing in python programs

@author: Ian Spielman
"""

import time
from queue import Queue
from threading import Thread

#
# Main timing class
# 

class base_timer():
    """
    provides ability to block program execution until time limit has expired
    
    privides a method to send ticks via a queue to other programs    
    
    Unlike sleep, you can start a timer, perform some computations and then
    wait until the time has elapsed.
    """

    def __init__(self, delay=0):
        """
        Setup timer
        """
                
        # expected delay time
        self._delay = delay       
        
        # Start time
        self._start_time = time.time()
                
        self._worker = Thread()
        
        self._control_queue = Queue()
        self.countdown_queue = Queue()
                
    def start(self, delay=None, interval=1.0, countdown_mode=None):
        """
        Start a timer that will expire after delay seconds
        
        if Delay is none, then we set a countup timer (stop_watch)
        
        that puts the remaining time into self.countdown_queue queue  every interval
        
        if countdown_mode == 'precent_remaining' then countdown monitor will monitor precent remaining
        if countdown_mode == 'precent_done' then countdown monitor will monitor precent done
        """
        
        if self.check() == True:
            raise RuntimeError('already timing')

        if delay is None or delay <= 0:
            self._delay = None
        else:
            self._delay = delay
                        
        self._start_time = time.time()

        # Emoty the control queue
        while self._control_queue.qsize() > 0: self._control_queue.get()
        while self.countdown_queue.qsize() > 0: self.countdown_queue.get()

        if self._delay is None:
            # Count-up process 
            self._worker = Thread(target=Count, args=(self.countdown_queue, self._control_queue, interval))
        else:
            # Count-down process 
            self._worker = Thread(target=Countdown, args=(self._delay, self.countdown_queue, self._control_queue, interval, countdown_mode))
        
        self._worker.setDaemon(True)
        self._worker.start()

    def stop(self):
        """
        stop the currently running timter
        """
        
        # send a stop message
        if self.check(): self._control_queue.put("stop")           
        self.wait()
    
    def elapsed(self):
        """
        time since timer started
        """
        
        if self.check():
            return time.time() -  self._start_time    
        else:
            return self._delay

    def remaining(self):
        """
        time reamining on timer
        """
        
        return self._delay - self.elapsed()


    def check(self):
        """
        see if a timer is running
        """
        
        # if we are not timing right now, just return
        if self._worker.isAlive():
            return True
        else:
           return False
        
    def wait(self):
        """
        wait until timer expires
        
        returns the amount of time waited in this function
        """
        
        # if we are not timing right now, just return
        if not self.check():
            return 0.0
        else:
            start_time = time.time()
            
            self._worker.join()

            return time.time() - start_time

#
# Thread programs that run independentally and monitor timing
#

def Count(countdown_queue, control_queue, interval):
    """
    This is for sending a timing stream to a queue, every interval we send an
    update that is the time elapsed since we started
    """

    initial_time = time.time()

    i = 0
    while True:
        i += 1
        
        elapsed = time.time()-initial_time
        sleep_time = max(
            (i+1)*interval - elapsed,
            0)
        time.sleep(sleep_time)

        countdown_queue.put(elapsed)

        while control_queue.qsize() > 0:
            if control_queue.get() == 'stop':
                return
            else:
                raise ValueError("Invalid control message passed")


def Countdown(delay, countdown_queue, control_queue, interval, countdown_mode):
    """
    This is for sending a timing stream to a queue, for example
    for making a progress bar.  interval is the time between updates
    to the queue.
    
    control_queue is a queue that the timer listens to to allow for messages
    """
    if interval > delay:
        interval = delay

    num = int(delay / interval)
    true_interval = delay / num

    initial_time = time.time()
    final_time = initial_time + delay
    for i in range(num):
        sleep_time = max(
            (i+1)*true_interval - (time.time()-initial_time),
            0)
        time.sleep(sleep_time)
        remainig_time = max(final_time - time.time(), 0)
        if countdown_mode == 'precent_remaining':
            remainig_time = 100*remainig_time/delay
        elif countdown_mode == 'precent_done':
            remainig_time = 100*(1-remainig_time/delay)
        countdown_queue.put(remainig_time)
        
        while control_queue.qsize() > 0:
            if control_queue.get() == 'stop':
                return
            else:
                raise ValueError("Invalid control message passed")
                 