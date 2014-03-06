import lxml.etree
import zipfile
from os.path import join, dirname
import os
from contextlib import contextmanager
from fractions import Fraction

from raygllib.utils import timeit
from raygllib import ui

from . import sheet as S
from . import sprite
from .utils import monad


class FormatError(Exception):
    pass

class ValidateError(Exception):
    pass

class ParseContext:
    def __init__(self):
        self.sheet = None
        self.page = None
        self.measure = None
        self.beams = {}
        self.endings = {}

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
        context = ParseContext()
        context.sheet = S.Sheet(xmlDoc)
        context.page = context.sheet.new_page()
        # Currently we only have single part support.
        partNode = xmlDoc.find('part')
        handledTags = ('attributes', 'note', 'backup', 'forward', 'barline')
        handlers = {tag: getattr(self, 'handle_' + tag) for tag in handledTags}
        for measureNode in partNode.findall('measure'):
            context.measure = measure = S.Measure(measureNode)
            if measureNode.find('print[@new-page="yes"]') is not None:
                context.page = context.sheet.new_page()
            context.page.add_measure(measure)
            if measureNode.find('print') is None:
                measure.follow_prev_layout()
            else:
                self.handle_print(context, measureNode.find('print'))
            for child in measureNode.getchildren():
                # Types handled:
                #   note, backup, forward, attributes, print, barline
                # Types not handled:
                #   direction, harmony, figured-bass, bookmark,
                #   link, grouping, sound
                if child.tag in handlers:
                    handlers[child.tag](context, child)
            measure.layout()
        # Parse credits
        for creditNode in xmlDoc.findall('credit'):
            pageNum = int(creditNode.attrib.get('page', '1')) - 1
            page = context.sheet.pages[pageNum]
            textNode = creditNode.find('credit-words')
            if textNode is not None:
                page.add_sprite(sprite.CreditWords(textNode))

        context.sheet.layout()
        return context.sheet

    def handle_print(self, context, node):
        measure = context.measure
        page = context.page
        staffSpacing = node.attrib.get('staff-spacing', None)
        if staffSpacing is not None:
            measure.staffSpacing = float(staffSpacing)
        newSystem = measure.prev is None or \
            node.attrib.get('new-system', 'no').lower() == 'yes'
        newPage = measure.prev is None or\
            node.attrib.get('new-page', 'no').lower() == 'yes'
        # system layout
        systemMargins = S.Margins(node.find('system-layout/system-margins'))
        if newPage:
            measure.isNewSystem = True
            if node.find('page-layout') is not None:
                # TODO: Adjust page layout.
                pass
            topSystemDistance = float(
                node.find('system-layout/top-system-distance').text)
            measure.y = (page.size[1] - page.margins.top - topSystemDistance
                - measure.height)
            measure.x = systemMargins.left + page.margins.left
        elif newSystem:
            measure.isNewSystem = True
            measure.x = systemMargins.left + measure.page.margins.left
            measure.y = (measure.prev.y
                - float(node.find('system-layout/system-distance').text)
                - measure.height)
        else:
            measure.follow_prev_layout()
            measureDistance = node.find('measure-layout/measure-distance')
            if measureDistance:
                measure.x += float(measureDistance.text)

    def handle_attributes(self, context, node):
        measure = context.measure
        if node.find('divisions') is not None:
            measure.timeDivisions = int(node.find('divisions').text)
        # Clef
        if node.find('clef') is not None:
            measure.set_clef(S.Clef(node.find('clef')))
        # Time
        # Key
        if node.find('key') is not None:
            key = S.KeySignature(
                int(node.find('key/fifths').text), node.find('key/mode'))
            measure.set_key(key)

    # @profile
    def handle_note(self, context, node):
        grace = node.find('grace')
        cue = node.find('cue')
        measure = context.measure
        if grace is not None:
            pass  # TODO
        elif cue is not None:
            pass  # TODO
        else:
            isChord = node.find('chord') is not None
            # Use lambda here to mimic the lazy behavior
            duration = lambda: \
                Fraction(node.find('duration').text) / measure.timeDivisions / 4
            dots = lambda: [None] * len(node.xpath('dot'))
            type = lambda: monad(node.find('type'), lambda x: x.text, None)
            timeMod = lambda: S.TimeModification(node.find('time-modification'))

            def pos():
                try:
                    return float(node.attrib['default-x']), \
                        float(node.attrib['default-y'])
                except (KeyError, ValueError):
                    return None

            if node.find('pitch') is not None:
                pitch = S.Pitch(node.find('pitch'))
                stem = monad(node.find('stem'), S.Stem, None) if not isChord else None
                accidental = monad(node.find('accidental'), S.Accidental, None)
                note = S.PitchedNote(
                    pos(), duration(), timeMod(), dots(), type(),
                    pitch, stem, accidental)
                measure.add_note(note, isChord)
                stem = note.stem
                if stem:
                    for beamNode in node.findall('beam'):
                        beamType = beamNode.text
                        number = beamNode.attrib['number']
                        if beamType == 'begin':
                            beam = S.Beam()
                            context.beams[number] = beam
                        elif beamType == 'continue':
                            beam = context.beams[number]
                        elif beamType == 'end':
                            beam = context.beams[number]
                            measure.add_beam(beam)
                        else:
                            beam = S.Beam(beamType)
                            measure.add_beam(beam)
                        beam.add_stem(stem)
            elif node.find('rest') is not None:
                note = S.Rest(pos(), duration(), timeMod(), dots(), type())
                measure.add_note(note, isChord)

    def handle_forward(self, context, node):
        measure = context.measure
        duration = Fraction(node.find('duration').text) / measure.timeDivisions / 4
        measure.change_time(duration)

    def handle_backup(self, context, node):
        measure = context.measure
        duration = -Fraction(node.find('duration').text) / measure.timeDivisions / 4
        measure.change_time(duration)

    def handle_barline(self, context, node):
        context.measure.add_barline(S.BarLine(node))
        sheet = context.sheet
        if node.find('ending') is not None:
            endingNode = node.find('ending')
            number = endingNode.attrib['number']
            if endingNode.attrib['type'] == 'start':
                ending = S.Ending(number)
                context.endings[number] = ending
                ending.start = context.measure
            else:
                ending = context.endings.pop(number)
                ending.end = context.measure
                ending.start.set_ending(ending)


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
