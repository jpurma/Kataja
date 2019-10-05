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

import subprocess
import tempfile

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
from PIL import Image

from kataja.singletons import ctrl, prefs, log


class Recorder:
    def __init__(self, scene):
        self.scene = scene
        self.recording = False
        self.frame_count = 0
        self.width = 640
        self.height = 480
        self.every_nth = 1
        self.frames = []
        self.gif = True
        self.webp = False

    def start_recording(self, width=640, height=480, every_nth=1, gif=True, webp=False):
        self.frame_count = 0
        self.recording = True
        self.frames = []
        self.width = width
        self.height = height
        self.every_nth = int(every_nth) or 1
        self.gif = gif
        self.webp = webp
        for node in ctrl.forest.nodes.values():
            node.setCacheMode(QtWidgets.QGraphicsItem.NoCache)
        # record initial frame before the animations start
        self.record_frame()

    def stop_recording(self):
        outfile = prefs.animation_file_name
        self.recording = False
        max_w = 0
        max_h = 0
        final_rest_frames = 30
        self.frames = [self.frames[0]] + self.frames + [self.frames[-1]]
        log.info(f'  Writing {len(self.frames)} animation frames...')
        fname = ''
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
                    new_w = int(r * w)
                    new_h = int(r * h)
                    top_left = (int((new_w - max_w) / 2), int((new_h - max_h) / 2))
                    log.info(f'resizing frame: {(new_w, new_h)}, top_left: {top_left}')
                    new_image = image.resize((new_w, new_h))
                    background = Image.new('RGBA', (max_w, max_h), ctrl.cm.paper().getRgb())
                    background.paste(new_image, top_left)
                    background = background.quantize(64)
                    resized.append(background)
                else:
                    resized.append(image.quantize(64))
            if resized:
                log.info(f'Adding {final_rest_frames} frames to end.')
                last_image = resized[-1]
                for i in range(0, final_rest_frames):
                    resized.append(last_image)
            if self.gif:
                fname = outfile + '.gif'
                resized[0].save(fname,
                                save_all=True,
                                append_images=resized[1:],
                                delay=0.3,
                                loop=1,
                                optimize=True)
                log.info(f'  Gif recorded as {repr(fname)}')
            if self.webp:
                fname_w = outfile + '.webp'
                resized[0].save(fname_w,
                                save_all=True,
                                append_images=resized[1:],
                                delay=0.3,
                                loop=1,
                                optimize=True)
                log.info(f'  WebP recorded as {repr(fname_w)}')
        if self.gif:
            self.try_optimising_with_gifsicle(fname)
        self.frames = []

    def record_frame(self):
        if self.frame_count % self.every_nth == 0:
            source = ctrl.main.view_manager.print_rect()
            self.frames.append(self._write_frame(source))
        self.frame_count += 1
        if len(self.frames) == prefs.animation_max_frames:
            log.info('  Stopping recording, max frame count reached '
                     f'({prefs.animation_max_frames}).')
            self.stop_recording()

    def _write_frame(self, source):
        sw = source.width()
        sh = source.height()
        max_w = self.width
        max_h = self.height
        iw = max_w / sw
        ih = max_h / sh
        r = iw if iw < ih else ih
        new_w = int(r * sw)
        new_h = int(r * sh)
        left = int((max_w - new_w) / 2)
        top = int((max_h - new_h) / 2)

        target = QtCore.QRectF(left, top, max_w, max_h)

        image = QtGui.QImage(target.size().toSize(), QtGui.QImage.Format_ARGB32_Premultiplied)
        image.fill(ctrl.cm.paper())
        painter = QtGui.QPainter()
        painter.begin(image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        self.scene.render(painter, source=source, target=target)
        painter.end()
        return image

    @staticmethod
    def try_optimising_with_gifsicle(gifname):
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
