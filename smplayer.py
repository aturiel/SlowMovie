#!/usr/bin/python
# -*- coding:utf-8 -*-

# *************************
# ** Before running this **
# ** code ensure you've  **
# ** turned on SPI on    **
# ** your Raspberry Pi   **
# ** & installed the     **
# ** Waveshare library   **
# *************************

import time 
import logging
import platform
import ffmpeg
from datetime import datetime

from smframes import generate_frame

# identify  PI vs  my developement machine
DEBUG_MODE = platform.machine() != 'armv7l'

if not DEBUG_MODE:
    from PIL import Image
    # Ensure this is the correct import for your particular screen 
    from waveshare_epd import epd7in5_V2

class SlowMoviePlayer:
    def __init__(self, data):
        self.smdata = data
        self.__lastUpdate = datetime.now()

        if not DEBUG_MODE:
            # Ensure this is the correct driver for your particular screen 
            self.epd = epd7in5_V2.EPD()
            # Initialise and clear the screen 
            self.epd.init()
            #epd.Clear()

    @property
    def lastUpdate(self):
        return self.__lastUpdate

    def play(self):
        while True: 
            start_time = time.time()
            if self.smdata.movieFile:
                try:
                    # Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it 
                    generate_frame(self.smdata.movieFile, self.smdata.currentFrameImage, self.smdata.currentTimeMs)
                    self.__lastUpdate = datetime.now()
                    ellapsed_generate = time.time() - start_time
                    start_time = time.time()

                    if not DEBUG_MODE:
                        # Open grab.jpg in PIL
                        pil_im = Image.open(self.smdata.currentFrameImage)
                        # Dither the image into a 1 bit bitmap (Just zeros and ones)
                        pil_im = pil_im.convert(mode='1',dither=Image.FLOYDSTEINBERG)
                        # display the image 
                        self.epd.display(self.epd.getbuffer(pil_im))

                except ffmpeg.Error as e:
                    logging.error("Could not read movie '{}' >>> {}".format(self.smdata.movieFile, e))
                except Exception as ex:
                    logging.error("Could not process current frame >>> {}".format(ex))

            ellapsed = time.time() - start_time

            logging.info('Movie:{} - {} - Frame {} of {} - Extracted:{:.1f} - Displayed:{:.1f} - {}'
                .format(
                    self.smdata.movie if self.smdata.movieFile else None, 
                    self.smdata.currentTimeHuman,
                    self.smdata.currentFrame, 
                    self.smdata.movieFrames, 
                    ellapsed_generate, 
                    ellapsed,
                    self.__lastUpdate.strftime("%H:%M:%S")
                ))

            time.sleep(self.smdata.delay)
            #epd.init()

            self.smdata.incrementFrame()

    def exit(self):
        logging.info("Clear screen")

        if not DEBUG_MODE:
            self.epd.Clear()
            self.epd.sleep()
