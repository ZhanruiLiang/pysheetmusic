import os
import json
import raygllib.ui as ui

class Sprite:
    def put(self, pos):
        pass

    def unput(self, pos):
        pass


class Empty(Sprite):
    def __init__(self):
        self.size = (0, 0)

def vec_add(a, b):
    return a[0] + b[0], a[1] + b[1]

def vec_minus(a, b):
    return a[0] - b[0], a[1] - b[1]


class Line(Sprite):
    renderType = 'line'

    def __init__(self, start, end, width):
        self.start = start
        self.end = end
        self.width = width

    def put(self, pos):
        self.start = vec_add(self.start, pos)
        self.end = vec_add(self.end, pos)

    def unput(self, pos):
        self.start = vec_minus(self.start, pos)
        self.end = vec_minus(self.end, pos)


class Texture(Sprite):
    renderType = 'texture'

    _config = None
    TEMPLATE_DPI = 500
    MARGIN = 10
    TEXTURE_TO_TENTHS = 950 / (7 * TEMPLATE_DPI)

    def __init__(self, pos, name):
        self.pos = pos
        self.name = name
        cx, cy, w, h = self.get_config(name)
        self.center = (cx, cy)
        self.size = (w, h)

    @staticmethod
    def get_config(name):
        if Texture._config is None:
            config = json.load(open(
                os.path.join(os.path.dirname(__file__), 'templates.json')))
            Texture._config = config
        _, _, w, h = Texture._config['rects'][name]
        cx, cy = Texture._config['centers'][name]
        m = Texture.MARGIN
        k = Texture.TEXTURE_TO_TENTHS
        w = (w - 2 * m) * k
        h = (h - 2 * m) * k
        cx = (cx - m) * k
        cy = (cy - m) * k
        return cx, cy, w, h

    def put(self, pos):
        self.pos = vec_add(self.pos, pos)

    def upput(self, pos):
        self.pos = vec_minus(self.pos, pos)


class Beam(Sprite):
    renderType = 'beam'

    def __init__(self, start, end, height):
        self.start = start
        self.end = end
        self.height = height

    def put(self, pos):
        self.start = vec_add(self.start, pos)
        self.end = vec_add(self.end, pos)

    def unput(self, pos):
        self.start = vec_minus(self.start, pos)
        self.end = vec_minus(self.end, pos)


class Text(Sprite, ui.TextBox):
    renderType = 'text'

    def __init__(self, **kwargs):
        ui.TextBox.__init__(self, **kwargs)
        Sprite.__init__(self)

    def put(self, pos):
        x0, y0 = pos
        self.x += x0
        self.y -= y0

    def unput(self, pos):
        x0, y0 = pos
        self.x -= x0
        self.y += y0


class CreditWords(Text):
    def __init__(self, xmlnode):
        justify = xmlnode.attrib.get('justify', 'center')
        super().__init__(
            fontSize=int(xmlnode.attrib.get('font-size', '10')),
            text=xmlnode.text,
            align='center',
            halign=xmlnode.attrib.get('valign', 'center'),
            color=ui.Color(0., 0., 0., 1.),
            x=float(xmlnode.attrib['default-x']),
            y=-float(xmlnode.attrib['default-y']),
            # autoResize=True,
        )
        size = self.guess_size()
        self.width, self.height = size
        if justify == 'center':
            self.x -= self.width / 2
        elif justify == 'right':
            self.x -= self.width

    def guess_size(self):
        k = self.fontSize
        return k * len(self.text), k
