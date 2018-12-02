from PyQt5 import QtWidgets, QtMultimedia, QtMultimediaWidgets

from kataja.ui_widgets.Panel import Panel
import kataja.globals as g

__author__ = 'purma'


class FaceCamPanel(Panel):
    """ Experimental panel for having a face cam window for screen casting. Not used for now.
    """

    def __init__(self, name, default_position='float', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """

        Panel.__init__(self, name, default_position, parent, folded)
        self.camera = None
        self.aspect = 1.333333333
        self.camera_width = 320
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.viewfinder = QtMultimediaWidgets.QCameraViewfinder()
        self.vlayout.addWidget(self.viewfinder)
        self.activate_camera()
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
        self.camera.load()
        sizes = self.camera.supportedViewfinderResolutions()
        if sizes:
            size = sizes[-1]
            if size.height() and size.width():
                self.aspect = float(size.width()) / size.height()
            else:
                self.aspect = 1.333333333
        else:
            self.aspect = 1.333333333
        self.viewfinder.setFixedWidth(self.camera_width)
        self.viewfinder.setFixedHeight(self.camera_width / self.aspect)

    def showEvent(self, event):
        self.camera.start()
        Panel.showEvent(self, event)

    def closeEvent(self, event):
        self.camera.stop()
        Panel.closeEvent(self, event)

    def hideEvent(self, event):
        self.camera.stop()
        Panel.hideEvent(self, event)
