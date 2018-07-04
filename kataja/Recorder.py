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

from kataja.singletons import ctrl, prefs, log
from PIL import Image

import tempfile
import subprocess

GIF = True
WEBP = False
TARGET_SIZE = (640, 480)


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
        # record initial frame before the animations start
        self.record_frame()

    def stop_recording(self):
        outfile = prefs.animation_file_name
        self.stopped = True
        max_w = 0
        max_h = 0
        self.frames = [self.frames[0]] + self.frames + [self.frames[-1]]
        log.info(f'  Writing {len(self.frames)} animation frames...')
        with tempfile.TemporaryDirectory() as tmpdirname:
            for i, image in enumerate(self.frames):
                w = image.width()
                h = image.height()
                if w > max_w:
                    max_w = w
                if h > max_h:
                    max_h = h
                image.save(f'{tmpdirname}/buffer{i}.png')
            resized = []
            count = len(self.frames)
            self.frames = []
            log.info('  Loading and resizing images...')
            for i in range(0, count):
                image = Image.open(f'{tmpdirname}/buffer{i}.png')
                w, h = image.size
                if w != max_w or h != max_h:
                    iw = max_w / w
                    ih = max_h / h
                    r = iw if iw < ih else ih
                    new_image = image.resize((int(r * w), int(r * h)))
                    background = Image.new('RGBA', (max_w, max_h), ctrl.cm.paper().getRgb())
                    background.paste(new_image)
                    background = background.quantize(64)
                    resized.append(background)
                else:
                    resized.append(image.quantize(64))
            if GIF:
                fname = outfile + '.gif'
                resized[0].save(fname,
                                save_all=True,
                                append_images=resized[1:],
                                delay=0.1,
                                loop=0,
                                optimize=True)
            if WEBP:
                fname_w = outfile + '.webp'
                resized[0].save(fname_w,
                                save_all=True,
                                append_images=resized[1:],
                                delay=0.1,
                                loop=0,
                                optimize=True)
        log.info(f'  Done. Written to {repr(fname)}')
        if GIF:
            self.try_gifsicle(fname)
        self.frames = []

    def try_gifsicle(self, gifname):
        commands = ['gifsicle', './gifsicle']
        command = None
        for candidate in commands:
            completed = subprocess.run(['which', candidate])
            if completed.returncode == 0:
                command = candidate
                break
        if command:
            ofile = open('o_' + gifname, 'wb')
            result = subprocess.run([command, '-O3', gifname], stdout=ofile, stderr=subprocess.PIPE)
            ofile.close()
            if result.returncode == 0:
                log.info(f'Writing optimized gif as o_{gifname}')

    def record_frame(self):
        source = ctrl.main.view_manager.print_rect()
        self.frames.append(self._write_frame(source))
        self.frame_count += 1
        if prefs.max_animation_frames == self.frame_count:
            log.info('  Stopping recording, max frame count reached '
                     f'({prefs.max_animation_frames}).')
            self.stop_recording()

    def _write_frame(self, source):
        target = QtCore.QRectF(0, 0, TARGET_SIZE[0], TARGET_SIZE[1])
        image = QtGui.QImage(target.size().toSize(), QtGui.QImage.Format_ARGB32_Premultiplied)
        image.fill(ctrl.cm.paper())
        painter = QtGui.QPainter()
        painter.begin(image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        self.scene.render(painter, source=source, target=target)
        painter.end()
        return image
