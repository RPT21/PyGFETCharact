# -*- coding: utf-8 -*-
"""
Created on Tue Feb  1 10:20:05 2022

@author: Anton Guimerà Brunet
"""

import numpy as np
import datetime
import pickle


class CharactFile():
    def __init__(self, FileName, SweepConf, ChNames):
        self.FileName = FileName
        Time = datetime.datetime.now()

        self.ChNames = ChNames
        VgsSw = SweepConf['VgsSw']
        VdsSw = SweepConf['VdsSw']
        self.DictDC = {}
        IdsShape = (len(VgsSw), len(VdsSw))
        for ch in ChNames:
            self.DictDC[ch] = {'Ids': np.ones(IdsShape)*np.NaN,
                               'Slope': np.ones(IdsShape)*np.NaN,
                               'Vds': VdsSw,
                               'Vgs': VgsSw,
                               'ChName': ch,
                               'Name': ch,
                               'DateTime': Time}

        if SweepConf['Gate']:
            self.DictDC['Gate'] = {'Ig': np.ones(IdsShape)*np.NaN,
                                   'Vds': VdsSw,
                                   'Vgs': VgsSw,
                                   'ChName': 'Gate',
                                   'Name': 'Gate',
                                   'DateTime': Time}

        if 'VgsSwAC' in SweepConf:
            self.DictAC = {}
            VgsSwAC = SweepConf['VgsSwAC']

            for ch in ChNames:
                Vals = {'VgsAC': VgsSwAC,
                        'VdsAC': VdsSw,
                        'ChName': ch,
                        'Name': ch,
                        'DateTime': Time}

                if 'PSDKwarg' in SweepConf:
                    nFpsd = SweepConf['PSDKwarg']['Freqs']
                    PSDshape = (len(VgsSwAC), nFpsd.size)
                    noise = {}
                    for i in range(VdsSw.size):
                        noise['Vd{}'.format(i)] = np.ones(PSDshape) * np.NaN
                    Vals['Fpsd'] = nFpsd
                    Vals['PSD'] = noise

                if 'BodeKwarg' in SweepConf:
                    nFgm = SweepConf['BodeKwarg']['Freqs']
                    gm = {}
                    BodeShape = (len(VgsSwAC), nFgm.size)
                    for i in range(VdsSw.size):
                        gm['Vd{}'.format(i)] = np.ones(BodeShape) * np.NaN * np.complex(1)
                    Vals['Fgm'] = nFgm
                    Vals['gm'] = gm

                self.DictAC[ch] = Vals
        else:
            self.DictAC = None

    def SavePickle(self):
        if self.FileName is not None:
            Data = {'DevDC': self.DictDC,
                    'DevAC': self.DictAC}
            pickle.dump(Data, open(self.FileName, 'wb'))
