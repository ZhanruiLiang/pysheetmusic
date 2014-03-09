from collections import deque
from time import time as get_time

def monad(node, func, default):
    return func(node) if node is not None else default

def debug(*args, **kwargs):
    print(*args, **kwargs)

def gcd(*nums):
    if not nums:
        return 1
    x = nums[0]
    for y in nums[1:]:
        while y != 0:
            x, y = y, x % y
    return x

class FPSCounter:
    UPDATE_INTERVAL = 1.0

    def __init__(self):
        self.ticks = deque()

    def tick(self):
        ticks = self.ticks
        time = get_time()
        ticks.append(time)
        while time - ticks[0] > self.UPDATE_INTERVAL:
            ticks.popleft()

    @property
    def fps(self):
        ticks = self.ticks
        if len(ticks) >= 2:
            return (len(ticks) - 1) / (ticks[-1] - ticks[0])
        else:
            return 0.

def find_one(node, path):
    result = node.find(path)
    if result is not None:
        yield result
