from fractions import Fraction
import numpy as np

from . import sprite
from .utils import monad, gcd

# All length value is represented in unit tenths.

def link(node1, node2):
    node1.next = node2
    node2.prev = node1

class Margins:
    top = 0.
    bottom = 0.
    left = 0.
    right = 0.

    def __init__(self, xmlnode):
        for name in ('top', 'bottom', 'left', 'right'):
            subnode = xmlnode.find(name + '-margin')
            if subnode is not None:
                setattr(self, name, float(subnode.text))

class Scaling:
    def __init__(self, xmlnode):
        self.mm = float(xmlnode.find('millimeters').text)
        self.tenths = float(xmlnode.find('tenths').text)

class Clef:
    DEFAULT_LINE = {'G': 2, 'F': 4, 'C': 3, 'TAB': 5}

    def __init__(self, xmlnode):
        if xmlnode is None:
            return
        sign = xmlnode.find('sign').text.upper()
        if xmlnode.find('line') is not None:
            lineNumber = int(xmlnode.find('line').text)
        else:
            lineNumber = self.DEFAULT_CLEF_LINE[sign]
        self.line = lineNumber
        self.sign = sign
        self.octave = 4
        change = xmlnode.find('clef-octave-change')
        if change is not None:
            self.octave += int(change.text)

        self.sprite = sprite.Texture(None, 'clef-' + self.sign)

    def copy(self):
        clef = Clef(None)
        clef.sign = self.sign
        clef.line = self.line
        clef.octave = self.octave
        clef.sprite = sprite.Texture(None, 'clef-' + clef.sign)
        return clef


class Sheet:
    """
    title
    composer
    pages: A list of Page instances.
    scaling
    size
    margins: margins[0] for even page, margins[1] for odd page.
    """

    def __init__(self, xmlnode):
        self.scaling = Scaling(xmlnode.find('defaults/scaling'))
        pageLayout = xmlnode.find('defaults/page-layout')
        self.size = (
            float(pageLayout.find('page-width').text),
            float(pageLayout.find('page-height').text))
        marginsBoth = pageLayout.find('page-margins[@type="both"]')
        if marginsBoth is not None:
            self.margins = [Margins(marginsBoth)] * 2
        else:
            self.margins = [
                Margins(pageLayout.find('page-margins[@type="even"]')),
                Margins(pageLayout.find('page-margins[@type="odd"]'))]
        self.pages = []
        # TODO: credits

    def new_page(self):
        page = Page()
        page.size = self.size
        page.number = len(self.pages) + 1
        page.margins = self.margins[page.number % 2]
        page.sheet = self
        if self.pages:
            link(self.pages[-1], page)
        self.pages.append(page)
        return page

    def finish(self):
        for page in self.pages:
            page.finish()


class Page:
    """
    measures: A list of Measure instances.
    margin
    size
    """
    def __init__(self):
        self.measures = []
        self.sprites = []
        self.sheet = None
        self.prev = None
        self.next = None
        self.size = (0, 0)
        self.number = 0

    def __repr__(self):
        return 'Page(number={number}, size={size})'\
            .format(**self.__dict__)

    def add_measure(self, measure):
        if self.measures:
            prev = self.measures[-1]
        elif self.prev and self.prev.measures:
            # TODO: Handle blank page properly
            prev = self.prev.measures[-1]
        else:
            prev = None
        if prev:
            link(prev, measure)
            measure.follow_defaults(prev)
        self.measures.append(measure)
        measure.page = self

    def add_sprite(self, sprite):
        self.sprites.append(sprite)

    def pop_measure(self):
        self.measures.pop()

    def finish(self):
        d = 2
        width, height = self.size
        self.add_sprite(sprite.Line((0, 0), (width, 0), d))
        self.add_sprite(sprite.Line((width, 0), (width, height), d))
        self.add_sprite(sprite.Line((width, height), (0, height), d))
        self.add_sprite(sprite.Line((0, height), (0, 0), d))


class Measure:
    BAR_WIDTH = 2.5
    LINE_WIDTH = 1.2

    def __init__(self, xmlnode):
        self.notes = []
        self.beams = []
        self.width = float(xmlnode.attrib['width'])  # TODO: Handle no width situation.
        self.number = int(xmlnode.attrib['number'])
        self.isNewSystem = False
        self.prev = None
        self.next = None
        self.page = None
        self.clef = None
        self.staffSpacing = 10
        self.nLines = 5
        self.timeCurrent = Fraction(0)
        self.timeDivisions = 1
        self.timeStart = Fraction(0)
        self.x = self.y = 0

    def __repr__(self):
        return 'Measure(number={number}, x={x}, y={y}, width={width})'\
            .format(**self.__dict__)

    @property
    def height(self):
        return (self.nLines - 1) * self.staffSpacing 

    def follow_defaults(self, refMeasure):
        self.nLines = refMeasure.nLines
        self.timeStart = refMeasure.timeCurrent + 0
        self.timeCurrent = refMeasure.timeCurrent + 0
        self.timeDivisions = refMeasure.timeDivisions
        self.clef = refMeasure.clef.copy()

    def add_beam(self, beam):
        self.beams.append(beam)

    def follow_prev_layout(self):
        if not self.prev:
            return
        self.y = self.prev.y
        self.x = self.prev.x + self.prev.width

    def get_line_y(self, lineNumber):
        " lineNumber: [1, nLines] "
        return self.y + (lineNumber - 1) * self.staffSpacing

    DEFAULT_CLEF_LINE = {'G': 2, 'F': 4, 'C': 3, 'TAB': 5}

    def set_clef(self, clef):
        self.clef = clef

    def finish(self):
        y0 = y = self.y
        x1 = self.x
        x2 = self.x + self.width
        add_sprite = self.page.add_sprite
        for i in range(5):
            add_sprite(sprite.Line(start=(x1, y), end=(x2, y), width=self.LINE_WIDTH))
            y += self.staffSpacing
        y -= self.staffSpacing
        add_sprite(sprite.Line(start=(x1, y0), end=(x1, y), width=self.BAR_WIDTH))
        add_sprite(sprite.Line(start=(x2, y0), end=(x2, y), width=self.BAR_WIDTH))

        self.layout_clef()
        self.layout_notes()
        self.layout_beams()
        for note in self.notes:
            note.finish()

    def layout_clef(self):
        if self.isNewSystem:
            clef = self.clef
            cx, cy = clef.sprite.center
            clef.sprite.pos = (self.x + cx + 5, self.get_line_y(clef.line))
            self.page.add_sprite(clef.sprite)
            self._beginX = clef.sprite.pos[0] + clef.sprite.size[0] - clef.sprite.center[0] + 5
        else:
            self._beginX = self.x + 5

    ADD_LINE_WIDTH = 20
    ADD_LINE_HEIGHT = 2

    def layout_notes(self):
        if not self.notes:
            return
        # First filter out the notes that with known positions.
        points = []
        for note in self.notes:
            if note.pos:
                x, y = note.pos
                x += self.x
                y += self.y + self.height
                note.pos = x, y
                points.append((note.timeStart, x))
        points.sort()
        # Then determine other notes' positive by interpolation.
        ts = [t for t, _ in points]
        xs = [x for _, x in points]
        if not ts or ts[0] != 0:
            ts.insert(0, self.timeStart)
            xs.insert(0, self._beginX)
        if ts[-1] != self.timeCurrent:
            ts.append(self.timeCurrent)
            xs.append(self.x + self.width)

        t1s = []  # The time values that we need to interpolate their x value.
        notesToSet = []
        for note in self.notes:
            if not note.pos:
                t1s.append(note.timeStart)
                notesToSet.append(note)
        x1s = np.interp(t1s, ts, xs)  # The interpolated x values.
        for x, note in zip(x1s, notesToSet):
            note.pos = (x + note.sprite.center[0], None)

        for note in self.notes:
            if isinstance(note, PitchedNote):
                y = self.get_line_y(
                    (self.get_abs_step(note.pitch.step, note.pitch.octave)
                    - self.get_abs_step(self.clef.sign, self.clef.octave)) / 2
                    + self.clef.line)
            elif isinstance(note, Rest): 
                if note.type == 'whole':
                    y = self.get_line_y(4)
                elif note.type == 'half':
                    y = self.get_line_y(3)
                else:
                    y = self.get_line_y(3)
            note.pos = (note.pos[0], y)

        add_sprite = self.page.add_sprite
        w = self.ADD_LINE_WIDTH
        h = self.ADD_LINE_HEIGHT
        dy = self.staffSpacing
        for note in self.notes:
            x, y = note.pos
            y1 = self.y - dy
            while y1 >= y - dy / 4:
                add_sprite(sprite.Line((x - w / 2, y1), (x + w / 2, y1), h))
                y1 -= dy
            y1 = self.y + self.height + dy
            while y1 <= y + dy / 4:
                add_sprite(sprite.Line((x - w / 2, y1), (x + w / 2, y1), h))
                y1 += dy
        for note in self.iter_pitched_notes():
            if note.stem:
                note.stem.set_geometry()

    def iter_pitched_notes(self):
        for note in self.notes:
            if isinstance(note, PitchedNote):
                yield note

    def layout_beams(self):
        add_sprite = self.page.add_sprite
        for beam in sorted(self.beams, key=lambda b: -len(b.stems)):
            anchors = list(filter(bool, map(Stem.next_beam_pos, beam.stems)))
            if len(anchors) >= 2:
                leftMost = min(anchors)
                rightMost = max(anchors)
                beam.set_geometry(leftMost, rightMost)
            # elif len(anchors) == 1:
            #     pass  # TODO
            else:
                upStems = [stem for stem in beam.stems if stem.direction == 'up']
                downStems = [stem for stem in beam.stems if stem.direction == 'down']
                minX = min(stem.head[0] for stem in beam.stems)
                maxX = max(stem.head[0] for stem in beam.stems)
                minY = lambda: max(stem.tail[1] for stem in upStems)
                maxY = lambda: min(stem.tail[1] for stem in downStems)
                if not upStems:
                    y1 = y2 = maxY()
                elif not downStems:
                    y1 = y2 = minY()
                else:
                    y1 = y2 = (minY + maxY) / 2
                beam.set_geometry((minX, y1), (maxX, y2))
            beam.adjust_stems()
            for stem in beam.stems:
                stem.beamDrawn += 1
            add_sprite(beam.sprite)
        DURATION_TO_TYPE = {
            Fraction(1, 8): 'tail-8',
            Fraction(1, 16): 'tail-16',
            Fraction(1, 32): 'tail-32',
            Fraction(1, 64): 'tail-64',
            Fraction(1, 128): 'tail-128',
        }
        for note in self.iter_pitched_notes():
            stem = note.stem
            if stem and note.duration < Fraction(1, 4):
                if stem.beamDrawn < len(stem.beams) \
                        or (stem.beamDrawn == 0 and not stem.beams):
                    stem.beamDrawn += 1
                    type = DURATION_TO_TYPE.get(note.duration, 'tail-128')
                    if stem.direction == 'up':
                        type = type.replace('tail', 'tail-up')
                    pos = note.stem.tail
                    add_sprite(sprite.Texture(pos, type))

    def get_abs_step(self, step, octave):
        return octave * 7 + 'CDEFGAB'.index(step.upper())

    def add_note(self, note, chord=False):
        if not self.notes:
            chord = False
        if chord:
            note.timeStart = self.notes[-1].timeStart
            note.chordRoot = self.notes[-1].chordRoot
            note.stem = note.chordRoot.stem
        else:
            note.chordRoot = note
            note.timeStart = self.timeCurrent
            self.timeCurrent += note.duration
        self.notes.append(note)
        note.measure = self

    def change_time(self, duration):
        "`duration` can be positive or negative."
        self.timeCurrent += duration


class Note:
    def __init__(self, pos, duration, dots):
        self.pos = pos
        self.duration = duration
        self.dots = dots
        self.sprite = self.make_sprite()
        self.measure = None

    def __repr__(self):
        return 'Note(pos={pos}, duration={duration})'.format(**self.__dict__)
    def make_sprite(self):
        pass

    def finish(self):
        pass

    def put_dots(self):
        x, y = self.pos
        w, h = self.sprite.size
        add_sprite = self.measure.page.add_sprite
        for i, dot in enumerate(self.dots):
            if dot is None:
                dot = x + w / 2 + 5 + 3 * i, y - h / 4
            # Each dot is a tuple, representing the position.
            add_sprite(sprite.Texture(dot, 'dot'))


class Stem:
    THICK = 1.5
    MIN_LENGTH = 30

    def __init__(self, xmlnode):
        self.direction = xmlnode.text.lower()
        self.head = None
        self.tail = None
        self.beams = []
        self.notes = []
        self.beamDrawn = 0
        self._geometrySet = False

    def set_geometry(self):
        if self._geometrySet:
            return
        self._geometrySet = True
        nBeams = len(self.beams)
        xMin = min(note.pos[0] for note in self.notes)
        xMax = max(note.pos[0] for note in self.notes)
        yMin = min(note.pos[1] for note in self.notes)
        yMax = max(note.pos[1] for note in self.notes)
        r = max(
            self.MIN_LENGTH + yMax - yMin, 
            Beam.GAP * (nBeams - 1) + Beam.THICK * nBeams,
        )
        w, h = self.notes[0].sprite.size
        if self.direction == 'up':
            # Use the lowest note as head pos
            x = xMin + w / 2 - self.THICK / 2
            y = yMin + h / 6
            self.head = (x, y)
            self.tail = (x, y + r)
        else:
            x = xMax - w / 2 + self.THICK / 2
            y = yMax - h / 6
            self.head = (x, y)
            self.tail = (x, y - r)

    def next_beam_pos(self):
        if self.beamDrawn == 0:
            return None
        x, y = self.tail
        if self.direction == 'up':
            return x, y - self.beamDrawn * (Beam.THICK + Beam.GAP) - Beam.THICK
        else:
            return x, y + self.beamDrawn * (Beam.THICK + Beam.GAP)


class Pitch:
    def __init__(self, xmlnode):
        self.step = xmlnode.find('step').text
        self.octave = int(xmlnode.find('octave').text)
        self.alter = monad(xmlnode.find('alter'), lambda x: float(x.text), 0)


class Accidental:
    TYPES = ('sharp', 'double-sharp', 'flat', 'natural', 'double-flat')

    def __init__(self, xmlnode):
        try:
            pos = float(xmlnode.attrib['default-x']), float(xmlnode.attrib['default-y'])
        except (KeyError, ValueError):
            pos = None
        self.pos = pos
        type = xmlnode.text
        if type in self.TYPES:
            self.sprite = sprite.Texture(pos, type)
        else:
            self.sprite = sprite.Empty()


class PitchedNote(Note):
    TYPE_TO_NAME = {
        'whole': 'head-1', 'half': 'head-2', 'quarter': 'head-4',
    }
    def __init__(self, pos, duration, dots, type, pitch, stem, accidental):
        self._stem = None
        self.pitch = pitch
        self.type = type
        self.stem = stem
        self.accidental = accidental
        super().__init__(pos, duration, dots)

    @property
    def stem(self):
        return self._stem

    @stem.setter
    def stem(self, stem):
        if stem is not self._stem:
            if self._stem:
                self._stem.notes.remove(self)
            self._stem = stem
            stem.notes.append(self)

    def make_sprite(self):
        return sprite.Texture(self.pos, self.TYPE_TO_NAME.get(self.type, 'head-4'))

    def finish(self):
        sp = self.sprite
        sp.pos = self.pos
        x, y = self.pos
        w, h = sp.size
        add_sprite = self.measure.page.add_sprite
        if self.stem:
            add_sprite(sprite.Line(self.stem.head, self.stem.tail, Stem.THICK))
        self.put_dots()
        add_sprite(self.sprite)


class Rest(Note):
    TYPE_TO_NAME = {
        'whole': 'rest-1', 'half': 'rest-2', 'quarter': 'rest-4',
        'eighth': 'rest-8', '16th': 'rest-16', '32th': 'rest-32',
        '64th': 'rest-64', '128th': 'rest-128',
    }
    DURATION_TO_TYPE = {
        Fraction(1): 'whole',
        Fraction(1, 2): 'half',
        Fraction(1, 4): 'quarter',
        Fraction(1, 8): 'eighth',
        Fraction(1, 16): '16th',
        Fraction(1, 32): '32th',
        Fraction(1, 64): '64th',
        Fraction(1, 128): '128th',
    }

    def __init__(self, pos, duration, dots, type):
        """
        pos can be None, so that it can be assigned later.
        type can be None, then it's value will be guessed by duration.
        duration must be Fraction.
        dots is a list of dots position. Each element can also be None.
        """
        self.type = type if type else self.DURATION_TO_TYPE.get(duration, 'whole')
        super().__init__(pos, duration, dots)

    def make_sprite(self):
        name = self.TYPE_TO_NAME.get(self.type, 'rest-128')
        return sprite.Texture(self.pos, name)

    def finish(self):
        sp = self.sprite
        sp.pos = self.pos
        x, y = self.pos
        w, h = sp.size
        add_sprite = self.measure.page.add_sprite
        self.put_dots()
        add_sprite(sp)


class Beam:
    THICK = 6
    GAP = 4

    def __init__(self):
        self.stems = []

    def set_geometry(self, start, end):
        self.start = start
        self.end = end
        x1, y1 = start
        x2, y2 = end
        h = self.THICK
        t = Stem.THICK
        self.sprite = sprite.Beam((x1 - t / 2, y1 - h / 2), (x2 + t / 2, y2 - h / 2), h)

    def adjust_stems(self):
        x1s = [stem.head[0] for stem in self.stems]
        xs = [self.start[0], self.end[0]]
        ys = [self.start[1], self.end[1]]
        y1s = np.interp(x1s, xs, ys)
        for x, y, stem in zip(x1s, y1s, self.stems):
            stem.tail = (x, y)
