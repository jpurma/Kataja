from PyQt5 import QtWidgets, QtMultimedia, QtMultimediaWidgets

from kataja.singletons import prefs, ctrl
from kataja.ui.panels.UIPanel import UIPanel

__author__ = 'purma'


class FaceCamPanel(UIPanel):
    """ Experimental panel for having a face cam window for screen casting. Not used for now.
    """

    def __init__(self, name, key, default_position='float', parent=None, ui_manager=None,
                 folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """

        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        self.camera = None
        layout = QtWidgets.QVBoxLayout()
        widget = QtWidgets.QWidget()
        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.viewfinder = QtMultimediaWidgets.QCameraViewfinder()
        self.viewfinder.setFixedWidth(220)
        self.viewfinder.setFixedHeight(179)
        layout.addWidget(self.viewfinder)
        widget.setLayout(layout)
        self.activate_camera()
        self.setWidget(widget)
        self.finish_init()
        self.releaseMouse()

    def activate_camera(self):
        cameras = QtMultimedia.QCameraInfo.availableCameras()
        for caminfo in cameras:
            self.camera = QtMultimedia.QCamera(caminfo)
            self.camera.setCaptureMode(QtMultimedia.QCamera.CaptureViewfinder)
            break
        if self.camera:
            self.camera.setViewfinder(self.viewfinder)

    def showEvent(self, event):
        self.camera.start()
        UIPanel.showEvent(self, event)

    def closeEvent(self, event):
        self.camera.stop()
        UIPanel.closeEvent(self, event)

    def hideEvent(self, event):
        self.camera.stop()
        UIPanel.hideEvent(self, event)
