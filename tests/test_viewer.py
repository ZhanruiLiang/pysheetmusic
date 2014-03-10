import unittest
import pyglet
import raygllib.ui as ui
import raygllib.ui.key as K
import pysheetmusic as M
from pysheetmusic.utils import FPSCounter
from pysheetmusic.player import Player
from pysheetmusic.layout import PagesLayout, LinearLayout, LinearTabLayout
from pysheetmusic.tab import attach_tab, attach_fingerings
from os.path import join, dirname

def get_path(*subPaths):
    return join(dirname(__file__), *subPaths)

SHEETS = [
    'Untitled_in_D_Major.mxl',
    'We_wish_you_a_Merry_Christmas.mxl',
    'K27_Domenico_Scarlatti.mxl',
    'Divertimento_No._1.mxl',
    'Allegro_by_Bernardo_Palma_V.mxl',
    'Giuliani_-_Op.50_No.1.mxl',
    'Chrono_Cross_-_Quitting_the_Body.mxl',
    'Unter_dem_Lindenbaum.mxl',
    'Lagrima.mxl',
    'Auld_Lang_Syne_guitar.mxl',
    'Guitar_Solo_No._116_in_A_Major.mxl',
    'Almain.mxl',
    'Somewhere_In_My_Memory.mxl',
    'Tango_Guitar_Solo_2.mxl',
    'Air.mxl',
    'Jeux_interdits.mxl',
    'Allegretto_in_C_Major_for_Guitar_by_Carcassi_-_arr._by_Gerry_Busch.mxl',
    'Fernando_Sor_Op.32_Mazurka.mxl',
    'Fernando_Sor_Op.32_Galop.mxl',
    'Guitar_Solo_No._117_in_E_Minor.mxl',
    'Chrono_Cross_-_Frozen_Flame.mxl',
    'Fernando_Sor_Op.32_Andante_Pastorale.mxl',
    'Fernando_Sor_Op.32_Andantino.mxl',
    'Guitar_Solo_No._118_-_Barcarolle_in_A_Minor.mxl',
    'Guitar_Solo_No._119_in_G_Major.mxl',
    'Guitar_Solo_No._15_in_E_Major.mxl',
    'Lute_Suite_No._1_in_E_Major_BWV_1006a_J.S._Bach.mxl',
    'Maria_Luisa_Mazurka_guitar_solo_the_original_composition.mxl',
    'Minuet_in_G_minor.mxl',
    'Pavane_No._6_for_Guitar_Luis_Milan.mxl',
    'People_Imprisoned_by_Destiny.mxl',
]

class Window(ui.Window):
    fpsCounter = FPSCounter()
    def update(self, dt):
        super().update(dt)
        self.fpsCounter.tick()
        print(self.fpsCounter.fps)

class TestViewer(unittest.TestCase):
    def test_viewer(self):
        parser = M.parse.MusicXMLParser()
        i = 0
        def quit():
            nonlocal _quit
            _quit = True
            window.close()
        def change_page(delta):
            if delta > 0:
                viewer.layout.next_page()
            elif delta < 0:
                viewer.layout.prev_page()
            viewer.canvas.update_sheet_layout()
        _quit = False
        player = Player()
        for name in SHEETS[:]:
            print('sheet #{}'.format(i))
            i += 1
            viewer = M.viewer.SheetViewer()
            window = ui.Window(width=1000, height=800, resizable=1)
            window.root.children.append(viewer)
            window.add_shortcut(K.chain(K.Q), quit)
            # window.add_shortcut(K.chain(K.RIGHT), change_page, 1)
            # window.add_shortcut(K.chain(K.LEFT), change_page, -1)
            window.add_shortcut(K.chain(K.SHIFT, K.P), lambda: player.pause() or True)
            window.add_shortcut(K.chain(K.P), lambda: player.play() or True)

            sheet = parser.parse(get_path('sheets', name))
            attach_tab(sheet)
            attach_fingerings(sheet)
            import random
            for measure in sheet.iter_measures():
                for note in measure.iter_pitched_notes():
                    note.fingering.finger = random.randint(0, 4)
                    note.fingering.string = random.randint(1, 6)
                    note.fingering.fret = random.randint(0, 15)
            # layout = PagesLayout(sheet)
            # layout = LinearLayout(sheet)
            layout = LinearTabLayout(sheet)
            layout.layout()
            viewer.set_sheet_layout(layout)
            # change_page(0)
            player.set_sheet(sheet)
            viewer.set_player(player)
            player.play()

            pyglet.clock.schedule_interval(viewer.update, 1 / 30)

            window.start()
            player.stop()
            sheet.free()
            if _quit:
                break

    def test_renders(self):
        window = ui.Window()
        for cls in (M.render.LineRender, M.render.BeamRender, M.render.TextureRender):
            render = cls()
            render.glId
            render.free()

class TestParser(unittest.TestCase):
    def test_parser(self):
        parser = M.parse.MusicXMLParser()
        for name in SHEETS:
            sheet = parser.parse(get_path('sheets', name))
            attach_tab(sheet)
            layout = LinearTabLayout(sheet)
            layout.layout()

    def test_key_signagure(self):
        for mode in ('major', 'minor'):
            assert M.sheet.KeySignature(0, mode).names == ''
            assert M.sheet.KeySignature(1, mode).names == 'F'
            assert M.sheet.KeySignature(2, mode).names == 'FC'
            assert M.sheet.KeySignature(3, mode).names == 'FCG'
            assert M.sheet.KeySignature(4, mode).names == 'FCGD'
            assert M.sheet.KeySignature(5, mode).names == 'FCGDA'
            assert M.sheet.KeySignature(6, mode).names == 'FCGDAE'
            assert M.sheet.KeySignature(7, mode).names == 'FCGDAEB'
            assert M.sheet.KeySignature(-1, mode).names == 'B'
            assert M.sheet.KeySignature(-2, mode).names == 'BE'
            assert M.sheet.KeySignature(-3, mode).names == 'BEA'
            assert M.sheet.KeySignature(-4, mode).names == 'BEAD'
            assert M.sheet.KeySignature(-5, mode).names == 'BEADG'
            assert M.sheet.KeySignature(-6, mode).names == 'BEADGC'
            assert M.sheet.KeySignature(-7, mode).names == 'BEADGCF'


if __name__ == '__main__':
    import crash_on_ipy
    # TestParser().test_key_signagure()
    # TestViewer().test_renders()
    # TestParser().test_parser()
    TestViewer().test_viewer()
