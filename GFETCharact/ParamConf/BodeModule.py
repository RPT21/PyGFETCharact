#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 13:08:01 2022

@author: aguimera
"""

import pyqtgraph.parametertree.parameterTypes as pTypes
import numpy as np
import matplotlib.pyplot as plt


BodeParams = ({'name': 'FreqMin',
               'title': 'Start Freq.',
               'type': 'float',
               'value': 1,
               'default': 1,
               'limits': (0.001, 100e3),
               'siPrefix': True,
               'suffix': 'Hz'},
              {'name': 'FreqMax',
               'title': 'Stop Freq',
               'type': 'float',
               'value': 10e3,
               'default': 10e3,
               'limits': (0.001, 100e3),
               'siPrefix': True,
               'suffix': 'Hz'},
              {'name': 'nFreqs',
               'type': 'int',
               'value': 50,
               'limits': (3, 200),
               'default': 50},
              {'name': 'Amp',
               'title': 'Harmonic Amplitude',
               'type': 'float',
               'value': 0.002,
               'default': 0.002,
               'step': 1e-3,
               'limits': (100e-6, 1),
               'siPrefix': True,
               'suffix': 'V'},
              {'name': 'nAvg',
               'title': 'Averaging',
               'type': 'int',
               'value': 2,
               'limits': (1, 20),
               'default': 2},
              {'name': 'FreqSplit',
               'title': 'Split Freq',
               'type': 'float',
               'value': 10,
               'default': 10,
               'limits': (0.001, 100e3),
               'siPrefix': True,
               'suffix': 'Hz'},
              {'name': 'FsHigh',
               'title': 'Single Channel Fs',
               'type': 'float',
               'value': 500e3,
               'default': 500e3,
               'readonly': True,
               'siPrefix': True,
               'suffix': 'Hz'},
              {'name': 'FsLow',
               'title': 'Multiple Channels Fs',
               'type': 'float',
               'value': 30e3,
               'default': 30e3,
               'limits': (100, 100e3),
               'siPrefix': True,
               'suffix': 'Hz'},
              {'name': 'PhOptim',
               'title': 'Optimize Phase',
               'type': 'bool',
               'value': False,
               'default': False},
              {'name': 'Plot',
               'title': 'Plot Test Signals',
               'type': 'action'},
              {'name': 'acqTime',
               'readonly': True,
               'type': 'float',
               'suffix': 's'},
              {'name': 'TestSigs',
               'title': 'Test Signals',
               'type': 'group',
               'expanded': False,
               'children': (
                            )}
              )


def CalcCoherentSweepFreqs(Freqs, Fs, **kwargs):
    FreqMin = np.min(Freqs)
    FreqMax = np.max(Freqs)
    nFreqs = len(Freqs)

    nFFT = int(2**((np.around(np.log2(Fs/FreqMin))+1)+2))

    nmin = (FreqMin*(nFFT))/Fs
    nmax = (FreqMax*(nFFT))/Fs

    ns = np.round(np.logspace(np.log10(nmin),
                              np.log10(nmax),
                              nFreqs),
                  0)

    wsFreqs = (float(Fs)/(nFFT))*np.unique(ns)
    fftfreqs = np.fft.rfftfreq(nFFT, 1/float(Fs))
    FFTInds = np.where(np.in1d(fftfreqs, wsFreqs))[0]

    BodeSignalConf = {'Freqs': wsFreqs,
                      'nFFT': nFFT,
                      'Fs': Fs,
                      'FFTInds': FFTInds}

    return BodeSignalConf


def CalcFFTavg(Data, nFFT=-1, nAvg=-1):
    a = Data.reshape((nAvg, nFFT))
    acc = np.zeros(((nFFT//2)+1))
    for w in a:
        acc = acc + (2 * np.fft.rfft(w, nFFT) / nFFT)
    return acc/nAvg


def GenSignal(Freqs, nFFT, Fs, Amp, FFTInds, PhOptim, nAvg=1, **kwargs):
    Ts = 1/float(Fs)
    Ps = nFFT * nAvg * Ts

    # Amp = Arms*np.sqrt(2)
    t = np.arange(0, Ps, Ts)

    if PhOptim:
        phs = []
        amps = []
        for i in range(10):
            Phs = np.random.rand(len(Freqs))*2*np.pi - np.pi
            phs.append(Phs)
            Signal = np.zeros(t.size)
            for f, p in zip(Freqs, Phs):
                s = Amp * np.cos(f * 2 * np.pi * t + p)
                Signal = Signal + s
            amps.append(np.max(Signal) + np.abs(np.min(Signal)))
        print(amps)
        Phs = phs[np.argmin(amps)]
    else:
        Phs = np.zeros((len(Freqs)))

    Signal = np.zeros(t.size)
    for f, p in zip(Freqs, Phs):
        s = Amp * np.cos(f * 2 * np.pi * t + p)
        Signal = Signal + s

    Signal[-1] = 0
    FFTAmps = CalcFFTavg(Signal, nFFT, nAvg)[FFTInds]
    Vpp = np.max(Signal) + np.abs(np.min(Signal))

    BodeSignalConf = {'Freqs': Freqs,
                      'Phs': Phs,
                      'nFFT': nFFT,
                      'Fs': Fs,
                      'FFTInds': FFTInds,
                      'Signal': Signal,
                      'FFTAmps': FFTAmps,
                      'Vpp': Vpp,
                      'acqTime': t[-1],
                      'times': t}

    return BodeSignalConf


SignalInfoParamsFloat = ('nFFT',
                         'Fs',
                         'Vpp',
                         'acqTime',
                         'Sequential')

SignalInfoParamsText = ('Freqs',
                        'Phs',
                        'FFTAmps',
                        )


class BodeConfig(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        self.BodeSignalConfs = None
        self.BodeKwargs = None
        self.Axs = None
        self.SigFig = None
        self.addChildren(BodeParams)

        self.param('FreqMin').sigValueChanged.connect(self.on_change)
        self.param('FreqMax').sigValueChanged.connect(self.on_change)
        self.param('nFreqs').sigValueChanged.connect(self.on_change)
        self.param('FsHigh').sigValueChanged.connect(self.on_change)
        self.param('FsLow').sigValueChanged.connect(self.on_change)
        self.param('FreqSplit').sigValueChanged.connect(self.on_change)
        self.param('nAvg').sigValueChanged.connect(self.on_change)
        self.param('Amp').sigValueChanged.connect(self.on_change)
        self.param('PhOptim').sigValueChanged.connect(self.on_change)

        self.param('Plot').sigActivated.connect(self.on_plot)

        self.on_change()

    def GetParams(self):
        BodeKwargs = {}
        for p in self.children():
            if p.type() == 'group':
                continue
            BodeKwargs[p.name()] = p.value()
        return BodeKwargs

    def GetTestSignals(self):
        Freqs = np.hstack([s['Freqs'] for s in self.BodeSignalConfs])
        return {'Freqs': Freqs,
                'TestSigs': self.BodeSignalConfs}

    def UpdateAcqTime(self, nChannels=16):
        acqTime = 0
        for s in self.BodeSignalConfs:
            if s['Sequential']:
                acqTime += s['acqTime'] * nChannels
            else:
                acqTime += s['acqTime']
        self.param('acqTime').setValue(acqTime)

    def on_change(self):
        swFreqMin = self.param('FreqMin').value()
        swFreqMax = self.param('FreqMax').value()
        swnFreqs = self.param('nFreqs').value()
        FsHigh = self.param('FsHigh').value()
        FsLow = self.param('FsLow').value()
        FreqSplit = self.param('FreqSplit').value()
        nAvg = self.param('nAvg').value()
        Amp = self.param('Amp').value()
        PhOptim = self.param('PhOptim').value()

        self.BodeKwargs = self.GetParams()

        fsweep = np.logspace(np.log10(swFreqMin),
                             np.log10(swFreqMax),
                             swnFreqs)

        sw1 = fsweep[np.where(fsweep < FreqSplit)]
        sw2 = fsweep[np.where(fsweep > FreqSplit)]

        self.BodeSignalConfs = []
        if len(sw1) > 0:
            BConf = GenSignal(Amp=Amp,
                              nAvg=nAvg,
                              PhOptim=PhOptim,
                              **CalcCoherentSweepFreqs(sw1,
                                                       FsLow))
            BConf['Sequential'] = 0
            self.BodeSignalConfs.append(BConf)

        if len(sw2) > 0:
            BConf = GenSignal(Amp=Amp,
                              nAvg=nAvg,
                              PhOptim=PhOptim,
                              **CalcCoherentSweepFreqs(sw2,
                                                       FsHigh))
            BConf['Sequential'] = 1
            self.BodeSignalConfs.append(BConf)

        self.param('TestSigs').clearChildren()
        for isc, s in enumerate(self.BodeSignalConfs):
            sstr = 'Sig{}'.format(isc)
            pars = []
            self.param('TestSigs').addChild({'name': sstr,
                                             'type': 'group',
                                             'expanded': False,
                                             'children': ()})
            for p in SignalInfoParamsFloat:
                pars.append({'name': p,
                             'type': 'float',
                             'value': s[p],
                             'readonly': True,
                             'siPrefix': True})
            for p in SignalInfoParamsText:
                pars.append({'name': p,
                             'type': 'text',
                             'value': str(s[p]),
                             'readonly': True,
                             'expanded': False})
            self.param('TestSigs').param(sstr).addChildren(pars)
        self.UpdateAcqTime()

    def on_plot(self):
        self.SigFig, axs = plt.subplots(len(self.BodeSignalConfs), 3)
        self.Axs = axs.flatten()
        Amp = self.param('Amp').value()

        for ix, s in enumerate(self.BodeSignalConfs):
            ax = self.Axs[(ix*3)]
            ax.plot(s['times'], s['Signal'])
            ax.set_xlabel('Time [s]')
            ax.set_ylabel('Amp [V]')

            ax = self.Axs[(ix*3)+1]
            ax.semilogx(s['Freqs'], np.real(s['FFTAmps']), 'k*', label='Real')
            ax.semilogx(s['Freqs'], np.imag(s['FFTAmps']), 'r*', label='Img')
            ax.set_ylabel('Amp [V]')
            ax.set_xlabel('Freq [Hz]')
            ax.legend()

            ax = self.Axs[(ix*3)+2]
            axp = plt.twinx(ax)
            ax.semilogx(s['Freqs'], np.abs(s['FFTAmps']), 'k*', label='Mag')
            axp.semilogx(s['Freqs'], np.angle(s['FFTAmps'], deg=True),
                         'r*', label='Ph')
            ax.set_ylabel('Amp [V]')
            axp.set_ylabel('Ph [º]')
            ax.set_xlabel('Freq [Hz]')
            ax.set_ylim((Amp-Amp*0.1, Amp+Amp*0.1))
            ax.legend()

        plt.tight_layout()
        plt.show()





