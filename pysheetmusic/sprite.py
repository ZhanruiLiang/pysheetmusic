import os
import json
import raygllib.ui as ui

class Sprite:
    pass


class Empty(Sprite):
    def __init__(self):
        self.size = (0, 0)


class Line(Sprite):
    def __init__(self, start, end, width):
        self.start = start
        self.end = end
        self.width = width


class Texture(Sprite):
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


class Beam(Sprite):
    def __init__(self, start, end, height):
        self.start = start
        self.end = end
        self.height = height


class Text(Sprite, ui.TextBox):
    def __init__(self, xmlnode):
        Sprite.__init__(self)
        justify = xmlnode.attrib.get('justify', 'center')
        ui.TextBox.__init__(self, 
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
