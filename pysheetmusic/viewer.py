import pyglet
import numpy as np
import raygllib.ui as ui
from . import render
from . import sprite

FPS = 30

class SheetCanvas(ui.Canvas):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._renders = {
            sprite.Line.renderType: render.LineRender(),
            sprite.Texture.renderType: render.TextureRender(),
            sprite.Beam.renderType: render.BeamRender(),
            sprite.Text.renderType: render.TextRender(),
            'indicator': render.IndicatorRender()
        }
        self._scale = 1
        self._viewPoint = (0, 0)
        self.layout = None

    def set_sheet_layout(self, layout):
        self.layout = layout
        self._viewPoint = layout.defaultViewPoint
        sps = {type: [] for type in self._renders}
        for sp in layout.sprites:
            sps[sp.renderType].append(sp)
        for renderType, sps1 in sps.items():
            self._renders[renderType].make_buffer(sps1)

    def __del__(self):
        for render in self._renders.values():
            render.free()

    def on_mouse_scroll(self, x, y, xs, ys):
        if not self.layout:
            return
        scaling = self.layout.sheet.scaling
        k = scaling.mm / scaling.tenths * self._scale
        ds = (1 + 0.1 * ys)
        k1 = k * ds
        vx, vy = self._viewPoint
        w, h = self.width, self.height
        dvx = (1 / k1 - 1 / k) * (w / 2 - x)
        dvy = (1 / k - 1 / k1) * (h / 2 - y)
        self._viewPoint = (vx + dvx, vy + dvy)
        self._scale *= ds
        self._update_matrix()
        return True

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        dvx, dvy, _ = self._matrixScreenToPage.dot([-dx, -dy, 0])
        vx, vy = self._viewPoint
        self._viewPoint = (vx + dvx, vy + dvy)
        self._update_matrix()
        return True

    def _update_matrix(self):
        layout = self.layout
        scaling = layout.sheet.scaling
        w, h = self.width, self.height
        vx, vy = self._viewPoint
        matrix = render.make_matrix(
            scaling,
            (w, h),
            (vx, vy),
            self._scale,
        )
        for r in self._renders.values():
            r.matrix = matrix
        self._matrixSheetToGL = matrix

        k = scaling.mm / scaling.tenths * self._scale
        self._matrixScreenToPage = np.array([
            [1 / k, 0, vx - w / (2 * k)],
            [0, - 1 / k, vy + h / (2 * k)],
            [0, 0, 1],
        ], dtype=np.float32)

    def on_relayout(self):
        layout = self.layout
        scaling = layout.sheet.scaling
        self._viewPoint = layout.defaultViewPoint
        self._scale = scaling.tenths * self.width / (scaling.mm * layout.size[0])

        self._update_matrix()

    def track_measure(self, measure, interval=0.5):
        if not self.layout or not measure:
            return

        def update(dt):
            nonlocal count
            try:
                count -= 1
                if count <= 0:
                    raise StopIteration()
                else:
                    x, y = self._viewPoint
                    x += vx * dt
                    y += vy * dt
                    self._viewPoint = x, y
                    self._update_matrix()
            except StopIteration:
                self._viewPoint = (destX, destY)
                self._update_matrix()
                pyglet.clock.unschedule(update)

        count = int(.5 + interval * FPS)
        layout = self.layout
        width, height = layout.size

        destX, destY = width / 2, measure.y
        vx = (destX - self._viewPoint[0]) / interval
        vy = (destY - self._viewPoint[1]) / interval
        pyglet.clock.schedule_interval(update, 1 / FPS)

    RENDER_ORDER = [
        'indicator',
        sprite.Line.renderType,
        sprite.Texture.renderType,
        sprite.Beam.renderType,
        sprite.Text.renderType,
    ]

    def draw(self):
        for renderType in self.RENDER_ORDER:
            r = self._renders[renderType]
            with r.batch_draw():
                r.render()


class SheetViewer(ui.Widget):

    def __init__(self):
        super().__init__()
        self.canvas = SheetCanvas()
        self.children.append(self.canvas)
        self.player = None
        self.layout = None
        pyglet.clock.schedule_interval(self.update, 1 / FPS)

    def set_player(self, player):
        self.player = player

    def set_sheet_layout(self, layout):
        self.layout = layout
        self.canvas.layout = layout
        self.canvas.set_sheet_layout(layout)

    def update(self, dt):
        if self.layout is None:
            return
        indicatorRender = self.canvas._renders['indicator']
        if self.player.currentMeasure is not indicatorRender.measure:
            measure = self.player.currentMeasure
            indicatorRender.set_measure(measure)
            self.canvas.track_measure(measure)
