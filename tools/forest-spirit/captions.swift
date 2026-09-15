import AppKit
import Foundation
struct Cue: Decodable { let id:Int; let character:String; let label:String; let text:String; let x:Double; let y:Double; let width:Double; let height:Double; let font:String; let fontSize:Double; let labelFont:String; let fontColor:String; let labelColor:String; let fill:String; let stroke:String }
let config=CommandLine.arguments[1], output=CommandLine.arguments[2]
let cues=try JSONDecoder().decode([Cue].self,from:Data(contentsOf:URL(fileURLWithPath:config)))
func color(_ s:String,_ alpha:Double=1)->NSColor {let n=UInt64(s,radix:16)!;return NSColor(srgbRed:Double((n>>16)&255)/255,green:Double((n>>8)&255)/255,blue:Double(n&255)/255,alpha:alpha)}
var measurements:[[String:Any]]=[]
for c in cues {
 let bitmap=NSBitmapImageRep(bitmapDataPlanes:nil,pixelsWide:1080,pixelsHigh:1920,bitsPerSample:8,samplesPerPixel:4,hasAlpha:true,isPlanar:false,colorSpaceName:.deviceRGB,bytesPerRow:0,bitsPerPixel:0)!
 let context=NSGraphicsContext(bitmapImageRep:bitmap)!;NSGraphicsContext.saveGraphicsState();NSGraphicsContext.current=context
 NSColor.clear.setFill();NSRect(x:0,y:0,width:1080,height:1920).fill()
 let r=NSRect(x:c.x-c.width/2,y:1920-c.y-c.height/2,width:c.width,height:c.height)
 let shape:NSBezierPath
 if c.character == "P2" {
  shape=NSBezierPath();shape.move(to:NSPoint(x:r.minX+5,y:r.minY+5));shape.line(to:NSPoint(x:r.maxX-4,y:r.minY));shape.line(to:NSPoint(x:r.maxX,y:r.maxY-26));shape.line(to:NSPoint(x:r.maxX-30,y:r.maxY));shape.line(to:NSPoint(x:r.minX,y:r.maxY-3));shape.close()
 } else if c.character == "T2" {
  shape=NSBezierPath();let k:CGFloat=10
  for (i,p) in [NSPoint(x:r.minX+k,y:r.minY),NSPoint(x:r.maxX-k,y:r.minY),NSPoint(x:r.maxX,y:r.minY+k),NSPoint(x:r.maxX,y:r.maxY-k),NSPoint(x:r.maxX-k,y:r.maxY),NSPoint(x:r.minX+k,y:r.maxY),NSPoint(x:r.minX,y:r.maxY-k),NSPoint(x:r.minX,y:r.minY+k)].enumerated(){if i==0{shape.move(to:p)}else{shape.line(to:p)}};shape.close()
 } else { shape=NSBezierPath(roundedRect:r,xRadius:c.character == "C3" ? 42:34,yRadius:c.character == "C3" ? 36:34) }
 NSGraphicsContext.saveGraphicsState();let shadow=NSShadow();shadow.shadowColor=NSColor.black.withAlphaComponent(0.42);shadow.shadowBlurRadius=13;shadow.shadowOffset=NSSize(width:0,height:-5);shadow.set();color(c.fill,c.character == "P2" ? 0.97:0.92).setFill();shape.fill();NSGraphicsContext.restoreGraphicsState()
 color(c.stroke).setStroke();shape.lineWidth=c.character == "C3" ? 3:2;shape.stroke()
 if c.character == "F1" {
  let stitch=NSBezierPath(roundedRect:r.insetBy(dx:10,dy:10),xRadius:26,yRadius:26);stitch.setLineDash([6,7],count:2,phase:0);stitch.lineWidth=1.5;color(c.stroke,0.8).setStroke();stitch.stroke()
 } else if c.character == "P2" {
  let fold=NSBezierPath();fold.move(to:NSPoint(x:r.maxX-30,y:r.maxY));fold.line(to:NSPoint(x:r.maxX-31,y:r.maxY-26));fold.line(to:NSPoint(x:r.maxX,y:r.maxY-26));fold.close();color("d8bb85").setFill();fold.fill()
  color(c.stroke,0.45).setStroke();let rule=NSBezierPath();rule.move(to:NSPoint(x:r.minX+24,y:r.minY+14));rule.line(to:NSPoint(x:r.maxX-23,y:r.minY+17));rule.lineWidth=1;rule.stroke()
 } else if c.character == "T2" {
  color(c.stroke,0.50).setStroke();let inner=NSBezierPath(roundedRect:r.insetBy(dx:7,dy:7),xRadius:2,yRadius:2);inner.lineWidth=1;inner.stroke()
  for px in [r.minX+20,r.maxX-20] {color(c.stroke).setFill();NSBezierPath(ovalIn:NSRect(x:px-2.5,y:r.midY-2.5,width:5,height:5)).fill()}
 }
 let para=NSMutableParagraphStyle();para.alignment = .center;para.lineBreakMode = .byClipping
 guard let font=NSFont(name:c.font,size:c.fontSize),let labelFont=NSFont(name:c.labelFont,size:31) else{fatalError("Missing selected font")}
 let attrs:[NSAttributedString.Key:Any]=[.font:font,.foregroundColor:color(c.fontColor),.paragraphStyle:para]
 let labelAttrs:[NSAttributedString.Key:Any]=[.font:labelFont,.foregroundColor:color(c.labelColor),.paragraphStyle:para,.kern:c.character == "P2" ? 2:4]
 let textSize=(c.text as NSString).size(withAttributes:attrs);let labelSize=(c.label.uppercased() as NSString).size(withAttributes:labelAttrs)
 precondition(textSize.width<c.width-65,"Caption exceeds panel: \(c.text)")
 let tr=NSRect(x:r.minX+30,y:r.minY+15,width:r.width-60,height:textSize.height+8)
 let lr=NSRect(x:r.minX+35,y:r.maxY-54,width:r.width-70,height:42)
 (c.label.uppercased() as NSString).draw(in:lr,withAttributes:labelAttrs)
 (c.text as NSString).draw(in:tr,withAttributes:attrs)
 context.flushGraphics();NSGraphicsContext.restoreGraphicsState()
 try bitmap.representation(using:.png,properties:[:])!.write(to:URL(fileURLWithPath:output+String(format:"/cue-%02d.png",c.id)))
 measurements.append(["id":c.id,"label":c.label,"text":c.text,"font":font.fontName,"textWidth":textSize.width,"panelWidth":c.width,"labelWidth":labelSize.width,"bounds":[r.minX,1920-r.maxY,r.width,r.height]])
}
let data=try JSONSerialization.data(withJSONObject:measurements,options:[.prettyPrinted,.sortedKeys]);try data.write(to:URL(fileURLWithPath:output+"/measurements.json"))
