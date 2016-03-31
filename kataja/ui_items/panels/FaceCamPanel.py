from PyQt5 import QtWidgets, QtMultimedia, QtMultimediaWidgets

from ui_items.Panel import Panel

__author__ = 'purma'


class FaceCamPanel(Panel):
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

        Panel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        self.camera = None
        self.aspect = 1.333333333
        self.camera_width = 320
        layout = QtWidgets.QVBoxLayout()
        widget = QtWidgets.QWidget()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.viewfinder = QtMultimediaWidgets.QCameraViewfinder()
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
        self.camera.load()
        sizes = self.camera.supportedViewfinderResolutions()
        if sizes:
            size = sizes[-1]
            self.aspect = float(size.width()) / size.height()
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
