# All length value is represented in unit mm.

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
        if marginsBoth:
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

    def add_measure(self, measure):
        if self.measures:
            prev = self.measures[-1]
            link(prev, measure)
            measure.set_defaults(prev)
        elif self.prev and self.prev.measures:
            # TODO: Handle blank page properly
            link(self.prev.measures[-1], measure)
        self.measures.append(measure)
        measure.page = self
        measure.number = len(self.measures)

    def add_sprites(self, sprite):
        self.sprites.append(sprite)

    def pop_measure(self):
        self.measures.pop()


class Measure:
    def __init__(self, xmlnode):
        self._layouted = False
        self.notes = []
        self.width = xmlnode.attrib['width']
        self.prev = None
        self.next = None
        self.page = None
        self.staffSpacing = 10
        self.nLines = 5
        self.timeCurrent = Fraction(0)
        self.timeDivisions = 1
        self.timeStart = Fraction(0)


    @property
    def height(self):
        return (self.nLines - 1) * self.staffSpacing 

    def set_defaults(self, refMeasure):
        self.nLines = refMeasure.nLines
        self.timeStart = refMeasure.timeCurrent + 0
        self.timeCurrent = refMeasure.timeCurrent + 0
        self.timeDivisions = refMeasure.timeDivisions

    def set_clef(self, clefNode):
        if clefNode is None:
            return


class Note:
    pass

class Accidental:
    pass
