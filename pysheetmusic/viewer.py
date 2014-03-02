import raygllib.ui as ui

class SheetCanvas(ui.Canvas):
    pass

class SheetViewer(ui.Widget):
    def __init__(self):
        super().__init__()
        self.canvas = SheetCanvas()
        self.children.append(self.canvas)
