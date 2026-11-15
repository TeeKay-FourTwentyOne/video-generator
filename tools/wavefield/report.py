#!/usr/bin/env python3
"""Build numerical field plates and a private, portable calculation report."""
import argparse
import html
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def font(size):
    return ImageFont.load_default(size=size)


def heat(a,scale):
    q=np.uint8(np.clip(np.sqrt(np.maximum(a,0)/scale)*255,0,255))
    return cv2.cvtColor(cv2.applyColorMap(q,cv2.COLORMAP_INFERNO),cv2.COLOR_BGR2RGB)


def signed(a,scale):
    q=np.clip(a/scale,-1,1)
    pos=np.maximum(q,0)[...,None]
    neg=np.maximum(-q,0)[...,None]
    return np.uint8(np.clip(pos*np.array([255,178,70])+neg*np.array([65,158,255]),0,255))


def plate(source,target,milestone):
    with np.load(source) as d:
        branches=d['branches'];coh=d['coherent'];inc=d['incoherent'];cross=d['cross']
        scale=float(np.quantile(np.r_[coh.ravel()[::8],inc.ravel()[::8]],.995))
        cross_scale=float(np.quantile(np.abs(cross),.995))
        arrays=[abs(b)**2 for b in branches]+[inc,coh,cross]
        labels=['Branch 1 intensity','Branch 2 intensity','Branch 3 intensity',
                'Sum of intensities','Intensity of the sum','Interference cross terms']
        subtitle=['|psi_1|^2','|psi_2|^2','|psi_3|^2',
                  'I_inc = sum |psi_j|^2','I_coh = |sum psi_j|^2','I_coh - I_inc']
        pw,ph,gap=300,534,18
        canvas=Image.new('RGB',(3*pw+4*gap,2*(ph+77)+150),(12,16,24))
        dr=ImageDraw.Draw(canvas)
        dr.text((gap,18),f'M{milestone:02d} / COMPUTED WAVE FIELDS',font=font(25),fill=(235,241,250))
        dr.text((gap,55),'Same spatial window. Scalar intensity before bloom, exposure or color mapping.',font=font(17),fill=(167,183,204))
        for j,a in enumerate(arrays):
            rgb=signed(a,cross_scale) if j==5 else heat(a,scale)
            im=Image.fromarray(rgb).resize((pw,ph),Image.Resampling.LANCZOS)
            x=gap+(j%3)*(pw+gap);y=96+(j//3)*(ph+77)
            canvas.paste(im,(x,y))
            dr.text((x,y+ph+8),labels[j],font=font(17),fill=(231,236,248))
            dr.text((x,y+ph+33),subtitle[j],font=font(16),fill=(145,166,194))
        y=canvas.height-46
        dr.text((gap,y),f'Intensity panels share sqrt scaling; reference {scale:.4g}.',font=font(16),fill=(167,183,204))
        dr.text((gap,y+22),'Cross terms: blue = destructive, amber = constructive, black = zero.',font=font(16),fill=(167,183,204))
        canvas.save(target)
        residual=float(np.max(np.abs(coh-inc-cross)))
        return {'milestone':milestone,'frame':int(source.stem.split('-')[1]),'shape':list(coh.shape),
                'intensityDisplayReference':scale,'crossDisplayReference':cross_scale,
                'crossIdentityMaxError':residual,'image':target.name}


def build(workspace,version,name=None):
    w=Path(workspace);suffix=f'-{name}' if name else ''
    out=w/f'status/diagnostics{suffix}';out.mkdir(exist_ok=True)
    sources=sorted((w/'simulation'/version).glob('field-*.npz'))
    if len(sources)!=6:raise ValueError('All six numerical snapshots are required.')
    plates=[]
    for i,p in enumerate(sources):
        plates.append(plate(p,out/f'M{i+1:02d}-fields.png',i+1))
        print(f'Field plate {i+1}/6',flush=True)
    (w/f'qa/field-plates{suffix}.json').write_text(json.dumps(plates,indent=2)+'\n')
    checks=json.loads((w/'qa/numerical-verification.json').read_text())
    selections=json.loads((w/'selections.json').read_text())
    rows=''.join(f'<tr><td>{html.escape(k)}</td><td>{v:.3g}</td><td>{checks["thresholds"][k]:.3g}</td></tr>' for k,v in checks['values'].items())
    figures=''.join(f'<figure id="m{p["milestone"]}"><img loading="lazy" src="diagnostics{suffix}/{p["image"]}" alt="Computed branch intensities and interference at milestone {p["milestone"]}"><figcaption>Frame {p["frame"]}, {p["frame"]/30:.1f} seconds. Numerical grid {p["shape"][1]} by {p["shape"][0]}. Cross-term identity error: {p["crossIdentityMaxError"]:.3g}.</figcaption></figure>' for p in plates)
    lineage=''.join(f'<li><strong>{r["selected"]}</strong> — {html.escape(r["reason"])}</li>' for r in selections)
    doc='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Wavefield / calculations</title><style>
body{margin:0;background:#0c1018;color:#e7ecf6;font:17px/1.65 system-ui,sans-serif}main{max-width:1000px;margin:0 auto;padding:44px 22px}h1{font-size:clamp(32px,5vw,58px);font-weight:500;letter-spacing:-.04em;margin:.2em 0}h2{font-size:24px;font-weight:500;margin-top:2em}p{max-width:800px;color:#b8c6da}a{color:#9adce8}pre{white-space:pre-wrap;background:#151d2b;padding:22px;border:1px solid #2a374b;border-radius:12px;font-size:16px}table{width:100%;border-collapse:collapse;font-size:14px}td,th{padding:10px;text-align:left;border-bottom:1px solid #2b3444}figure{margin:32px 0}img{width:100%;height:auto;border:1px solid #253248;border-radius:10px}figcaption{font-size:14px;color:#a8b9cf;margin-top:8px}li{margin:14px 0;color:#b8c6da}.eyebrow{font-size:12px;letter-spacing:.17em;text-transform:uppercase;color:#8ea6c7}nav{display:flex;gap:18px;flex-wrap:wrap}strong{color:#edf3ff}</style></head><body><main>
<div class="eyebrow">Wavefield / calculation notebook</div><h1>What the light is doing</h1>
<p>The film's luminous material is treated as three overlapping complex scalar fields. Brightness follows the squared magnitude of their summed amplitudes. Their relative phase creates real positive and negative interference terms.</p>
<nav><a href="index.html">Production status</a><a href="#verification">Numerical checks</a><a href="#lineage">Image lineage</a></nav>
<h2>The calculation</h2><pre>psi_j = sqrt(L_j / 3) exp(i phi_j)
psi_j(z) = IFFT[ FFT(psi_j) exp(-i z (kx² + ky²) / (2 k0)) ]
I_coherent = |psi_1 + psi_2 + psi_3|²
I_incoherent = |psi_1|² + |psi_2|² + |psi_3|²
I_cross = I_coherent - I_incoherent</pre>
<p>Generated images supply changing boundary amplitudes. Dense optical flow carries their folds between six selected states. Camera travel, phase disturbances at the six clicks, color, glow, disappearance and white expansion are authored. The propagation uses a padded periodic FFT grid in dimensionless coordinates.</p>
<p>This is a scalar optical construction and an abstract film. It does not implement GRW, CSL or Diósi–Penrose collapse dynamics. Numerical verification checks the stated calculation; it does not establish a physical collapse mechanism.</p>
<p>Optical reference: <a href="https://www.mit.edu/~birge/formulas/fourieroptics.pdf">MIT Fourier optics formulas</a>.</p>
<h2>Six field snapshots</h2><p>Compare the bottom-left and bottom-center panels. Their difference is the interference contribution at bottom right. All intensity panels within a plate use the same display scale. The retained numerical arrays contain the unscaled values.</p>'''+figures+'''
<h2 id="verification">Numerical checks</h2><table><thead><tr><th>Check</th><th>Measured error</th><th>Limit</th></tr></thead><tbody>'''+rows+'''</tbody></table>
<p>These controlled tests use independent analytic Gaussian and plane-wave solutions, reversibility, energy conservation, constructive/destructive interference, grid refinement and a Helmholtz comparator. They are distinct from the measurements on the film's changing source fields.</p>
<h2 id="lineage">Six selections from twelve images</h2><ol>'''+lineage+'''</ol><p>Both candidates, exact prompts, original source hashes and selection lineage are preserved. The built-in image tool does not expose its resolved model or itemized billing; those remain unknown in the private records.</p>
</main></body></html>'''
    if name=='v2':
        doc=doc.replace('<h2>Six field snapshots</h2>',
            '<h2>The revised approach</h2><p>Version 2 tracks the same bright intersection through all six image anchors. '
            'The camera reaches a scale of 3.3 at four seconds and 42 just before the final click. '
            'At close range, curved strand masks resolve the crossing, with 84 inward-moving Gaussian packets '
            'and 24 secondary strands that converge and vanish. These are authored amplitude controls. '
            'Every resulting complex field still passes through the numerical propagator before interference is evaluated.</p>'
            '<p>Cyan, violet and amber identify overlapping branches. Colored pulse fronts follow the click-driven phase disturbances. '
            'Packet removal is an artistic absorption rule, not a prediction of a collapse theory. '
            '<a href="calculation.html">The first draft\'s calculation notebook remains available.</a></p><h2>Six field snapshots</h2>')
    (w/f'status/calculation{suffix}.html').write_text(doc)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workspace',default='data/workspace/wavefield-v1');p.add_argument('--version',default='picture-v1');p.add_argument('--name')
    a=p.parse_args();build(a.workspace,a.version,a.name)
