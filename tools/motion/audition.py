#!/usr/bin/env python3
"""Make a still-image audition beside the standard production status page.

Run with the existing Pillow/NumPy Python environment. Original anchors are
never modified. This does not simulate motion, exposure pumping or H.264 GOPs.
"""
import argparse
import hashlib
import html
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_window(source, font, temperature, clock):
    width, height = source.size
    crop_width = height * 4 // 3
    left = (width - crop_width) // 2
    frame = source.crop((left, 0, left + crop_width, height))
    frame = frame.convert('L').resize((960, 720), Image.Resampling.LANCZOS)
    frame = frame.filter(ImageFilter.GaussianBlur(0.6))
    a = np.asarray(frame).astype(np.float32)
    # Existing anchors already contain an illuminator falloff and noise. Keep
    # that image, adding only modest grain for this still audition.
    a = 8 + np.power(a / 255, 1.08) * 247
    a = np.clip(a + np.random.default_rng(20261030).normal(0, 3, a.shape), 0, 255)
    frame = Image.fromarray(a.astype('uint8')).convert('RGB')
    d = ImageDraw.Draw(frame)
    d.rectangle((0, 668, 959, 719), fill='#141414')
    # A waning gibbous icon: retain the left half and a convex illuminated
    # terminator in the right half. The icon expresses phase, not precision.
    moon = Image.new('L', (96, 96), 0)
    m = np.asarray(moon).copy()
    yy, xx = np.mgrid[:96, :96]
    xn, yn = (xx - 47.5) / 47, (yy - 47.5) / 47
    disc = xn * xn + yn * yn <= 1
    terminator = 0.48 * np.sqrt(np.maximum(0, 1 - yn * yn))
    m[disc & (xn <= terminator)] = 255
    moon = Image.fromarray(m).resize((24, 24), Image.Resampling.LANCZOS)
    frame.paste((230, 230, 230), (16, 682, 40, 706), moon)
    d.text((52, 694), f'{temperature}°F', font=font, fill='#e6e6e6', anchor='lm')
    d.text((480, 694), clock, font=font, fill='#e6e6e6', anchor='mm')
    d.rectangle((915, 688, 941, 700), outline='#e6e6e6', width=2)
    d.rectangle((942, 691, 944, 697), fill='#e6e6e6')
    for x in (919, 925, 931):
        d.rectangle((x, 691, x + 3, 697), fill='#e6e6e6')
    return frame, [left, 0, left + crop_width, height]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('workspace', type=Path)
    p.add_argument('--manifest', type=Path, required=True)
    args = p.parse_args()
    w = args.workspace
    manifest = json.loads(args.manifest.read_text())
    previous = w / 'audition' / 'preview-receipt.json'
    if previous.exists():
        before = json.loads(previous.read_text())
        if (before['recipeSha256'], before['manifestSha256']) != (sha(Path(__file__)), sha(args.manifest)):
            history = w / 'audition' / 'history' / sha(previous)[:16]
            if not history.exists():
                history.mkdir(parents=True)
                shutil.copy2(previous, history / previous.name)
                if (w / 'status' / 'audition.html').exists():
                    shutil.copy2(w / 'status' / 'audition.html', history / 'audition.html')
                if (w / 'status' / 'audition-assets').exists():
                    shutil.copytree(w / 'status' / 'audition-assets', history / 'audition-assets')
    out = w / 'status' / 'audition-assets'
    out.mkdir(parents=True, exist_ok=True)
    font_path = w / 'sources/fonts/RobotoMono-wght.ttf'
    font = ImageFont.truetype(str(font_path), 30)
    font.set_variation_by_axes([700])
    receipts, cards, views = [], [], {}
    for item in manifest['images']:
        source_path = w / item['source']
        if not source_path.exists():
            continue
        source = Image.open(source_path).convert('RGB')
        frame, crop = make_window(source, font, item['temperatureF'], item['clock'])
        phone = Image.new('RGB', (1080, 1920), '#000000')
        phone.paste(frame.resize((1080, 810), Image.Resampling.BILINEAR), (0, 555))
        # Verify that the static layout really preserves the stipulated black.
        pixels = np.asarray(phone)
        assert not pixels[:555].any() and not pixels[1365:].any()
        outputs = {}
        for name, img in [('window', frame), ('phone', phone), ('source', source)]:
            target = out / f"{item['id']}-{name}.png"
            img.save(target, optimize=True)
            outputs[name] = {'path': target.relative_to(w).as_posix(), 'sha256': sha(target),
                             'width': img.width, 'height': img.height}
        views[item['id']] = {name: 'audition-assets/' + Path(x['path']).name for name, x in outputs.items()}
        receipts.append({'id': item['id'], 'source': item['source'], 'sourceSha256': sha(source_path),
                         'cropBox': crop, 'outputs': outputs})
        esc = html.escape
        cards.append(f'''<article id="{esc(item['id'])}"><h2>{esc(item['id'])} · {esc(item['title'])}</h2>
<a class="image" href="{views[item['id']]['window']}" target="_blank" rel="noopener">
<img data-id="{esc(item['id'])}" src="{views[item['id']]['window']}" alt="{esc(item['title'])}"></a>
<p>{esc(item['note'])}</p></article>''')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Untitled trail-camera film · image audition</title><style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#111;color:#e4e4df}body{max-width:1400px;margin:auto;padding:24px}
a{color:#d5e4d0}header{max-width:850px}h1{font-size:clamp(26px,4vw,44px);font-weight:500;letter-spacing:-.04em;margin:16px 0}
p{line-height:1.6;color:#bfbfb8}nav{display:flex;gap:8px;flex-wrap:wrap;margin:24px 0}button{font:inherit;cursor:pointer;background:#222;color:#ddd;border:1px solid #555;padding:10px 16px;border-radius:4px}
button[aria-pressed=true]{background:#d8dfd2;color:#111}main{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:32px}
article{min-width:0}h2{font-size:17px;font-weight:500}.image{display:flex;background:#000;justify-content:center;align-items:center;min-height:100px}
img{max-width:100%;height:auto;display:block}body[data-view=phone] img{max-height:720px;width:auto}article p{font-size:14px}
@media(max-width:700px){body{padding:16px}main{grid-template-columns:1fr}body[data-view=phone] img{max-height:75vh}}
</style><body data-view="window"><header><a href="index.html">← Production status</a><h1>Image audition 01</h1>
<p>Untitled trail-camera film. One camera, one cast, no motion generated. Review the ordinary infrared texture, wardrobe continuity, crop and final count of four pairs. These are candidates awaiting your direction.</p>
<p>The camera view includes the planned crop, data strip, softness and grain. The phone view places that frame on the exact black portrait canvas. Final motion compression and changing exposure are not simulated. P3 is the supporting cast reference, not the complete C3 shot.</p>
<p>Leave notes in our conversation using the image IDs below. Click any image to open it at full size.</p></header>
<nav aria-label="Image view"><button data-view="window" aria-pressed="true">Camera crop</button><button data-view="phone" aria-pressed="false">Phone frame</button><button data-view="source" aria-pressed="false">Full source</button></nav>
<main>''' + '\n'.join(cards) + '''</main><script>
const views = ''' + json.dumps(views) + ''';
for(const button of document.querySelectorAll('button[data-view]')) button.addEventListener('click',()=>{
 document.body.dataset.view=button.dataset.view;
 for(const b of document.querySelectorAll('button[data-view]'))b.setAttribute('aria-pressed',String(b===button));
 for(const img of document.querySelectorAll('img[data-id]')){img.src=views[img.dataset.id][button.dataset.view];img.parentElement.href=img.src;}
});</script></body></html>'''
    (w / 'status' / 'audition.html').write_text(page)
    (w / 'audition' / 'preview-receipt.json').write_text(json.dumps({
        'schemaVersion': 1, 'recipe': 'tools/motion/audition.py', 'recipeSha256': sha(Path(__file__)),
        'manifestSha256': sha(args.manifest), 'font': 'Roboto Mono Bold, weight 700',
        'fontSha256': sha(font_path), 'blackOutsideWindowVerified': True,
        'finalCodecSimulated': False, 'directorApproval': 'pending', 'images': receipts
    }, indent=2) + '\n')
    print(json.dumps({'images': len(receipts), 'gallery': str(w / 'status' / 'audition.html')}))


if __name__ == '__main__':
    main()
