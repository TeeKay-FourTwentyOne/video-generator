#!/usr/bin/env python3
"""Complex scalar Fresnel propagation, with explicit coherent cross terms.

Units are dimensionless. This is a boundary-driven optical construction, not an
objective-collapse simulation. Display geometry and detector ending are authored.
"""
import numpy as np
from scipy.fft import fft2, ifft2, fftfreq


class Fresnel:
    def __init__(self, shape, spacing, k0=1600.0, workers=2):
        self.shape = tuple(shape)
        self.spacing = float(spacing)
        self.k0 = float(k0)
        self.workers = workers
        ky = 2 * np.pi * fftfreq(shape[0], spacing)
        kx = 2 * np.pi * fftfreq(shape[1], spacing)
        self.k2 = ky[:, None] ** 2 + kx[None, :] ** 2

    def propagate(self, field, distance):
        """Unitary periodic-grid paraxial propagator, carrier phase removed."""
        transfer = np.exp(-.5j * distance * self.k2 / self.k0).astype(field.dtype)
        return ifft2(fft2(field, workers=self.workers) * transfer, workers=self.workers)

    def exact(self, field, distance):
        """Band-limited Helmholtz comparator; evanescent modes decay forward."""
        kz = np.sqrt((self.k0 ** 2 - self.k2).astype(np.complex128))
        transfer = np.exp(1j * distance * (kz - self.k0))
        return ifft2(fft2(field) * transfer)


def interference(branches):
    total = np.sum(branches, axis=0)
    coherent = np.abs(total) ** 2
    incoherent = np.sum(np.abs(branches) ** 2, axis=0)
    cross = np.zeros_like(coherent)
    for j in range(len(branches)):
        for k in range(j + 1, len(branches)):
            cross += 2 * np.real(branches[j] * np.conjugate(branches[k]))
    return total, coherent, incoherent, cross


def phase_screen(x, y, time, clicks=(2, 6, 10, 14, 18, 22)):
    """Smooth, finite-speed ring disturbances; click timing is authored."""
    r = np.sqrt((x + .35) ** 2 + (y - .4) ** 2 + 1e-9)
    phase = np.zeros_like(x)
    displacement = np.zeros_like(x)
    for j, onset in enumerate(clicks):
        age = time - onset
        if 0 <= age < 5:
            strength = (.025, .07, .18, .42, .9, 1.9)[j]
            front = r - age * (2.1 + .12 * j)
            ring = np.exp(-front ** 2 / (.25 + .055 * j))
            carrier = np.sin(7.5 * front - 1.2 * age)
            phase += strength * ring * carrier * np.exp(-age * .13)
            displacement += strength * ring * np.sin(4.8 * front) * np.exp(-age * .15)
    return phase, displacement


def verify():
    """Independent analytic identities, reversibility and discretization checks."""
    rng = np.random.default_rng(20261114)
    n, dx, k0 = 128, .1, 1600.
    op = Fresnel((n, n), dx, k0)
    yy, xx = np.mgrid[:n, :n]
    x, y = (xx - n // 2) * dx, (yy - n // 2) * dx
    a = np.exp(-(x*x + y*y) / (2 * .7**2)).astype(np.complex128)
    z = 300.
    out = op.propagate(a, z)
    norm_error = float(abs(np.sum(abs(out)**2) / np.sum(abs(a)**2) - 1))
    reverse_error = float(np.linalg.norm(op.propagate(out, -z) - a) / np.linalg.norm(a))
    sigma2 = .7**2
    q = 1 + 1j * z / (k0 * sigma2)
    analytic = np.exp(-(x*x+y*y)/(2*sigma2*q))/q
    gaussian_error = float(np.linalg.norm(out-analytic)/np.linalg.norm(analytic))
    plane = np.exp(2j * np.pi * (3*xx/n + 4*yy/n))
    expected = plane * np.exp(-.5j*z*((2*np.pi*3/(n*dx))**2+(2*np.pi*4/(n*dx))**2)/k0)
    plane_error = float(np.max(np.abs(op.propagate(plane, z)-expected)))
    branches = rng.normal(size=(3, n, n)) + 1j*rng.normal(size=(3, n, n))
    _, coherent, incoherent, cross = interference(branches)
    cross_error = float(np.max(np.abs(coherent-incoherent-cross)))
    destructive = float(np.max(interference(np.stack([a,-a]))[1]))
    constructive = float(np.max(np.abs(interference(np.stack([a,a]))[1]-4*np.abs(a)**2)))
    # Same physical domain, doubled sampling; compare at coincident grid points.
    hi = Fresnel((2*n, 2*n), dx/2, k0)
    hy,hx = np.mgrid[:2*n,:2*n]
    ah = np.exp(-(((hx-n)*dx/2)**2+((hy-n)*dx/2)**2)/(2*.7**2)).astype(np.complex128)
    high = hi.propagate(ah,z)[::2,::2]
    refinement = float(np.linalg.norm(out-high)/np.linalg.norm(high))
    exact_error = float(np.linalg.norm(out-op.exact(a,z))/np.linalg.norm(out))
    thresholds = {'normRelativeError':1e-12, 'roundTripRelativeError':1e-12,
                  'analyticGaussianRelativeError':1e-10, 'planeWaveMaxError':1e-12,
                  'crossTermMaxError':1e-12, 'destructiveResidual':1e-20,
                  'constructiveMaxError':1e-12, 'gridRefinementRelativeError':1e-10,
                  'paraxialVsHelmholtzGaussianRelativeError':1e-5}
    values = dict(zip(thresholds,[norm_error,reverse_error,gaussian_error,plane_error,cross_error,
                                 destructive,constructive,refinement,exact_error]))
    return {'method':'Periodic FFT Fresnel propagator; independent Gaussian and plane-wave solutions',
            'values':values, 'thresholds':thresholds,
            'passed':all(values[k] <= thresholds[k] for k in values),
            'limits':['The analytic checks validate the propagator, not a collapse theory.',
                      'Generated source masks, camera motion, pulse phase screens and final disappearance are authored.',
                      'The film changes boundary apertures with time; norm conservation is checked per propagation, not across those changes.']}
