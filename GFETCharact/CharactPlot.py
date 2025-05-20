#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  6 23:29:34 2021

@author: aguimera
"""

import numpy as np
import time
from scipy import interpolate

import pyqtgraph as pg

from PyQt5 import Qt
from pyqtgraph.parametertree import ParameterTree, Parameter
import pyqtgraph.parametertree.parameterTypes as pTypes


class PlotterParameters(pTypes.GroupParameter):
    NewConf = Qt.pyqtSignal()

    def __init__(self, DevDCVals, DevACVals, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        ShowChilds = []
        # ColorsChilds = []
        nChannels = len(DevDCVals)
        for ind, (chn, d) in enumerate(DevDCVals.items()):
            pen = pg.mkPen((ind, 1.3 * nChannels))
            ShowChilds.append({'name': chn,
                               'type': 'bool',
                               'value': True})
            ShowChilds.append({'name': 'C_' + chn,
                               'title': '',
                               'type': 'color',
                               'value': pen.color()})

        chn = list(DevDCVals.keys())[0]
        VdsChilds = []
        for ivd, vd in enumerate(DevDCVals[chn]['Vds']):
            VdsChilds.append({'name': str(ivd),
                              'title': '{}'.format(vd),
                              'type': 'bool',
                              'value': True})

        self.addChild({'title': 'Ids vs Vgs',
                       'name': 'DCconf',
                       'type': 'group',
                       'children': ({'name': 'VdsConf',
                                     'title': 'Vds',
                                     'type': 'group',
                                     'children': VdsChilds},
                                    {'name': 'Show',
                                     'type': 'group',
                                     'expanded': False,
                                     'children': ShowChilds},
                                    # {'name': 'Color',
                                    #  'type': 'group',
                                    #  'expanded': False,
                                    #  'children': ColorsChilds}
                                    )
                       })

        self.DCchConf = self.param('DCconf').param('Show')
        self.DCchConf.sigTreeStateChanged.connect(self.on_DC_conf_change)

        self.VdsConf = self.param('DCconf').param('VdsConf')
        self.VdsConf.sigTreeStateChanged.connect(self.on_Vds_conf_change)

        self.ChShow = {}
        self.ChColors = {}
        self.ShowVdsInds = []
        self.ChViewConf = {'Show': self.ChShow,
                           'Pens': self.ChColors,
                           'ShowVdsInds': self.ShowVdsInds}

        self.on_DC_conf_change()
        self.on_Vds_conf_change()

        self.bPSD = False
        self.bGM = False
        if DevACVals is None:
            return

        if 'Fpsd' in DevACVals[chn]:
            self.bPSD = True
        if 'Fgm' in DevACVals[chn]:
            self.bGM = True

        VgsChilds = []
        for ivg, vg in enumerate(DevACVals[chn]['VgsAC']):
            VgsChilds.append({'name': str(ivg),
                              'title': '{}'.format(vg),
                              'type': 'bool',
                              'value': True})
        VdsChilds = []
        for ivd, vd in enumerate(DevACVals[chn]['VdsAC']):
            VdsChilds.append({'name': str(ivd),
                              'title': '{}'.format(vd),
                              'type': 'bool',
                              'value': True})

        self.addChild({'title': 'AC',
                       'name': 'ACconf',
                       'type': 'group',
                       'children': ({'name': 'VdsACConf',
                                     'title': 'Vds',
                                     'type': 'group',
                                     'children': VdsChilds},
                                    {'name': 'VgsACConf',
                                     'title': 'Vgs',
                                     'type': 'group',
                                     'children': VgsChilds},
                                    )
                       })

        self.VdsACConf = self.param('ACconf').param('VdsACConf')
        self.VdsACConf.sigTreeStateChanged.connect(self.on_VdsAC_conf_change)

        self.VgsACConf = self.param('ACconf').param('VgsACConf')
        self.VgsACConf.sigTreeStateChanged.connect(self.on_VgsAC_conf_change)

        self.ShowACVdsInds = []
        self.ShowACVgsInds = []
        self.ChViewConf['ShowACVdsInds'] = self.ShowACVdsInds
        self.ChViewConf['ShowACVgsInds'] = self.ShowACVgsInds
        self.on_VdsAC_conf_change()
        self.on_VgsAC_conf_change()

    def on_DC_conf_change(self):
        for p in self.DCchConf.children()[0::2]:
            self.ChShow[p.name()] = p.value()
        for p in self.DCchConf.children()[1::2]:
            # print(p.name(), p.value())
            self.ChColors[p.name()[2:]] = pg.mkPen(color=p.value(),
                                                   width=1)
        self.NewConf.emit()

    def on_Vds_conf_change(self):
        self.ShowVdsInds.clear()
        for p in self.VdsConf.children():
            if p.value():
                self.ShowVdsInds.append(int(p.name()))
        self.NewConf.emit()

    def on_VdsAC_conf_change(self):
        self.ShowACVdsInds.clear()
        for p in self.VdsACConf.children():
            if p.value():
                self.ShowACVdsInds.append(int(p.name()))
        self.NewConf.emit()

    def on_VgsAC_conf_change(self):
        self.ShowACVgsInds.clear()
        for p in self.VgsACConf.children():
            if p.value():
                self.ShowACVgsInds.append(int(p.name()))
        self.NewConf.emit()


class ChannelsWindow(Qt.QWidget):
    ''' Main Window '''

    def __init__(self, DevDCVals, DevACVals):
        super(ChannelsWindow, self).__init__()
        layout = Qt.QVBoxLayout(self)

        self.setGeometry(650, 20, 400, 800)
        self.setWindowTitle('Characterization Results Configuration')

        self.ViewConfig = PlotterParameters(DevDCVals, DevACVals,
                                            name='ViewConfig',
                                            title='Channels',
                                            expanded=True)

        self.treepar = ParameterTree()
        self.treepar.setParameters(self.ViewConfig, showTop=False)
        layout.addWidget(self.treepar)


class PlotDC():
    def __init__(self, Plot, PlotIg, DevDCVals, ChViewConf):
        self.Plot = Plot
        self.DevDCVals = DevDCVals
        self.ChViewConf = ChViewConf

        # Configure IDS plot
        self.Plot.setLabel('left', 'Ids', units='A')
        self.Plot.setLabel('bottom', 'Vgs', units='V')
        self.Plot.showGrid(x=True, y=True)

        chn = list(self.DevDCVals.keys())[0]
        self.Vds = self.DevDCVals[chn]['Vds']
        self.Vgs = self.DevDCVals[chn]['Vgs']

        if 'Gate' in self.DevDCVals:
            self.PlotIg = PlotIg
            self.PlotIg.setLabel('left', 'Ig', units='A')
            self.PlotIg.setLabel('bottom', 'Vgs', units='V')
            self.PlotIg.showGrid(x=True, y=True)
            self.PlotIg.setYRange(0, 50e-9)

        # Init Ids curves
        self.IdsCurves = []  # Ids curves one for each channel and Vds
        for vdi, vd in enumerate(self.Vds):
            for chn in self.DevDCVals.keys():
                if chn == 'Gate':
                    c = pg.PlotCurveItem(parent=self.PlotIg,
                                         pen=self.ChViewConf['Pens'][chn],
                                         clickable=True,
                                         name=chn)
                    self.PlotIg.addItem(c)
                else:
                    c = pg.PlotCurveItem(parent=self.Plot,
                                         pen=self.ChViewConf['Pens'][chn],
                                         clickable=True,
                                         name=chn)
                    self.Plot.addItem(c)
                c.opts['vdi'] = vdi
                c.opts['vds'] = vd
                self.IdsCurves.append(c)
        # Add curves to plot and connect event
        for c in self.IdsCurves:
            c.sigClicked.connect(self.on_IdsClicked)

    def Refresh(self):
        for c in self.IdsCurves:
            chn = c.opts['name']
            vdi = c.opts['vdi']
            if chn == 'Gate':
                Ids = self.DevDCVals[chn]['Ig']
                dat = Ids[:, vdi]
            else:
                Ids = self.DevDCVals[chn]['Ids']
                dat = Ids[:, vdi]
            c.setData(self.Vgs, dat,
                      pen=self.ChViewConf['Pens'][chn])
        self.SetVisible()

    def SetVisible(self):
        for c in self.IdsCurves:
            chn = c.opts['name']
            vdi = c.opts['vdi']
            if vdi not in self.ChViewConf['ShowVdsInds']:
                c.setVisible(False)
            else:
                c.setVisible(self.ChViewConf['Show'][chn])

    def on_IdsClicked(self):
        print('cliked')


class PlotPSD():
    PSDInterpolationPoints = 100

    def __init__(self, Plot, DevACVals, ChViewConf):
        self.Plot = Plot
        self.Plot.setLabel('left', 'PSD [A**2/Hz]')
        self.Plot.setLabel('bottom', 'Frequency [Hz]')
        self.Plot.getAxis('left').enableAutoSIPrefix(False)
        self.Plot.getAxis('bottom').enableAutoSIPrefix(False)
        self.Plot.showGrid(x=True, y=True)
        self.Plot.setLogMode(True, True)

        self.DevACVals = DevACVals
        self.ChViewConf = ChViewConf

        self.PSDCurves = []  # Psd curves one for each channel

        chn = list(self.DevACVals.keys())[0]
        self.Fpsd = self.DevACVals[chn]['Fpsd']
        self.FpsdLog = np.logspace(np.log10(self.Fpsd[1]),
                                   np.log10(self.Fpsd[-2]),
                                   self.PSDInterpolationPoints)

        self.Vgs = self.DevACVals[chn]['VgsAC']
        self.Vds = self.DevACVals[chn]['VdsAC']

        for chn in self.DevACVals.keys():
            for vdi, vd in enumerate(self.Vds):
                for vgi, vg in enumerate(self.Vgs):
                    c = pg.PlotDataItem(pen=self.ChViewConf['Pens'][chn],
                                        name=chn)
                    c.opts['vdi'] = vdi
                    c.opts['vds'] = vd
                    c.opts['vgi'] = vgi
                    c.opts['vgs'] = vg
                    self.PSDCurves.append(c)

        # Add curves to plot and connect event
        for c in self.PSDCurves:
            self.Plot.addItem(c)
            c.sigClicked.connect(self.on_IdsClicked)

    def on_IdsClicked(self):
        print('cliked')

    def Refresh(self):
        for c in self.PSDCurves:
            chn = c.opts['name']
            vdi = c.opts['vdi']
            vgi = c.opts['vgi']
            sVdi = 'Vd{}'.format(vdi)
            dat = self.DevACVals[chn]['PSD'][sVdi][vgi, :]
            pltpsd = interpolate.interp1d(self.Fpsd, dat)(self.FpsdLog)
            c.setData(self.FpsdLog, pltpsd)
        self.SetVisible()

    def SetVisible(self):
        for c in self.PSDCurves:
            chn = c.opts['name']
            vdi = c.opts['vdi']
            vgi = c.opts['vgi']
            bVis1 = vgi not in self.ChViewConf['ShowACVgsInds']
            bVis2 = vdi not in self.ChViewConf['ShowACVdsInds']

            if bVis1 or bVis2:
                c.setVisible(False)
            else:
                c.setVisible(self.ChViewConf['Show'][chn])


class PlotGM():
    PSDInterpolationPoints = 100

    def __init__(self, PlotM, PlotP, DevACVals, ChViewConf):
        self.PlotM = PlotM
        self.PlotM.setLabel('left', 'GM Mag [S]')
        self.PlotM.setLabel('bottom', 'Frequency [Hz]')
        self.PlotM.getAxis('left').enableAutoSIPrefix(False)
        self.PlotM.getAxis('bottom').enableAutoSIPrefix(False)
        self.PlotM.showGrid(x=True, y=True)
        self.PlotM.setLogMode(x=True, y=True)

        self.PlotP = PlotP
        self.PlotP.setLabel('left', 'GM Phase [º]')
        self.PlotP.setLabel('bottom', 'Frequency [Hz]')
        self.PlotP.getAxis('left').enableAutoSIPrefix(False)
        self.PlotP.getAxis('bottom').enableAutoSIPrefix(False)
        self.PlotP.showGrid(x=True, y=True)
        self.PlotP.setLogMode(x=True)

        self.DevACVals = DevACVals
        self.ChViewConf = ChViewConf

        self.MagCurves = []
        self.PhCurves = []

        chn = list(self.DevACVals.keys())[0]
        self.Fgm = self.DevACVals[chn]['Fgm']
        self.Vgs = self.DevACVals[chn]['VgsAC']
        self.Vds = self.DevACVals[chn]['VdsAC']

        for chn in self.DevACVals.keys():
            for vdi, vd in enumerate(self.Vds):
                for vgi, vg in enumerate(self.Vgs):
                    c = pg.PlotDataItem(pen=self.ChViewConf['Pens'][chn],
                                        name=chn)
                    c.opts['vdi'] = vdi
                    c.opts['vds'] = vd
                    c.opts['vgi'] = vgi
                    c.opts['vgs'] = vg
                    self.MagCurves.append(c)

                    c = pg.PlotDataItem(pen=self.ChViewConf['Pens'][chn],
                                        name=chn)
                    c.opts['vdi'] = vdi
                    c.opts['vds'] = vd
                    c.opts['vgi'] = vgi
                    c.opts['vgs'] = vg
                    self.PhCurves.append(c)

        # Add curves to plot and connect event
        for c in self.PhCurves:
            self.PlotP.addItem(c)
            c.sigClicked.connect(self.on_IdsClicked)

        for c in self.MagCurves:
            self.PlotM.addItem(c)
            c.sigClicked.connect(self.on_IdsClicked)

    def on_IdsClicked(self):
        print('cliked')

    def Refresh(self):
        for c in self.MagCurves:
            chn = c.opts['name']
            vdi = c.opts['vdi']
            vgi = c.opts['vgi']
            sVdi = 'Vd{}'.format(vdi)
            dat = self.DevACVals[chn]['gm'][sVdi][vgi, :]
            c.setData(self.Fgm, np.abs(dat))

        for c in self.PhCurves:
            chn = c.opts['name']
            vdi = c.opts['vdi']
            vgi = c.opts['vgi']
            sVdi = 'Vd{}'.format(vdi)
            dat = self.DevACVals[chn]['gm'][sVdi][vgi, :]
            c.setData(self.Fgm, np.angle(dat, deg=True))

        self.SetVisible()

    def SetVisible(self):
        for c in self.MagCurves:
            chn = c.opts['name']
            vdi = c.opts['vdi']
            vgi = c.opts['vgi']
            bVis1 = vgi not in self.ChViewConf['ShowACVgsInds']
            bVis2 = vdi not in self.ChViewConf['ShowACVdsInds']

            if bVis1 or bVis2:
                c.setVisible(False)
            else:
                c.setVisible(self.ChViewConf['Show'][chn])

        for c in self.PhCurves:
            chn = c.opts['name']
            vdi = c.opts['vdi']
            vgi = c.opts['vgi']
            bVis1 = vgi not in self.ChViewConf['ShowACVgsInds']
            bVis2 = vdi not in self.ChViewConf['ShowACVdsInds']

            if bVis1 or bVis2:
                c.setVisible(False)
            else:
                c.setVisible(self.ChViewConf['Show'][chn])


class PlotLive():
    def __init__(self, Plot, DevDCVals, ChViewConf):
        self.Plot = Plot
        self.ChViewConf = ChViewConf

        self.Plot.setLabel('left', 'Ids', units='A')
        self.Plot.setLabel('bottom', 'Samples')
        self.Plot.showGrid(x=True, y=True)

        self.Curves = []
        for chn in DevDCVals.keys():
            c = pg.PlotCurveItem(parent=self.Plot,
                                 pen=self.ChViewConf['Pens'][chn],
                                 downsample=1000,
                                 downsampleMethod='subsample',
                                 name=chn)
            self.Curves.append(c)
            self.Plot.addItem(c)

    def Refresh(self, Data):
        x = np.arange(Data.shape[0])
        for ic, c in enumerate(self.Curves):
            if ic >= Data.shape[1]:
                c.setData([], [])
            else:
                c.setData(x, Data[:, ic])


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


class CharactPlotter():
    PSDInterpolationPoints = 100

    def WindowParamsInit(self, DevDCVals, DevACVals):
        self.ParWindow = ChannelsWindow(DevDCVals, DevACVals)
        self.ParWindow.show()
        self.ViewConf = self.ParWindow.ViewConfig

    def __init__(self, DevDCVals, DevACVals=None):

        self.ViewConf = None
        self.ParWindow = None
        self.WindowParamsInit(DevDCVals, DevACVals)

        # Create Plotter window
        self.Wind = PgPlotWindow()
        self.Wind.resize(1000, 750)
        self.Wind.setWindowTitle('Characterization Results')
        # Create Plots
        self.PlotIds = self.Wind.pgLayout.addPlot(col=0,
                                                  row=0,
                                                  rowspan=1,
                                                  colspan=2
                                                  )
        self.PlotIg = self.Wind.pgLayout.addPlot(col=2,
                                                 row=0,
                                                 rowspan=1,
                                                 colspan=1
                                                 )

        self.PlotLive = self.Wind.pgLayout.addPlot(col=0,
                                                   row=1,
                                                   # rowspan=1,
                                                   # colspan=2
                                                   )

        self.PlotPSD = self.Wind.pgLayout.addPlot(col=1,
                                                  row=1,
                                                  rowspan=1,
                                                  colspan=2
                                                  )

        self.PltIds = PlotDC(Plot=self.PlotIds,
                             PlotIg=self.PlotIg,
                             DevDCVals=DevDCVals,
                             ChViewConf=self.ViewConf.ChViewConf)
        self.ViewConf.NewConf.connect(self.on_new_view)

        self.PltLive = PlotLive(Plot=self.PlotLive,
                                DevDCVals=DevDCVals,
                                ChViewConf=self.ViewConf.ChViewConf)

        if self.ParWindow.ViewConfig.bPSD:
            self.PltPSD = PlotPSD(Plot=self.PlotPSD,
                                  DevACVals=DevACVals,
                                  ChViewConf=self.ViewConf.ChViewConf)
        else:
            self.PltPSD = None

        if self.ParWindow.ViewConfig.bGM:
            self.PlotGMM = self.Wind.pgLayout.addPlot(col=3,
                                                      row=0)
            self.PlotGMP = self.Wind.pgLayout.addPlot(col=3,
                                                      row=1)
            self.PltGM = PlotGM(PlotM=self.PlotGMM,
                                PlotP=self.PlotGMP,
                                DevACVals=DevACVals,
                                ChViewConf=self.ViewConf.ChViewConf)
        else:
            self.PltGM = None

    def on_new_view(self):
        self.RefreshPlot()

    def RefreshPlot(self):
        self.PltIds.Refresh()
        if self.PltPSD is not None:
            self.PltPSD.Refresh()
        if self.PltGM is not None:
            self.PltGM.Refresh()
