from PyQt5 import QtWidgets

from kataja.singletons import prefs, ctrl
from kataja.ui.panels.UIPanel import UIPanel
from PyQt5 import QtMultimedia, QtMultimediaWidgets

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
        layout = QtWidgets.QVBoxLayout()
        widget = QtWidgets.QWidget(self)
        #layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        cameras = QtMultimedia.QCameraInfo.availableCameras()
        camera = None
        for caminfo in cameras:
            camera = QtMultimedia.QCamera(caminfo)
            break
        if camera:
            print('adding camera: ', camera)
            viewfinder = QtMultimediaWidgets.QCameraViewfinder()
            viewfinder.setFixedWidth(220)
            viewfinder.setFixedHeight(179)
            camera.setViewfinder(viewfinder)
            layout.addWidget(viewfinder)
            viewfinder.show()
            camera.start()
            self.camera = camera # if the reference is lost, camera shuts down
        widget.setLayout(layout)

        self.setWidget(widget)
        self.finish_init()

