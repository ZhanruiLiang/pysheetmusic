import PIL.Image
import raygllib.gllib as gl
import raygllib.ui as ui
import os
import json
import numpy as np
from . import sprite


def get_resouce_path(*subPaths):
    return os.path.join(os.path.dirname(__file__), *subPaths)

DEFAULT_COLOR = np.array((0., 0., 0., 1.), dtype=gl.GLfloat)

def make_matrix(scaling, viewPortSize, viewPoint, scale):
    k = scaling.mm / scaling.tenths * scale
    vx, vy = viewPoint
    w, h = viewPortSize
    s = 2 * k / w
    t = 2 * k / h
    return np.array([
        [s, 0, -vx * s],
        [0, t, -vy * t],
        [0, 0, 1],
    ], dtype=gl.GLfloat)


class Render(gl.Program):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.matrix = np.eye(4, dtype=gl.GLfloat)
        self.color = DEFAULT_COLOR

    def enable_blending(self):
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def set_default_uniforms(self):
        gl.glUniform4fv(self.get_uniform_loc('color'), 1, self.color)
        gl.glUniformMatrix3fv(self.get_uniform_loc('matrix'), 1, gl.GL_TRUE, self.matrix)

    def make_buffer(self, sprites):
        pass

    def render(self):
        pass

    def free_buffers(self):
        pass


class TextureRender(Render):
    def __init__(self):
        super().__init__([
            (get_resouce_path('shaders', 'texture.v.glsl'), gl.GL_VERTEX_SHADER),
            (get_resouce_path('shaders', 'texture.f.glsl'), gl.GL_FRAGMENT_SHADER),
        ], [
            ('xyuv', 4, gl.GL_FLOAT),
        ])
        self.buffer = None
        self.textureUnit = gl.TextureUnit(0)
        self.load_templates(os.path.dirname(__file__), 'templates')
        self.color = np.array((1, 1, 1, 1), dtype=gl.GLfloat)

    def load_templates(self, dir, name):
        image = PIL.Image.open(os.path.join(dir, name + '.png'))
        self.textureSize = image.size
        self.texture = gl.Texture2D(image)
        config = json.load(open(os.path.join(dir, name + '.json')))
        self.rects = config['rects']
        self.centers = config['centers']

    def make_buffer(self, sprites):
        # (x, y, u, v)
        buffer = np.zeros((len(sprites) * 6, 4), dtype=gl.GLfloat)
        centers = self.centers
        rects = self.rects
        i = 0
        k = sprite.Texture.TEXTURE_TO_TENTHS
        for sp in sprites:
            cx, cy = centers[sp.name]
            u1, v1, tw, th = rects[sp.name]
            x, y = sp.pos
            x1 = x - k * cx
            y1 = y - k * (th - cy)
            x2 = x + k * (tw - cx)
            y2 = y + k * cy
            buffer[(i, i + 2, i + 3), 0] = x1
            buffer[(i, i + 1, i + 4), 1] = y1
            buffer[(i + 1, i + 4, i + 5), 0] = x2
            buffer[(i + 2, i + 3, i + 5), 1] = y2
            u2 = u1 + tw
            v2 = v1 + th
            buffer[(i, i + 2, i + 3), 2] = u1
            buffer[(i + 2, i + 3, i + 5), 3] = v1
            buffer[(i + 1, i + 4, i + 5), 2] = u2
            buffer[(i, i + 1, i + 4), 3] = v2
            i += 6
        buffer[:, (2, 3)] /= self.textureSize
        self.free_buffers()
        self.buffer = gl.VertexBuffer(buffer)

    def free_buffers(self):
        if self.buffer:
            self.buffer.free()
        self.buffer = None

    def render(self):
        if self.buffer:
            self.enable_blending()
            self.set_default_uniforms()
            # Set texture
            gl.glActiveTexture(self.textureUnit.glenum)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture.glId)
            gl.glUniform1i(self.get_uniform_loc('textureSampler'), self.textureUnit.id)

            self.set_buffer('xyuv', self.buffer)
            super().draw(gl.GL_TRIANGLES, len(self.buffer))


class LineRender(Render):
    def __init__(self):
        super().__init__([
            (get_resouce_path('shaders', 'line.v.glsl'), gl.GL_VERTEX_SHADER),
            # (get_resouce_path('shaders', 'line-round.g.glsl'), gl.GL_GEOMETRY_SHADER),
            (get_resouce_path('shaders', 'line.g.glsl'), gl.GL_GEOMETRY_SHADER),
            (get_resouce_path('shaders', 'line.f.glsl'), gl.GL_FRAGMENT_SHADER),
        ], [
            ('line', 4, gl.GL_FLOAT),
            ('width', 1, gl.GL_FLOAT),
        ])
        self.lineBuffer = None
        self.widthBuffer = None

    def make_buffer(self, lines):
        buffer = np.zeros((len(lines), 5), dtype=gl.GLfloat)
        for i, line in enumerate(lines):
            buffer[i, (0, 1)] = line.start
            buffer[i, (2, 3)] = line.end
            buffer[i, 4] = line.width
        self.free_buffers()
        self.lineBuffer = gl.VertexBuffer(buffer[:, :4])
        self.widthBuffer = gl.VertexBuffer(buffer[:, 4])

    def free_buffers(self):
        if self.lineBuffer:
            self.lineBuffer.free()
        if self.widthBuffer:
            self.widthBuffer.free()
        self.lineBuffer = self.widthBuffer = None

    def render(self):
        if self.lineBuffer and self.widthBuffer:
            self.enable_blending()
            self.set_default_uniforms()
            self.set_buffer('line', self.lineBuffer)
            self.set_buffer('width', self.widthBuffer)
            super().draw(gl.GL_POINTS, len(self.lineBuffer))


class IndicatorRender(LineRender):
    MEASURE_INDICATOR_COLOR = ui.Color(.96, .92, .37, .5)

    def __init__(self):
        super().__init__()
        self.color = self.MEASURE_INDICATOR_COLOR
        self.lineBuffer = gl.DynamicVertexBuffer()
        self.widthBuffer = gl.DynamicVertexBuffer()
        self.measure = None

    def set_measure(self, measure):
        self.measure = measure
        self.update_buffer()

    def make_buffer(self, *args):
        pass

    def free_buffers(self):
        pass

    def update_buffer(self):
        measure = self.measure
        if not measure:
            return
        buffer = np.zeros((1, 5), dtype=gl.GLfloat)
        # x1, y1, x2, y2, width
        y = measure.y + (measure.bottomY + measure.topY)/ 2
        buffer[0, 0:2] = measure.x, y
        buffer[0, 2:4] = measure.x + measure.width, y
        buffer[0, 4] = measure.topY - measure.bottomY
        self.lineBuffer.set_data(buffer[:, 0:4])
        self.widthBuffer.set_data(buffer[:, 4])

    def render(self):
        if not self.measure:
            return
        super().render()


class BeamRender(Render):
    def __init__(self):
        super().__init__([
            (get_resouce_path('shaders', 'beam.v.glsl'), gl.GL_VERTEX_SHADER),
            (get_resouce_path('shaders', 'beam.g.glsl'), gl.GL_GEOMETRY_SHADER),
            (get_resouce_path('shaders', 'beam.f.glsl'), gl.GL_FRAGMENT_SHADER),
        ], [
            ('line', 4, gl.GL_FLOAT),
            ('height', 1, gl.GL_FLOAT),
        ])
        self.lineBuffer = None
        self.heightBuffer = None

    def make_buffer(self, beams):
        buffer = np.zeros((len(beams), 5), dtype=gl.GLfloat)
        for i, beam in enumerate(beams):
            buffer[i, (0, 1)] = beam.start
            buffer[i, (2, 3)] = beam.end
            buffer[i, 4] = beam.height
        self.free_buffers()
        self.lineBuffer = gl.VertexBuffer(buffer[:, :4])
        self.heightBuffer = gl.VertexBuffer(buffer[:, 4])

    def free_buffers(self):
        if self.lineBuffer:
            self.lineBuffer.free()
        if self.heightBuffer:
            self.heightBuffer.free()
        self.lineBuffer = self.heightBuffer = None

    def render(self):
        if self.lineBuffer and self.heightBuffer:
            self.enable_blending()
            self.set_default_uniforms()
            self.set_buffer('line', self.lineBuffer)
            self.set_buffer('height', self.heightBuffer)
            self.draw(gl.GL_POINTS, len(self.lineBuffer))


class TextRender(ui.render.FontRender):
    def __init__(self):
        super().__init__()
        self._textboxes = []

    def make_buffer(self, textSps):
        self._textboxes = list(textSps)

    @property
    def matrix(self):
        return self._matrix

    @matrix.setter
    def matrix(self, matrix):
        mat4 = np.eye(4, dtype=gl.GLfloat)
        mat4[0:2, 0:2] = matrix[0:2, 0:2]
        mat4[1, :] *= -1
        mat4[3, 3] = matrix[2, 2]
        mat4[0:2, 3] = matrix[0:2, 2]
        self._matrix = mat4

    def render(self):
        self.draw_textboxs(self._textboxes)

    def free_buffers(self):
        pass
