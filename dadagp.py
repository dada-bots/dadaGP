#!/usr/bin/python

import os
import json
import guitarpro # Note: works only with PyGuitarPro version 0.6
import guitarpro as gp
from collections import Counter
import re
import json
import math
from fractions import Fraction
import sys

from token_splitter import split_rare_token, unsplit_fx

# Note: 
# "clean" = Clean Electric Guitar or Acoustic Guitar
# "distorted" = Distorted Guitar or Overdrive Guitar
# "bass" = Any Bass Guitar
# "leads" = Any other instrument more stacatto with sharp attacks (like Piano)
# "pads" = Any other instrument used more ambiently (like Choir)
# "remove" = Sound FX -- removing them for this dataset
# "drums" ... Actually drums are determined by track.isPercussionTrack=True not track.channel.instrument. 
# Drum tracks could have any instrument, usually 0 or 255.

instrument_groups = {0: 'leads',
 1: 'leads',
 2: 'leads',
 3: 'leads',
 4: 'leads',
 5: 'leads',
 6: 'leads',
 7: 'leads',
 8: 'leads',
 9: 'leads',
 10: 'leads',
 11: 'leads',
 12: 'leads',
 13: 'leads',
 14: 'leads',
 15: 'leads',
 16: 'leads',
 17: 'leads',
 18: 'leads',
 19: 'leads',
 20: 'leads',
 21: 'leads',
 22: 'leads',
 23: 'leads',
 24: 'clean',
 25: 'clean',
 26: 'clean',
 27: 'clean',
 28: 'clean',
 29: 'distorted', 
 30: 'distorted',
 31: 'distorted',
 32: 'bass',
 33: 'bass',
 34: 'bass',
 35: 'bass',
 36: 'bass',
 37: 'bass',
 38: 'bass',
 39: 'bass',
 40: 'leads',
 41: 'leads',
 42: 'leads',
 43: 'leads',
 44: 'leads',
 45: 'leads',
 46: 'leads',
 47: 'leads',
 48: 'pads',
 49: 'pads',
 50: 'pads',
 51: 'pads',
 52: 'pads',
 53: 'pads',
 54: 'pads',
 55: 'pads',
 56: 'leads',
 57: 'leads',
 58: 'leads',
 59: 'leads',
 60: 'leads',
 61: 'leads',
 62: 'leads',
 63: 'leads',
 64: 'leads',
 65: 'leads',
 66: 'leads',
 67: 'leads',
 68: 'leads',
 69: 'leads',
 70: 'leads',
 71: 'leads',
 72: 'leads',
 73: 'leads',
 74: 'leads',
 75: 'leads',
 76: 'leads',
 77: 'leads',
 78: 'leads',
 79: 'leads',
 80: 'leads',
 81: 'leads',
 82: 'leads',
 83: 'leads',
 84: 'leads',
 85: 'leads',
 86: 'leads',
 87: 'leads',
 88: 'pads',
 89: 'pads',
 90: 'pads',
 91: 'pads',
 92: 'pads',
 93: 'pads',
 94: 'pads',
 95: 'pads',
 96: 'leads',
 97: 'pads',
 98: 'leads',
 99: 'leads',
 100: 'pads',
 101: 'pads',
 102: 'pads',
 103: 'pads',
 104: 'clean',
 105: 'clean',
 106: 'clean',
 107: 'clean',
 108: 'leads',
 109: 'leads',
 110: 'leads',
 111: 'leads',
 112: 'leads',
 113: 'leads',
 114: 'leads',
 115: 'leads',
 116: 'leads',
 117: 'leads',
 118: 'leads',
 119: 'leads',
 120: 'remove',
 121: 'remove',
 122: 'remove',
 123: 'remove',
 124: 'remove',
 125: 'remove',
 126: 'remove',
 127: 'remove',
 255: 'drums'}

# Basically the same function as numpy.diff
# Subtracts consecutive numbers
# Takes a list of numbers as input size n, returns list of numbers size n-1 
def diff(number_list):
    nums = len(number_list)
    if nums<=1:
        return []
    diff_list = []
    for i in range(0,nums-1):
        diff_list.append(number_list[i+1]-number_list[i])
    return diff_list
assert diff([])==[]
assert diff([9])==[]
assert diff([9,9])==[0]
assert diff([9,10])==[1]
assert diff([9,8])==[-1]
assert diff([1,2,3,4])==[1,1,1]
assert diff([69,64,60,55,50,45])==[-5, -4, -5, -5, -5]


# Returns the instrument group (string) given the Track object
# Throws error if track is not supported (no Banjo)
def get_instrument_group(track):
    assert not track.isBanjoTrack, "Banjo not supported"
    if(track.isPercussionTrack):
        return "drums"
    else:
        midinumber = track.channel.instrument
        group_name = instrument_groups[midinumber]
        return group_name

# TUNING FUNCTIONS

# Takes a NoteString like "E4" and gives you a few different representations. Mostly interested in midi_number
def noteNumber(n):
    octave=int(n[-1:])
    pitch_class=n[:-1]
    pitch_value = guitarpro.PitchClass(pitch_class).value
    midi_number = (octave)*12 + pitch_value
    return octave, pitch_class, pitch_value, midi_number
# Tests
assert noteNumber("C#1") == (1, 'C#', 1, 13)
assert noteNumber("E5") == (5, 'E', 4, 64)

# calculates the pitch differences between successive strings
# for example, ['E5', 'B4', 'G4', 'D4', 'A3', 'E3'] => [-5, -4, -5, -5, -5]
# This representation verifies the tuning regardless of the pitch_shift component
def strtodiff(strings):
    strnums = [noteNumber(s)[3] for s in strings]
    strdiff = list(diff(strnums))
    return strdiff

# Supported Guitar tunings. Give it the output from strtodiff
def is_g6standard(strdiff):
    return strdiff == [-5, -4, -5, -5, -5]
def is_g7standard(strdiff):
    return strdiff == [-5, -4, -5, -5, -5, -5]
def is_g6drop(strdiff):
    return strdiff == [-5, -4, -5, -5, -7]
def is_g7drop(strdiff):
    return strdiff == [-5, -4, -5, -5, -7, -5]

# Test if the set of strings is a supported guitar tuning. Give it a notename list
def is_good_guitar_tuning(strings):
    strnums = [noteNumber(s)[3] for s in strings]
    strdiff = list(diff(strnums))
    if(len(strings)==6):
        return is_g6standard(strdiff) or is_g6drop(strdiff)
    elif(len(strings)==7):
        return is_g7standard(strdiff) or is_g7drop(strdiff)
    else:
        return False
# Tests
strings = ['E5', 'B4', 'G4', 'D4', 'A3', 'E3']
assert is_good_guitar_tuning(strings)
strings = ['E5', 'B4', 'G4', 'D4', 'A3', 'D3']
assert is_good_guitar_tuning(strings)
strings = ['D5', 'A4', 'F4', 'C4', 'G3', 'D3']
assert is_good_guitar_tuning(strings)
strings = ['D5', 'A4', 'F4', 'C4', 'G3', 'C3']
assert is_good_guitar_tuning(strings)
strings = ['E5', 'B4', 'G4', 'D4', 'A3', 'E3', "B2"]
assert is_good_guitar_tuning(strings)
strings = ['E5', 'B4', 'G4', 'D4', 'A3', 'D3', "A2"]
assert is_good_guitar_tuning(strings)
strings = ['D5', 'A4', 'F4', 'C4', 'G3', 'D3', "A2"]
assert is_good_guitar_tuning(strings)
strings = ['D5', 'A4', 'F4', 'C4', 'G3', 'C3', "G2"]
assert is_good_guitar_tuning(strings)

# Supported Guitar tunings. Give it the output from strtodiff
def is_b4standard(strdiff):
    return strdiff == [-5, -5, -5]
def is_b5standard(strdiff):
    return strdiff == [-5, -5, -5, -5]
def is_b6standard(strdiff):
    return strdiff == [-5, -5, -5, -5, -5]
def is_b4drop(strdiff):
    return strdiff == [-5, -5, -7]

# Returns a string describing the tuning type
def get_tuning_type(instrument_group, strings):
    strnums = [noteNumber(s)[3] for s in strings]
    strdiff = list(diff(strnums))
    if(instrument_group=="bass"):
        if is_b4standard(strdiff): 
            return "b4_standard"
        elif is_b5standard(strdiff): 
            return "b5_standard"
        elif is_b6standard(strdiff): 
            return "b6_standard"
        elif is_b4drop(strdiff): 
            return "b4_drop"
    else:
        if is_g6standard(strdiff): 
            return "g6_standard"
        elif is_g7standard(strdiff): 
            return "g7_standard"
        elif is_g6drop(strdiff): 
            return "g6_drop"
        elif is_g7drop(strdiff): 
            return "g7_drop"
    print(instrument_group, strings)
    raise Exception # unsupported        
assert get_tuning_type("guitar",['E5', 'B4', 'G4', 'D4', 'A3', 'E3']) == "g6_standard"
assert get_tuning_type("guitar",['E5', 'B4', 'G4', 'D4', 'A3', 'D3']) == "g6_drop"


# Test if the set of strings is a supported bass tuning. Give it a notename list
def is_good_bass_tuning(strings):
    strnums = [noteNumber(s)[3] for s in strings]
    strdiff = list(diff(strnums))
    if(len(strings)==6):
        return is_b6standard(strdiff)
    elif(len(strings)==5):
        return is_b5standard(strdiff)
    elif(len(strings)==4):
        return is_b4standard(strdiff) or is_b4drop(strdiff)
    else:
        return False
# Tests
strings = ['G2', 'D2', 'A1', 'E1']
assert is_good_bass_tuning(strings)
strings = ['G2', 'D2', 'A1', 'D1']
assert is_good_bass_tuning(strings)
strings = ['F2', 'C2', 'G1', 'D1']
assert is_good_bass_tuning(strings)
strings = ['F2', 'C2', 'G1', 'C1']
assert is_good_bass_tuning(strings)
strings = ['G2', 'D2', 'A1', 'E1', 'B0']
assert is_good_bass_tuning(strings)
strings = ['C3','G2', 'D2', 'A1', 'E1', 'B0']
assert is_good_bass_tuning(strings)

# how many steps did we downtune the guitar?
# Note: dropD or dropAD does not count as downtuning in our representation
# The extra low notes will be represented as frets -2 and -1 on an E-standard-like fretboard
def guitar_downtunage(strings):
    strnums = [noteNumber(s)[3] for s in strings]
    return strnums[0] - 64
# Tests
assert guitar_downtunage(['E5', 'B4', 'G4', 'D4', 'A3', 'E3']) == 0
assert guitar_downtunage(['E5', 'B4', 'G4', 'D4', 'A3', 'D3']) == 0
assert guitar_downtunage(['D5', 'A4', 'F4', 'C4', 'G3', 'C3']) == -2

# how many steps did we downtune the bass?
# Note: dropD or dropAD does not count as downtuning in our representation
# The extra low notes will be represented as frets -2 and -1 on an E-standard-like fretboard
def bass_downtunage(strings):
    strnums = [noteNumber(s)[3] for s in strings]
    if(len(strings)==4 or len(strings)==5):
        return strnums[0] - 31 - 12
    elif(len(strings)==6):
        return strnums[1] - 31 - 12 
# Tests
assert bass_downtunage(['G3', 'D3', 'A2', 'E2']) == 0
assert bass_downtunage(['F3', 'C3', 'G2', 'D2']) == -2
assert bass_downtunage(['C4', 'G3', 'D3', 'A2', 'E2', 'B1']) == 0

# from filename, get the artist_name
def get_artist(file):
    # artist_name should be the parent folder in the directory structure
    return file.split("/")[-2]

# round tempo to nearest 10bpm
def roundtempo(tempo):
    return round(tempo/10)*10

# It's important, for resolving token contradictions, that I use the the format measure_name[_params]
# because there should only be one each of "measure_name" token per measure. 
def get_measure_tokens(measure):
    measure_tokens = ["new_measure"]
    #if(measure.tempo):
    #    measure_tokens.append("tempo:%s" % roundtempo(measure.tempo.value))
    # measure tempo is fucked and buggy, you should really look at beatEffect.mixTableChange.tempo
    header = measure.header
    if(header.tripletFeel.value>0):
        measure_tokens.append("measure:triplet_feel:%s" % header.tripletFeel.value)
    if(header.isRepeatOpen):
        measure_tokens.append("measure:repeat_open")
    if(header.repeatAlternative>0):
        # sometimes this is a large value 16383 or 16384
        # For multiple endings for example endings 1-8
        # However pygp doesn't seem to support this
        print(header.repeatAlternative)
        if(header.repeatAlternative<=255):
            measure_tokens.append("measure:repeat_alternative:%s" % header.repeatAlternative)
    if(header.repeatClose>0):
        measure_tokens.append("measure:repeat_close:%s" % header.repeatClose)
    if(header.direction):
        measure_tokens.append("measure:direction:%s" % header.direction.name.replace(" ",""))
    if(header.fromDirection):
        measure_tokens.append("measure:from_direction:%s" % header.fromDirection.name.replace(" ",""))
    return measure_tokens

# It's important to maintain the format of bfx:name(:params..)
# Because we use that to resolve contradictory beatfx tokens

def beat_effect_list(effect):
    effects = []
    # simple effects true/false
    if(effect.fadeIn):
        effects.append("bfx:fade_in")
    if(effect.hasRasgueado):
        effects.append("bfx:has_rasgueado")
    if(effect.vibrato):
        effects.append("bfx:vibrato")
    # complex effects
    # mixTableChange # IGNORE
    if(effect.pickStroke.value>0):
        # 0 (off) 1 (up) 2 (down)
        effects.append("bfx:pick_stroke:%s" % effect.pickStroke.value)
    if(effect.slapEffect.value>0):
        # 0,1,2,3
        effects.append("bfx:slap_effect:%s" % effect.slapEffect.value)
    if(effect.stroke.direction.value>0 and effect.stroke.value>0):
        # direction: 0 (off) 1 (up) 2 (down)
        # value: an amount of time
        effects.append("bfx:stroke:%s:%s" % (effect.stroke.direction.value, effect.stroke.value))
        # tremoloBar
    if(effect.tremoloBar):
        # treat it the same as bend I think ----
        # type
        # - 0 nothing
        # - 1 simple bend
        # - 2 bendRelease  
        # - 3 bendRelesaeBend
        # - 4 preBend
        # - 5 prebendRelease
        # - 6 Tremolo dip 
        # - 7 Dive bar
        # - 8 relesaeUp
        # - 9 invertedDip
        # - 10 return bar
        # - 11 release bar
        # value 100?
        # points:
        # BendPoint (up to 4 bend points)
        # - position 
        # - value (0-6) quartertones
        # - vibrato true/false
        # - BendPoint.getTime
        tremoloBar = "bfx:tremolo_bar:type%s"% effect.tremoloBar.type.value
        for points in effect.tremoloBar.points:
            tremoloBar += ":pos%s:val%s:vib%s" % (points.position, points.value, int(points.vibrato))
        effects.append(tremoloBar)
    # TEMPO
    if(effect.mixTableChange and effect.mixTableChange.tempo):
        #if(effect.mixTableChange.tempo.value != tempo): 
        # could be a change in tempo, or could be the same tempo. no harm if it's the same tempo.
        effects.append("bfx:tempo_change:%s"% roundtempo(effect.mixTableChange.tempo.value))
        if(effect.mixTableChange.tempo.duration>0):
            # start speeding up or slowing down into the next tempo marker
            # the duration amount doesn't really matter
            # because it always goes until the next tempo marker
            effects.append("bfx:tempo_interpolation") 
    return effects

# take a list of bfx tokens and modify the beateffect
# give it beat.effect and a list
def tokens_to_beat_effect(effect, bfx_tokens):
    for token in bfx_tokens:
        # DadaGP v1.1 begin ====>
        token = unsplit_fx(token) # convert v1.1 format (dict with param tokens) to v1.0 (long string)
        # <==== DadaGP v1.1 end

        t = token.split(":")
        if(t[0]!="bfx"):
            # the first part of the token should be bfx, if it's not, it shouldn't be here, ignore it
            print("This token shouldn't be here, it's not a BFX", token)
            continue
        if t[1]=="fade_in":
            effect.fadeIn = True
        elif t[1]=="has_rasgueado":
            effect.hasRasgueado = True
        elif t[1]=="vibrato":
            effect.vibrato = True
        elif t[1]=="pick_stroke":
            effect.pickStroke = gp.BeatStroke()
            effect.pickStroke.direction = gp.BeatStrokeDirection(int(t[2]))
        elif t[1]=="slap_effect":
            effect.slapEffect = gp.SlapEffect(int(t[2]))
        elif t[1]=="stroke":
            effect.stroke = gp.BeatStroke()
            effect.stroke.direction = gp.BeatStrokeDirection(int(t[2]))
            effect.stroke.value = int(t[3])
        elif t[1]=="tremolo_bar":
            effect.tremoloBar = gp.BendEffect()
            effect.tremoloBar.type = gp.BendType(int(t[2][4:]))
            # tremoloBar += ":pos%s:val%s:vib%s" % (points.position, points.value, int(points.vibrato))
            effect.tremoloBar.points = []
            effect.tremoloBar.value = 50
            # should only be a multiple of 3
            assert len(t)%3==0, "Tremolo effect token has a typo. %s" % token
            num_points = int((len(t)-3)/3)
            # for each triplet, create a point:
            for p in range(num_points):
                point = guitarpro.models.BendPoint()
                point.position = int(t[3+p*3][3:])
                point.value = int(t[4+p*3][3:])
                point.vibrato = t[5+p*3][3:]==1
                effect.tremoloBar.points.append(point)
        elif t[1]=="tempo_change":
            if(not effect.mixTableChange):
                # if there's no mixTableChange on this effect, add it
                effect.mixTableChange = gp.MixTableChange()
            if(not effect.mixTableChange.tempo):
                # default: zero duration means no change in tempo
                effect.mixTableChange.tempo = gp.MixTableItem(value=int(t[2]), duration=0, allTracks=False)
            effect.mixTableChange.tempo.value = int(t[2])
        elif t[1]=="tempo_interpolation":
            if(not effect.mixTableChange):
                effect.mixTableChange = gp.MixTableChange()
            if(not effect.mixTableChange.tempo):
                # the default tempo needs to be whatever the current tempo is
                # I don't know what it is inside of this function. 
                # There needs to be another runthrough that corrects these values. 
                effect.mixTableChange.tempo = gp.MixTableItem(value=120, duration=0, allTracks=False)
            # this acceleration/deceleration is supposed to last until the next tempo marker
            # I don't know how long that is, from inside of this function. 
            # There needs to be another runthrough that corrects the current tempo and duration 
            effect.mixTableChange.tempo.duration=1 

# Given a NoteEffect object, returns a list of note effect tokens
def note_effect_list(effect):
    effects = []
    # simple effects true/false
    # accentuatedNote, ghostNote, hammer, heavyAccentuatedNote, letRing, palmMute, staccato, vibrato
    if(effect.accentuatedNote):
        effects.append("nfx:accentuated_note")
    if(effect.ghostNote):
        effects.append("nfx:ghost_note")
    if(effect.hammer):
        effects.append("nfx:hammer")
    if(effect.heavyAccentuatedNote):
        effects.append("nfx:heavy_accentuated_note")
    if(effect.letRing):
        effects.append("nfx:let_ring")
    if(effect.palmMute):
        effects.append("nfx:palm_mute")  
    if(effect.staccato):
        effects.append("nfx:staccato")
    if(effect.vibrato):
        effects.append("nfx:vibrato")
    # complex effects
    if(effect.bend):
        # type
        # - 0 nothing
        # - 1 simple bend
        # - 2 bendRelease
        # - 3 bendRelesaeBend
        # - 4 preBend
        # - 5 prebendRelease
        # - 6 Tremolo dip 
        # - 7 Dive bar
        # - 8 relesaeUp
        # - 9 invertedDip
        # - 10 return bar
        # - 11 release bar
        # value 100?
        # points:
        # BendPoint (up to 4 bend points)
        # - position 
        # - value (0-6) quartertones
        # - vibrato true/false
        # - BendPoint.getTime
        bend = "nfx:bend:type%s"% effect.bend.type.value
        for points in effect.bend.points:
            bend += ":pos%s:val%s:vib%s" % (points.position, points.value, int(points.vibrato))
        effects.append(bend)
    if(effect.grace):
        # duration number
        # fret number
        # isDead true/false
        # isOnBeat true/false
        # transition 0,1,2,3
        effects.append("nfx:grace:fret%s:duration%s:dead%s:beat%s:transition%s" % (effect.grace.fret, 
                                                                               effect.grace.duration,
                                                                               int(effect.grace.isDead),
                                                                               int(effect.grace.isOnBeat),
                                                                               effect.grace.transition.value))

    if(effect.harmonic):
        # type = 1 natural harmonic 
        # type = 2 artificial harmonic (pitch.value, octave.quindicesima)
        # type = 3 tapped harmonic
        # type = 4 pinch harmonic
        # type = 5 semi harmonic
        if(effect.harmonic.type==2):
            harmonic = "nfx:harmonic:%s:pitch%s:octave%s" % (effect.harmonic.type, 
                                                         effect.harmonic.pitch.value, 
                                                         effect.harmonic.octave.value)
        elif(effect.harmonic.type==3):
            harmonic = "nfx:harmonic:%s:fret%s" % (effect.harmonic.type, 
                                                         effect.harmonic.fret)
        else:
            harmonic = "nfx:harmonic:%s" % effect.harmonic.type
        effects.append(harmonic)
    # leftHandFinger -- ignoring it
    # rightHandFinger -- ignoring it
    if(effect.slides):
        # you can have multiple slides
        # [<SlideType.shiftSlideTo: 1>]
        """intoFromAbove = -2
            intoFromBelow = -1
            none = 0
            shiftSlideTo = 1
            legatoSlideTo = 2
            outDownwards = 3
            outUpwards = 4
            """
        for slide in effect.slides:
            effects.append("nfx:slide:%s" % slide.value)
    if(effect.tremoloPicking):
        # duration (how fast the picking happens)
        effects.append("nfx:tremoloPicking:duration%s" % effect.tremoloPicking.duration.time)
    if(effect.trill):
        # (switching between two notes really fast)
        # fret number
        # duration (how fast the switching happens)
        effects.append("nfx:trill:fret%s:duration%s" % (effect.trill.fret, effect.trill.duration.time))
    return effects

# take a list of nfx tokens and modify the note effect
# give it note and a list
def tokens_to_note_effect(note, nfx_tokens):
    effect = note.effect
    for token in nfx_tokens:
        # DadaGP v1.1 begin ====>
        token = unsplit_fx(token) # convert v1.1 format (dict with param tokens) to v1.0 (long string)
        # <==== DadaGP v1.1 end
        t = token.split(":")
        if(t[0]!="nfx"):
            # the first part of the token should be nfx, if it's not, it shouldn't be here, ignore it
            print("This token shouldn't be here, it's not a NFX", token)
            continue
        if t[1]=="tie":
            note.type = gp.NoteType(2)
        elif t[1]=="dead":
            note.type = gp.NoteType(3)
        elif t[1]=="accentuated_note":
            effect.accentuatedNote = True
        elif t[1]=="ghost_note":
            effect.ghostNote = True
        elif t[1]=="hammer":
            effect.hammer = True
        elif t[1]=="heavy_accentuated_note":
            effect.heavyAccentuatedNote = True
        elif t[1]=="let_ring":
            effect.letRing = True
        elif t[1]=="palm_mute":
            effect.palmMute = True
        elif t[1]=="staccato":
            effect.staccato = True
        elif t[1]=="vibrato":
            effect.vibrato = True
        elif t[1]=="bend":
            #print("bend effect")
            effect.bend = gp.BendEffect()
            effect.bend.type = gp.BendType(int(t[2][4:]))
            # bend += ":pos%s:val%s:vib%s" % (points.position, points.value, int(points.vibrato))
            effect.bend.points = []
            effect.bend.value = 50
            # should only be a multiple of 3
            assert len(t)%3==0, "Bend effect token has a typo. %s" % token
            num_points = int((len(t)-3)/3)
            # for each triplet, create a point:
            for p in range(num_points):
                point = guitarpro.models.BendPoint()
                point.position = int(t[3+p*3][3:])
                point.value = int(t[4+p*3][3:])
                point.vibrato = int(t[5+p*3][3:])==1
                effect.bend.points.append(point)
            #print(effect.bend)
        elif t[1]=="grace":
            # duration number
            # fret number
            # isDead true/false
            # isOnBeat true/false
            # transition 0,1,2,3
            # effects.append("nfx:grace:fret%s:duration%s:dead%s:beat%s:transition%s" % (effect.grace.fret, 
            #                                                                        effect.grace.duration,
            #                                                                        int(effect.grace.isDead),
            #                                                                        int(effect.grace.isOnBeat),
            #                                                                        effect.grace.transition.value))
            effect.grace = gp.GraceEffect()
            #print(token)
            #print(int(t[2][4:]))
            effect.grace.fret = max(0,int(t[2][4:])) # sometimes fret can be below zero?
            effect.grace.duration = int(t[3][8:])
            effect.grace.isDead = int(t[4][4:])
            effect.grace.isOnBeat = int(t[5][4:])
            effect.grace.transition = gp.GraceEffectTransition(int(t[6][10:]))
        elif t[1]=="harmonic":
            harmonic_type = int(t[2])
            if(harmonic_type==1):
                effect.harmonic = gp.NaturalHarmonic()
            elif(harmonic_type==2):
                effect.harmonic = gp.ArtificialHarmonic()
                effect.harmonic.pitch = gp.PitchClass(int(t[3][5:]))
                effect.harmonic.octave = gp.Octave(int(t[4][6:]))
            elif(harmonic_type==3):
                fret = int(t[3][4:])
                effect.harmonic = gp.TappedHarmonic(fret=fret)
            elif(harmonic_type==4):
                effect.harmonic = gp.PinchHarmonic()
            elif(harmonic_type==5):
                effect.harmonic = gp.SemiHarmonic()
        elif t[1]=="slide":
            slide = gp.SlideType(int(t[2]))
            effect.slides.append(slide)
        elif t[1]=="tremolo_picking":
            effect.tremoloPicking = gp.TremoloPickingEffect()
            effect.tremoloPicking.duration = gp.Duration.fromTime(int(t[2][8:]))
            print(token)
        elif t[1]=="trill":
            effect.trill = gp.TrillEffect()
            effect.trill.fret = int(t[2][4:])
            effect.trill.duration = gp.Duration.fromTime(int(t[3][8:]))
        
# Return the instrument token prefix for notes
# If there are multiple drums tracks, they will all return the same prefix "drums"
# the same goes for leads and pads
def get_instrument_token_prefix(track, tracks_by_group):
    if(track in tracks_by_group["drums"]):
        return "drums"
    elif(track in tracks_by_group["bass"]):
        return "bass"
    elif(track in tracks_by_group["leads"]):
        return "leads"
    elif(track in tracks_by_group["pads"]):
        return "pads"
    elif(track in tracks_by_group["remove"]):
        return "remove"
    elif(track in tracks_by_group["distorted"]):
        for i,test in enumerate(tracks_by_group["distorted"]):
            if(track==test):
                return "distorted%s" % i
    elif(track in tracks_by_group["clean"]):
        for i,test in enumerate(tracks_by_group["clean"]):
            if(track==test):
                return "clean%s" % i
    else:
        print(track)
        assert False, "This track doesn't belong to a group"        
# test
# for t,track in enumerate(song.tracks):
#    print(t, get_instrument_token_prefix(track, tracks_by_group))

# I'm trying to insert a new note or rest (event) into the current list of events for this measure. 
# Test if there is already a note in this spot (same beat/instrument/fret)
# If I'm inserting a note:
#   If there is a note there, return false
#   If there is a rest there, return true, and remove the rest (NOTE: THIS FUNCTION MUTATES events_this_measure)
#   If there is nothing there, return true
# If I'm inserting a rest:
#   If there's a note or rest there, return false
#   If there's nothing there, return true
def oops_theres_a_note_here(new_event, events_this_measure, verbose=False):
    assert new_event["type"] in ["note" ,"rest"] , "Only notes or rests should call this function"
    # Look through all the events this measure
    # If a conflicting note is discovered, return False
    # If a conflicting rest is discovered, delete it.
    # If there is no conflict, at the end of the loop, return True
    # warning: do not use enumerate, because i'll be using del to remove rest events
    i = 0
    while i<len(events_this_measure):
        event = events_this_measure[i]
        if event["start"]==new_event["start"] \
         and event["type"] in ["note", "rest"] \
         and event["instrument_prefix"] == new_event["instrument_prefix"]:
            # Found an note or rest at the same time on the same instrument.
            if event["type"]=="note":
                # Found a note 
                if(new_event["type"]=="rest"):
                    # I was trying to insert a rest. Ignore my rest because there's already a note. 
                    verbose and print("I was trying to insert a rest. Ignore my rest because there's already a note.")
                    verbose and print(event,new_event)
                    return False
                if(new_event["type"]=="note"):
                    # I am trying to insert a note. 
                    if(event["instrument_prefix"]=="drums"): 
                        # Ignore drum strings for now.
                        # With drums, fret == midinumber. 
                        # But you can't have two drums of the same midinumber. 
                        # HMM: I think you can only have 6 simultaneous drums max. 
                        # That's okay. Just leave the extra drums if they exist.. deal with it when rebuilding GP file.
                        if(event["fret"]==new_event["fret"]):
                            # This drum is already being played
                            verbose and print("This drum note is already being played. Ignore my note.")
                            verbose and print(event,new_event)
                            return False
                    else:
                        # Melodic instruments can only have one note per string
                        if(new_event["string"]==event["string"]):
                            # There's already a note on this string. Ignore my note.
                            verbose and print("There's already a note on this string. Ignore my note.")
                            verbose and print(event,new_event)
                            return False
                        else:
                            # Don't return true yet. There could still be a note on this string.
                            pass
            elif event["type"]=="rest":
                # Found a rest 
                if(new_event["type"]=="note"):
                    # I want to insert a note here. 
                    # Remove the rest. 
                    verbose and print(" I want to insert a note here. Remove the rest") ####
                    # Will this really work I'm kind of scared
                    del events_this_measure[i] 
                    continue
                    # careful, this is tricky, deleting elements from a list while iterating
                    # the continue avoids the i += 1 at the end of the loop
                    # Should I return true now to insert my note?
                    # In theory, there would only be a rest here, if there were no other rests and no other notes
                    # return True
                elif(new_event["type"]=="rest"):
                    # I watn to insert a rest, and there's already a rest here. 
                    # Do nothing. 
                    verbose and print("I wanted to insert a rest, but there's already a rest here. ")
                    verbose and print(event,new_event)
                    return False
        # okay now handle cases where a note was already playing on the same instrument
        elif event["type"] in ["note"] \
         and event["start"]+event["duration"]>new_event["start"] \
         and event["instrument_prefix"] == new_event["instrument_prefix"]:
            # A note was already playing
            if(new_event["type"]=="rest"):
                # I'm trying to insert a rest, but notes are alread playing. 
                # Ignore my new rest.
                verbose and print("I was trying to insert a rest. There's already a note playing though.")
                return False
            elif(new_event["type"]=="note"):
                # I'm trying to insert a note where a note was already playing
                if(event["instrument_prefix"]=="drums"): 
                    # don't deny the new note. drum hits dont interefere with each other in this way
                    pass 
                else:
                    if(new_event["string"]==event["string"]):
                        # New note on same string. 
                        # Don't deny the new note. Sorry old note, you're getting overwritten.
                        pass
                    else:
                        # A note is already playing on this string. 
                        # If I accept the new note, it will silence the old note's ringing out. 
                        # This ends up sounding choppy. 
                        # Instead, I will let the old note ring out with let_ring note effect
                        # (note: we could also add a repeat of that note, and tie it, to ring it out, but I think this is more complicated)
                        # Add let_ring to the old event's notefx
                        #print("added let_ring")
                        #if "nfx:let_ring" not in event["effects"]:
                        #    event["effects"].append("nfx:let_ring")
                        pass
        i += 1
    return True # found no conflicts

# I'm trying to insert a new beatfx (event) into the current list of events for this measure. 
# Test if there are already beatfx of the same type. 
# Return a list of non-contradicting beatfx tokens
def oops_theres_a_conflicting_beatfx(new_event, events_this_measure):
    assert new_event["type"] == "beatfx" , "Only notes or rests should call this function"
    # Build a list of non-contracting beatfx tokens
    new_effects = []
    for i,event in enumerate(events_this_measure):
        if event["start"]==new_event["start"] \
         and event["type"] == ["beatfx"] \
         and event["instrument_prefix"] == new_event["instrument_prefix"]:
            # There was already a beatfx event with effects in the same beat on the same instrument
            # Loop through my new effects, see which ones we can keep
            for b1,effect1 in enumerate(new_event["beatfx"]):
                # because bfx follow the format bfx_name[_params..] we can compare contradictory tokens by name
                es1 = effect1.split(":") 
                passes = True
                for b2,effect2 in enumerate(event["beatfx"]):
                    es2 = effect2.split(":")
                    if(es1[0]==es2[0] and es1[1]==es2[1]):
                        # There's already a bfx with the same name.
                        # Ignore this effect
                        passes = False
                        break
                if(passes):
                    # Ok there were no contradictions
                    new_effects.append(effect1)
    return new_effects

# CALCULATING FRET VALUES

# offset is the capo
# it affects all note values
# (don't use pyguitarpro's "realValue" because it ignores offset)
# (note value zero means an open note at the capo)

# D standard: String 6 midinote = 38
# E standard: String 6 midinote = 40

# offset 0, note value 0, string 6, E-Standard, is E,  realValue 40
# offset 0, note value 2, string 6, E-Standard, is F#, realValue 42 # Windowpane (2).gp3
# offset 2, note value 0, string 6, E-Standard, is F#, realValue 40 # Windowpane (3).gp4
# offset 2, note value 2, string 6, D-Standard, is F#, realValue 40 # Windowpane.gp3

# offset 0, note value 2, string 5, E-Standard, is B,  realValue 47
# offset 0, note value 4, string 5, E-Standard, is C#, realValue 49 # Windowpane (2).gp3
# offset 2, note value 2, string 5, E-Standard, is C#, realValue 47 # Windowpane (3).gp4
# offset 2, note value 4, string 5, D-Standard, is C#, realValue 47 # Windowpane.gp3

# Calculate the (E-standardized) fret number
# Adjust by tuning and offset and pitch_shift
# Drop tunings use frets -1 and -2
def get_fret(note, track, pitch_shift):
    # note.string -- 1st string is the highest string
    # note.value -- supposedly the fret number but not quite
    # note.realValue -- midinote number (don't use this, it ignores offset)
    # pitch_shift --- the instruments have been downtuned this many pitches
    # track.offset -- there is a capo on this fret 
    # len(track.strings) -- number of strings
    # track.strings[0].value -- midinote number of 0th string (highest string)
    string = note.string
    instrument_group = get_instrument_group(track)
    strings = [str(s) for s in track.strings] 
    #print(instrument_group, strings)
    if(instrument_group=="drums"):
        return note.value # this is supposed to be equivalent to the midinote number of the drum hit
    tuning = get_tuning_type(instrument_group,strings)
    drop_shift = 0
    if instrument_group=="bass":
        if tuning=="b4_drop":
            if string==4:
                drop_shift = 2
    else: 
        # everything else is treated like a guitar
        if tuning=="g6_drop" or tuning=="g7_drop":
            if string==6 or string==7:
                drop_shift = 2
    # print(instrument_group, tuning, string, drop_shift)
    # Okay finally 
    # The (E-standardized) fret number is the GP note value, minus any drop tuning pitches, 
    return note.value + track.offset - drop_shift

#note = song.tracks[0].measures[139].voices[0].beats[0].notes[0]
#print(note)
#get_fret(note, song.tracks[0], pitch_shift)



# supported_times = [0]
# for i in range(0,10000):
#     try:
#         y = gp.models.Duration.fromTime(i)
#         supported_times.append(i)
#     except:
#         continue
supported_times = [3, 5, 6, 9, 10, 12, 15, 18, 20, 24, 30, 36, 40, 45, 48, 60, 72, 80, 90, 96, 120, 144, 160, 180, 192, 240, 288, 320, 360, 384, 480, 576, 640, 720, 768, 960, 1152, 1280, 1440, 1536, 1920, 2304, 2560, 2880, 3072, 3840, 5760]

# time duration may be an int or Fraction
# if it is a supported time duration, it will return itself
# if it is not, it will find a neighboring duration that is supported
def convert_to_nearest_supported_time(x):
    if(x==0):
        return 0
    for i in range(1,len(supported_times)):
        t = supported_times[i]
        if t > x:
            t_larger = t
            t_smaller = supported_times[i-1]
            if(t_larger - x < x - t_smaller):
                return t_larger
            else:
                return t_smaller
    # x is too large. 
    # return the max(?)
    return 5760
    
assert convert_to_nearest_supported_time(Fraction(99/3)) == 30
assert convert_to_nearest_supported_time(99/3) == 30
assert convert_to_nearest_supported_time(480) == 480
assert convert_to_nearest_supported_time(480.1) == 480
assert convert_to_nearest_supported_time(481) == 480
assert convert_to_nearest_supported_time(920*1000) == 5760 ## if duration is too large, use the max supported duration


# Takes a GP file, converts to token format
def guitarpro2tokens(song, artist, verbose=False):
    # - Map every track in song to an instrument group 
    # - Remove SoundFX tracks
    # - Throw error if any track has an instrument change event in mixTable
    # - Throw error if song has more than 3 distorted guitars, 2 clean guitars, or 1 bass
    # - Non-guitar instruments will become either piano (leads) or choir (pads) and treated like a guitar track.
    # - Multiple drums tracks get combined into one track. Same for leads/pads.
    # - Throw error if any guitar/bass/pad/lead track has a non-supported tuning
    #     - 6,7 string guitars and 4,5,6 string basses allowed
    #     - Drop D or Drop AD is allowed, and those extra low notes will be on Frets -2 or -1
    #     - Downtuning is allowed, but only if all guitar/bass/pad/lead tracks are downtuned together the same pitch_shift
    #     - Capo offsets will be removed. Frets will be shifted
    #         - Normally if capo is at fret 2, and open strings are played, GP tabs this at fret 0, which I disagree with.
    #         - Instead, if capo was at fret 2, those open strings will now be at fret 2. As expected!
    
    ##############################
    ## Identify channels by group

    tracks_by_group = {
        "drums": [],
        "distorted": [],
        "clean": [],
        "bass": [],
        "leads": [],
        "pads": [],
        "remove": []
    }

    for i,track in enumerate(song.tracks):
        group = get_instrument_group(track)
        tracks_by_group[group].append(track)
        
    # remove sfx tracks
    while True:
        removed = False
        for i,track in enumerate(song.tracks):
            if get_instrument_group(track)=="remove":
                del song.tracks[i]
                removed = True
                break
        if removed: 
            continue
        break

    max_bass = 1
    max_clean = 2
    max_distorted = 3
    n_bass = len(tracks_by_group["bass"])
    n_clean = len(tracks_by_group["clean"])
    n_distorted = len(tracks_by_group["distorted"])
    assert n_bass<=max_bass, "Too many bass guitar channels. Max %s. You have %s" % (max_bass, n_bass)
    assert n_clean<=max_clean, "Too many clean/acoustic guitar channels. Max %s. You have %s" % (max_clean, n_clean)
    assert n_distorted<=max_distorted, "Too many distorted/overdrive guitar channels. Max %s. You have %s" % (max_distorted, n_distorted)

    verbose and print(tracks_by_group)

    # Throw error if there is an instrument change
    for t,track in enumerate(song.tracks):
        for m,measure in enumerate(track.measures):
            for v,voice in enumerate(measure.voices):
                for b,beat in enumerate(voice.beats):
                    if(beat.effect.mixTableChange):
                        assert beat.effect.mixTableChange.instrument == None, "Instrument Change Not Supported"
    
    #############################################
    # TUNING SHIFT

    # Pre-processing

    ## All Guitar/Bass/Leads/Pads have 
    ##  - no weird tuning combinations
    ##  - Downtuning is supported, but only if all tracks are downtuned the same pitch_shift together. 
    ##  - Guitar is basically always 7 string, with possible dropD or dropAD represented as fret -2 or -1
    ##  - Bass is basically always 6 string, with possible dropD or drop AD represented as fret -2 or -1
    ##  - Pads/Leads are treated the same as a guitar track.
    ##  - In Post, the stringing will be determined based on what notes were generated. 
    ##      - If no string7 notes then use 6 string, etc.
    ##      - If no -2 or -1 frets, then use E standard or BE standard.
    ##  - In Post, the uniform pitch shift will be applied 
    ##  - In Pre, remember to add the capo offset to the fret number
    
    # Verify support TUNING
    downtunages = []
    tuning_types = {} # keep tracking of tuning types

    for t,track in enumerate(song.tracks):
        midinumber = track.channel.instrument
        group_name = instrument_groups[midinumber]
        strings = [str(string) for string in track.strings]
        if(track.isPercussionTrack):
            tuning_types[t] = "drums"
            continue
        if(group_name=="distorted" or group_name=="clean"):
            assert is_good_guitar_tuning(strings), "Error: Track %s has unsupported guitar tuning: %s" % (t," ".join(strings))
            downtunages.append(guitar_downtunage(strings))
        elif(group_name=="bass"):
            assert is_good_bass_tuning(strings), "Error: Track %s has unsupported bass tuning: %s" % (t," ".join(strings))
            downtunages.append(bass_downtunage(strings))
        elif(group_name=="pads" or group_name=="leads"):
            assert is_good_guitar_tuning(strings), "Error: Track %s has unsupported pads/leads tuning: %s" % (t," ".join(strings))
            downtunages.append(guitar_downtunage(strings))
        tuning_types[t] = get_tuning_type(group_name,strings)

    verbose and print("Downtuning scheme of guitar/bass/pads/leads tracks:", downtunages)
    allthesame = all([x%12==downtunages[0]%12 for x in downtunages]) 
    # for example, (-3, -3, -3) are all the same downtune
    # also, (-3, -3, -15) is all the same downtune. That third instrument will end up changing octave to meet the others. 
    assert allthesame, "Error: Guitar/bass/pads/leads tracks must be all be downtuned by same pitch."

    # Find the PITCH SHIFT 
    # if downtunages are all the exact same, use that pitch
    # if downtunages are different, but mod 12 equivalent, then choose the pitch closest to zero.
    # Note: Whatever -12 pitchshift there was just gets shifted to 0. That instrument may change octave. 
    # Find the pitch closest to zero by sorting
    downtunages.sort(key = lambda x: abs(int(x)))
    if(len(downtunages)==0):
        pitch_shift = 0
    else:
        pitch_shift = downtunages[0] 
    verbose and print("Pitch Shift:", pitch_shift)
    verbose and print(tuning_types)
    
    #############################################
    # CONDITIONING

    # Tempo
    # song.tempo is the initial tempo
    # Note: please ignore measure.tempo, it's wrong and seems to be a bug in guitarpro
    # tempo may change later in the song in a beatEffect
    tempo_token = "tempo:%s" % roundtempo(song.tempo)

    downtune_token = "downtune:%s" % pitch_shift

    head_tokens = [artist, downtune_token, tempo_token, "start"]
    
    verbose and print("=========\nHead tokens")
    verbose and print(head_tokens)
    
    ######################################################
    ## BUILD THE LIST OF EVENTS
    
    events_all = [] # a list of measures. each measure is a list of events. 
    # there's four types of events: measure, note, rest, beatfx
    # measure event tokens always come at the beginning of the measure before the notes
    # notefx tokens always come immediately after the note
    # beatfx tokens always come at the end of the beat
    # the order of beats matters
    # but the order of notes/tracks within a beat doesn't matter (this can be changed for dataset augmentation)

    # measures (im representing measures as the top of the hierarchy so that autoregression always moves forward in time)
    for m, _ in enumerate(song.tracks[0].measures):
        measure = song.tracks[0].measures[m] 
        events_this_measure = [] # just this measures' events
        # Measure event is always the first event in the list:
        # (hack: setting track to -1 ensures the measure tokens will come before the note tokens when sorting0
        event = {"type": "measure", "track": -1, "start": measure.start, "tokens": get_measure_tokens(measure)}
        events_this_measure.append(event)
        # tracks in measures 
        for t, track in enumerate(song.tracks):
            instrument_prefix = get_instrument_token_prefix(track, tracks_by_group)
            measure = track.measures[m]
            # voices in tracks (i guess tracks have 2 voices? i will just combine them into one voice)
            for v, voice in enumerate(measure.voices):
                #print(m, t, v)
                for b, beat in enumerate(voice.beats):
                    # in the latest version of pyguitarpro (September 25 2020) 
                    # duration.time may be int or Fraction
                    # We could convert Fraction to int for wait:## format
                    # But Fraction may be rounded to an integer that is not supported by fromTime
                    # Use this function which finds the nearest time supported by FromTime
                    #beat_duration = convert_to_nearest_supported_time(beat.duration.time) 
                    #beat_start = convert_to_nearest_supported_time(beat.start - measure.start) + measure.start
                    beat_duration = beat.duration.time
                    beat_start = beat.start
                    #print(beat_start, beat.start)
                    if(beat.status.name=="empty"): 
                        # there's supposedly nothing in this measure for this voice/track
                        # however even an empty beat can still have beat effects
                        # and we care about tempo changes via mixtable changes
                        pass
                    elif(beat.status.name=="normal"):
                        # note or a set of notes
                        for n, note in enumerate(beat.notes):
                            # NOTE EFFECTS
                            # woah I almsot forgot note.type, which hands tied notes and dead notes
                            notefx = []
                            if(note.type.value==2):
                                notefx.append("nfx:tie")
                            elif(note.type.value==3):
                                notefx.append("nfx:dead")
                            # elif(note.type==1):
                            #   a rest note? ˙hmm
                            notefx.extend(note_effect_list(note.effect))
                            if(track.isPercussionTrack):
                                # Need to verify how percussion behaves on strings/values
                                string = note.string
                                fret = note.value
                            else:
                                # strings are 1-indexed. They start from string 1 and go to string 6 or 7
                                # GP's string value is OK to copy over into our representation
                                # UNLESS it's a 4 or 5 string bass, which I want to start from string 2
                                # the reason for this is that 6 string bass adds in the high C string which we want as string 1
                                if(instrument_prefix=="bass" and len(track.strings)<6):
                                    string = note.string + 1
                                else:
                                    string = note.string
                                fret = get_fret(note, track, pitch_shift)
                            # Tricky calculation to get the fret number
                            # note.velocity=95 -- maybe ignore velocity for now
                            event = {"type": "note",
                                     "track": t, 
                                     "instrument_prefix": instrument_prefix,
                                     "start": beat_start,
                                     "duration": beat_duration, 
                                     "string": string,
                                     "fret": fret,
                                     "effects": notefx,
                                     }
                            # Test if there's already a note/rest in this spot
                            # This may happen when combining tracks into one track
                            # Or if the generator is so dumb that it puts two notes on the same string
                            # Note: If there was a rest here, remove it, replace it with a note.
                            test = oops_theres_a_note_here(event, events_this_measure, verbose);
                            if(test):                            
                                events_this_measure.append(event)
                            else:
                                verbose and print("Note insertion: Oops theres already a note here", m, beat_start, instrument_prefix)
                    elif(beat.status.name=="rest"):
                        #print(beat.status.name)
                        # a rest 
                        event = {"type": "rest",
                                 "track": t, 
                                 "duration": beat_duration,
                                 "instrument_prefix": instrument_prefix,
                                 "start": beat_start
                                 }
                        # Test if there's already a note/rest in this spot
                        # This may happen when combining tracks into one track
                        # Or if the generator is so dumb that it puts two notes on the same string
                        #print("rest",event)
                        test = oops_theres_a_note_here(event, events_this_measure, verbose);
                        if(test):
                            events_this_measure.append(event)
                        else:
                            verbose and print("Rest insertion: Oops theres already a note here", m, beat_start, instrument_prefix)
                    ## Beat Effects come after the notes/rests
                    beatfx = beat_effect_list(beat.effect)
                    if(len(beatfx)):
                        event = {"type": "beatfx", 
                                 "effects": beatfx,
                                 "duration": beat_duration,
                                 "instrument_prefix": instrument_prefix,
                                 "start": beat_start, "track": t}
                        # Test if there's already a beatfx in this spot that conflicts (contradicting value)
                        # This may happen when combining tracks into one track
                        # Or if the generator is too dumb and puts two opposing beatfx's on same the same beat
                        test = oops_theres_a_conflicting_beatfx(event, events_this_measure);
                        if(test):
                            verbose and print("Oops theres already a beatfx here", m, beat_start, instrument_prefix)
                        else:
                            # Add the BeatFX event
                            events_this_measure.append(event)
                        # Check if this was an empty measure. An empty measure with a beatfx should get a rest.
                        # This will happen in the case of a tempo change on an empty measure
                        if beat.status.name=="empty":
                            event = {"type": "rest",
                                 "track": t, 
                                 "duration": beat_duration,
                                 "instrument_prefix": instrument_prefix,
                                 "start": beat_start}
                            # Test if there's already a note/rest in this spot
                            # This may happen when combining tracks into one track
                            # Or if the generator is so dumb that it puts two notes on the same string
                            #print("rest",event)
                            test = oops_theres_a_note_here(event, events_this_measure, verbose);
                            if(test):
                                # Add the "fake" rest which the beat effect attaches to
                                events_this_measure.append(event)
                            else:
                                verbose and print("Rest insertion: Oops theres already a note here", m, beat_start, instrument_prefix)
        events_all.extend(events_this_measure)
        
    verbose and print("=========\nFirst 5 events:")
    verbose and print(events_all[:5])

    #############################################
    ## CONVERT LIST OF EVENTS INTO LIST OF BODY TOKENS
    
    # body_tokens remove start/durations from notes/rests and introduce waits between them
    # also note_effects immediately proceed their notes 
    body_tokens = []
    t = 0

    # sort by start time
    # Measure tokens first
    # Then note/rest/notefx/beatfx tokens sorted by track number
    # Notefx tokens come right after note tokens
    # Beatfx tokens come right after all note/notefx tokens for that beat
    events_sorted = sorted(events_all, key=lambda x: (x['start']*1000 + x["track"]*10 + int(x["type"]=="beatfx")))
    for e in events_sorted:
        e = e.copy()

        # test if we moved ahead in time. Whether it's a new measure/note/rest anything. If so, emit a wait token
        if(e["start"]>t):
            if(t>0):
                # ignore the first wait
                # yes. calculate how much time we advanced
                wait_time = e["start"]-t
                # append the WAIT token for amount of time advancement
                body_tokens.append("wait:%s" % wait_time)
                # remember old start value
            t = e["start"]     
        if(e["type"]=="measure"):
            #w_events.append(e)
            # since the first measure start on beat 1 (960 ticks), this also removes the unnecesary wait960
            t = e["start"]
            body_tokens.extend(e["tokens"])
        if(e["type"]=="note" or e["type"]=="rest"):   
            effects = []
            if(e["type"]=="note"):
                # note has effects. append them after the note
                effects = e["effects"]
                #del e["start"]
                del e["effects"]
                # append the NOTE  token
                #w_events.append(e)
                if(e["instrument_prefix"]=="drums"):
                    # Ignore strings for drums. Rebuild the strings later. 
                    body_tokens.append("drums:note:%s" % e["fret"])
                else:
                    body_tokens.append("%s:note:s%s:f%s" % (e["instrument_prefix"], e["string"], e["fret"]))
                if(len(effects)>0):
                    # append the NOTE EFFECTS
                    body_tokens.extend(effects)
                    pass
            elif(e["type"]=="rest"):
                # append the REST
                # w_events.append(e)
                body_tokens.append("%s:rest" % (e["instrument_prefix"]))
                pass
        if(e["type"]=="beatfx"):
            # append the BEAT EFFECTS after the notes/rests of that beat
            #w_events.append(e)
            body_tokens.extend(e["effects"])
            pass
    # If the last event has duration information, this becomes the last "wait" token
    if "duration" in e:
        body_tokens.append("wait:%s" % e["duration"])
        
    # DadaGP v1.1 begin ===>
    # Split some rare tokens into many tokens
    body_tokens_v1_1 = []
    for token in body_tokens:
        body_tokens_v1_1.extend(split_rare_token(token))
    # <=== DadaGP 1.1 end 
    
    end_tokens = ["end"]
    all_tokens = head_tokens + body_tokens_v1_1 + end_tokens
    verbose and print("=========\nFirst 20 tokens:")
    verbose and print(all_tokens[:20])
    verbose and print("=========\nTotal tokens:",len(all_tokens))
    return all_tokens


# Converts a list of NoteNames to a list of GuitarString pyguitarpro objects
def convert_strings_for_pygp(strings, pitch_shift=0):
    gs = []
    for i,x in enumerate(strings):
        note_number = int(noteNumber(x)[3]) + int(pitch_shift)
        gs.append(gp.GuitarString(number=i+1, value=note_number))
    return gs
# Tests
## LOAD a BLANK GP5 SCORE 
blankgp5 = gp.parse("blank.gp5")
blankgp5.tracks = []
new_track = gp.Track(blankgp5)
strings = ['E5', 'B4', 'G4', 'D4', 'A3', 'E3']
new_track.strings = convert_strings_for_pygp(strings)
assert new_track.strings[0].value==64
#print(new_track.strings)
# Test pitchshift
new_track.strings = convert_strings_for_pygp(strings,-2)
#print(new_track.strings)
assert new_track.strings[0].value==62

# Given a list of tokens, constructs a guitarpro song object
def tokens2guitarpro(all_tokens, verbose=False):
    # Interpret a token list back into a GP song file
    ## TODO: some kinda validation/flexibility for weird files the net generates?
    ## For now let's just support valid dataset files 
    head = all_tokens[:4]
    body = all_tokens[4:]
    artist_token = head[0] 
    assert head[1].split(":")[0]=="downtune"
    assert head[2].split(":")[0]=="tempo"
    assert head[3]=="start"
    initial_tempo = int(head[2].split(":")[1])
    pitch_shift = int(head[1].split(":")[1])
    verbose and print(artist_token, initial_tempo, pitch_shift)
    
    ###########
    ## Instruments / Strings / Droptuning
    ## Check which instruments we got

    instrument_check = {
        "distorted0": False,
        "distorted1": False,
        "distorted2": False,
        "clean0": False,
        "clean1": False,
        "bass": False,
        "leads": False,    
        "pads": False,
        "drums": False,

    }
    for token in body:
        tokensplit = token.split(":")
        if len(tokensplit)>1 and tokensplit[1]=="note":
            instrument = tokensplit[0]
            assert instrument in instrument_check.keys(), "Unknown instrument %s"%instrument
            instrument_check[instrument]=True
    verbose and print(instrument_check)
    
    instrument_stringinfo = {
        "distorted0": False,
        "distorted1": False,
        "distorted2": False,
        "clean0": False,
        "clean1": False,
        "bass": False,
        "pads": False,
        "leads": False
    }

    for instrument in instrument_stringinfo:
        if(not instrument_check[instrument]):
            # this instrument doesn't exist in the score
            continue
        if(instrument == "drums"):
            # ignore drums
            continue
        # treat bass differently
        if(instrument =="bass"):
            ## Get info on bass strings

            # Check which strings we got 
            # "b4_standard", "b5_standard", "b6_standard", "b4_drop"

            # bass strings
            strings = 4
            drop_tuning = False

            # Note: Strings are 1-indexed
            # Note: 4 string and 5 string basses start at string 2
            string_count = {1:0,2:0,3:0,4:0,5:0,6:0}
            for token in body:
                t = token.split(":")
                if len(t)>1 and t[0]=="bass" and t[1]=="note":
                    string = int(t[2][1:]) # ex "s4" 
                    fret = int(t[3][1:])  # ex "f5"
                    if fret == -1 or fret == -2:
                        if string == 5 or string == 6:
                            drop_tuning = True
                        else:
                            assert False, "Drop tuning only allowed on string 5 and 6"

                    string_count[string]+=1
            #print(string_count)
            if(string_count[1]>0):
                # it's a 6 string, it has the high C string (strings 1,2,3,4,5,6)
                strings = 6
            elif(string_count[6]>0):
                # it's a 5 string (strings 2,3,4,5,6)
                strings = 5
            else:
                # it's a 4 string (strings 2,3,4,5)
                strings = 4
            instrument_stringinfo[instrument] = {"drop_tuning": drop_tuning, "strings": strings}

        else:
            # everything else
            ## Guitars / Pads / Leads info
            # Check which strings we got 
            # "g6_standard", "g7_standard", "g6_drop", "g7_drop"
            # Treat all like guitar

            strings = 6
            drop_tuning = False

            # Note: Strings are 1-indexed
            string_count = {1:0,2:0,3:0,4:0,5:0,6:0,7:0}
            for token in body:
                t = token.split(":")
                if len(t)>1 and t[1]=="note" and t[0]==instrument:
                    string = int(t[2][1:]) # ex "s4" 
                    fret = int(t[3][1:])  # ex "f5"
                    if fret == -1 or fret == -2:
                        if string == 6 or string == 7:
                            drop_tuning = True
                        else:
                            assert False, "Drop tuning only allowed on string 6 and 7"
                    string_count[string]+=1
            #print(string_count)
            if(string_count[7]>0):
                # it's a 7 string, it has the low string (strings 1,2,3,4,5,6,7)
                strings = 7
            else:
                # it's a 6 string (strings 1,2,3,4,5,6)
                strings = 6
            instrument_stringinfo[instrument] = {"drop_tuning": drop_tuning, "strings": strings}
            
    verbose and print(instrument_stringinfo)
    
    ##########
    ## READ MEASURES
    
    ## Interpret the body tokens into a dictionary object

    ## Group the body into measures
    ## Each measure has measure_tokens 
    ## Group each measure into tracks (by instrument)
    ## Each track is a list of beats with a clock time 
    ## Each beat has beat effects (bfx) and a list of notes
    ## Each note has note effects (nfx) and a note token 

    all_measures = []
    this_measure = {}

    clock = 960 # increments whenever we see a wait
    # clock starts at 960 for some reason??? 1-indexed quarter notes i guess

    current_note = None
    current_beat = None
    current_effect = None
    orphaned_nfx = []
    orphaned_bfx = []

    # If notes appear that have no duration (they are not followed by wait token before the end of the measure)
    # use this value for their duration:
    last_reported_duration = 480
    # clocktime of the last beat we iterated over  
    last_reported_beat_clock = 480

    for i,token in enumerate(body):
        # Check if this measure has ended
        if token in ["end", "new_measure"] and len(this_measure):
            # End of measure. Wrap it up
            # move the old measure to all_measures
            all_measures.append(this_measure)
            # If there was a previous measure with notes, and it ended with notes and no wait token
            # We could do nothing and drop those notes, or we could give them an arbitary duration 
            # ..by moving the clock forward here by some arbitrary amount
            if(last_reported_beat_clock == clock):
                if last_reported_duration == 0:
                    # defeats the purpose to move it ahead by zero
                    # this is a failsafe, just in case the calculation failed in a corner case
                    last_reported_duration = 480
                # move the clock ahead
                clock += last_reported_duration
        # Ok now deal with the next token
        if token == "end":
            # End of the song
            break
        if token=="new_measure":
            # starting a new measure
            this_measure = {
                "trackbeats": {},
                "measure_tokens": [],
                "clock": clock
            }
            # reset
            current_note = None
            current_beat = None
            current_effect = None
            orphaned_nfx = []
            orphaned_bfx = []
        else:
            # In the middle of a measure
            #this_measure["tokens"].append(token)        
            t = token.split(":")
            if(t[0]=="measure"):
                # measure token
                # these are supposed to only be at the very beginning
                # (but if they appear somewhere in the middle of the measure that might be ok?)
                # Measure tokens are of the format measure:type[:params]
                # Per measure there can only be one of each type of measure token
                # Check if that type already exists
                passed = True
                for mt in this_measure["measure_tokens"]:
                    if mt.split(":")[1]==t[1]:
                        # this type is already here, ignore it
                        verbose and print("Measure Token contradiction", mt, token)
                        passed = False
                if(passed):
                    # No contradictions, add the token
                    this_measure["measure_tokens"].append(token)
            elif len(t)>1 and (t[1]=="note" or t[1]=="rest"):
                # we have encountered a new note or rest token
                # (technically a rest can't co-exist with a note in the same instrument_beat.. but hmm)
                instrument = t[0]

                current_note = {"token": token, "nfx": []}
                current_effect = None

                # Experimental: If there were orphaned nfx, attach them now
                if len(orphaned_nfx):
                    current_note["nfx"] = orphaned_nfx
                orphaned_nfx = []

                if not instrument in this_measure["trackbeats"]:
                    # first time this instrument appeared in this measure
                    this_measure["trackbeats"][instrument] = {}
                    
                if not clock in this_measure["trackbeats"][instrument]:
                    # first time this instrument appeared in this measure at this clocktime
                    # that means it's a new beat
                    current_beat = {"bfx": [], "notes": []}
                    this_measure["trackbeats"][instrument][clock] = current_beat
                    # Experimental: If there were orphaned bfx, attach them now
                    if len(orphaned_bfx):
                        current_beat["bfx"] = orphaned_bfx
                    orphaned_bfx = []

                # add the note to the beat 
                this_measure["trackbeats"][instrument][clock]["notes"].append(current_note)

                # calculate the latest time difference between beats
                if clock - last_reported_beat_clock == 0:
                    # same beat, no time difference occured, skip for now
                    pass
                else:   
                    # a time difference occured!
                    # the last duration is this beat's clock minus the last beat's clock
                    # warning: this definition of duration is inter-instrument (time since the last beat of any instrument)
                    last_reported_duration = clock - last_reported_beat_clock
                # remember this beat's clocktime for later
                last_reported_beat_clock = clock

            elif(t[0]=="nfx"):
                current_effect = {"token": token, "params": []}
                if(current_note):
                    # great we know what note this effect belongs to
                    current_note["nfx"].append(current_effect)
                else:
                    # uhh this token is out of place. 
                    # we could just skip it
                    # verbose and print("warning: nfx token doesn't belong to a note", token)
                    # OR we could attach to the next note like so:
                    orphaned_nfx.append(current_effect)
            elif(t[0]=="bfx"):
                current_effect = {"token": token, "params": []}
                if(current_beat):
                    # great we know what beat this effect belongs to
                    # Now we are no longer attached to a particular note
                    # actually I guess that is optional. A beat effect could appear between a note and notefx i guess.
                    # current_note = None 
                    current_beat["bfx"].append(current_effect)
                else:                 
                    # uhh this token is out of place. 
                    # verbose and print("warning: bfx token doesn't belong to a beat", token)
                    # we could skip it
                    # OR we could attach to the next beat like so:
                    orphaned_bfx.append(current_effect)
            elif(t[0]=="param"):
                if(current_effect):
                    # great we know what effect this param belongs to
                    current_effect["params"].append(token)
                else:
                    # uhh this token is out of place. skip it
                    verbose and print("warning: param token doesn't belong to an effect", token)
            elif(t[0]=="wait"):
                # wait token can come any time inside a measure
                # it resets the beat/note, and we may move to a new beat/note
                current_beat = None
                current_note = None
                current_effect = None
                time = int(t[1])
                clock += time # move the clock upward

    final_clock = clock
    verbose and print("Final clock:",final_clock)
    verbose and print("=======\nFirst measure")
    verbose and print(all_measures[0])
    
    ###########
    ## NEW GP FILE
    # CREATE a new GP5 file from BLANKGP5 

    ## LOAD the BLANK GP5 SCORE 
    blankgp5 = gp.parse("blank.gp5")
    blankgp5.tracks = []
    blankgp5.tempo = initial_tempo
    
    # Determine the order the tracks will come in 
    track_numbering = []
    for i in instrument_check:
        if instrument_check[i]:
            track_numbering.append(i)
    verbose and print(track_numbering)
    
    #############
    # Creating the GP Instrument Tracks
        
    # Most common instruments in dataset:
    # 30     47073   Distortion Guitar
    # 29     21111   Overdriven Guitar
    # 33     18085   Electric Bass (finger)
    # 34     12438   Electric Bass (pick)
    # 25     11933   Acoustic Guitar (steel)
    # 24     10201   Acoustic Guitar (nylon)
    # 27     8483    Electric Guitar (clean)
    # 48     5606    String Ensemble 1
    # 26     4453    Electric Guitar (jazz)
    # 0      4047    Acoustic Grand Piano
    # 52     2546    Choir Aahs
    # 81     2009    Lead 2 (sawtooth)
    verbose and print("pitch_shift", pitch_shift)
    blankgp5.tracks = []
    for i,instrument in enumerate(track_numbering):
        verbose and print(i, instrument)
        new_track = gp.Track(blankgp5)
        new_track.number = i+1 # track numbers are 1-indexed
        new_track.offset = 0
        # there used to be a bug here when loading 9 instruments (because channels 16 and 17 were used)
        # This should only be values 0-15 
        new_track.channel.channel = i
        # im not sure about this, but seems to work ok
        new_track.channel.effectChannel = max(15,9+i) 
        if(instrument=="drums"):
            new_track.channel.instrument = 0
            new_track.isPercussionTrack = True
            new_track.color = gp.Color(r=100, g=100, b=250, a=1)
            new_track.name = "Drums"
        elif(instrument=="bass"):
            new_track.channel.instrument = 34 # Electric Bass (pick) 
            new_track.color = gp.Color(r=215, g=215, b=100, a=1)
            new_track.name = "Bass"
        elif(instrument=="clean0"):
            new_track.channel.instrument = 27 # Electric Guitar (clean)
            new_track.color = gp.Color(r=255, g=150, b=100, a=1)
            new_track.name = "Clean Guitar"
        elif(instrument=="clean1"):
            new_track.channel.instrument = 26 # Electric Guitar (jazz)
            new_track.color = gp.Color(r=255, g=180, b=100, a=1)
            new_track.name = "Clean Guitar 2"
        elif(instrument=="distorted0"):
            new_track.channel.instrument = 30 # Distortion Guitar
            new_track.color = gp.Color(r=255, g=70, b=70, a=1)
            new_track.name = "Guitar"
        elif(instrument=="distorted1"):
            new_track.channel.instrument = 30 # Distortion Guitar
            new_track.color = gp.Color(r=255, g=100, b=100, a=1)
            new_track.name = "Guitar 2"
        elif(instrument=="distorted2"):
            new_track.channel.instrument = 30 # Distortion Guitar
            new_track.color = gp.Color(r=255, g=130, b=130, a=1)
            new_track.name = "Guitar 3" 
        elif(instrument=="leads"):
            new_track.channel.instrument = 0 # Acoustic Grand Piano 
            new_track.color = gp.Color(r=180, g=120, b=250, a=1)
            new_track.name = "Piano"
            #new_track.settings.autoLetRing = True # this would be aesthetically nice when combining tracks, if I could turn "Stringed" on as well, which might be >GP5
        elif(instrument=="pads"):
            new_track.channel.instrument = 48 # String Ensemble 1
            new_track.color = gp.Color(r=120, g=230, b=120, a=1)
            new_track.name = "Ensemble"
            #new_track.settings.autoLetRing = True # this would be aesthetically nice when combining tracks, if I could turn "Stringed" on as well, which might be >GP5
        else:
            assert False, "Unsupported instrument"
        # Now set the strings
        if(instrument=="drums"):
            strings = ["C0","C0","C0","C0","C0","C0"]
            new_track.strings = convert_strings_for_pygp(strings, 0) # drums are never "downtuned"
        elif(instrument=="bass"):
            drop = instrument_stringinfo[instrument]["drop_tuning"]
            n_strings = instrument_stringinfo[instrument]["strings"]
            if(n_strings==4):
                if drop:
                    strings = ['G3', 'D3', 'A2', 'D2']
                else:
                    strings = ['G3', 'D3', 'A2', 'E2']
            elif(n_strings==5):
                if drop:
                    strings = ['G3', 'D3', 'A2', 'D2', 'A1']
                else:
                    strings = ['G3', 'D3', 'A2', 'E2', 'B1'] 
                    # note: bass 5 string drop tuning isn't really supported, but here it is anyway
            elif(n_strings==6):
                if drop:
                    strings = ['C4', 'G3', 'D3', 'A2', 'D2', 'A1']
                else:
                    strings = ['C4', 'G3', 'D3', 'A2', 'E2', 'B1']
                    # note: bass 6 string drop tuning isn't really supported, but here it is anyway
            new_track.strings = convert_strings_for_pygp(strings, pitch_shift) 
        else:
            # treat other instruments like guitars
            drop = instrument_stringinfo[instrument]["drop_tuning"]
            n_strings = instrument_stringinfo[instrument]["strings"]
            if(n_strings==6):
                if drop:
                    strings = ['E5', 'B4', 'G4', 'D4', 'A3', 'D3']
                else:
                    strings = ['E5', 'B4', 'G4', 'D4', 'A3', 'E3']
            elif(n_strings==7):
                if drop:
                    strings = ['E5', 'B4', 'G4', 'D4', 'A3', 'D3', 'A2']
                else:
                    strings = ['E5', 'B4', 'G4', 'D4', 'A3', 'E3', 'B2']
            new_track.strings = convert_strings_for_pygp(strings, pitch_shift) 

        blankgp5.tracks.append(new_track)
        
    #################
    ## BUILD THE MEASURES
    
    # Blank the measures
    blankgp5.measureHeaders = []
    for t,track in enumerate(blankgp5.tracks):
        track.measures=[]

    # Now build the measures

    #tempo = initial_tempo
    for m,measure in enumerate(all_measures):
        # the time of the begining of the mesaure
        measure_clock = measure["clock"]
        # the time at the end of the measure 
        if(m<len(all_measures)-1):
            # Subtract the measure start time from the next measure start time
            end_measure_clock = all_measures[m+1]["clock"]
        else:
            # Last measure, subtract the measure start time from the total length
            end_measure_clock = final_clock  
        # create a measure header
        header = guitarpro.models.MeasureHeader() # same header for every track's same measure?
        header.start = measure["clock"]
        # use the measure tokens to change the parameters of the header
        for measure_token in measure["measure_tokens"]:
            mt = measure_token.split(":")
            if(mt[0]=="measure"): 
                # all measure tokens begin like this
                # If contradicting measure tokens exist, the later one will overwrite the previous one
                if(mt[1]=="triplet_feel"):
                    header.tripletFeel = gp.TripletFeel(int(mt[2]))
                elif(mt[1]=="repeat_open"):
                    header.isRepeatOpen = True
                elif(mt[1]=="repeat_alternative"):
                    header.repeatAlternative = int(mt[2])
                elif(mt[1]=="repeat_close"):
                    header.repeatClose = int(mt[2])
                elif(mt[1]=="direction"):
                    header.direction = int(mt[2])
                elif(mt[1]=="from_direction"):
                    header.fromDirection = int(mt[2])
        # Get the measure length
        measure_duration = end_measure_clock - measure_clock
        
        if(measure_duration==0):
            # flexibility
            #raise Exception("measure duration zero")
            continue
        # quarterTime = 960*4
        # round down to the nearest 32th measure_duration
        thirtysecondths = math.floor(measure_duration/120)
        # Now find the simplest fraction
        signature = Fraction(thirtysecondths, 32)
        n = signature.numerator
        d = signature.denominator

        # We don't want measures of 1:1.. we want 4:4 instead. Minimum dominator is 4
        if(d==2): 
            n*=2
            d*=2
        elif(d==1):
            n*=4
            d*=4

        # print(n,d, n/d)
        # numerator cannot be greater than 32
        # if it is above 32, try to round down to a simpler fraction
        while(n>32):
            n -= 1
            signature = Fraction(n, d)
            n = signature.numerator
            d = signature.denominator
            # We don't want measures of 1:1.. we want 4:4 instead. Minimum dominator is 4
            if(d==2): 
                n*=2
                d*=2
            elif(d==1):
                n*=4
                d*=4
        #print(n,d, n/d)
        # finally, if all else fails, force it to be 32 max
        n = min(32,n)
        #print(n,d, n/d)

        # timesignatures can go down to 32ths
        d = guitarpro.models.Duration(value=d)
        header.timeSignature = guitarpro.models.TimeSignature(numerator=n,denominator=d)
        print("measure_clock",measure_clock,end_measure_clock, final_clock)
        print("Measure:", m, "TS:",n,"/",d,"measure_duration",measure_duration,"thirtysecondths",thirtysecondths)
        # header.tempo = tempo # don't use mesaureHeader.tempo it's fucked
        blankgp5.addMeasureHeader(header)

        ##########
        # TRACKS
        for t,track in enumerate(blankgp5.tracks):
            # create a measure
            gp_measure = guitarpro.models.Measure(track, header)
            gp_measure.start = measure["clock"]
            # This creates two voices, ignore the second
            gp_voice = gp_measure.voices[0]
            instrument = track_numbering[t]
            if(instrument in measure["trackbeats"]):
                # this instrument is present in this measure
                beats = measure["trackbeats"][instrument]
                clocks = list(beats.keys())
                #print("beats", beats)

                # Check if the first beat is also the measure start
                if len(clocks)>0 and gp_measure.start != clocks[0]:
                    # The first beat is not the measure start
                    # So we need to insert the initial rest
                    initial_rest = {"notes":[{"token": instrument + ":rest"}],"bfx": []}
                    beats[gp_measure.start] = initial_rest
                    clocks.insert(0,gp_measure.start)
                    # okay continue as usual

                ## BEATS
                for b,clock in enumerate(clocks): 
                    beat = beats[clock]
                    if b<len(clocks)-1:
                        #print("next event is the next beat", clock, clocks[b+1])
                        # the next event in this track is the next beat in this measure
                        duration = clocks[b+1] - clock
                    else:                        
                        # the next event in this track is the next measure
                        duration = end_measure_clock - clock
                    # create the guitarpro beat object
                    gp_beat = guitarpro.models.Beat(gp_voice)

                    if(duration==0):
                        # This beat has zero duration for some reason
                        # It shouldn't have zero duration, it accidentally got this way somehow
                        # In this case, just ignore the beat entirely
                        # gp_beat.duration = 0
                        # raise Exception("beat duration zero")
                        continue
                    else:
                        try:
                            # Handy function for converting clock duration to its equivalent notelength/dotted/tuplet
                            # This function might fail if the model generates a weird time combination 
                            gp_beat.duration = gp.models.Duration.fromTime(duration)
                            # print(duration, m, len(all_measures), b, len(clocks))
                        except:
                            # It's anweird duration
                            # Instead round it to the nearest supported time
                            new_time = convert_to_nearest_supported_time(duration)
                            gp_beat.duration = gp.models.Duration.fromTime(new_time)

                            verbose and print("Duration Conversion Measure %s, Track %s: %s => %s" % (m, t, duration, new_time))
                            # todo:
                            # Instead of rounding, maybe it's better to split it into multiple beats to additively reach the duration
                            # Notes get ties
                            # Rests double up
                        
                    bfx_tokens = beat["bfx"]
                    ## Modify Beat.Effect with beat effect tokens
                    tokens_to_beat_effect(gp_beat.effect, bfx_tokens)

                    gp_beat.start = clock
                    ## NOTES 
                    for n,note in enumerate(beat["notes"]):
                        #print(instrument, note)
                        # Could be note or rest
                        note_info = note["token"].split(":")
                        assert note_info[0]==instrument
                        if(note_info[1]=="rest"):
                            # rest
                            # do nothing. at the end of the beat we'll figure out what type of beat it was (normal, rest)
                            continue
                        elif(note_info[1]=="note"):
                            if(instrument=="drums"):
                                # a drum note
                                fret = int(note_info[2])
                                # which string should it be?
                                # I think you only get one drum note per string..
                                # So put each note on its own string..
                                # six max
                                number_of_drum_notes_already = len(gp_beat.notes)
                                if(number_of_drum_notes_already==6): 
                                    # We've hit the limit of simultaneous drum notes
                                    verbose and print("Skipped the drum note. Measure %s Beat %s Note %s" % (m, b, n))
                                    continue
                                else:
                                    # note: strings are 1-indexed
                                    string = number_of_drum_notes_already+1 
                            else:
                                # a non-drum note
                                string = int(note_info[2][1:]) # s4
                                fret = int(note_info[3][1:]) # f0, f20, f-2, etc

                                # get information about the instrument tuning type
                                stringinfo = instrument_stringinfo[instrument]
                                # if this is on a drop string the fret value has to be +2 
                                if(stringinfo["drop_tuning"]):
                                    if(instrument=="bass"):
                                        if(string==5 or string==6):
                                            fret += 2
                                    else:
                                        if(string==6 or string==7):
                                            fret += 2
                                # 4 and 5 string basses start on string2 in token format, bring it back to string1 for GP
                                if(instrument=="bass" and stringinfo["strings"]<6):
                                    string -= 1

                                ## TODO: PLEASE DOUBLE CHECK NO TWO NOTES ON SAME STRING. 
                                ignore = False
                                for notes2 in gp_beat.notes:
                                    if(notes2.string==string):
                                        # note already on string. ignore this note
                                        ignore = True
                                        break
                                if ignore:
                                    continue
                            # create the guitarpro note object
                            gp_note = guitarpro.models.Note(gp_beat)
                            gp_note.string = string
                            gp_note.value = fret
                            gp_note.type = gp.NoteType(1)
                            nfx = note["nfx"]
                            ## Add nfx to gp_note
                            tokens_to_note_effect(gp_note, nfx)
                            # Add the note to the list of notes
                            gp_beat.notes.append(gp_note)
                    # Okay we're done adding notes (if there were any)
                    # If there were notes, change the beat status to "normal"
                    # If there were no notes, change the beat status to "rest"
                    if(len(gp_beat.notes)==0):
                        gp_beat.status = guitarpro.BeatStatus.rest
                    else:
                        gp_beat.status = guitarpro.BeatStatus.normal
                    gp_voice.beats.append(gp_beat)
            else:
                # this instrument isn't present in this measure
                pass
            track.measures.append(gp_measure) # append it to gp_measure
            
    verbose and print("Measures:",(len(blankgp5.measureHeaders)))
    verbose and print("Measures:",(len(blankgp5.tracks[0].measures)))
    #########
    ### DONE
    #print(blankgp5.tracks[8].measures[0].voices[0].beats[0].notes[2])
    return blankgp5


# guitar pro --> tokens
def dadagp_encode(input_file, output_file, artist_token):
    song = gp.parse(input_file)
    # Convert the song to tokens
    tokens = guitarpro2tokens(song, artist_token, verbose=True)
    # Write the tokens to text file
    f = open(output_file, "w")
    f.write("\n".join(tokens))
    f.close()


# tokens --> guitarpro
def dadagp_decode(input_file, output_file):
    text_file = open(input_file, "r")
    tokens = text_file.read().split("\n")

    # Convert the tokens to a song 
    song = tokens2guitarpro(tokens, verbose=True)
    # Appears at the top of the GP score
    song.artist = tokens[0]
    song.album = 'Generated by DadaGP'
    song.title = "untitled"
    guitarpro.write(song, output_file) # GP file transcoded into tokens and back again


def main():
    usage = """#### DadaGP v1.1 Encoder/Decoder ####
#### follow us on twitter @dadabots ####
Usage:

ENCODE (guitar pro --> tokens)
python dadagp.py encode input.gp3 output.txt [artist_name]
python dadagp.py encode examples/progmetal.gp3 progmetal.tokens.txt unknown

DECODE (tokens --> guitar pro)
python dadagp.py decode input.txt output.gp5
python dadagp.py encode progmetal.tokens.txt progmetal.decoded.gp5

Note: only gp3, gp4, gp5 files supported by encoder.
Rare combinations of instruments and tunings may not be supported. 
Instrument changes are not supported. Banjos are not supported. 
"""
    if len(sys.argv)>=4 and sys.argv[1] in ["encode", "decode"]:
        input_file = sys.argv[2]
        output_file = sys.argv[3]
        if(not os.path.exists(input_file)):
            print("input file not found:", input_file)
            return 
        if(not os.path.exists(output_file)):
            print("output file already exists, overwriting...")
        if(sys.argv[1]=="encode"):
            try:
                artist_token = sys.argv[4]
            except:
                artist_token = "unknown" # default
            dadagp_encode(input_file, output_file, artist_token)
        else:
            dadagp_decode(input_file, output_file)
        print("done.")
    else:
        print(usage)
    
if __name__ == "__main__":
    main()
