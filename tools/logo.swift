// Logoul BIG Solutions cu textul transformat în contururi: SVG + PNG.
// Reproduce exact SVG-ul din antetul site-ului (viewBox 0 0 270 64).
import Foundation
import CoreText
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

let FONTS = URL(fileURLWithPath: #filePath).deletingLastPathComponent().appendingPathComponent("../src/assets/fonts").standardized.path + "/"
let OUT = CommandLine.arguments[1]

func font(_ file: String, weight: Double, size: CGFloat) -> CTFont {
  let d = try! Data(contentsOf: URL(fileURLWithPath: FONTS + file))
  let base = (CTFontManagerCreateFontDescriptorsFromData(d as CFData) as! [CTFontDescriptor])[0]
  let wght = 0x77676874 // 'wght'
  let desc = CTFontDescriptorCreateCopyWithAttributes(base, [kCTFontVariationAttribute: [wght: weight]] as CFDictionary)
  return CTFontCreateWithFontDescriptor(desc, size, nil)
}

// Textul ca un singur contur, cu linia de bază la (x, y) în coordonate SVG (y în jos).
func textPath(_ s: String, _ f: CTFont, x: CGFloat, y: CGFloat, tracking: CGFloat = 0) -> CGPath {
  var attrs: [NSAttributedString.Key: Any] = [NSAttributedString.Key(kCTFontAttributeName as String): f]
  if tracking != 0 { attrs[NSAttributedString.Key(kCTKernAttributeName as String)] = tracking }
  let line = CTLineCreateWithAttributedString(NSAttributedString(string: s, attributes: attrs))
  let out = CGMutablePath()
  for run in CTLineGetGlyphRuns(line) as! [CTRun] {
    let n = CTRunGetGlyphCount(run)
    var glyphs = [CGGlyph](repeating: 0, count: n), pos = [CGPoint](repeating: .zero, count: n)
    CTRunGetGlyphs(run, CFRange(location: 0, length: n), &glyphs)
    CTRunGetPositions(run, CFRange(location: 0, length: n), &pos)
    let rf = (CTRunGetAttributes(run) as NSDictionary)[kCTFontAttributeName as String] as! CTFont
    for i in 0..<n {
      var t = CGAffineTransform(a: 1, b: 0, c: 0, d: -1, tx: x + pos[i].x, ty: y - pos[i].y)
      if let g = CTFontCreatePathForGlyph(rf, glyphs[i], &t) { out.addPath(g) }
    }
  }
  return out
}

func svgD(_ p: CGPath) -> String {
  func f(_ v: CGFloat) -> String { var s = String(format: "%.2f", v); while s.hasSuffix("0") { s.removeLast() }; if s.hasSuffix(".") { s.removeLast() }; return s == "-0" ? "0" : s }
  func pt(_ q: CGPoint) -> String { f(q.x) + " " + f(q.y) }
  var d = ""
  p.applyWithBlock { e in
    let a = e.pointee.points
    switch e.pointee.type {
    case .moveToPoint: d += "M" + pt(a[0])
    case .addLineToPoint: d += "L" + pt(a[0])
    case .addQuadCurveToPoint: d += "Q" + pt(a[0]) + " " + pt(a[1])
    case .addCurveToPoint: d += "C" + pt(a[0]) + " " + pt(a[1]) + " " + pt(a[2])
    case .closeSubpath: d += "Z"
    @unknown default: break
    }
  }
  return d
}

let ORANGE = "#F28C28"
let bars: [CGRect] = [CGRect(x: 0, y: 30, width: 12, height: 26), CGRect(x: 17, y: 18, width: 12, height: 38), CGRect(x: 34, y: 6, width: 12, height: 50)]
let big = textPath("BIG Solutions", font("bricolage-grotesque-latin.woff2", weight: 800, size: 27), x: 60, y: 38)
let mgmt = textPath("MANAGEMENT", font("hanken-grotesk-latin.woff2", weight: 600, size: 10.5), x: 61, y: 55, tracking: 3.4)

// Margini reale ale desenului (fără spațiul gol din dreapta).
let all = CGMutablePath(); bars.forEach { all.addRect($0) }; all.addPath(big); all.addPath(mgmt)
let bb = all.boundingBoxOfPath
let W = (bb.maxX).rounded(.up)
let VIEW = CGRect(x: 0, y: 6, width: W, height: 50) // barele dau înălțimea: y 6–56
print("bbox", bb, "-> viewBox", VIEW)

func hex(_ s: String) -> CGColor {
  var v: UInt64 = 0; Scanner(string: String(s.dropFirst())).scanHexInt64(&v)
  return CGColor(red: CGFloat((v >> 16) & 255) / 255, green: CGFloat((v >> 8) & 255) / 255, blue: CGFloat(v & 255) / 255, alpha: 1)
}

struct Variant { let name: String; let ink: String; let sub: String }
let variants = [Variant(name: "logo-big-solutions", ink: "#1F1B18", sub: "#6B625B"),
                Variant(name: "logo-big-solutions-alb", ink: "#FFFFFF", sub: "#B9AEA5")]

func barsSVG() -> String { bars.map { "<rect x=\"\(Int($0.minX))\" y=\"\(Int($0.minY))\" width=\"\(Int($0.width))\" height=\"\(Int($0.height))\" rx=\"3\" fill=\"\(ORANGE)\"/>" }.joined() }

for v in variants {
  let svg = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 6 \(Int(W)) 50\" role=\"img\" aria-label=\"BIG Solutions Management\">" +
    barsSVG() + "<path fill=\"\(v.ink)\" d=\"\(svgD(big))\"/><path fill=\"\(v.sub)\" d=\"\(svgD(mgmt))\"/></svg>\n"
  try! svg.write(toFile: OUT + "/" + v.name + ".svg", atomically: true, encoding: .utf8)
}
let symSVG = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 6 46 50\" role=\"img\" aria-label=\"BIG Solutions Management\">" + barsSVG() + "</svg>\n"
try! symSVG.write(toFile: OUT + "/logo-simbol.svg", atomically: true, encoding: .utf8)

// PNG transparent, desenat direct din aceleași contururi.
func png(_ file: String, width px: Int, view: CGRect, bg: CGColor? = nil, draw: (CGContext) -> Void) {
  let s = CGFloat(px) / view.width
  let hpx = Int((view.height * s).rounded())
  let ctx = CGContext(data: nil, width: px, height: hpx, bitsPerComponent: 8, bytesPerRow: 0, space: CGColorSpace(name: CGColorSpace.sRGB)!, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
  if let bg { ctx.setFillColor(bg); ctx.fill(CGRect(x: 0, y: 0, width: px, height: hpx)) }
  ctx.translateBy(x: 0, y: CGFloat(hpx)); ctx.scaleBy(x: s, y: -s); ctx.translateBy(x: -view.minX, y: -view.minY)
  draw(ctx)
  let dest = CGImageDestinationCreateWithURL(URL(fileURLWithPath: OUT + "/" + file) as CFURL, UTType.png.identifier as CFString, 1, nil)!
  CGImageDestinationAddImage(dest, ctx.makeImage()!, nil); CGImageDestinationFinalize(dest)
}
func drawBars(_ c: CGContext) { c.setFillColor(hex(ORANGE)); for r in bars { c.addPath(CGPath(roundedRect: r, cornerWidth: 3, cornerHeight: 3, transform: nil)); c.fillPath() } }
for v in variants {
  png(v.name + ".png", width: 1600, view: VIEW) { c in
    drawBars(c); c.setFillColor(hex(v.ink)); c.addPath(big); c.fillPath(); c.setFillColor(hex(v.sub)); c.addPath(mgmt); c.fillPath()
  }
}
// Pătrat centrat pe bare (centrul lor e la 23, 31).
func square(_ side: CGFloat) -> CGRect { CGRect(x: 23 - side / 2, y: 31 - side / 2, width: side, height: side) }
png("logo-simbol.png", width: 512, view: square(54)) { drawBars($0) }
// Pătrat pentru profiluri (Facebook, LinkedIn, Google): barele pe fond închis, centrate.
png("logo-simbol-profil.png", width: 1024, view: square(100), bg: hex("#1F1B18")) { drawBars($0) }
print("gata")
