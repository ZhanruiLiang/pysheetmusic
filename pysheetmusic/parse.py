import lxml.etree
import zipfile
from os.path import join, dirname
import os
from contextlib import contextmanager
from . import sheet as S
from raygllib.utils import timeit

class FormatError(Exception):
    pass

class ValidateError(Exception):
    pass

class ParseInfo:
    def __init__(self):
        self.sheet = None
        self.page = None
        self.measure = None
        self.beams = []

class MusicXMLParser:
    @staticmethod
    def get_schema():
        with _run_in_dir(join(dirname(__file__), 'schema')):
            with open('musicxml.xsd') as schemaFile:
                schemaDoc = lxml.etree.XML(schemaFile.read().encode('utf-8'))
                schema = lxml.etree.XMLSchema(schemaDoc)
        return schema

    def __init__(self):
        self.schema = self.get_schema()

    @timeit
    def parse(self, path):
        print('parsing:', os.path.split(path)[-1])
        xmlDoc = _read_musicxml(path)
        if not self.schema(xmlDoc):
            raise ValidateError(path, self.schema.error_log.filter_from_errors())
        parseInfo = ParseInfo()
        parseInfo.sheet = S.Sheet(xmlDoc)
        parseInfo.page = parseInfo.sheet.new_page()
        # Support single part only.
        partNode = xmlDoc.find('part')
        for measureNode in partNode.findall('measure'):
            parseInfo.measure = S.Measure(measureNode)
            if measureNode.find('print[@new-page="yes"]'):
                parseInfo.page = parseInfo.sheet.new_page()
            parseInfo.page.add_measure(parseInfo.measure)
            for child in measureNode.getchildren():
                # Types handled:
                #   note, backup, forward, attributes, print, barline
                # Types not handled:
                #   direction, harmony, figured-bass, bookmark,
                #   link, grouping, sound
                if child.tag == 'print':
                    self.handle_print_node(parseInfo, child)
                elif child.tag == 'attributes':
                    self.handle_attributes_node(parseInfo, child)


    def handle_print_node(self, parseInfo, node):
        measure = parseInfo.measure
        page = parseInfo.page
        if measure._layouted:
            return
        staffSpacing = node.attrib.get('staff-spacing', None)
        if staffSpacing is not None:
            measure.staffSpacing = float(staffSpacing)
        newSystem = measure.number == 1 or \
            node.attrib.get('new-system', 'no').lower() == 'yes'
        newPage = measure.number == 1 and parseInfo.page.prev is None or\
            node.attrib.get('new-page', 'no').lower() == 'yes'
        # system layout
        systemMargins = S.Margins(node.find('system-layout/system-margins'))
        if newPage:
            if node.find('page-layout'):
                # TODO: Adjust page layout.
                pass
            topSystemDistance = float(
                node.find('system-layout/top-system-distance').text)
            measure.y = page.size[1] - page.margins.top - topSystemDistance\
                - measure.height
            measure.x = systemMargins.left + page.margins.left
        elif newSystem:
            measure.x = systemMargins.left + measure.page.margins.left
            measure.y = page.size[1]\
                - float(node.find('system-layout/system-distance').text)\
                - measure.height
        else:
            measure.y = measure.prev.y
            measure.x = measure.prev.x + measure.prev.width
            measureDistance = node.find('/measure-layout/measure-distance')
            if measureDistance:
                measure.x += float(measureDistance.text)

    def handle_attributes_node(self, parseInfo, node):
        measure = parseInfo.measure
        if node.find('divisions'):
            measure.timeDivisions = int(node.find('divisions').text)
        # Clef
        measure.set_clef(node.find('clef'))
        # Time
        # Key


def _read_musicxml(path):
    content = None
    try:
        zfile = zipfile.ZipFile(path)
        for name in zfile.namelist():
            if not name.startswith('META-INF/') and name.endswith('.xml'):
                content = zfile.read(name)
                break
    except zipfile.BadZipFile:
        with open(path, 'rb') as infile:
            content = infile.read()
    if not content:
        raise FormatError()
    try:
        return lxml.etree.XML(content)
    except lxml.etree.XMLSyntaxError:
        raise FormatError()

@contextmanager
def _run_in_dir(dest):
    curDir = os.path.abspath(os.curdir)
    os.chdir(dest)
    yield
    os.chdir(curDir)

def from_musicxml_file(path):
    pass
