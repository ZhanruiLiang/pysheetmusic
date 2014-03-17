from .sprite import Line, Texture, TabFingering

class TabMeasure:
    TOP_MARGIN = 20
    BOTTOM_MARGIN = 50
    BAR_WIDTH = 2.5
    LINE_THICK = 1.2
    STAFF_SPACING = 12

    def __init__(self, measure):
        self.isNewSystem = False
        self.width = measure.width
        self.isNewSystem = measure.isNewSystem
        self.x = 0
        self.y = 0
        self.nLines = 6
        self.measure = measure
        self.sprites = []

    @property
    def height(self):
        return self.STAFF_SPACING * (self.nLines - 1)

    def layout_objects(self):
        if self.isNewSystem:
            clefTab = Texture(None, 'clef-TAB')
            clefTab.pos = clefTab.center[0], self.get_line_y((1 + self.nLines) / 2)
            self.add_sprite(clefTab)
        self.layout_barlines()
        self.layout_lines()
        self.layout_fingerings()

    def layout_fingerings(self):
        for note in self.measure.iter_pitched_notes():
            f = note.fingering
            if f.string > 0:
                x = note.pos[0]
                y = self.get_line_y(self.nLines + 1 - f.string)
                numText = str(f.fret)
                if len(numText) == 1:
                    self.add_sprite(Texture((x, y), 'tabnum-' + numText))
                else:
                    spLeft = Texture(None, 'tabnum-' + numText[0])
                    spLeft.pos = (x - (spLeft.size[0] - spLeft.center[0]), y)
                    self.add_sprite(spLeft)
                    spRight = Texture(None, 'tabnum-' + numText[1])
                    spRight.pos = (x + spRight.center[0], y)
                    self.add_sprite(spRight)
                # if f.finger > 0:
                #     spFinger = Texture((x + 8, y - 8), 'tabnum-' + str(f.finger))
                #     self.add_sprite(spFinger)

    def layout_barlines(self):
        x = self.width
        self.add_sprite(Line(
            (x, - self.LINE_THICK / 2), (x, self.height + self.LINE_THICK / 2), 
            self.BAR_WIDTH,
        ))

    def add_sprite(self, sprite):
        self.sprites.append(sprite)

    def get_line_y(self, lineNumber):
        " lineNumber: [1, nLines] "
        return (lineNumber - 1) * self.STAFF_SPACING

    def layout_lines(self):
        x1 = 0
        x2 = self.width
        add_sprite = self.add_sprite
        y = 0
        for i in range(self.nLines):
            add_sprite(Line(start=(x1, y), end=(x2, y), width=self.LINE_THICK))
            y += self.STAFF_SPACING


def attach_tab(sheet):
    for measure in sheet.iter_measures():
        tab = TabMeasure(measure)
        measure.tab = tab


class Fingering:
    def __init__(self, finger, string, fret):
        """
        finger: 1, 2, 3, 4. 0 means no finger
        string: 1, 2, ...
        fret: 0, 1, 2, ...
        """
        self.finger = finger
        self.string = string
        self.fret = fret


def attach_fingerings(sheet):
    for measure in sheet.iter_measures():
        for note in measure.iter_pitched_notes():
            note.fingering = Fingering(0, 0, 0)
