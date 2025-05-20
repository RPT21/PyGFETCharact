# -*- coding: utf-8 -*-
"""

@author: aguimera
"""

import pyqtgraph.parametertree.parameterTypes as pTypes

SamplingSettingsPars = ({'title': 'Sampling Freq.',
                         'name': 'Fs',
                         'type': 'float',
                         'value': 20e3,
                         'default': 20e3,
                         'step': 1e3,
                         'siPrefix': True,
                         'suffix': 'Hz'
                         },
                        {'title': 'Acqisition Buffer',
                         'name': 'EverySamps',
                         'type': 'int',
                         'value': 10e3,
                         'default': 10e3,
                         },
                        {'title': 'Interrupt time',
                         'name': 'intTime',
                         'type': 'float',
                         'siPrefix': True,
                         'suffix': 's',
                         'readonly': True,
                         },
                        {'title': 'View Buffer time',
                         'name': 'tBufferView',
                         'type': 'float',
                         'value': 60,
                         'siPrefix': True,
                         'suffix': 's',
                         },
                        {'title': 'View Buffer',
                         'name': 'ViewBuffer',
                         'type': 'int',
                         'readonly': True,
                         },
                        )


class SamplingSettingsConfig(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        self.addChildren(SamplingSettingsPars)
        self.param('Fs').sigValueChanged.connect(self.on_FsChange)
        self.param('EverySamps').sigValueChanged.connect(self.on_FsChange)
        self.param('tBufferView').sigValueChanged.connect(self.on_BufferViewChange)
        self.on_FsChange()

    def on_FsChange(self):
        Fs = self.param('Fs').value()
        nSamps = self.param('EverySamps').value()
        self.param('intTime').setValue(nSamps / Fs)

    def on_BufferViewChange(self):
        Fs = self.param('Fs').value()
        ViewTime = self.param('tBufferView').value()
        self.param('ViewBuffer').setValue(ViewTime * Fs)

    def GetParams(self):
        Params = {}
        for p in self.children():
            if p.readonly():
                continue
            Params[p.name()] = p.value()
        return Params


BiasSettingsPars = ({'title': 'Vgs',
                     'name': 'Vgs',
                     'value': 0.1,
                     'default': 0.1,
                     'step': 0.01,
                     'type': 'float',
                     'siPrefix': True,
                     'suffix': 'V'
                     },
                    {'title': 'Vds',
                     'name': 'Vds',
                     'value': 0.05,
                     'default': 0.05,
                     'step': 0.001,
                     'type': 'float',
                     'siPrefix': True,
                     'suffix': 'V'
                     },)


class BiasSettingsConfig(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        self.addChildren(BiasSettingsPars)

    def GetParams(self):
        Params = {}
        for p in self.children():
            if p.readonly():
                continue
            Params[p.name()] = p.value()
        return Params
