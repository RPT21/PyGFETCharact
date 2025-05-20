# -*- coding: utf-8 -*-
"""

@author: aguimera
"""
import numpy as np
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import ParameterTree, Parameter
from pyqtgraph.parametertree.parameterTypes import PenParameter, SliderParameter
from PyQt5 import Qt
import pyqtgraph as pg


class SelectChannels(pTypes.GroupParameter):
    def __init__(self, Channels, **kwargs):
        super(SelectChannels, self).__init__(**kwargs)

        self.addChild({'name': 'SelAll',
                       'type': 'action',
                       'title': 'Un-Select all'})
        self.addChild({'name': 'SelInvert',
                       'type': 'action',
                       'title': 'Invert Selection'})
        self.seltrufalse = True
        self.param('SelAll').sigActivated.connect(self.on_SelAll)
        self.param('SelInvert').sigActivated.connect(self.on_SelInvert)

        for chn in sorted(Channels):
            self.addChild({'name': chn,
                           'type': 'bool',
                           'value': True,
                           }, )

    def on_SelAll(self):
        self.seltrufalse = not self.seltrufalse
        for p in self.children():
            if p.type() == 'action':
                continue
            p.setValue(self.seltrufalse)

    def on_SelInvert(self):
        for p in self.children():
            if p.type() == 'action':
                continue
            p.setValue(not p.value())

    def GetSelected(self):
        chs = {}
        for p in self.children():
            if p.type() == 'action':
                continue
            chs[p.name()] = p.value()
        return chs


class AcqTimePlotConfig(pTypes.GroupParameter):
    ApplyChangesReady = Qt.pyqtSignal()

    def __init__(self, SampSettings, HardConf, **kwargs):
        super(AcqTimePlotConfig, self).__init__(**kwargs)
        self.Viewtime = None
        self.cDCChannels = HardConf.AInputs.GetDCChannels()
        self.cACChannels = HardConf.AInputs.GetACChannels()

        self.tView = SliderParameter(name='tView',
                                     title='View time [s]',
                                     limits=[0.1, SampSettings['tBufferView']],
                                     value=0.1,
                                     step=0.1,
                                     precision=3, )
        self.addChild(self.tView)
        self.tView.sigValueChanged.connect(self.on_tView_change)
        self.on_tView_change()

        self.addChild({'title': 'Apply',
                       'type': 'action',
                       'name': 'Apply'})
        self.param('Apply').sigActivated.connect(self.on_Apply)

        DCChs = list(self.cDCChannels.keys())
        self.DCSelect = SelectChannels(title='View Channels DC',
                                       name='DCSel',
                                       Channels=DCChs,
                                       expanded=False,
                                       )

        ACChs = list(self.cACChannels.keys())
        self.ACSelect = SelectChannels(title='View Channels AC',
                                       name='ACSel',
                                       Channels=ACChs,
                                       expanded=False,
                                       )

        if len(ACChs) > len(DCChs):
            Chs = ACChs
        else:
            Chs = DCChs

        ChPens = []
        nch = len(Chs)
        for i, chn in enumerate(Chs):
            ChPens.append(PenParameter(name=chn,
                                       width=1.5,
                                       expanded=False,
                                       color=(i, nch)))

        self.addChild({'title': 'Select Channels',
                       'name': 'SelChs',
                       'type': 'group',
                       'children': (self.ACSelect,
                                    self.DCSelect)})
        self.addChild({'title': 'Format Channels',
                       'name': 'ChPens',
                       'type': 'group',
                       'children': ChPens})

    def GetPens(self):
        ChPens = {}
        for p in self.param('ChPens').children():
            ChPens[p.name()] = p.mkPen(p.saveState())
        return ChPens

    def on_tView_change(self):
        self.Viewtime = self.tView.value()

    def on_Apply(self):
        self.ApplyChangesReady.emit()


class AcqTimePlotConfWindow(Qt.QWidget):
    ''' Main Window '''

    def __init__(self, SampSettings, HardConf):
        super(AcqTimePlotConfWindow, self).__init__()
        layout = Qt.QVBoxLayout(self)

        self.setGeometry(650, 20, 400, 800)
        self.setWindowTitle('Time View Configuration')

        self.ViewConfig = AcqTimePlotConfig(SampSettings, HardConf,
                                            name='ViewConfig',
                                            title='Channels',
                                            expanded=True)

        self.treepar = ParameterTree()
        self.treepar.setParameters(self.ViewConfig, showTop=False)
        layout.addWidget(self.treepar)


class PgPlotWindow(Qt.QWidget):
    def __init__(self):
        super(PgPlotWindow, self).__init__()
        layout = Qt.QVBoxLayout(self)  # crea el layout
        self.pgLayout = pg.GraphicsLayoutWidget()
        self.pgLayout.setFocusPolicy(Qt.Qt.WheelFocus)
        layout.addWidget(self.pgLayout)
        self.setLayout(layout)  # to install the QVBoxLayout onto the widget
        self.setFocusPolicy(Qt.Qt.WheelFocus)
        self.show()


class Buffer2D(np.ndarray):
    def __new__(subtype, Fs, nChannels, ViewBuffer,
                dtype=float, buffer=None, offset=0,
                strides=None, order=None, info=None):
        # Create the ndarray instance of our type, given the usual
        # ndarray input arguments.  This will call the standard
        # ndarray constructor, but return an object of our type.
        # It also triggers a call to InfoArray.__array_finalize__
        BufferSize = int(ViewBuffer * Fs)
        shape = (BufferSize, nChannels)
        obj = super(Buffer2D, subtype).__new__(subtype, shape, dtype,
                                               buffer, offset, strides,
                                               order)
        # set the new 'info' attribute to the value passed
        obj.counter = 0
        obj.totalind = 0
        obj.Fs = float(Fs)
        obj.Ts = 1 / obj.Fs
        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self, obj):
        # see InfoArray.__array_finalize__ for comments
        if obj is None:
            return
        self.bufferind = getattr(obj, 'bufferind', None)

    def AddData(self, NewData):
        newsize = NewData.shape[0]
        if newsize > self.shape[0]:
            self[:, :] = NewData[:self.shape[0], :]
        else:
            self[0:-newsize, :] = self[newsize:, :]
            self[-newsize:, :] = NewData
        self.counter += newsize
        self.totalind += newsize

    def IsFilled(self):
        return self.counter >= self.shape[0]

    def GetData(self, ViewTime):
        size = int(ViewTime/self.Ts)
        self.counter = 0
        return self[-size:], self.GetTimes(size)

    def GetTimes(self, Size):
        stop = self.Ts * self.totalind
        start = stop - self.Ts * Size
        times = np.arange(start, stop, self.Ts)
        return times[-Size:]

    def Reset(self):
        self.counter = 0


class AcqPlotter(Qt.QThread):
    PSDInterpolationPoints = 100
    labelStyle = {'color': '#FFF',
                  'font-size': '7pt',
                  'bold': True}

    def WindowParamsInit(self, SampSettings, HardConf):
        self.ParWindow = AcqTimePlotConfWindow(SampSettings, HardConf)
        self.ParWindow.show()
        self.ViewConf = self.ParWindow.ViewConfig
        self.ViewConf.ApplyChangesReady.connect(self.UpdatePlotsConfig)
        self.SelDCChs = self.ViewConf.param('SelChs').param('DCSel')
        self.SelACChs = self.ViewConf.param('SelChs').param('ACSel')

    def BuffersInit(self, SampSettings, HardConf):
        self.DCBuffer = Buffer2D(Fs=SampSettings['Fs'],
                                 nChannels=len(HardConf.AInputs.GetDCChannels()),
                                 ViewBuffer=SampSettings['tBufferView'])

    def __init__(self, SampSettings, HardConf):
        super(AcqPlotter, self).__init__()
        self.ChnPens = None
        self.SelDCChs = None
        self.SelACChs = None
        self.ViewConf = None
        self.ParWindow = None
        self.WindowParamsInit(SampSettings, HardConf)

        self.BuffersInit(SampSettings, HardConf)

        # Create Plotter windows
        self.WindDC = PgPlotWindow()
        self.WindDC.resize(1000, 750)
        self.WindDC.setWindowTitle('DC Time Plot')

        DCChns = HardConf.AInputs.GetDCChannels()
        self.DCCurves = {}
        self.DCPlots = {}
        for chn in DCChns.keys():
            p = pg.PlotItem(name=chn)
            p.setDownsampling(auto=True,
                              mode='subsample',
                              )
            p.setLabel('left', '', units='A')
            self.DCCurves[chn] = pg.PlotCurveItem(name=chn)
            p.addItem(self.DCCurves[chn])
            self.DCPlots[chn] = p

        # Create Plotter windows
        self.WindAC = PgPlotWindow()
        self.WindAC.resize(1000, 750)
        self.WindAC.setWindowTitle('AC Time Plot')

        ACChns = HardConf.AInputs.GetACChannels()
        self.ACCurves = {}
        for chn in ACChns.keys():
            c = pg.PlotCurveItem(name=chn)
            self.ACCurves[chn] = c

        self.UpdatePlotsConfig()

    def UpdatePlotsConfig(self):
        xlink = None
        px = None
        for chn, sel in self.SelDCChs.GetSelected().items():
            p = self.DCPlots[chn]
            if sel:
                px = p
                p.hideAxis('bottom')
                if p.parent() is not None:
                    continue
                else:
                    self.WindDC.pgLayout.nextRow()
                    self.WindDC.pgLayout.addItem(p)
                    if xlink is not None:
                        p.setXLink(xlink)
                    xlink = p
                    p.setParent(self.WindDC.pgLayout)
            else:
                if p.parent() is not None:
                    self.WindDC.pgLayout.removeItem(p)
                    p.setParent(None)

        if px is not None:
            # p.setClipToView(True)
            px.showAxis('bottom')
            px.setLabel('bottom', 'Time', units='s', **self.labelStyle)

        self.ChnPens = self.ViewConf.GetPens()
        for chn, c in self.DCCurves.items():
            c.setPen(self.ChnPens[chn])

    def run(self):
        while True:
            if self.DCBuffer.counter > 10000:
                Dat, t = self.DCBuffer.GetData(self.ViewConf.Viewtime)
                for i, (chn, c) in enumerate(self.DCCurves.items()):
                    c.setData(x=t,
                              y=Dat[:, i])
            else:
                Qt.QThread.msleep(100)

    def AddData(self, Data):
        self.DCBuffer.AddData(Data)


