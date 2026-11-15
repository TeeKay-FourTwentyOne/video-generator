#!/usr/bin/env python3
"""A tracked approach into one junction, with authored absorbing wave packets.

The scalar propagation and interference are numerical. Camera, chromatic display,
macro strand masks and removal of arriving packets are artistic boundary controls.
"""
from pathlib import Path
import json

import cv2
import numpy as np
from scipy.interpolate import PchipInterpolator

import render
from render import Film, smooth, display, digest, CLICKS
from field import interference


class RevisionFilm(Film):
    preview_times=[0,.8,2,4,6,8,10,12,14,16,18,20,21.0,21.7,22.07,22.4,23.0,23.6]
    camera_times=[0,.8,2,4,6,9,12,15,18,20,21.9,22.12]
    camera_zooms=[1.12,1.35,2,3.3,4.6,7,10,16,24,32,42,43]
    anchor_times=[0,1.4,3.1,5,7.1,9.5]
    packet_births=[8.6,10,11.2,12.5,13.5,14.5,15.4,16.3,17.1,17.9,18.6,19.3,20,20.6]
    palette=np.array([[.05,.8,1],[.32,.10,1],[1,.08,.45],[1,.48,.045],[.08,.9,1],[1,.7,.28]],np.float32)

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.boundary.times=np.array(self.anchor_times)
        self.camera=PchipInterpolator(self.camera_times,self.camera_zooms)
        self.focus_file=self.ws/'revisions/v2/focus-points.json'
        rows=json.loads(self.focus_file.read_text())
        self.focus_points=np.array([r['world'] for r in rows],np.float32)
        self.branch_angles=[.11,-.91,1.18]
        self.rr=np.sqrt(self.x*self.x+self.y*self.y+1e-8)

    def focus(self,t):
        i=min(max(0,np.searchsorted(self.anchor_times,t,side='right')-1),5)
        if i==5:return self.focus_points[-1]
        u=float(smooth((t-self.anchor_times[i])/(self.anchor_times[i+1]-self.anchor_times[i])))
        return (1-u)*self.focus_points[i]+u*self.focus_points[i+1]

    def pulses(self,t,nx,ny):
        r=np.sqrt(nx*nx+ny*ny+1e-8)
        phase=np.zeros_like(r);ring=np.zeros_like(r);color=np.zeros((*r.shape,3),np.float32)
        for j,onset in enumerate(CLICKS):
            age=t-onset
            if 0<=age<3.7:
                front=r-age*(2.7+.22*j)
                width=.23+.035*j
                main=np.exp(-.5*(front/width)**2)
                wake=np.exp(-.5*((front+.48)/(width*1.6))**2)
                strength=(.14,.24,.40,.65,.95,1.7)[j]*np.exp(-.35*age)
                envelope=strength*(main+.38*wake)
                phase+=envelope*np.sin(9*front-1.4*age)*(1+.18*j)
                ring+=envelope
                color+=strength*(main[...,None]*self.palette[j]+.32*wake[...,None]*self.palette[(j+1)%6])
        return phase,ring,color

    def scaffold(self,t,j,x,y,zoom):
        theta=self.branch_angles[j]+.035*np.sin(.19*t+j)
        s=np.cos(theta)*x+np.sin(theta)*y
        d=-np.sin(theta)*x+np.cos(theta)*y
        d+=(.16,-.19,.145)[j]*s*s/(1+.20*np.abs(s))
        width=.065+.0105*zoom
        # The apparent microscope reveals curved sub-strands within the same node.
        filaments=.40+.60*(.5+.5*np.cos(44*d/(1+.025*zoom)+.15*s-.35*t))**3
        primary=np.exp(-.5*(d/width)**2)*filaments
        ribs=.46*primary
        ghost_count=0
        for m in [-4,-3,-2,-1,1,2,3,4]:
            start=9.0+.65*abs(m)+.24*j
            progress=float(smooth((t-start)/(7.9-.65*abs(m))))
            alive=1-float(smooth((progress-.68)/.32))
            if alive<1e-5:continue
            ghost_count+=1
            offset=m*(.27+.019*zoom)*(1-.94*progress)
            center=d-offset*(1+.08*np.sin(.65*s+.25*t+m))
            ribs+=.17*alive*np.exp(-.5*(center/(width*.35+.018))**2)
        packets=np.zeros_like(x);absorbed=0;active=0
        for k,birth in enumerate(self.packet_births):
            birth+=.13*j
            duration=2.65-1.65*k/(len(self.packet_births)-1)
            q=(t-birth)/duration
            if q>=1:
                absorbed+=2;continue
            if q<0:continue
            active+=2
            distance=(7.8-.08*k)*(1-q)**1.35
            along=np.exp(-.5*((np.abs(s)-distance)/(.13+.16*(1-q)))**2)
            across=np.exp(-.5*(d/(width*.54+.025))**2)
            # Each arriving packet fades at the junction instead of emerging on the other side.
            gate=float(smooth(q/.11))*(1-float(smooth((q-.91)/.09)))
            packets+=1.6*gate*along*across
        # Outer haze drains away while the actual crossing remains until the click.
        haze=.045*(1-float(smooth((t-11)/9)))
        return ribs+packets+haze,packets,ghost_count,active,absorbed

    def fields(self,t):
        p=float(np.clip(t/22,0,1));zoom=float(self.camera(t))
        target=self.focus(t);lock=float(smooth(t/6.4));center=target*lock
        node=(target-center)*zoom
        nx=self.x-node[0];ny=self.y-node[1]
        source=self.boundary.at(t)
        macro=float(smooth((t-7)/7))
        phase_ripple,ring,pulse_color=self.pulses(t,nx,ny)
        breath=.028*np.sin(.43*t+1.4*ny)+.016*np.sin(.67*t-.8*nx)
        separation=(.13+.05*np.sin(.22*t))*(1-float(smooth((t-7)/13)))
        fields=[];colors=[];errors=[];packets=[];ghosts=active=absorbed=0
        for j,off in enumerate([-1,0,1]):
            # Track the selected bright intersection, rather than zooming about the image center.
            ox=off*separation;oy=off*separation*.45
            local_x=self.x-ox;local_y=self.y-oy
            displacement=(breath+.075*ring)*(1-macro*.75)
            sx=(local_x+displacement*nx/(self.rr+.5))/zoom+center[0]
            sy=(local_y+displacement*ny/(self.rr+.5))/zoom+center[1]
            rgb=cv2.remap(source,(sx/self.dx+self.fw/2).astype(np.float32),
                          (sy/self.dx+self.fh/2).astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
            lum=np.maximum(rgb @ np.array([.2126,.7152,.0722],np.float32),0)
            scaffold,packet,g,a,ab=self.scaffold(t,j,nx-ox,ny-oy,zoom)
            ghosts+=g;active+=a;absorbed+=ab;packets.append(packet)
            boundary_intensity=lum*((1-macro)+macro*scaffold)
            boundary_intensity*=1+.65*ring
            phase=off*((3.0+1.5*macro)*nx+(1.8+.7*macro)*ny+(.045+.12*macro)*(nx*nx-ny*ny))
            phase+=(.24,-.13,.37)[j]*t+(.15,0,-.35)[j]+phase_ripple*(1+.22*off)
            psi=(np.sqrt(np.maximum(boundary_intensity,0)/3)*np.exp(1j*phase)).astype(np.complex64)
            padded=np.pad(psi,((self.pad[0],self.pad[0]),(self.pad[1],self.pad[1])))
            propagated=self.op.propagate(padded,.08+.16*p+.012*j)
            before=np.sum(np.abs(padded)**2,dtype=np.float64);after=np.sum(np.abs(propagated)**2,dtype=np.float64)
            errors.append(float(abs(after/max(before,1e-20)-1)))
            fields.append(propagated[self.crop]);colors.append(rgb)
        fields=np.stack(fields)
        total,coherent,incoherent,cross=interference(fields)
        color=np.mean(colors,axis=0);luma=color @ np.array([.2126,.7152,.0722],np.float32)
        chroma=np.clip(color/(luma[...,None]+.008),.30,1.8)
        relphase=np.angle(total)
        tint=np.stack([.72+.24*np.cos(relphase+1.5),.72+.24*np.cos(relphase),.88+.12*np.cos(relphase-1.4)],axis=-1)
        branch_palette=np.array([[.14,.85,1],[.8,.18,1],[1,.58,.18]],np.float32)
        branch_color=np.einsum('jhw,jc->hwc',np.abs(fields)**2,branch_palette)/(incoherent[...,None]+1e-6)
        base_color=chroma*(1-.8*macro)+branch_color*(.8*macro)
        base_color*=.9+.1*tint
        packet_sum=np.sum(packets,axis=0)
        packet_tint=np.stack([.55+.4*np.cos(.7*t),.48+.42*np.cos(.7*t+2.1),.65+.32*np.cos(.7*t+4.2)])
        pulse_hue=pulse_color/(np.max(pulse_color,axis=-1)[...,None]+1e-6)
        pulse_blend=np.clip(ring*2.2,0,.95)[...,None]
        base_color=base_color*(1-pulse_blend)+1.5*pulse_hue*pulse_blend
        base_color+=macro*.24*packet_sum[...,None]*packet_tint
        rgb=coherent[...,None]*base_color
        visible=np.power(np.clip(incoherent,0,1),.55)
        # Ring color is a display cue tied to the propagated material, plus a faint free-space halo.
        rgb+=pulse_color*(.20*visible[...,None]+.025)
        self.last_stats={'time':float(t),'energyRelativeErrorMax':max(errors),
            'crossIdentityMaxError':float(np.max(np.abs(coherent-incoherent-cross))),
            'coherentPower':float(np.sum(coherent,dtype=np.float64)),
            'incoherentPower':float(np.sum(incoherent,dtype=np.float64)),
            'zoom':zoom,'focusSourceWorld':target.tolist(),'junctionScreenWorld':node.tolist(),
            'macroMaskBlend':macro,'remainingGhostStrands':ghosts,'activeInwardPackets':active,
            'absorbedPackets':absorbed,'rippleMax':float(ring.max()),'finite':bool(np.isfinite(rgb).all())}
        self.last_fields={'branches':fields,'coherent':coherent,'incoherent':incoherent,'cross':cross,
                          'phase':relphase,'authoredPackets':packet_sum}
        return rgb

    def frame(self,frame):
        t=frame/30
        if t>=22.12:return self.ending(t)
        rgb=self.fields(t)
        gain=.65+.48*float(smooth(t/13))
        if t>=22:gain*=max(0,1-(t-22)/.12)**2
        rgb*=gain
        rgb+=.24*cv2.GaussianBlur(rgb,(0,0),1.4)+.09*cv2.GaussianBlur(rgb,(0,0),7)
        rgb=display(1-np.exp(-rgb*2.45))
        rgb=cv2.resize(rgb,(self.width,self.height),interpolation=cv2.INTER_CUBIC)
        return np.uint8(np.clip(rgb*255+.5,0,255))

    def recipe_metadata(self):
        return {'revision':'v2','cameraTimes':self.camera_times,'cameraZooms':self.camera_zooms,
                'boundaryAnchorTimes':self.anchor_times,'focusPointsFile':str(self.focus_file.relative_to(self.ws)),
                'focusPointsSha256':digest(self.focus_file),'packetBirths':self.packet_births,
                'authoredControls':['camera tracking','strand masks','inward wave packet envelopes and absorption','phase ripples and display color'],
                'physicalLimits':'Paraxial scalar propagation per frame; authored absorption is not an objective-collapse law.'}


if __name__=='__main__':
    render.main(RevisionFilm,__file__,snapshots=(0,120,240,420,540,645))
