# -*- coding: utf-8 -*-
"""

@author: aguimera
"""

from PyQt5 import Qt
from GFETCharact.DaqInterface import ReadAnalog, WriteAnalog
from GFETCharact.AcqTimePlot import AcqPlotter


class HardwareInterface(Qt.QThread):
    NewDataReady = Qt.pyqtSignal(object)

    def __init__(self, HardConf):
        super(HardwareInterface, self).__init__()
        self.Ains = None
        self.Aouts = None
        self.BiasVd = None
        self.HardConf = HardConf
        self.cGains = self.HardConf.Gains.GetGains()
        self.cDCChannels = self.HardConf.AInputs.GetDCChannels()
        self.cACChannels = self.HardConf.AInputs.GetACChannels()
        self.cAouts = self.HardConf.AOutputs.GetAOuts()

        self.aiDC = self.cDCChannels.values()
        self.aiAC = self.cACChannels.values()
        self.aiChNames = self.cDCChannels.keys()

        self.InitAouts()
        self.InitAins()
        self.SetBias(0, 0)

        self.SamplingSettings = None

    def InitAouts(self):
        self.Aouts = {}
        for n, c in self.cAouts.items():
            self.Aouts[n] = WriteAnalog((c,))
        if 'Vg' in self.Aouts:
            self.Aouts['Vg'].SetVal(0)

    def SetBias(self, Vgs, Vds):
        self.Aouts['Vs'].SetVal(-Vgs)
        self.Aouts['Vds'].SetVal(Vds)
        self.BiasVd = Vds - Vgs

    def InitAins(self):
        self.Ains = ReadAnalog(self.aiDC)

    def run(self, *args, **kwargs):
        self.Ains.ReadContData(**self.SamplingSettings)
        self.Ains.EveryNEvent = self.NewData
        loop = Qt.QEventLoop()
        loop.exec_()

    def NewData(self, Data):
        self.NewDataReady.emit(Data)


class AdquisitionCore(Qt.QObject):
    CharactFinished = Qt.pyqtSignal()

    def __init__(self, SamplingConf, InfoOut=None):
        super(AdquisitionCore, self).__init__()
        self.CharPlot = None
        self.StartTime = None
        self.HardInt = None
        self.SamplingConf = SamplingConf
        self.AdcRunning = False
        self.InfoOut = InfoOut

    def InitPlot(self, HardConf):
        self.AcqPlot = AcqPlotter(SampSettings=self.SamplingConf.GetParams(),
                                  HardConf=HardConf)

    def StartAcquisition(self, HardConf):
        self.HardInt = HardwareInterface(HardConf)
        self.HardInt.SamplingSettings = self.SamplingConf.GetParams()

        self.HardInt.NewDataReady.connect(self.on_NewData)

        # self.StartTime = datetime.now()
        self.InitPlot(HardConf=HardConf)
        self.AdcRunning = True
        self.HardInt.start()
        self.AcqPlot.start()

    def StopAcquisition(self):
        self.AdcRunning = False

    def on_NewData(self, Data):
        self.AcqPlot.AddData(Data)
