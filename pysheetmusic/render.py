import PIL.Image
import raygllib.gllib as gl
import os
import json
import numpy as np


def get_resouce_path(*subPaths):
    return os.path.join(os.path.dirname(__file__), *subPaths)

DEFAULT_COLOR = np.array((0., 0., 0., 1.), dtype=gl.GLfloat)

def make_matrix(page, viewPortSize, viewPoint, scale):
    k = page.scaling.mm / page.scaling.tenths * scale
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
        gl.glUniform4fv(self.get_uniform_loc('color'), self.color)
        gl.glUniformMatrix3fv(self.get_uniform_loc('matrix'), 1, gl.GL_TRUE, self.matrix)


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

    def load_templates(dir, name):
        image = PIL.Image.open(os.path.join(dir, name + '.png'))
        self.texture = gl.Texture2D(image)
        config = json.load(open(os.path.join(dir, name + '.json')))
        self.rects = config['rects']
        self.centers = config['centers']

    def make_buffer(self, sprites):
        # (x, y, u, v)
        buffer = np.zeros((len(sprites), 4), dtype=gl.GLfloat)
        centers = self.centers
        rects = self.rects
        i = 0
        for sp in sprites:
            cx, cy = centers[sp.name]
            u1, v1, tw, th = rects[sp.name]
            x, y = sp.pos
            x1 = x - cx
            y1 = y - (th - cy)
            x2 = x + tw - cx
            y2 = y + cy
            buffer[(i, i + 2, i + 3), 0] = x1
            buffer[(i, i + 1, i + 4), 1] = y1
            buffer[(i + 1, i + 4, i + 5), 0] = x2
            buffer[(i + 2, i + 3, i + 5), 1] = y2
            u2 = u1 + tw
            v1 = v1 + th
            buffer[(i, i + 2, i + 3), 2] = u1
            buffer[(i + 2, i + 3, i + 5), 3] = v1
            buffer[(i + 1, i + 4, i + 5), 2] = u2
            buffer[(i, i + 1, i + 4), 3] = v2
            i += 6
        self.buffer = gl.VertexBuffer(buffer)

    def render(self):
        self.enable_blending()
        self.set_default_uniforms()
        # Set texture
        gl.glActiveTexture(self.textureUnit.glenum)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture.glId)
        gl.glUniform1i(self.get_uniform_loc('textureSampler'), self.textureUnit.id)

        self.set_buffer('xyuv', self.buffer)
        super.draw(gl.GL_TRIANGLES, len(self.buffer))


class LineRender(Render):
    def __init__(self):
        super().__init__([
            (get_resouce_path('shaders', 'line.v.glsl'), gl.GL_VERTEX_SHADER),
            (get_resouce_path('shaders', 'line.g.glsl'), gl.GL_GEOMETRY_SHADER),
            (get_resouce_path('shaders', 'line.f.glsl'), gl.GL_FRAGMENT_SHADER),
        ], [
            ('line', 4, gl.GL_FLOAT),
            ('width', 1, gl.GL_FLOAT),
        ])
        self.lineBuffer = None
        self.widthBuffer = None

    def make_buffer(self, lines):
        pass

    def render(self):
        self.enable_blending()
        self.set_default_uniforms()
        self.set_buffer('line', self.lineBuffer)
        self.set_buffer('width', self.widthBuffer)
        super.draw(gl.GL_POINTS, len(self.lineBuffer))


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
        pass

    def render(self):
        self.enable_blending()
        self.set_default_uniforms()
        self.set_buffer('line', self.lineBuffer)
        self.set_buffer('height', self.heightBuffer)
        self.draw(gl.GL_POINTS, len(self.lineBuffer))
