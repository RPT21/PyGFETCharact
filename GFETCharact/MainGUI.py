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
from GFETCharact.ParamConf.FileModule import SaveSateParams
from GFETCharact.ParamConf.SweepsConf import SweepsConfig
from GFETCharact.ParamConf.HardwareConf import HardwareConfig
from GFETCharact.CracterizationCore import CharacterizationMachine

import sys

_version = '0.1.b5'


class MainWindow(Qt.QWidget):
    ''' Main Window '''

    def __init__(self):
        super(MainWindow, self).__init__()
        layout = Qt.QVBoxLayout(self)

        self.setGeometry(650, 20, 400, 800)
        self.setWindowTitle('GFET Characterization v' + _version)

        # Add objects to main window
        # start Button
        self.btnAcq = Qt.QPushButton("Start Measure")
        layout.addWidget(self.btnAcq)

        self.InfoStr = Parameter.create(**{'name': 'InfoStr',
                                           'title': 'Status Info',
                                           'type': 'text',
                                           'expanded': True,
                                           'readonly': True})

        self.SaveStateConf = SaveSateParams(QTparent=self,
                                            name='SaveStateConf',
                                            title='Save Load State',
                                            expanded=False)

        self.SaveFileConf = SaveDataParams(QTparent=self,
                                           name='SaveFileConf',
                                           title='Save Data',
                                           expanded=True)

        self.HardConf = HardwareConfig(name='HardConf',
                                       title='Hardware Config')

        self.SweepsConf = SweepsConfig(HardConf=self.HardConf,
                                       name='SweepsConfig',
                                       title='Characterization Configuration')

        self.Parameters = Parameter.create(name='App Parameters',
                                           type='group',
                                           children=(
                                               self.InfoStr,
                                               self.HardConf,
                                               self.SweepsConf,
                                               self.SaveFileConf,
                                               self.SaveStateConf,
                                           ))

        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)

        layout.addWidget(self.treepar)

        self.Charact = CharacterizationMachine(SweepsConf=self.SweepsConf,
                                               InfoOut=self.InfoStr)

        self.Charact.CharactFinished.connect(self.on_CharactFinished)
        self.btnAcq.clicked.connect(self.on_btnStart)

    def on_btnStart(self):
        if self.Charact.ChactRunning:
            self.SweepsConf.Cycles.setValue(1)
            self.Charact.StopCharact()
        else:
            if not self.SaveFileConf.param('bSave').value():
                self.SaveFileConf.on_Save()

            self.SaveFileConf.CheckFile()
            FileName = self.SaveFileConf.FileName
            self.Charact.StartCharact(HardConf=self.HardConf,
                                      FileName=FileName)
            self.btnAcq.setText('Stop Measure')

    def on_CharactFinished(self):
        self.btnAcq.setText('Start Measure')
        Cy = self.SweepsConf.Cycles.value() - 1
        self.SweepsConf.Cycles.setValue(Cy)
        if Cy > 0:
            self.on_btnStart()


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
