# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 10:56:29 2020

@author: Javier
"""

# from PyQt5 import Qt
import pyqtgraph.parametertree.parameterTypes as pTypes
from PyQt5 import Qt

import GFETCharact.ParamConf.HwConfig as BoardConf


class HwGainsConfig(pTypes.GroupParameter):
    def __init__(self, Gains, **kwargs):
        super(HwGainsConfig, self).__init__(**kwargs)
        for n, v in Gains.items():
            self.addChild({'name': n,
                           'type': 'float',
                           'value': v,
                           'default': v,
                           'siPrefix': True,
                           'suffix': ' '}, )

    def GetGains(self):
        Gains = {}
        for p in self.children():
            Gains[p.name()] = p.value()
        return Gains


class AInputsConfig(pTypes.GroupParameter):
    def __init__(self, AInputs, **kwargs):
        super(AInputsConfig, self).__init__(**kwargs)

        self.addChild({'name': 'SelAll',
                       'type': 'action',
                       'title': 'Un-Select all'})
        self.addChild({'name': 'SelInvert',
                       'type': 'action',
                       'title': 'Invert Selection'})
        self.seltrufalse = True
        self.param('SelAll').sigActivated.connect(self.on_SelAll)
        self.param('SelInvert').sigActivated.connect(self.on_SelInvert)

        for n, v in sorted(AInputs.items()):
            self.addChild({'name': n,
                           'type': 'bool',
                           'value': True,
                           'aiDC': v[0],
                           'aiAC': v[-1],
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

    def GetDCChannels(self):
        DCChannels = {}
        for p in self.children():
            if p.type() == 'action':
                continue
            if p.value():
                DCChannels[p.name()] = p.opts['aiDC']
        return DCChannels

    def GetACChannels(self):
        ACChannels = {}
        for p in self.children():
            if p.type() == 'action':
                continue
            if p.value():
                ACChannels[p.name()] = p.opts['aiAC']
        return ACChannels


class AOutputsConfig(pTypes.GroupParameter):
    def __init__(self, AOutputs, **kwargs):
        super(AOutputsConfig, self).__init__(**kwargs)
        for n, v in AOutputs.items():
            self.addChild({'name': n,
                           'type': 'str',
                           'value': v,
                           }, )

    def GetAOuts(self):
        Aouts = {}
        for p in self.children():
            Aouts[p.name()] = p.value()
        return Aouts


class DOutputsConfig(pTypes.GroupParameter):
    def __init__(self, DOutputs, **kwargs):
        super(DOutputsConfig, self).__init__(**kwargs)
        self.douts = DOutputs['douts']

        self.Cols = DOutputs['Columns']
        for n, v in sorted(self.Cols.items()):
            self.addChild({'name': v,
                           'type': 'bool',
                           'value': True,
                           'DoKey': n,
                           }, )

        self.DigitalSignals = DOutputs['DigitalSignal']
        SignalChilds = []
        j = 0
        for i in DOutputs['DigitalSignal']:
            SignalChilds.append({'name': str(i),
                                 'type': 'str',
                                 'readonly': True,
                                 'value': str(DOutputs['Columns'][j]),
                                 }, )
            j += 1

        self.addChild({'name': 'douts',
                       'type': 'str',
                       'readonly': True,
                       'value': str(DOutputs['douts']),
                       })

        self.addChild({'name': 'States',
                       'type': 'group',
                       'expanded': True,
                       'children': SignalChilds,
                       })

    def GetDOColumns(self):
        DOColumns = {}
        for p in self.children():
            if p.value():
                DOColumns[p.name()] = p.opts['DoKey']
        return DOColumns


class ACDCSwitchConfig(pTypes.GroupParameter):
    def __init__(self, ACDCSwitch, **kwargs):
        super(ACDCSwitchConfig, self).__init__(**kwargs)

        self.douts = ACDCSwitch['douts']
        self.addChild({'name': 'douts',
                       'type': 'str',
                       'readonly': True,
                       'value': str(ACDCSwitch['douts']),
                       })
        self.GateAI = ACDCSwitch['GateAI']
        self.addChild({'name': 'GateAI',
                       'type': 'str',
                       'readonly': True,
                       'value': str(ACDCSwitch['GateAI']),
                       })

        self.States = ACDCSwitch['states']
        StateChilds = []
        for n, v in ACDCSwitch['states'].items():
            StateChilds.append({'name': n,
                                'type': 'str',
                                'readonly': True,
                                'value': str(v),
                                }, )
        self.addChild({'name': 'States',
                       'type': 'group',
                       'expanded': True,
                       'children': StateChilds,
                       })


class BoardConfig(pTypes.GroupParameter):
    def __init__(self, Board, **kwargs):
        super(BoardConfig, self).__init__(**kwargs)

        self.Gains = HwGainsConfig(Gains=Board['Gains'],
                                   name='Gains',
                                   expanded=False, )
        self.AInputs = AInputsConfig(AInputs=Board['AnalogInputs'],
                                     name='AInputs',
                                     title='Analog Inputs',
                                     expanded=False, )
        self.AOutputs = AOutputsConfig(AOutputs=Board['AnalogOutputs'],
                                       name='AOutputs',
                                       title='Analog Outputs',
                                       expanded=False, )
        self.addChildren((self.Gains,
                          self.AInputs,
                          self.AOutputs))

        if 'DigitalOutputs' in Board:
            self.DOutputs = DOutputsConfig(DOutputs=Board['DigitalOutputs'],
                                           name='DOutputs',
                                           title='Digital Outputs',
                                           expanded=False, )
            self.addChildren((self.DOutputs,))
        else:
            self.DOutputs = None

        if 'ACDCSwitch' in Board:
            self.ACDCSwitch = ACDCSwitchConfig(ACDCSwitch=Board['ACDCSwitch'],
                                               name='ACDCSwitch',
                                               # title='Analog Outputs',
                                               expanded=False, )
            self.addChildren((self.ACDCSwitch,))
        else:
            self.ACDCSwitch = None


class HardwareConfig(pTypes.GroupParameter):
    on_board_sel = Qt.pyqtSignal(object)

    def __init__(self, **kwargs):
        super(HardwareConfig, self).__init__(**kwargs)
        self.addChild({'name': 'BoardSel',
                       'title': 'Board Selection',
                       'type': 'list',
                       'limits': list(BoardConf.Boards.keys()),
                       'value': list(BoardConf.Boards.keys())[0]
                       })

        self.param('BoardSel').sigValueChanged.connect(self.on_BoardSel)
        self.Add_Board()

    def on_BoardSel(self):
        self.param('BoardConf').remove()
        self.Add_Board()
        self.on_board_sel.emit(self.param('BoardConf'))

    def Add_Board(self):
        Board = self.param('BoardSel').value()
        self.addChild(BoardConfig(Board=BoardConf.Boards[Board],
                                  name='BoardConf',
                                  title='Hardware Configuration'))
