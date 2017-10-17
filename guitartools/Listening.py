# -*- coding: utf-8 -*-
"""
Created on Fri Apr 28 13:58:37 2017

@author: Ian Spielman


highlight current row in table mode
move “mode selection” to above table (?) and have different possible displays 
	* such as increase xxx bpm each repeat
	* add units to repeats so “repeat 1 of 5”
	* allow infinite repeats

—————————————————————
Chord Quality/Type Recognition (CQR)
—————————————————————
Stage 2: Major or Minor (static root note)
Stage 3: Major or Minor (static root note)
Stage 4: Major or Minor or 7 (static root note)
Stage 5: Major or Minor or 7
Stage 6: Major or Minor or 7
Stage 7: Major or Minor or 7
Stage 8: Major or Minor, 7, Maj7, and Power Chords (5th)
Stage 9: Major, Minor, 7, Maj7, Power Chords (5th), and Sus chords.

—————————————————————
Single Sound Recognition (SSR)
—————————————————————
Stage 1: D, A, E
Stage 2: E, A, D, Em, Am, Dm
Stage 3: E, A, D, Em, Am, Dm, G, C
Stage 4: E, A, D, Em, Am, Dm, G, C, G7, C7, B7, F maj7
Stage 5: E, A, D, Em, Am, Dm, G, C, G7, C7, B7, D7, E7, A7, Fmaj7
Stage 6: E, A, D, Em, Am, Dm, G, C, G7, C7, B7, D7, E7, A7, Fmaj7 [faster]
Stage 7: E, A, D, Em, Am, Dm, G, C, G7, C7, B7, D7, E7, A7, Fmaj7, F
Stage 8: All Power Chords but from any root note! either 5th or 6th string root
Stage 9: E, A, D, Em, Am, Dm, G, C, G7, C7, B7, D7, E7, A7, Fmaj7, F, power chords, Asus2, Asus4, Dsus2, Dsus4, Esus4, G/B, C/G, D/F#

—————————————————————
Chord Progression Recognition (CPR)
—————————————————————
Stage 1: D, A, E
Stage 2: E, A, D, Em, Am, Dm
Stage 3: E, A, D, Em, Am, Dm, G, C
Stage 4: E, A, D, Em, Am, Dm, G, C, G7, C7, B7, Fmaj7
Stage 5: Two or four strums
Stage 6: Two or four strums
Stage 7: E, A, D, Em, Am, Dm, G, C, G7, C7, B7, D7, E7, A7, Fmaj7, F; [Two or four strums, changes in tempo]
Stage 8: Power chord progressions [Two or four strums]
Stage 9: Longer progressions



"""


from guitartools.Support import UiLoader, LocalPath, MakeAutoConfig

AutoConfig = MakeAutoConfig()
class Listening(AutoConfig):
    """
    Play chords from a known menu to work on sound skills
    """

    def __init__(self, GuitarTools, **kwargs):
        super().__init__(**kwargs)
        
        self.GuitarTools = GuitarTools
        
        loader = UiLoader()

        self.ui = loader.load(LocalPath('listening.ui'))
        

        