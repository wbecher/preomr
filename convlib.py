# -*- coding: iso-8859-15 -*
# Copyright (C) 2009 S�ren Bjerregaard Vrist
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import logging
import os
import sys
import os
import random
import time
from subprocess import Popen,PIPE,STDOUT
from pdftools.pdffile import PDFDocument
from sheetmusic import *

from class_dynamic import Classifier_with_remove

gspath="\"c:/Program Files/gs/gs8.70/bin/gswin32c.exe\"".replace("/","\\")

class Page:

    def __init__(self,origfile,pagenumber,classifier=None):
        self._pagenumber = pagenumber
        self._file = None
        self._origfile = origfile
        self._noend = origfile[:-4]
        self._mi = None
        self._classifier = classifier
        self.l = logging.getLogger(self.__class__.__name__)

    def save(self,filename=None):
        if filename is None:
            filename = self._genfilename()
            logging.info("Filename not given. Using %s",filename)

        cmd = ' '.join([gspath,
                            '-dNOPAUSE',
                            '-q',
                            '-r300',
                            '-sDEVICE=tiffg4',
                            '-dBATCH',
                            '-sOutputFile=%s'%filename,
                            '-sPAPERSIZE=a4',
                            '-dFirstPage=%d'%self._pagenumber,
                            '-dLastPage=%d'%self._pagenumber,
                            self._origfile
                        ])
        po = Popen(cmd,shell=True,stdout=PIPE,stderr=STDOUT).stdout
        for l in po.readlines():
            self.l.debug("GS Output:%s",l)
        po.close()
        self._file = filename

    def _init_mi(self):
        self._mi = MusicImage(self._file,classifier=self._classifier)

    def save_nostaves(self,filename=None):
        if self._file is None:
            self.l.debug("No converted tif page. Forcing one now.")
            self.save()

        if filename is None:
            filename = self._genfilename(postfix="-nostaves",extension=".png")
            self.l.info("Filename not given. Using %s",filename)

        if self._mi is None:
            self._init_mi()

        self._mi.without_staves().save_PNG(filename)
        self._nostavesfile = filename

    def generate_gamera_script(self,dir=".",filename=None):
        if filename is None:
            filename = self._genfilename(dir=dir,extension=".py")
            self.l.info("Filename not given. Using %s",filename)

        gamscript = open(filename,'w')
        gamscript_head = open("gamscripthead.py")
        gamscript.write("# Open %s in gamera with a classifier\n"%self._nostavesfile)
        gamscript.write(gamscript_head.read())
        gamscript_head.close()
        gamscript.write("\n####\n")
        gamscript.write("image = load_image(\"%s\")\n"%self._nostavesfile)
        gamscript.write("ccs = image.cc_analysis()\n")
        gamscript.write("classifier.display(ccs,image)\n")
        gamscript.close()

    def save_color_segmented(self,filename=None):
        if self._mi is None:
            self._init_mi()

        if filename is None:
            filename = self._genfilename(postfix="-colorseg",extension=".png")

        color = self._mi.color_segment(classified_box=True)
        color.save_PNG(filename)


    def _genfilename(self,dir=None,postfix="",extension=".tif"):
        if dir is None:
            dir = self._noend
        filename = "%s/%s-page%02d%s%s"%\
                (dir,self._noend,self._pagenumber,postfix,extension)
        if not os.path.exists(dir):
            logging.debug("%s dir dint exits. Creating it.",dir)
            os.mkdir(dir)

        return filename

class Pdfsampler:

    def __init__(self,filename):
        self.filename = filename
        self.l = logging.getLogger(self.__class__.__name__)
        self.c = Classifier_with_remove(training_filename="../preomr_edited_cnn.xml")
        self.c.set_k(1)

    def randompages(self,count):
        doc = PDFDocument(self.filename)
        pages = doc.count_pages()
        chosen_pages = random.sample([i for i in xrange(1,pages+1)],min(pages,10))
        chosen_pages.sort()
        self.l.info("%s - %d pages. %s chosen",self.filename,pages,chosen_pages)
        def pi(n): return Page(self.filename,n,self.c)
        return [ pi(p) for p in chosen_pages ]

