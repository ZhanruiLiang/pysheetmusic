import pygame.midi as midi
from threading import Thread, Lock
from fractions import Fraction
from collections import namedtuple
from time import sleep

from raygllib import ui

midi.init()

class PlayerState:
    PLAYING = 'playing'
    PAUSED = 'paused'
    STOPPED = 'stopped'

class EventType:
    NOTE_OFF = 0
    NOTE_ON = 1
    TEMPO = 2

NoteEvent = namedtuple('NoteEvent', 'time type note')

class Player:
    INST_NYLON_GUITAR = 24
    INST_STEEL_GUITAR = 25

    def __init__(self):
        self.sheet = None
        self.speedScale = 1
        self.state = PlayerState.STOPPED
        self.stateLock = Lock()
        self.thread = None
        self.output = None
        self.outputLock = Lock()
        self.currentMeasure = None
        self.currentNotes = set()

    def __del__(self):
        if self.output:
            with self.outputLock:
                self.output.close()

    @staticmethod
    def get_midi_output_id():
        for id in range(midi.get_count()):
            interface, name, input, output, open = midi.get_device_info(id)
            if not output:
                continue
            name = name.decode('utf-8').lower()
            if name.find('synth') != -1:
                return id
        return midi.get_default_output_id()

    def play(self):
        if self.state is PlayerState.PLAYING:
            return
        if not self.output:
            self.output = midi.Output(self.get_midi_output_id())
            self.output.set_instrument(self.INST_NYLON_GUITAR, 1)

            noteEvents = []
            sheet = self.sheet
            for timeStart, timeEnd, note in sheet.iter_note_sequence():
                # note on
                noteEvents.append(NoteEvent(timeStart, EventType.NOTE_ON, note))
                # note off
                noteEvents.append(NoteEvent(timeEnd, EventType.NOTE_OFF, note))
            noteEvents.sort(key=lambda x: x[:2])

            self.thread = thread = Thread(target=self._run, args=(noteEvents,))
            thread.daemon = True
            self.state = PlayerState.PLAYING
            thread.start()
        else:
            self.state = PlayerState.PLAYING

    def _run(self, noteEvents):
        p = 0
        time = Fraction(0)
        measureRestTime = Fraction(0)
        output = self.output
        notes = self.currentNotes
        notes.clear()
        self.currentMeasure = None
        while p < len(noteEvents):
            with self.stateLock:
                if self.state is PlayerState.PAUSED:
                    if notes:
                        with self.outputLock:
                            for note in notes:
                                output.note_off(*args)
                        notes.clear()
                    sleep(0.02)
                    continue
                elif self.state is PlayerState.STOPPED:
                    notes.clear()
                    self.currentMeasure = None
                    return

            event = noteEvents[p]
            deltaTime = event.time - time
            if deltaTime > 0:
                sleep(float(1 / self.speedScale * deltaTime))
                time = event.time
                measureRestTime -= deltaTime

            pitch = event.note.pitch
            level = event.note.pitchLevel
            args = level, 127, 1

            with self.outputLock:
                if not self.output:
                    break
                # print('level', level, 'time', event.time, 'type', event.type)
                if event.type == EventType.NOTE_ON:
                    if event.note.measure is not self.currentMeasure:
                        self.currentMeasure = event.note.measure
                    output.note_on(*args)
                    notes.add(args)
                elif event.type == EventType.NOTE_OFF:
                    if args in notes:
                        output.note_off(*args)
                        notes.discard(args)
            p += 1
        self.currentMeasure = None
        with self.stateLock:
            self.state = PlayerState.STOPPED
        with self.outputLock:
            self.output.close()
            self.output = None

    def pause(self):
        with self.stateLock:
            self.state = PlayerState.PAUSED

    def stop(self):
        if self.state is PlayerState.STOPPED:
            return
        with self.stateLock:
            self.state = PlayerState.STOPPED
        if self.thread and self.thread.is_alive():
            self.thread.join()
        with self.outputLock:
            self.output.close()
            self.output = None
        self.currentMeasure = None

    def set_sheet(self, sheet):
        if self.state is not PlayerState.STOPPED:
            self.stop()
        self.sheet = sheet
