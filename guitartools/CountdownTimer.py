# -*- coding: utf-8 -*-
"""
Created on Sun May 24 22:08:53 2015

This file provides a countdown timer for guitar pratice tools
"""

import sys

from guitartools.timing_utils import base_timer

# We are going to try to have nice information for the user during timers 
try:
    from IPython.core.display import clear_output
    have_ipython = True
except ImportError:
    have_ipython = False

# #############################################################################
#
# Countdown Timer
#
# #############################################################################

            
class CountdownTimer():
    """
    Provides a user friendly countdown timer
    """
    
    def __init__(self):
        self._timer = base_timer()
                
    def start(self, delay, repeats=1, display=True):
        """
        Start a countdown for a time given by delay
        
        delay: countdown time in s
        
        display: True/False print output or not
        """
        
        interval = 1
        
        for j in range(repeats):
            self._timer.start(
                    delay=delay,
                    interval=interval)
            
            t = None
                    
            while self._timer.check():
                try:
                    t = self._timer.countdown_queue.get(timeout=2*interval)
                except:
                    pass
                else:  
                
                    if display:
                        if have_ipython:
                            try:
                                clear_output()
                            except Exception:
                                # terminal IPython has no clear_output
                                pass
            
                        msg = r"Time Remaning ({0}): {1:.2f} s".format(j, t)
            
                        sys.stdout.write(msg)
                        sys.stdout.flush()
            
            if display:
                sys.stdout.write('\a')
                sys.stdout.flush()
                
            self._timer.wait()
     
            
    def __call__(self, *args, **kwargs):
        """
        When called we behave as a timer
        """
        self.start(*args, **kwargs)