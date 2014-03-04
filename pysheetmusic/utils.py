
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
