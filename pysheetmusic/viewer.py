import numpy as np
import raygllib.ui as ui
from . import render
from . import sprite


class SheetCanvas(ui.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._renders = {
            sprite.Line: render.LineRender(),
            sprite.Texture: render.TextureRender(),
            sprite.Beam: render.BeamRender(),
            sprite.Text: render.TextRender(),
        }
        self._scale = 3

    def set_page(self, page):
        sps = {type: [] for type in self._renders}
        for sp in page.sprites:
            sps[sp.__class__].append(sp)
        for spriteClass, sps1 in sps.items():
            self._renders[spriteClass].make_buffer(sps1)
        self._page = page

    def __del__(self):
        for render in self._renders.values():
            render.free()

    def on_mouse_scroll(self, x, y, xs, ys):
        scaling = self._page.sheet.scaling
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

    # def on_key_press(self, symbol, modifiers):
    #     print(symbol)

    def _update_matrix(self):
        page = self._page
        scaling = page.sheet.scaling
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

        k = scaling.mm / scaling.tenths * self._scale
        self._matrixScreenToPage = np.array([
            [1 / k, 0, vx - w / (2 * k)],
            [0, - 1 / k, vy + h / (2 * k)],
            [0, 0, 1],
        ], dtype=np.float32)

    def on_relayout(self):
        page = self._page
        self._viewPoint = (page.size[0] / 2, page.size[1] / 2)
        self._update_matrix()

    def draw(self):
        for r in self._renders.values():
            with r.batch_draw():
                r.render()


class SheetViewer(ui.Widget):
    def __init__(self):
        super().__init__()
        self.canvas = SheetCanvas()
        self.children.append(self.canvas)
