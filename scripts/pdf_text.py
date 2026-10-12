"""Recover missing PDF Unicode maps from embedded TrueType cmap tables.

No spelling substitutions are made. Original bytes are never changed; a temporary
copy receives the font's own glyph-to-Unicode mapping before pdftotext reads it.
"""
from collections import defaultdict
from io import BytesIO
from pathlib import Path
import subprocess
import tempfile

from fontTools.ttLib import TTFont
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject


def layout_text(path):
    reader = PdfReader(path)
    repaired, seen = [], set()
    for page in reader.pages:
        for ref in page.get('/Resources', {}).get('/Font', {}).values():
            font = ref.get_object()
            key = (getattr(ref, 'idnum', None), str(font.get('/BaseFont')))
            if key in seen or '/ToUnicode' in font or font.get('/Encoding') != '/Identity-H':
                continue
            seen.add(key)
            descendants = font.get('/DescendantFonts', [])
            if len(descendants) != 1:
                raise ValueError('Cannot recover Unicode for an unfamiliar composite font')
            descendant = descendants[0].get_object()
            descriptor = descendant.get('/FontDescriptor')
            if descriptor is None or '/FontFile2' not in descriptor.get_object():
                raise ValueError('Missing embedded TrueType font for Unicode recovery')
            ttf = TTFont(BytesIO(descriptor.get_object()['/FontFile2'].get_data()))
            by_glyph = defaultdict(set)
            for codepoint, glyph in (ttf.getBestCmap() or {}).items():
                by_glyph[ttf.getGlyphID(glyph)].add(codepoint)
            if not by_glyph:
                raise ValueError('Embedded font has no usable Unicode cmap')
            cid_map = descendant.get('/CIDToGIDMap', '/Identity')
            if str(cid_map) == '/Identity':
                pairs = [(gid, points) for gid, points in by_glyph.items()]
            else:
                data = cid_map.get_object().get_data()
                pairs = [(cid, by_glyph.get(int.from_bytes(data[cid * 2:cid * 2 + 2], 'big'), set()))
                         for cid in range(len(data) // 2)]
            mappings = []
            for cid, points in pairs:
                # Arial shares glyphs between these whitespace/hyphen variants.
                # Their visible form is identical; keep a stable visible form.
                if points and points <= {0x20, 0xA0}:
                    points = {0x20}
                elif points and points <= {0x2009, 0x202F}:
                    points = {0x2009}
                elif points and points <= {0x2D, 0xAD}:
                    points = {0x2D}
                elif points and points <= {0x2044, 0x2215}:
                    points = {0x2044}
                if len(points) > 1:
                    raise ValueError(f'Ambiguous glyph-to-Unicode mapping in {font.get("/BaseFont")}: {sorted(points)}')
                if points:
                    encoded = chr(next(iter(points))).encode('utf-16-be').hex().upper()
                    mappings.append(f'<{cid:04X}> <{encoded}>')
            lines = ['/CIDInit /ProcSet findresource begin', '12 dict begin', 'begincmap',
                     '/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def',
                     '/CMapName /RecoveredUnicode def', '/CMapType 2 def',
                     '1 begincodespacerange', '<0000> <FFFF>', 'endcodespacerange']
            for offset in range(0, len(mappings), 100):
                chunk = mappings[offset:offset + 100]
                lines.extend([f'{len(chunk)} beginbfchar', *chunk, 'endbfchar'])
            lines.extend(['endcmap', 'CMapName currentdict /CMap defineresource pop', 'end', 'end'])
            stream = DecodedStreamObject()
            stream.set_data(('\n'.join(lines) + '\n').encode('ascii'))
            font[NameObject('/ToUnicode')] = stream
            repaired.append(str(font.get('/BaseFont')))
    with tempfile.TemporaryDirectory() as temp:
        target = path
        if repaired:
            writer = PdfWriter()
            writer.append_pages_from_reader(reader)
            target = Path(temp) / 'unicode.pdf'
            writer.write(target)
        result = subprocess.run(['pdftotext', '-layout', str(target), '-'],
                                check=True, capture_output=True, text=True)
    return result.stdout, repaired
