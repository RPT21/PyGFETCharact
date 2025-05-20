# -*- coding: utf-8 -*-
"""
Created on Wed Dec 18 09:25:47 2019

@author: Lucia
"""

import pyqtgraph.parametertree.parameterTypes as pTypes
import numpy as np

from GFETCharact.ParamConf.BodeModule import BodeConfig

###############################################################################
# Generic voltage sweep
###############################################################################

VoltageSweepParams = ({'name': 'Start',
                       'type': 'float',
                       'value': 0,
                       'default': 0,
                       'step': 0.01,
                       'siPrefix': True,
                       'suffix': 'V'},
                      {'name': 'Stop',
                       'type': 'float',
                       'value': 0.4,
                       'default': 0.4,
                       'step': 0.01,
                       'siPrefix': True,
                       'suffix': 'V'},
                      {'name': 'bPoints',
                       'title': 'Fixed points',
                       'type': 'bool',
                       'value': True,
                       'default': True},
                      {'name': 'Points',
                       'type': 'int',
                       'value': 20,
                       'step': 1,
                       'default': 20,
                       'suffix': 'Points',
                       'readonly': False},
                      {'name': 'bStep',
                       'title': 'Fixed step',
                       'type': 'bool',
                       'value': False,
                       'default': False},
                      {'name': 'Step',
                       'type': 'float',
                       'value': 0.01,
                       'siPrefix': True,
                       'step': 0.005,
                       'suffix': 'V',
                       'readonly': True},
                      {'name': 'Sweep',
                       'title': 'Sweep Points',
                       'type': 'text',
                       'expanded': False,
                       'readonly': True}
                      )


class VoltageSweepConfig(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        self.addChildren(VoltageSweepParams)

        self.param('bPoints').sigValueChanged.connect(self.on_bPoints)
        self.param('bStep').sigValueChanged.connect(self.on_bStep)

        self.param('Start').sigValueChanged.connect(self.CalcSweep)
        self.param('Stop').sigValueChanged.connect(self.CalcSweep)
        self.param('Points').sigValueChanged.connect(self.CalcSweep)
        self.param('Step').sigValueChanged.connect(self.CalcSweep)

        self.CalcSweep()

    def on_bPoints(self, value):
        self.param('bStep').setValue(not value.value(),
                                     blockSignal=self.on_bStep)
        self.param('Step').setOpts(readonly=value.value())
        self.param('Points').setOpts(readonly=not value.value())
        self.CalcSweep()

    def on_bStep(self, value):
        self.param('bPoints').setValue(not value.value(),
                                       blockSignal=self.on_bPoints)
        self.param('Step').setOpts(readonly=not value.value())
        self.param('Points').setOpts(readonly=value.value())
        self.CalcSweep()

    def CalcSweep(self):
        if self.param('bPoints').value():
            sweep = np.linspace(self.param('Start').value(),
                                self.param('Stop').value(),
                                self.param('Points').value())
            if len(sweep) > 1:
                step = np.mean(np.diff(sweep))
            else:
                step = 0
            self.param('Step').setValue(step,
                                        blockSignal=self.CalcSweep)

        else:
            sweep = np.arange(self.param('Start').value(),
                              self.param('Stop').value(),
                              self.param('Step').value())
            self.param('Points').setValue(len(sweep),
                                          blockSignal=self.CalcSweep)

        self.SweepVals = sweep
        self.param('Sweep').setValue(str(sweep))


###############################################################################
# Chracterizacion config
###############################################################################


ACSelectionParams = {'title': 'AC selection points',
                     'name': 'ACSel',
                     'expanded': False,
                     'visible': False,
                     'type': 'group',
                     'children': ({'name': 'nVgs',
                                   'title': 'Vgs points',
                                   'readonly': True,
                                   'type': 'int'},
                                  {'name': 'SelIndex',
                                   'title': 'Vgs indexes',
                                   'type': 'str',
                                   'value': ':'},
                                  {'name': 'ACPoints',
                                   'title': 'AC measures',
                                   'type': 'int',
                                   'readonly': True},
                                  {'name': 'VgsSel',
                                   'title': 'Selected Vgs values',
                                   'readonly': True,
                                   'type': 'text'},
                                  )}

DCMeasureParams = ({'name': 'MaxSlope',
                    'title': 'Maximum Slope',
                    'type': 'float',
                    'value': 1e-8,
                    'step': 1e-9,
                    'default': 1e-8,
                    'siPrefix': True,
                    'suffix': 'A/s'},
                   {'name': 'StabCriteria',
                    'type': 'list',
                    'limits': ['All channels',
                               'One Channel',
                               'Mean'],
                    'value': 'All channels',
                    'default': 'All channels'},
                   {'name': 'TimeOut',
                    'title': 'Maximum Time',
                    'type': 'float',
                    'value': 25,
                    'default': 25,
                    'siPrefix': True,
                    'suffix': 's'},
                   {'name': 'TimeBuffer',
                    'title': 'DC evaluation time',
                    'type': 'float',
                    'value': 1,
                    'default': 1,
                    'siPrefix': True,
                    'suffix': 's',
                    'readonly': True},
                   {'name': 'nSamps',
                    'title': 'Evaluation Samples',
                    'type': 'int',
                    'value': 1000,
                    'default': 1000,
                    'siPrefix': True,
                    'suffix': ' ',
                    'readonly': True},
                   {'name': 'Fs',
                    'title': 'DC Sampling Frequency',
                    'type': 'float',
                    'value': 1000,
                    'default': 1000,
                    'siPrefix': True,
                    'suffix': 'Hz',
                    'readonly': True},
                   )


class DCConfig(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        self.addChildren(DCMeasureParams)

        for p in self.children():
            p.sigValueChanged.connect(self.UpdateParams)

        self.DCKwargs = {}
        self.UpdateParams()

    def UpdateParams(self):
        for p in self.children():
            self.DCKwargs[p.name()] = p.value()

    def GetParams(self):
        return self.DCKwargs


PSDParameters = ({'name': 'Fs',
                  'title': 'Sampling Frequnecy',
                  'type': 'float',
                  'value': 30e3,
                  'default': 30e3,
                  'siPrefix': True,
                  'suffix': 'Hz'},
                 {'name': 'nFFT',
                  'title': 'nFFT 2**x',
                  'type': 'int',
                  'value': 17,
                  'default': 17,
                  'step': 1},
                 {'name': 'Fmin',
                  'type': 'float',
                  'readonly': True,
                  'suffix': 'Hz'},
                 {'name': 'nAvg',
                  'type': 'int',
                  'value': 4,
                  'default': 4,
                  'step': 1},
                 {'name': 'acqTime',
                  'readonly': True,
                  'type': 'float',
                  'siPrefix': True,
                  'suffix': 's'},
                 )


class PSDConfig(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.addChildren(PSDParameters)
        self.param('Fs').sigValueChanged.connect(self.on_nFFTChange)
        self.param('nFFT').sigValueChanged.connect(self.on_nFFTChange)
        self.param('nAvg').sigValueChanged.connect(self.on_nAvgChange)
        self.on_nFFTChange()

    def on_nFFTChange(self):
        Fs = self.param('Fs').value()
        nFFT = self.param('nFFT').value()
        FMin = 1 / (2 ** nFFT / Fs)
        self.param('Fmin').setValue(FMin)
        self.on_nAvgChange()
        self.Freqs = np.fft.rfftfreq(2 ** nFFT, 1 / float(Fs))

    def on_nAvgChange(self):
        Fs = self.param('Fs').value()
        nFFT = self.param('nFFT').value()
        nAvg = self.param('nAvg').value()
        acqTime = ((2 ** nFFT) / Fs) * nAvg
        self.param('acqTime').setValue(acqTime)

    def GetParams(self):
        PSDKwargs = {}
        for p in self.children():
            PSDKwargs[p.name()] = p.value()
        PSDKwargs['Freqs'] = self.Freqs
        return PSDKwargs


InfoParams = ({'title': 'Total Time',
               'name': 'TTime',
               'type': 'float',
               # 'siPrefix': True,
               'suffix': 's',
               'readonly': True},
              {'title': 'DC Time',
               'name': 'DCTime',
               'type': 'float',
               # 'siPrefix': True,
               'suffix': 's',
               'readonly': True},
              {'title': 'AC Time',
               'name': 'ACTime',
               'type': 'float',
               # 'siPrefix': True,
               'suffix': 's',
               'readonly': True},
              )


class SweepsConfig(pTypes.GroupParameter):

    def __init__(self, HardConf, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        HardConf.on_board_sel.connect(self.on_Board_sel)

        # Add paramters
        self.bGate = False
        self.bPSD = False
        self.bBode = False
        self.addChildren(InfoParams)
        self.addChildren(({'title': 'Cycles',
                           'name': 'Cycles',
                           'type': 'int',
                           'default': 1,
                           'value': 1},
                          {'title': 'Measure PSD',
                           'name': 'CheckPSD',
                           'type': 'bool',
                           'value': False},
                          {'title': 'Measure Bode',
                           'name': 'CheckBode',
                           'type': 'bool',
                           'value': False},
                          {'title': 'Measure Gate',
                           'name': 'CheckGate',
                           'type': 'bool',
                           'value': False},
                          ))

        self.addChild(VoltageSweepConfig(name='VgsSweep',
                                         title='Vgs Points',
                                         expanded=True))
        self.addChild(VoltageSweepConfig(name='VdsSweep',
                                         title='Vds Points',
                                         expanded=False))
        self.addChild(DCConfig(name='DCConfig',
                               title='DC Stability Configuration',
                               expanded=False))

        self.addChild(ACSelectionParams)
        self.addChild(BodeConfig(name='BodeConfig',
                                 title='Bode Configuration',
                                 expanded=False,
                                 visible=False))
        self.addChild(PSDConfig(name='PSDConfig',
                                title='PSD Configuration',
                                expanded=False,
                                visible=False))

        self.Cycles = self.param('Cycles')

        # Configure Vds parameters
        self.VdsVals = self.param('VdsSweep')
        self.VdsVals.param('Points').setValue(1)
        self.VdsVals.param('Start').setValue(0.05)
        self.VdsVals.param('Stop').setValue(0.05)
        self.VdsVals.param('Points').setDefault(1)
        self.VdsVals.param('Start').setDefault(0.05)
        self.VdsVals.param('Stop').setDefault(0.05)

        # Singal coonetions
        self.VgsVals = self.param('VgsSweep')
        self.ACSlection = self.param('ACSel')
        self.cBode = self.param('BodeConfig')
        self.cPSD = self.param('PSDConfig')
        self.VgsVals.param('Sweep').sigValueChanged.connect(self.on_VgsSweep)
        self.VdsVals.param('Sweep').sigValueChanged.connect(self.on_VdsSweep)
        self.ACSlection.param('SelIndex').sigValueChanged.connect(self.on_SelIndex)
        self.cBode.param('acqTime').sigValueChanged.connect(self.on_acqTime)
        self.cPSD.param('acqTime').sigValueChanged.connect(self.on_acqTime)
        self.param('DCConfig').param('TimeOut').sigValueChanged.connect(self.on_acqTime)

        self.param('CheckPSD').sigValueChanged.connect(self.on_ACCheck)
        self.param('CheckBode').sigValueChanged.connect(self.on_ACCheck)
        self.param('CheckGate').sigValueChanged.connect(self.on_CheckGate)

        self.on_ACCheck()
        self.on_VgsSweep()
        self.on_CheckGate()
        # self.on_SelIndex()

    def on_Board_sel(self, BoardConf):
        if 'GateGain' in BoardConf.Gains.GetGains():
            self.param('CheckGate').setOpts(**{'visible': True})
        else:
            self.param('CheckGate').setOpts(**{'value': False,
                                               'visible': False})

        if 'Vg' in BoardConf.AOutputs.GetAOuts():
            self.param('CheckBode').setOpts(**{'visible': True})
        else:
            self.param('CheckBode').setOpts(**{'value': False,
                                               'visible': False})

    def on_CheckGate(self):
        self.bGate = self.param('CheckGate').value()

    def on_ACCheck(self):
        self.bPSD = self.param('CheckPSD').value()
        self.cPSD.setOpts(visible=self.bPSD)
        self.bBode = self.param('CheckBode').value()
        self.cBode.setOpts(visible=self.bBode)
        self.ACSlection.setOpts(visible=(self.bBode or self.bPSD))
        self.on_acqTime()

    def on_acqTime(self):
        vdPoints = len(self.VdsVals.SweepVals)
        vgPoints = len(self.VgsVals.SweepVals)
        DCpoints = vdPoints * vgPoints
        DCt = self.param('DCConfig').param('TimeOut').value()
        dcTime = DCpoints * DCt

        self.param('DCTime').setValue(dcTime)

        bodeT = self.cBode.param('acqTime').value()
        psdT = self.cPSD.param('acqTime').value()

        acp = self.ACSlection.param('ACPoints').value()
        acTime = 0
        if self.bBode:
            acTime += acp * vdPoints * bodeT
        if self.bPSD:
            acTime += acp * vdPoints * psdT

        self.param('ACTime').setValue(acTime)
        self.param('TTime').setValue(acTime + dcTime)

    def on_VdsSweep(self):
        self.on_acqTime()

    def on_VgsSweep(self):
        nVgs = self.VgsVals.param('Points').value()
        self.ACSlection.param('nVgs').setValue(nVgs)
        sstr = '0:' + str(nVgs) + ':4'
        self.ACSlection.param('SelIndex').setValue(sstr)
        self.on_SelIndex()

    def on_SelIndex(self):
        strind = self.ACSlection.param('SelIndex').value()
        nVgs = self.VgsVals.param('Points').value()

        try:
            # strind = '0, 9, 2:8, 9:16:2'
            inds = []
            for parts in strind.split(','):
                raargs = []
                ra = parts.split(':')
                if len(ra) == 1:
                    inds.append(int(ra[0]))
                else:
                    for r in ra:
                        raargs.append(int(r))
                    for i in range(*raargs):
                        inds.append(i)
            inds = list(set(sorted(inds)))
            inds = [x for x in inds if x < nVgs]
            inds = [x for x in inds if x >= 0]
        except:
            print('Invalid parsing')
            return

        self.VgsIndexes = inds
        ACVgsVals = self.VgsVals.SweepVals[inds]
        self.ACSlection.param('VgsSel').setValue(str(ACVgsVals))
        self.ACSlection.param('ACPoints').setValue(len(inds))
        self.on_acqTime()

    def GetSweepConf(self):
        swC = {'VgsSw': self.VgsVals.SweepVals,
               'VdsSw': self.VdsVals.SweepVals,
               'Gate': self.bGate
               }

        if self.bBode or self.bPSD:
            swC['VgsSwAC'] = self.VgsVals.SweepVals[self.VgsIndexes]
        if self.bBode:
            swC['BodeKwarg'] = self.cBode.GetTestSignals()
        if self.bPSD:
            swC['PSDKwarg'] = self.cPSD.GetParams()
        return swC

    def GetCharactSteps(self):
        Steps = []

        AcqKwargs = self.param('DCConfig').GetParams()
        BodeKwargs = self.cBode.GetTestSignals()
        PSDKwargs = self.cPSD.GetParams()

        LVd = len(self.VdsVals.SweepVals)
        LVg = len(self.VgsVals.SweepVals)
        for iVd, Vd in enumerate(self.VdsVals.SweepVals):
            for iVg, Vg in enumerate(self.VgsVals.SweepVals):
                ist = 'Vds {} of {} Vgs {} of {}'.format(iVd + 1, LVd,
                                                         iVg + 1, LVg)
                Kwargs = {'AcqKwargs': AcqKwargs,
                          'Bias': {'Vds': Vd,
                                   'Vgs': Vg},
                          'SweepInds': {'iVd': iVd,
                                        'iVg': iVg}}
                Steps.append({'Funct': 'GetIds',
                              'Kwargs': Kwargs,
                              'Info': 'DCIds {}'.format(ist)})

                if self.bGate:
                    Steps.append({'Funct': 'GetGate',
                                  'Kwargs': Kwargs,
                                  'Info': 'Gate {}'.format(ist)})

                if iVg not in self.VgsIndexes:
                    continue

                iVgac = self.VgsIndexes.index(iVg)
                if self.bBode:
                    bkwargs = BodeKwargs.copy()
                    bkwargs.update({'iVd': iVd,
                                    'iVgac': iVgac})
                    Steps.append({'Funct': 'GetBode',
                                  'Kwargs': bkwargs,
                                  'Info': 'Bode {}'.format(ist)})

                if self.bPSD:
                    pkwargs = PSDKwargs.copy()
                    pkwargs.update({'iVd': iVd,
                                    'iVgac': iVgac})
                    Steps.append({'Funct': 'GetPSD',
                                  'Kwargs': pkwargs,
                                  'Info': 'PSD {}'.format(ist)})

        # for s in Steps: print(s)
        return Steps
