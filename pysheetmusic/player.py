import pygame.midi as midi
from threading import Thread, Lock
from fractions import Fraction
from collections import namedtuple
from time import sleep

midi.init()

class PlayerState:
    PLAYING = 'playing'
    PAUSED = 'paused'
    STOPPED = 'stopped'

SoundEvent = namedtuple('SoundEvent', 'time type note')

class Player:
    INST_NYLON_GUITAR = 24
    INST_STEEL_GUITAR = 25

    def __init__(self):
        self.sheet = None
        self.state = PlayerState.STOPPED
        self.output = None
        self.stateLock = Lock()

    def __del__(self):
        if self.output:
            with self.outputLock:
                self.output.close()

    @staticmethod
    def get_midi_output_id():
        for id in range(midi.get_count()):
            interface, name, input, output, open = midi.get_device_info(id)
            if output and name.decode('utf-8').lower().find('synth') != -1:
                return id
        return midi.get_default_output_id()

    def play(self):
        if self.state is PlayerState.PLAYING:
            return
        self.outputLock = Lock()
        if not self.output:
            self.output = midi.Output(self.get_midi_output_id())
            self.output.set_instrument(self.INST_NYLON_GUITAR, 1)
            events = []
            sheet = self.sheet
            k = sheet.tempo.scaler
            time = Fraction(0)
            for measure in sheet.measureSeq:
                for note in measure.iter_pitched_notes():
                    # note on
                    events.append(SoundEvent(
                        k * (time + note.timeStart),
                        0, note
                    ))
                    # note off
                    events.append(SoundEvent(
                        k * (time + note.timeStart + note.duration),
                        1, note
                    ))
                time += measure.timeLength
            events.sort(key=lambda x: x[:2])

            thread = Thread(target=self._run, args=(events,))
            thread.daemon = True
            self.state = PlayerState.PLAYING
            thread.start()
        else:
            self.state = PlayerState.PLAYING

    def _run(self, events):
        p = 0
        time = Fraction(0)
        output = self.output
        notes = set()
        while p < len(events):
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
                    return

            event = events[p]
            deltaTime = event.time - time
            if deltaTime > 0:
                sleep(float(deltaTime))
                time = event.time
            pitch = event.note.pitch
            level = event.note.pitchLevel
            args = level, 127, 1

            with self.outputLock:
                if not self.output:
                    break
                # print('level', level, 'time', event.time, 'type', event.type)
                if event.type == 0:
                    # note on
                    output.note_on(*args)
                    notes.add(args)
                else:
                    if args in notes:
                        output.note_off(*args)
                        notes.discard(args)
            p += 1
        self.stop()

    def pause(self):
        with self.stateLock:
            self.state = PlayerState.PAUSED

    def stop(self):
        if self.state is PlayerState.STOPPED:
            return
        with self.stateLock:
            self.state = PlayerState.STOPPED
        with self.outputLock:
            self.output.close()
            self.output = None

    def set_sheet(self, sheet):
        if self.state is not PlayerState.STOPPED:
            self.stop()
        self.sheet = sheet
