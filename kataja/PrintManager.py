import os

from PyQt5 import QtCore, QtWidgets, QtGui

from kataja.singletons import ctrl, prefs, running_environment, log
from kataja.utils import find_free_filename


class PrintManager:
    def __init__(self):
        self.print_started = False

    # Printing ###################################

    def start_printing(self):
        """ Starts the printing process.
         1st step is to clean the scene for a printing and display the printed
         area -frame.
         2nd step: after 50ms remove printed area -frame and prints to pdf,
         and write the file.

         2nd step is triggered by a timer in main window.
         :return: None
        """
        sc = ctrl.graph_scene
        # hide unwanted components
        no_brush = QtGui.QBrush(QtCore.Qt.NoBrush)
        sc.setBackgroundBrush(no_brush)
        sc.photo_frame = sc.addRect(ctrl.view_manager.print_rect().adjusted(-1, -1, 2, 2), ctrl.cm.selection())
        sc.update()
        for node in ctrl.forest.nodes.values():
            node.setCacheMode(QtWidgets.QGraphicsItem.NoCache)
        ctrl.graph_view.repaint()
        self.print_started = True  # to avoid a bug where other timers end up triggering main's
        ctrl.main.startTimer(50)

    def snapframe_timer(self, event):
        """ for 'snapshot' effect
        :param event:
        """

        if not self.print_started:
            return
        else:
            self.print_started = False
        ctrl.main.killTimer(event.timerId())
        # Prepare file and path
        path = prefs.userspace_path or running_environment.default_userspace_path
        if not os.path.exists(path):
            print("bad path for printing (userspace_path in preferences) , "
                  "using '.' instead.")
            path = '.'
        # Prepare image
        ctrl.graph_scene.removeItem(ctrl.graph_scene.photo_frame)
        ctrl.graph_scene.photo_frame = None
        self.print_to_file(path, prefs.print_file_name)

    def print_all(self, path, filename='output_trees.pdf'):
        """ If there """
        doc = ctrl.document
        if len(ctrl.document.forests) > 1:
            base_part, suffix = filename.rsplit('.')
            os.makedirs(base_part, exist_ok=True)
            for i, forest in enumerate(doc.forests):
                doc.set_forest(forest)
                filename = os.path.join(base_part, f'{i}.{suffix}')
                self.print_to_file(path, filename, overwrite=True)
        else:
            self.print_to_file(path, filename, overwrite=True)

    def print_to_file(self, path, filename, overwrite=False):
        if filename.endswith(('.pdf', '.png')):
            filename = filename[:-4]
        # Prepare printer
        png = prefs.print_format == 'png'
        suffix = '.png' if png else '.pdf'
        source = ctrl.view_manager.print_rect()

        for node in ctrl.forest.nodes.values():
            node.setCacheMode(QtWidgets.QGraphicsItem.NoCache)

        if overwrite:
            write_path = os.path.join(path, f'{filename}{suffix}')
        else:
            write_path = find_free_filename(os.path.join(path, filename), suffix, 0)

        if png:
            self._write_png(source, write_path)
        else:
            self._write_pdf(source, write_path)

        # Restore image
        for node in ctrl.forest.nodes.values():
            node.setCacheMode(QtWidgets.QGraphicsItem.DeviceCoordinateCache)
        ctrl.graph_scene.setBackgroundBrush(ctrl.cm.gradient)

    def _write_png(self, source, write_path):
        scale = 4
        target = QtCore.QRectF(QtCore.QPointF(0, 0), source.size() * scale)
        writer = QtGui.QImage(target.size().toSize(), QtGui.QImage.Format_ARGB32_Premultiplied)
        writer.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter()
        painter.begin(writer)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

        ctrl.graph_scene.render(painter, target=target, source=source)
        painter.end()
        iwriter = QtGui.QImageWriter(write_path)
        iwriter.write(writer)
        msg = f"printed to {write_path} as PNG ({int(target.width())}px x {int(target.height())}px, {scale}x size)."
        print(msg)
        log.info(msg)

    def _write_pdf(self, source, write_path):
        dpi = 25.4
        target = QtCore.QRectF(0, 0, source.width() / 2.0, source.height() / 2.0)

        writer = QtGui.QPdfWriter(write_path)
        writer.setResolution(dpi)
        writer.setPageSizeMM(target.size())
        writer.setPageMargins(QtCore.QMarginsF(0, 0, 0, 0))
        ctrl.printing = True
        painter = QtGui.QPainter()
        painter.begin(writer)
        # painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        ctrl.graph_scene.render(painter, target=target, source=source)
        painter.end()
        ctrl.printing = False
        msg = f"printed to {write_path} as PDF with {dpi} dpi."
        print(msg)
        log.info(msg)
