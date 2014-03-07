from .tab import TabMeasure

class Layout:
    def __init__(self, sheet):
        self.sheet = sheet
        self.sprites = []
        self.size = (0, 0)
        self.defaultViewPort = (0, 0)

    def layout(self):
        pass
    

class PagesLayout(Layout):
    def layout(self):
        sheet = self.sheet
        for page in sheet.pages:
            page.add_border()
        for measure in sheet.iter_measures():
            page = measure.page
            measure.layout_objects()
            if measure.isNewPage:
                measure.y = (page.size[1] - page.margins.top 
                    - measure.topSystemDistance - measure.height)
            if measure.isNewSystem:
                measure.x = measure.systemMargins.left + page.margins.left
                if not measure.isNewPage:
                    measure.y = measure.prev.y \
                        - float(measure.systemDistance) - measure.height
            else:
                measure.y = measure.prev.y
                measure.x = measure.prev.x + measure.prev.width + measure.measureDistance
            for sprite in measure.sprites:
                sprite.put((measure.x, measure.y))
                measure.page.add_sprite(sprite)

        self.switch_page(0)

    def switch_page(self, pageId):
        self.pageId = pageId
        page = self.sheet.pages[pageId]
        self.sprites = page.sprites
        self.size = page.size
        self.defaultViewPort = (page.size[0] / 2, page.size[1] / 2)

    def next_page(self):
        self.switch_page((self.pageId + 1) % len(self.sheet.pages))

    def prev_page(self):
        self.switch_page((self.pageId - 1) % len(self.sheet.pages))


class LinearLayout(Layout):
    def layout(self):
        sheet = self.sheet
        y = 0
        width = 0
        margins = sheet.pages[0].margins
        for measure in sheet.iter_measures():
            measure.layout_objects()
            if measure.isNewSystem:
                measure.x = measure.systemMargins.left + margins.left
                if measure.isNewPage:
                    y -= margins.top + measure.topSystemDistance + measure.height
                else:
                    y -= measure.systemDistance + measure.height
                measure.y = y
            else:
                measure.x = measure.prev.x + measure.prev.width + measure.measureDistance
                measure.y = measure.prev.y
            width = max(width, measure.x + measure.width + margins.right)
        height = - y + 100

        page = sheet.pages[0]
        self.defaultViewPort = (page.size[0] / 2, -page.size[1] / 2)
        self.sprites = []
        for measure in sheet.iter_measures():
            for sprite in measure.sprites:
                sprite.put((measure.x, measure.y))
                self.sprites.append(sprite)
        self.size = (width, height)


class LinearTabLayout(Layout):
    def layout(self):
        sheet = self.sheet
        y = 0
        width = 0
        margins = sheet.pages[0].margins
        lastFirstMeasure = None
        rows = []
        row = []
        for measure in sheet.iter_measures():
            if measure.isNewSystem:
                row = [measure]
                rows.append(row)
            else:
                row.append(measure)
            measure.layout_objects()

        nTabLines = 6
        y = - margins.top
        self.sprites = []

        for row in rows:
            maxTopDist = max(m.topY for m in row)
            maxBottomDist = max(-m.bottomY for m in row)
            y -= maxTopDist
            tabY = y - maxBottomDist - TabMeasure.TOP_MARGIN \
                - (nTabLines - 1) * TabMeasure.STAFF_SPACING
            for measure in row:
                measure.y = y
                if measure.isNewSystem:
                    measure.x = measure.systemMargins.left + margins.left
                else:
                    measure.x = \
                        measure.prev.x + measure.prev.width + measure.measureDistance
                for sprite in measure.sprites:
                    sprite.put((measure.x, measure.y))
                    self.sprites.append(sprite)
                # Add tab
                tab = measure.tab
                tab.x = measure.x
                tab.y = tabY
                tab.layout_objects()
                width = max(width, measure.x + measure.width + margins.right)
                for sprite in tab.sprites:
                    sprite.put((tab.x, tab.y))
                    self.sprites.append(sprite)
            y = tabY - TabMeasure.BOTTOM_MARGIN

        height = - y + 100

        page = sheet.pages[0]
        self.defaultViewPort = (page.size[0] / 2, -page.size[1] / 2)
        self.size = (width, height)
