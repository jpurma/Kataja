#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2013 Jukka Purma
#
# This file is part of Kataja.
#
# Kataja is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kataja is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kataja.  If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice

from kataja.singletons import ctrl, prefs, log
from PIL import Image

import io

GIF = True
WEBP = False


class Recorder:
    def __init__(self, scene):
        self.scene = scene
        self.stopped = True
        self.frame_count = 0
        self.frames = []

    def start_recording(self):
        self.frame_count = 0
        self.stopped = False
        self.frames = []
        for node in ctrl.forest.nodes.values():
            node.setCacheMode(QtWidgets.QGraphicsItem.NoCache)

    def stop_recording(self):
        outfile = prefs.animation_file_name
        self.stopped = True
        images = []
        max_w = 0
        max_h = 0
        log.info(f'  Writing {len(self.frames)} animation frames...')
        for image in self.frames:
            ba = QByteArray()
            buffer = QBuffer(ba)
            buffer.open(QIODevice.WriteOnly)
            image.save(buffer, "PNG")
            pil_image = Image.open(io.BytesIO(ba))
            images.append(pil_image)
            w, h = pil_image.size
            if w > max_w:
                max_w = w
            if h > max_h:
                max_h = h
        if images:
            log.info('  Resizing and adjusting...')
            resized = []
            for image in images:
                w, h = image.size
                iw = max_w / w
                ih = max_h / h
                r = iw if iw < ih else ih
                new_image = image.resize((int(r * w), int(r * h)))
                background = Image.new('RGBA', (max_w, max_h), ctrl.cm.paper().getRgb())
                background.paste(new_image)
                background = background.quantize(64)
                resized.append(background)
            if GIF:
                fname = outfile + '.gif'
                resized[0].save(fname,
                                save_all=True,
                                append_images=resized[1:],
                                delay=0.1,
                                loop=0,
                                optimize=True)
            if WEBP:
                fname = outfile + '.webp'
                resized[0].save(fname,
                                save_all=True,
                                append_images=resized[1:],
                                delay=0.1,
                                loop=0,
                                optimize=True)
        log.info(f'  Done. Written to {repr(fname)}')
        self.frames = []

    def record_frame(self):
        source = ctrl.main.view_manager.print_rect()
        self.frames.append(self._write_frame(source))
        self.frame_count += 1
        if prefs.max_animation_frames == self.frame_count:
            log.info('  Stopping recording, max frame count reached '
                     f'({prefs.max_animation_frames}).')
            self.stop_recording()

    def _write_frame(self, source):
        image = QtGui.QImage(source.size().toSize(), QtGui.QImage.Format_ARGB32_Premultiplied)
        image.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter()
        painter.begin(image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        self.scene.render(painter, source=source)
        painter.end()
        return image
