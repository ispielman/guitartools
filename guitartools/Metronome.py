# -*- coding: utf-8 -*-
"""
Created on Sun May 24 22:08:53 2015

This file provides guitar pratice tools

@author: Ian Spielman

I expext this will be the most used function called in this way

c = Changes()
c.SuggestAndTime()
c.RecordChanges(changes) # This will write to disk!  

Right now we keep a full history, which might be useful for something in the 
figure to look at plataueing for example.
"""

import numpy as np

import sys

try:
    import pygame.mixer, pygame.time, pygame.sndarray
    
except ImportError:
    print("ERROR: PyGame needed to run this program. \
          Please install it and try again")
    sys.exit(2)

# #############################################################################
#
# Metronome
#
# #############################################################################

class Metronome(object):
    def __init__(self):
        pygame.mixer.init()

        self._started = False
    
        # Get open the sound file for the click and get a numpy array of its
        # raw samples
        # path = os.path.join(os.path.split(__file__)[0], "Click.wav")
        #click = pygame.mixer.Sound(path)
        #self._click_array = np.array(click)       
        # click, self._click_array
        # self._sample_dt = click.get_length()/self._click_array.shape[0]
    
        self._make_click()
    
    def _make_click(self):
        inited = pygame.mixer.get_init()

        # make a 0.01 s click
        sample_rate = inited[0]
        channels = inited[2]
        # channels = pygame.mixer.get_num_channels()
        duration = 0.01
        samples = int(sample_rate*duration)
        
        time_array = np.linspace(0, duration, samples)
        channels_array = np.zeros(channels)
        time_array = np.meshgrid(channels_array, time_array)[1]
        
        sound_array = 2**15 * (np.sin(5*2*np.pi*time_array / duration) * 
                       np.sin(np.pi*time_array / duration)**2 )
                                    
        sound_array = sound_array.astype(np.int16)
        
        sound = pygame.sndarray.make_sound(sound_array)
        
        self._sample_dt = sound.get_length()/sound_array.shape[0] 
        self._click_array = sound_array
    
    def _generate_sound(self, bpm, emphasis=1):
        beat_period = 60/bpm
         
        beat_nsamples = int(round(beat_period/self._sample_dt))
        
        # Truncate the audio of the click to ensure it's not longer than one
        # beat. Crude way of making sure that when constructing the loop we
        # don't write past the end of the array. Better approach would be to
        # write whatever would go past the end of the array to the start of
        # the array instead.
        click_array = self._click_array[:beat_nsamples]
        
        # Make an array for audio long enough to contain the emphasis pattern:
        loop_nsamples = int(round((emphasis * beat_nsamples)))
        
        loop_array = np.zeros((loop_nsamples,) + click_array.shape[1:],
        dtype=click_array.dtype)
        
        
        # First click emphasised:
        loop_array[0:len(click_array)] += click_array
        
        # Remaining clicks not emphasised (here just done with a decrease in
        # amplitude by a factor of 3):
        for i in range(1, emphasis):
            start_sample = i * beat_nsamples
            stop_sample = start_sample + len(click_array)
            loop_array[start_sample:stop_sample] += click_array//3
        
        # Make a pygame sound object ready for playing
        self._clickloop = pygame.sndarray.make_sound(loop_array)
    
    def update(self, *args, **kwargs):
        """
        If we are ticking, update, otherwise do nothing
        """
        
        if self._started: self.start(*args, **kwargs)
    
    def start(self, *args, **kwargs):
        """
        Start ticking.  Update to new settings if already ticking.  
        """
        
        if self._started:
            self.stop()
        
        # Start playing on a loop:
        self._generate_sound(*args, **kwargs)
        self._started = True
        self._clickloop.play(-1)
    
    def stop(self):
        # Stop playing:
        if self._started:
            self._clickloop.stop()
            self._started = False
