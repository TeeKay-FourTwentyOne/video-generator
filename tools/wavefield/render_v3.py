#!/usr/bin/env python3
"""Slow only the opening camera growth, smoothly returning to v2 at frame 250."""
import numpy as np

import render
from render_v2 import RevisionFilm


class SlowerOpeningFilm(RevisionFilm):
    hold_until=3.0
    rejoin=250/30
    opening_ratio=2/3
    preview_times=[0,.8,2,3,4,6,8,250/30]

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.v2_camera=self.camera
        self.camera=self.slower_camera

    def slower_camera(self,t):
        original=float(self.v2_camera(t))
        if t>=self.rejoin:return original
        u=float(np.clip((t-self.hold_until)/(self.rejoin-self.hold_until),0,1))
        # Quintic ease has zero first and second derivatives at both ends.
        blend=u*u*u*(10+u*(-15+6*u))
        ratio=self.opening_ratio+(1-self.opening_ratio)*blend
        return self.camera_zooms[0]+(original-self.camera_zooms[0])*ratio

    def recipe_metadata(self):
        d=super().recipe_metadata()
        d.update(revision='v3',openingZoomIncrementRatio=self.opening_ratio,
                 ratioHoldThroughSeconds=self.hold_until,rejoinV2AtFrame=250,
                 cameraFormula='z0 + (z_v2(t)-z0) * (2/3 + smootherstep((t-3)/(250/30-3))/3)',
                 unchangedControls='Image evolution, phase, ripple times, color, packets, absorption and ending use v2 timeline time.')
        return d


if __name__=='__main__':
    render.main(SlowerOpeningFilm,__file__,snapshots=(0,120,240))
