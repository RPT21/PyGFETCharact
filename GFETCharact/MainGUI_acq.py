# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 10:26:32 2020

@author: aguimera
"""
#

from PyQt5 import Qt
from qtpy import QtWidgets

from pyqtgraph.parametertree import ParameterTree, Parameter

from GFETCharact.ParamConf.FileModule import SaveDataParams
from GFETCharact.ParamConf.HardwareConf import HardwareConfig
from GFETCharact.ParamConf.SamplingSettings import SamplingSettingsConfig, BiasSettingsConfig
from GFETCharact.AcquisitionCore import AdquisitionCore

import sys

_version = '0.1.b5'


class MainWindow(Qt.QWidget):
    ''' Main Window '''

    def __init__(self):
        super(MainWindow, self).__init__()
        layout = Qt.QVBoxLayout(self)

        self.setGeometry(650, 20, 400, 800)
        self.setWindowTitle('Signal Acquisition v' + _version)

        # Add objects to main window
        # start Button
        self.btnAcq = Qt.QPushButton("Start Acquisition")
        layout.addWidget(self.btnAcq)

        self.InfoStr = Parameter.create(**{'name': 'InfoStr',
                                           'title': 'Status Info',
                                           'type': 'text',
                                           'expanded': True,
                                           'readonly': True})

        self.SaveFileConf = SaveDataParams(QTparent=self,
                                           name='SaveFileConf',
                                           title='Save Data',
                                           expanded=True)

        self.HardConf = HardwareConfig(name='HardConf',
                                       title='Hardware Config')

        self.HardConf.param('BoardSel').setValue('MB42')

        self.SamplingConf = SamplingSettingsConfig(name='SamplingConf',
                                                   title='Sampling Settings')

        self.BiasConf = BiasSettingsConfig(name='BiasConf',
                                           title='Bias Settings')

        self.Parameters = Parameter.create(name='App Parameters',
                                           type='group',
                                           children=(
                                               self.InfoStr,
                                               self.HardConf,
                                               self.SamplingConf,
                                               self.BiasConf,
                                               self.SaveFileConf,
                                           ))

        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)

        layout.addWidget(self.treepar)

        self.AcqTime = AdquisitionCore(SamplingConf=self.SamplingConf)

        self.btnAcq.clicked.connect(self.on_btnStart)

    def on_btnStart(self):
        if self.AcqTime.AdcRunning:
            self.AcqTime.StopCharact()
        else:
            # if not self.SaveFileConf.param('bSave').value():
            #     self.SaveFileConf.on_Save()
            #
            # self.SaveFileConf.CheckFile()
            # FileName = self.SaveFileConf.FileName
            self.AcqTime.StartAcquisition(HardConf=self.HardConf.param('BoardConf'))
            self.btnAcq.setText('Stop Measure')


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
