from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

def create_font(filename, weight=400):
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder([".notdef"])
    fb.setupCharacterMap({})
    pen = TTGlyphPen(None)
    pen.moveTo((0,0))
    pen.lineTo((500,0))
    pen.lineTo((500,500))
    pen.lineTo((0,500))
    pen.closePath()
    fb.setupGlyf({".notdef": pen.glyph()})
    fb.setupHorizontalMetrics({".notdef": (500, 0)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupOS2(usWeightClass=weight)
    fb.setupPost()
    fb.setupNameTable({"familyName":"Test","styleName":"W"})
    fb.save(filename)

create_font("source-light.ttf", 100)
create_font("source-regular.ttf", 400)
print("[+] Generated source-light.ttf and source-regular.ttf")
