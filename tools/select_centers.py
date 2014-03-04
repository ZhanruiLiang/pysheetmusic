import sys
import pygame as pg
import shutil
import pygame.image
import json

def run(image, config):
    rects = config['rects']
    centers = config['centers']
    names = list(rects.keys())

    pg.display.init()
    screen = pg.display.set_mode(image.get_size(), 0, 32)
    image = image.convert_alpha()
    R = 5
    circle = pg.Surface((R * 2 + 1, R * 2 + 1)).convert_alpha()
    circle.fill((255, 255, 255, 0))
    pg.draw.circle(circle, (0, 255, 0, 255), (R + 1, R + 1), R, 1)
    circle.set_at((R + 1, R + 1), (0, 255, 0, 255))

    tm = pg.time.Clock()
    quit = False
    while not quit:
        for e in pg.event.get():
            if e.type == pg.QUIT:
                quit = True
            elif e.type == pg.MOUSEBUTTONDOWN:
                x1, y1 = e.pos
                for name in names:
                    x, y, w, h = rects[name]
                    if x <= x1 < x + w and y <= y1 < y + h:
                        centers[name] = x1 - x, y1 - y
                        print(name, centers[name])
                        break
        screen.fill((255, 255, 255, 255))
        screen.blit(image, (0, 0))
        for name in names:
            x, y, w, h = rects[name]
            cx, cy = centers[name]
            screen.blit(circle, (x + cx - R - 1, y + cy - R - 1))
        pg.display.update()
        tm.tick(30)

    return config


if __name__ == '__main__':
    base = sys.argv[1]
    imagePath = base + '.png'
    configPath = base + '.json'
    image = pygame.image.load(imagePath)
    with open(configPath) as configFile:
        config = json.load(configFile)
    newConfig = run(image, config)
    shutil.copy(configPath, configPath + '.bak')
    with open(configPath, 'w') as configFile:
        json.dump(newConfig, configFile)
