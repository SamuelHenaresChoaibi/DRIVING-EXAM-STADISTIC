from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow: QtWidgets.QMainWindow) -> None:  # noqa: N802
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1200, 800)

        self.actionImportCsv = QtGui.QAction(MainWindow)
        self.actionExit = QtGui.QAction(MainWindow)

        self.menubar = QtWidgets.QMenuBar(MainWindow)
        MainWindow.setMenuBar(self.menubar)
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menubar.addAction(self.menuFile.menuAction())

        self.menuFile.addAction(self.actionImportCsv)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)

        self.filtersGroup = QtWidgets.QGroupBox(self.centralwidget)
        self.filtersLayout = QtWidgets.QGridLayout(self.filtersGroup)

        self.yearLabel = QtWidgets.QLabel(self.filtersGroup)
        self.yearCombo = QtWidgets.QComboBox(self.filtersGroup)

        self.monthLabel = QtWidgets.QLabel(self.filtersGroup)
        self.monthCombo = QtWidgets.QComboBox(self.filtersGroup)

        self.provinceLabel = QtWidgets.QLabel(self.filtersGroup)
        self.provinceCombo = QtWidgets.QComboBox(self.filtersGroup)
        self.provinceCombo.setEditable(True)
        self.provinceCombo.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)

        self.centerLabel = QtWidgets.QLabel(self.filtersGroup)
        self.centerCombo = QtWidgets.QComboBox(self.filtersGroup)
        self.centerCombo.setEditable(True)
        self.centerCombo.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)

        self.examTypeLabel = QtWidgets.QLabel(self.filtersGroup)
        self.examTypeCombo = QtWidgets.QComboBox(self.filtersGroup)
        self.examTypeCombo.setEditable(True)
        self.examTypeCombo.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)

        self.permitLabel = QtWidgets.QLabel(self.filtersGroup)
        self.permitCombo = QtWidgets.QComboBox(self.filtersGroup)
        self.permitCombo.setEditable(True)
        self.permitCombo.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)

        self.schoolCodeLabel = QtWidgets.QLabel(self.filtersGroup)
        self.schoolCodeLineEdit = QtWidgets.QLineEdit(self.filtersGroup)
        self.schoolCodeLineEdit.setPlaceholderText("e.g. AB0198")

        self.schoolNameLabel = QtWidgets.QLabel(self.filtersGroup)
        self.schoolNameLineEdit = QtWidgets.QLineEdit(self.filtersGroup)
        self.schoolNameLineEdit.setPlaceholderText("contains...")

        self.applyButton = QtWidgets.QPushButton(self.filtersGroup)
        self.clearButton = QtWidgets.QPushButton(self.filtersGroup)

        self.exportPdfButton = QtWidgets.QToolButton(self.filtersGroup)
        self.exportPdfButton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.exportMenu = QtWidgets.QMenu(self.exportPdfButton)
        self.exportPdfTableAction = QtGui.QAction(self.exportMenu)
        self.exportPdfChartAction = QtGui.QAction(self.exportMenu)
        self.exportPdfBothAction = QtGui.QAction(self.exportMenu)
        self.exportMenu.addAction(self.exportPdfTableAction)
        self.exportMenu.addAction(self.exportPdfChartAction)
        self.exportMenu.addAction(self.exportPdfBothAction)
        self.exportPdfButton.setMenu(self.exportMenu)

        self.filtersLayout.addWidget(self.yearLabel, 0, 0)
        self.filtersLayout.addWidget(self.yearCombo, 0, 1)
        self.filtersLayout.addWidget(self.monthLabel, 0, 2)
        self.filtersLayout.addWidget(self.monthCombo, 0, 3)
        self.filtersLayout.addWidget(self.provinceLabel, 0, 4)
        self.filtersLayout.addWidget(self.provinceCombo, 0, 5)

        self.filtersLayout.addWidget(self.centerLabel, 1, 0)
        self.filtersLayout.addWidget(self.centerCombo, 1, 1, 1, 3)
        self.filtersLayout.addWidget(self.examTypeLabel, 1, 4)
        self.filtersLayout.addWidget(self.examTypeCombo, 1, 5)

        self.filtersLayout.addWidget(self.permitLabel, 2, 0)
        self.filtersLayout.addWidget(self.permitCombo, 2, 1)
        self.filtersLayout.addWidget(self.schoolCodeLabel, 2, 2)
        self.filtersLayout.addWidget(self.schoolCodeLineEdit, 2, 3)
        self.filtersLayout.addWidget(self.schoolNameLabel, 2, 4)
        self.filtersLayout.addWidget(self.schoolNameLineEdit, 2, 5)

        self.buttonsLayout = QtWidgets.QHBoxLayout()
        self.buttonsLayout.addStretch(1)
        self.buttonsLayout.addWidget(self.applyButton)
        self.buttonsLayout.addWidget(self.clearButton)
        self.buttonsLayout.addWidget(self.exportPdfButton)
        self.filtersLayout.addLayout(self.buttonsLayout, 3, 0, 1, 6)

        self.verticalLayout.addWidget(self.filtersGroup)

        self.tabs = QtWidgets.QTabWidget(self.centralwidget)
        self.tableTab = QtWidgets.QWidget()
        self.tableLayout = QtWidgets.QVBoxLayout(self.tableTab)
        self.tableView = QtWidgets.QTableView(self.tableTab)
        self.tableView.setSortingEnabled(True)
        self.tableLayout.addWidget(self.tableView)
        self.tabs.addTab(self.tableTab, "")

        self.chartTab = QtWidgets.QWidget()
        self.chartLayout = QtWidgets.QVBoxLayout(self.chartTab)
        self.chartContainer = QtWidgets.QWidget(self.chartTab)
        self.chartContainerLayout = QtWidgets.QVBoxLayout(self.chartContainer)
        self.chartLayout.addWidget(self.chartContainer)
        self.tabs.addTab(self.chartTab, "")

        self.verticalLayout.addWidget(self.tabs)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow: QtWidgets.QMainWindow) -> None:  # noqa: N802
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Driving Exams Statistics"))

        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionImportCsv.setText(_translate("MainWindow", "Import CSV..."))
        self.actionExit.setText(_translate("MainWindow", "Exit"))

        self.filtersGroup.setTitle(_translate("MainWindow", "Filters"))
        self.yearLabel.setText(_translate("MainWindow", "Year"))
        self.monthLabel.setText(_translate("MainWindow", "Month"))
        self.provinceLabel.setText(_translate("MainWindow", "Province"))
        self.centerLabel.setText(_translate("MainWindow", "Exam center"))
        self.examTypeLabel.setText(_translate("MainWindow", "Exam type"))
        self.permitLabel.setText(_translate("MainWindow", "Permit"))
        self.schoolCodeLabel.setText(_translate("MainWindow", "School code"))
        self.schoolNameLabel.setText(_translate("MainWindow", "School name"))

        self.applyButton.setText(_translate("MainWindow", "Apply"))
        self.clearButton.setText(_translate("MainWindow", "Clear"))

        self.exportPdfButton.setText(_translate("MainWindow", "Export PDF"))
        self.exportPdfTableAction.setText(_translate("MainWindow", "Table"))
        self.exportPdfChartAction.setText(_translate("MainWindow", "Chart"))
        self.exportPdfBothAction.setText(_translate("MainWindow", "Table + Chart"))

        self.tabs.setTabText(self.tabs.indexOf(self.tableTab), _translate("MainWindow", "Table"))
        self.tabs.setTabText(self.tabs.indexOf(self.chartTab), _translate("MainWindow", "Chart"))

