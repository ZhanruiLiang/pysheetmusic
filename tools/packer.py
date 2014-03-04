import heapq
import pygame as pg
import pygame.image

class ImagePack:
    """
    Attributes:
        size
        positions
        rate
        images
        image
    """
    N_WIDTH_STEP = 8
    MAX_WIDTH = 2 ** 11
    AUTO_TRANSPOSE = True

    def __init__(self, images, width=None):
        " Each image should be a pygame.Surface with alpha channel. "
        self.width = width
        self.images = list(images)
        self._packed = False
        self.pack()

    def _calculate(self, transpose):
        """
        return (size, positions, rate)
        """
        if transpose:
            swap = lambda a: (a[1], a[0])
        else:
            swap = lambda a: a
        images = self.images

        # Perform a swap here
        sizes = [(swap(img.get_size()), i) for i, img in enumerate(images)]

        # Sort by height, from high to low.
        sizes.sort(key=lambda x: (-x[0][1], -x[0][0]))
        pos = [None] * len(sizes)
        area = sum(w * h for (w, h), _ in sizes)
        maxRate = 0
        bestSize = bestPos = None
        maxSingleW = max(w for (w, h), id in sizes)

        def fill(gw):
            if gw < maxSingleW: 
                return
            nonlocal maxRate, bestSize, bestPos
            rowRests = []
            heapq.heappush(rowRests, (-gw, 0))
            rowYs = [0]
            rowHeight = sizes[0][0][1]
            for (w, h), id in sizes:
                maxW = -rowRests[0][0]
                if maxW >= w:
                    # Add to this row
                    i = rowRests[0][1]
                    heapq.heapreplace(rowRests, (- (maxW - w), i))
                    pos[id] = (gw - maxW, rowYs[i])
                else:
                    # Create new row
                    heapq.heappush(rowRests, (-(gw - w), len(rowRests)))
                    rowYs.append(rowYs[-1] + rowHeight)
                    rowHeight = h
                    pos[id] = (0, rowYs[-1])
            size = (gw, rowYs[-1] + rowHeight)
            rate = area / (size[0] * size[1])
            if rate > maxRate:
                maxRate = rate
                bestSize = size
                bestPos = pos[:]
        # caculate wmax
        if self.width:
            gw = self.width
            fill(int(gw))
        else:
            wmax = self.MAX_WIDTH
            nSteps = self.N_WIDTH_STEP
            wmin = maxSingleW
            while 1:
                stepSize = (wmax - wmin) / nSteps
                if stepSize < 1:
                    break
                gw = wmin
                while gw <= wmax:
                    fill(int(gw))
                    gw += stepSize
                gw = bestSize[0]
                wmin = gw - stepSize
                wmax = gw + stepSize
        # Swap again and return
        print('rate: {}, transpose: {}'.format(maxRate, transpose))
        return swap(bestSize), list(map(swap, bestPos)), maxRate

    def pack(self):
        """
        Calculate self.size, self.positions, self.rate
        """
        if self._packed:
            return
        self._packed = True
        images = self.images

        if self.AUTO_TRANSPOSE:
            self.size, self.positions, self.rate = max(
                (self._calculate(0), self._calculate(1)),
                key=lambda x: x[-1] 
            )
        else:
            self.size, self.positions, self.rate = self._calculate(1)

        self.image = self._make_image()
        self.images = [
            self.image.subsurface((p, img.get_size())) 
            for p, img in zip(self.positions, images)
        ]
        print(
            'Packed {} images. Final size {}. Memory: {:.2f}MB. Rate: {:.3f}'.
            format(
                len(self.images), self.size,
                self.size[0] * self.size[1] * 4 / 2 ** 20, self.rate
            )
        )

    def _make_image(self):
        surface = pg.Surface(self.size).convert_alpha()
        surface.fill((0, 0, 0, 0))
        for image, pos in zip(self.images, self.positions):
            surface.blit(image, pos)
        return surface


def pack_dir(dirPath, output, margin=10):
    import os
    import json
    pg.display.init()
    pg.display.set_mode((1, 1), 0, 32)
    images = []
    names = []
    for name in os.listdir(dirPath):
        if name.endswith('.png'):
            path = os.path.join(dirPath, name)
            images.append(padded_image(pygame.image.load(path).convert_alpha(), margin))
            names.append(name[:-4])
    imagePack = ImagePack(images)
    resultImage = imagePack.image
    pygame.image.save(resultImage, output + '.png')
    rects = {}
    centers = {}
    try:
        centers.update(json.load(open(output + '.json'))['centers'])
    except FileNotFoundError:
        pass
    except IsADirectoryError:
        pass
    config = {'rects': rects, 'centers': centers}
    for name, image, pos in zip(names, images, imagePack.positions):
        x, y = pos
        w, h = image.get_size()
        # x -= margin
        # y -= margin
        # w -= 2 * margin
        # h -= 2 * margin
        rects[name] = (x, y, w, h)
        if name not in centers:
            centers[name] = (w//2, h//2)
    json.dump(config, open(output + '.json', 'w'))
    print('saved to {}'.format(output + '.png'))


def padded_image(image, margin):
    w, h = image.get_size()
    w1 = w + margin * 2
    h1 = h + margin * 2
    image1 = pg.Surface((w1, h1)).convert_alpha()
    image1.fill((0, 0, 0, 0))
    image1.blit(image, (margin, margin))
    return image1

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        print('packer.py {input directory} {output base name}')
    else:
        dir = sys.argv[1]
        output = sys.argv[2]
        pack_dir(dir, output)
