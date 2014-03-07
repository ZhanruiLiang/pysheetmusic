#! /usr/bin/env python3
import zipfile
import os
import sys
import re

def read_zip(path):
    zfile = zipfile.ZipFile(path)
    for name in zfile.namelist():
        if not name.startswith('META-INF/') and name.endswith('.xml'):
            yield zfile.read(name).decode('utf-8')

def iter_dir(path):
    for name in os.listdir(path):
        if name.endswith('.mxl'):
            yield os.path.join(path, name)

if __name__ == '__main__':
    dir = sys.argv[2]
    key = sys.argv[1]
    pattern = re.compile(key)
    for path in iter_dir(dir):
        for content in read_zip(path):
            for lineId, line in enumerate(content.split('\n')):
                lineId += 1
                matched = pattern.search(line)
                if matched:
                    print('{}:{}: {}'.format(path, lineId, line))
