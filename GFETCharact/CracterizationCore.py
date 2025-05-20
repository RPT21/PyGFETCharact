#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 25 19:52:05 2022

@author: aguimera
"""

from GFETCharact.DaqInterface import ReadAnalog, WriteAnalog, WriteDigital
from GFETCharact.SaveData import CharactFile
from GFETCharact.ParamConf.BodeModule import CalcFFTavg
from GFETCharact.CharactPlot import CharactPlotter
import numpy as np
import scipy.signal as signal
from PyQt5.QtCore import QTimer
from PyQt5 import Qt
from datetime import datetime


class HardwareInterface(Qt.QObject):
    SigReadDC = Qt.pyqtSignal(object)
    SigReadAC = Qt.pyqtSignal(object)
    SigReadGate = Qt.pyqtSignal(object)
    SigDebug = Qt.pyqtSignal(object)

    def __init__(self, HardConf):
        super(HardwareInterface, self).__init__()

        self.BiasVd = None
        self.HardConf = HardConf.param('BoardConf')
        self.cGains = self.HardConf.Gains.GetGains()
        self.cDCChannels = self.HardConf.AInputs.GetDCChannels()
        self.cACChannels = self.HardConf.AInputs.GetACChannels()
        self.cAouts = self.HardConf.AOutputs.GetAOuts()
        # self.cDOuts = self.HardConf.DOutputs.GetDOColumns()

        self.aiDC = self.cDCChannels.values()
        self.aiAC = self.cACChannels.values()
        self.aiChNames = self.cDCChannels.keys()

        self.InitAouts()
        self.Init_ACDCSwitch()

        # print(self.Aouts)
        # print(self.cDCChannels)
        # print(self.cDCChannels)

    def Init_ACDCSwitch(self):
        self.ACDCSwitch = self.HardConf.ACDCSwitch
        if self.ACDCSwitch is not None:
            self.ACDCSwDouts = WriteDigital(self.ACDCSwitch.douts)

    def Select_ACDCSwitch(self, State):
        if self.ACDCSwitch is not None:
            val = self.ACDCSwitch.States[State]
            self.ACDCSwDouts.SetDigitalSignal(val)

    def InitAouts(self):
        self.Aouts = {}
        for n, c in self.cAouts.items():
            self.Aouts[n] = WriteAnalog((c,))
        if 'Vg' in self.Aouts:
            self.Aouts['Vg'].SetVal(0)
    
    def SetBias(self, Vgs, Vds):
        self.Aouts['Vs'].SetVal(-Vgs)
        self.Aouts['Vds'].SetVal(Vds)
        self.BiasVd = Vds-Vgs

    def SetTestSignal(self, Sig):
        # self.Aouts['Vg'] = WriteAnalog((self.cAouts['Vg'],))
        self.Aouts['Vg'].SetSignal(Signal=Sig,
                                   nSamps=Sig.size)

    def StopTestSignal(self):
        # print('End Bode Gen')
        # self.Aouts['Vg'].StopTask()
        if 'Vg' in self.Aouts:
            self.Aouts['Vg'].ClearTask()
            self.Aouts['Vg'] = WriteAnalog((self.cAouts['Vg'],))
            self.Aouts['Vg'].SetVal(0)

    def ReadGate(self, Fs, nSamps, **kwargs):
        self.Ains = ReadAnalog((self.ACDCSwitch.GateAI, ))
        self.Select_ACDCSwitch('Gate')
        self.Ains.EveryNEvent = None
        self.Ains.DoneEvent = self.on_Gate_Data
        self.Ains.ReadData(Fs=Fs,
                           nSamps=nSamps,
                           EverySamps=nSamps)

    def on_Gate_Data(self, Data):
        Ig = Data/self.cGains['GateGain']
        self.SigReadGate.emit(Ig)
        self.SigDebug.emit(Ig)

    def ReadDC(self, Fs, nSamps, **kwargs):
        self.Ains = ReadAnalog(self.aiDC)
        self.Select_ACDCSwitch('DC')
        self.Ains.EveryNEvent = self.on_DC_Data        
        self.Ains.ReadContData(Fs=Fs,
                               EverySamps=nSamps)

    def on_DC_Data(self, Data):
        Ids = (Data-self.BiasVd)/self.cGains['DCGain']
        self.SigReadDC.emit(Ids)
        self.SigDebug.emit(Ids)

    def ReadAC(self, Fs, nSamps, EverySamps, **kwargs):
        self.Ains = ReadAnalog(self.aiAC)
        self.Select_ACDCSwitch('AC')
        self.Ains.EveryNEvent = self.on_AC_Data_Debug
        self.Ains.DoneEvent = self.on_AC_Data
        self.Ains.ReadData(Fs=Fs,
                           nSamps=nSamps,
                           EverySamps=EverySamps)

    def on_AC_Data(self, Data):
        # Data = signal.detrend(Data)
        Ids = Data/self.cGains['ACGain']
        self.StopTestSignal()
        self.SigReadAC.emit(Ids)

    def on_AC_Data_Debug(self, Data):
        Ids = Data/self.cGains['ACGain']
        self.SigDebug.emit(Ids)

    def ReadBode(self, Fs, Signal, Sequential, **kwargs):
        if Sequential:
            self.BodeChannels = list(self.aiAC)
            self.BodeFs = Fs
            self.BodeSignal = Signal
            self.bData = np.zeros((Signal.size, len(self.BodeChannels)))
            self.bCount = 0
            self.ReadBodeSeq()
        else:
            self.Ains = ReadAnalog(self.aiAC)
            self.Select_ACDCSwitch('AC')
            self.SetTestSignal(Signal)
            self.ReadAC(Fs=Fs,
                        nSamps=Signal.size,
                        EverySamps=Signal.size)

    def ReadBodeSeq(self):
        if len(self.BodeChannels):
            ch = self.BodeChannels.pop(0)
            self.Ains = ReadAnalog((ch, ))
            self.Select_ACDCSwitch('AC')
            self.SetTestSignal(self.BodeSignal)
            self.Ains.EveryNEvent = self.on_AC_Data_Debug
            self.Ains.DoneEvent = self.on_Bode_seq_data
            self.Ains.ReadData(Fs=self.BodeFs,
                               nSamps=self.BodeSignal.size,
                               EverySamps=self.BodeSignal.size)
        else:
            Ids = self.bData/self.cGains['ACGain']
            self.SigReadAC.emit(Ids)

    def on_Bode_seq_data(self, Data):
        self.StopTestSignal()
        self.StopRead()

        self.bData[:, self.bCount] = Data[:, 0]
        self.bCount += 1
        self.ReadBodeSeq()

    def StopRead(self):
        self.Ains.ClearTask()


def StabDetector(Data, Fs, MaxSlope, StabCriteria, **kwargs):
    r = Data.shape[0]
    t = np.arange(0, (1/Fs)*r, (1/Fs))
    Slope, Ids = np.polyfit(t, Data, 1)
    # print(Slope, StabCriteria)
    # print(np.all(MaxSlope > np.abs(Slope)))
    # print(MaxSlope > np.min(np.abs(Slope)))
    # print(MaxSlope > np.mean(np.abs(Slope)))
    if StabCriteria == 'All channels':
        Stable = np.all(MaxSlope > np.abs(Slope))
    elif StabCriteria == 'One Channel':
        Stable = MaxSlope > np.min(np.abs(Slope))
    elif StabCriteria == 'Mean':
        Stable = MaxSlope > np.mean(np.abs(Slope))

    return Stable, Slope, Ids


class CharacterizationMachine(Qt.QObject):
    CharactFinished = Qt.pyqtSignal()

    def __init__(self, SweepsConf, InfoOut=None):
        super(CharacterizationMachine, self).__init__()
        self.GMF = None
        self.StepKwargs = None
        self.DCTimeOut = None
        self.BodeSteps = None
        self.StartTime = None
        self.Steps = None
        self.CharactFile = None
        self.HardInt = None
        self.CharPlot = None
        self.currentBode = None
        self.SweepsConf = SweepsConf
        self.Timer = QTimer()
        self.Timer.timeout.connect(self.on_TimeOut)
        self.ChactRunning = False
        self.InfoOut = InfoOut

    def Report(self, Text, Append=True):
        if self.InfoOut is not None:
            TimeStamp = datetime.now() - self.StartTime
            Txt = '{} - {}'.format(int(TimeStamp.total_seconds()),
                                   Text)
            if Append:
                st = '{} \n {}'.format(Txt,
                                       self.InfoOut.value())
            else:
                st = Txt
            self.InfoOut.setValue(st)

    def InitPlot(self):
        self.CharPlot = CharactPlotter(self.CharactFile.DictDC,
                                       self.CharactFile.DictAC)
        self.HardInt.SigDebug.connect(self.on_Debug)

    def on_Debug(self, Data):
        self.CharPlot.PltLive.Refresh(Data)

    def RefreshPlot(self):
        self.CharPlot.RefreshPlot()

    def InitDataFile(self, FileName, SweepConf):
        self.CharactFile = CharactFile(FileName,
                                       SweepConf,
                                       self.HardInt.aiChNames)
        self.CharactFile.SavePickle()

    def SaveGate(self, Ig):
        ivd = self.StepKwargs['SweepInds']['iVd']
        ivg = self.StepKwargs['SweepInds']['iVg']
        self.CharactFile.DictDC['Gate']['Ig'][ivg, ivd] = Ig
        # self.CharactFile.DictDC['Gate']['Slope'][ivg, ivd] = slo
        self.CharactFile.SavePickle()

    def SaveDC(self, Ids, Slope):
        ivd = self.StepKwargs['SweepInds']['iVd']
        ivg = self.StepKwargs['SweepInds']['iVg']
        for ch, ids, slo in zip(self.HardInt.aiChNames, Ids, Slope):
            self.CharactFile.DictDC[ch]['Ids'][ivg, ivd] = ids
            self.CharactFile.DictDC[ch]['Slope'][ivg, ivd] = slo
        self.CharactFile.SavePickle()

    def SavePSD(self, ff, PSD):
        ivd = self.StepKwargs['iVd']
        iVgac = self.StepKwargs['iVgac']
        for ch, p in zip(self.HardInt.aiChNames, PSD.transpose()):
            self.CharactFile.DictAC[ch]['PSD']['Vd{}'.format(ivd)][iVgac, :] = p
            if not np.all(self.CharactFile.DictAC[ch]['Fpsd'] == ff):
                print('WARNING BAD frequency vector')
        self.CharactFile.SavePickle()

    def SaveBode(self):
        ivd = self.StepKwargs['iVd']
        iVgac = self.StepKwargs['iVgac']
        for ch, p in zip(self.HardInt.aiChNames, self.GMF.transpose()):
            self.CharactFile.DictAC[ch]['gm']['Vd{}'.format(ivd)][iVgac, :] = p
            # if not np.all(self.CharactFile.DictAC[ch]['Fpsd'] == ff):
            #     print('WARNING BAD frequency vector')
        self.CharactFile.SavePickle()

    def StartCharact(self, HardConf, FileName=None):
        self.HardInt = HardwareInterface(HardConf)
        self.Steps = self.SweepsConf.GetCharactSteps()
        self.StartTime = datetime.now()

        self.InitDataFile(FileName,
                          SweepConf=self.SweepsConf.GetSweepConf())

        self.InitPlot()
        
        self.ChactRunning = True
        st = 'Characterization Start -- Steps {}'.format(len(self.Steps))
        self.Report(st, Append=False)
        self.ExecuteStep()

    def StopCharact(self):
        self.ChactRunning = False
        self.Report('Stopping')

    def ExecuteStep(self):
        if self.ChactRunning and len(self.Steps):
            s = self.Steps.pop(0)
            self.Report(s['Info'])
            Funct = getattr(self, s['Funct'])
            self.StepKwargs = s['Kwargs']
            Funct(**s['Kwargs'])
        else:
            self.Report('Finish')
            self.ChactRunning = False
            self.HardInt.SetBias(0, 0)
            self.CharactFinished.emit()

    def GetGate(self, **kwargs):
        self.HardInt.SigReadGate.connect(self.on_Gate_Data)
        self.HardInt.ReadGate(Fs=kwargs['AcqKwargs']['Fs'],
                              nSamps=kwargs['AcqKwargs']['nSamps'])

    def on_Gate_Data(self, Data):
        self.HardInt.StopRead()
        self.HardInt.SigReadGate.disconnect(self.on_Gate_Data)
        self.SaveGate(np.mean(Data))
        self.RefreshPlot()
        self.ExecuteStep()

    def GetIds(self, **kwargs):
        print('Get Ids')
        self.HardInt.SetBias(**kwargs['Bias'])
        self.HardInt.SigReadDC.connect(self.on_DC_data)
        self.HardInt.ReadDC(Fs=kwargs['AcqKwargs']['Fs'],
                            nSamps=kwargs['AcqKwargs']['nSamps'])
        self.Timer.start(kwargs['AcqKwargs']['TimeOut'] * 1000)
        self.DCTimeOut = False

    def on_TimeOut(self):
        self.Timer.stop()
        self.DCTimeOut = True

    def on_DC_data(self, Data):
        print('Ids Step')
        Stable, Slope, Ids = StabDetector(Data, **self.StepKwargs['AcqKwargs'])
        NextStep = False
        if Stable:
            self.Timer.stop()
            self.Report('Stable')
            NextStep = True
        if self.DCTimeOut:
            NextStep = True
            self.Report('End By TimeOut')

        if NextStep or not self.ChactRunning:
            print('Ids Done')
            self.HardInt.StopRead()
            self.HardInt.SigReadDC.disconnect(self.on_DC_data)
            if NextStep:
                self.SaveDC(Ids, Slope)
                self.RefreshPlot()
            self.ExecuteStep()

    def GetPSD(self, Fs, nFFT, nAvg, **kwargs):
        print('Get PSD')
        nSamps = 2**nFFT
        self.HardInt.SigReadAC.connect(self.on_PSD_data)
        self.HardInt.ReadAC(Fs=Fs,
                            nSamps=nSamps*nAvg,
                            EverySamps=nSamps)

    def on_PSD_data(self, Data):
        print('PSD Done')
        Fs = self.StepKwargs['Fs']
        nFFT = self.StepKwargs['nFFT']
        ff, psd = signal.welch(x=Data,
                               fs=Fs,
                               window='hanning',
                               nperseg=2**nFFT,
                               scaling='density',
                               axis=0)
        self.HardInt.StopRead()
        self.HardInt.SigReadAC.disconnect(self.on_PSD_data)
        self.SavePSD(ff, psd)
        self.RefreshPlot()
        self.ExecuteStep()

    def GetBode(self, **bkwargs):
        print('Get Bode')
        self.BodeSteps = bkwargs['TestSigs'].copy()
        self.GMF = np.array([])
        self.ExecuteBodeStep()

    def ExecuteBodeStep(self):
        print('Bode Step')
        if self.ChactRunning and len(self.BodeSteps):
            self.currentBode = self.BodeSteps.pop(0)
            # print(self.currentBode)
            self.HardInt.SigReadAC.connect(self.on_bode_data)
            self.HardInt.ReadBode(**self.currentBode)
        else:
            print('Bode Done')
            if self.ChactRunning:
                self.SaveBode()
                self.RefreshPlot()
            self.ExecuteStep()

    def on_bode_data(self, Data):
        self.HardInt.StopRead()
        self.HardInt.SigReadAC.disconnect(self.on_bode_data)
        print('On Bode Data')

        shape = (len(self.currentBode['FFTAmps']), Data.shape[1])
        gmF = np.ones(shape) * np.NaN * np.complex(1)
        for ic, d in enumerate(Data.transpose()):
            g = CalcFFTavg(Data=d,
                           nFFT=self.currentBode['nFFT'],
                           nAvg=-1)
            out = g[self.currentBode['FFTInds']]
            gmF[:, ic] = out / self.currentBode['FFTAmps']

        self.GMF = np.vstack((self.GMF, gmF)) if self.GMF.size else gmF
        self.ExecuteBodeStep()

        # nSamps = 2**nFFT
        # self.HardInt.ReadAC(Fs=Fs,
        #                     nSamps=nSamps*nAvg,
        #                     EverySamps=nSamps,
        #                     Callback=self.on_PSD_data)


