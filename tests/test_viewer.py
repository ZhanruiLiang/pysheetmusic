import unittest
import raygllib.ui as ui
import pysheetmusic as M
from os.path import join, dirname

def get_path(*subPaths):
    return join(dirname(__file__), *subPaths)

SHEETS = [
    'Air.mxl',
    'Allegretto_in_C_Major_for_Guitar_by_Carcassi_-_arr._by_Gerry_Busch.mxl',
    'Allegro_by_Bernardo_Palma_V.mxl',
    'Almain.mxl',
    'Auld_Lang_Syne_guitar.mxl',
    'Chrono_Cross_-_Frozen_Flame.mxl',
    'Chrono_Cross_-_Quitting_the_Body.mxl',
    'Divertimento_No._1.mxl',
    'Fernando_Sor_Op.32_Andante_Pastorale.mxl',
    'Fernando_Sor_Op.32_Andantino.mxl',
    'Fernando_Sor_Op.32_Galop.mxl',
    'Fernando_Sor_Op.32_Mazurka.mxl',
    'Giuliani_-_Op.50_No.1.mxl',
    'Guitar_Solo_No._116_in_A_Major.mxl',
    'Guitar_Solo_No._117_in_E_Minor.mxl',
    'Guitar_Solo_No._118_-_Barcarolle_in_A_Minor.mxl',
    'Guitar_Solo_No._119_in_G_Major.mxl',
    'Guitar_Solo_No._15_in_E_Major.mxl',
    'Jeux_interdits.mxl',
    'Lagrima.mxl',
    'Lute_Suite_No._1_in_E_Major_BWV_1006a_J.S._Bach.mxl',
    'Maria_Luisa_Mazurka_guitar_solo_the_original_composition.mxl',
    'Minuet_in_G_minor.mxl',
    'Pavane_No._6_for_Guitar_Luis_Milan.mxl',
    'People_Imprisoned_by_Destiny.mxl',
    'Somewhere_In_My_Memory.mxl',
    'Tango_Guitar_Solo_2.mxl',
    'Unter_dem_Lindenbaum.mxl',
    'Untitled_in_D_Major.mxl',
    'We_wish_you_a_Merry_Christmas.mxl',
    'K27_Domenico_Scarlatti.mxl',
]

class TestViewer(unittest.TestCase):
    def test_viewer(self):
        parser = M.parse.MusicXMLParser()
        i = 0
        for name in SHEETS[:]:
            print('sheet #{}'.format(i))
            i += 1
            viewer = M.viewer.SheetViewer()
            window = ui.Window(width=1000, height=800)
            window.root.children.append(viewer)
            sheet = parser.parse(get_path('sheets', name))
            viewer.canvas.set_page(sheet.pages[0])
            window.start()

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

if __name__ == '__main__':
    import crash_on_ipy
    TestParser().test_parser()
    # TestViewer().test_renders()
    # TestViewer().test_viewer()
