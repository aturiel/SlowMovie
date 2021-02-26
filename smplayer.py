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
import ffmpeg
import logging
import platform

# identify  PI vs  my developement machine
DEBUG_MODE = platform.machine() != 'armv7l'

if not DEBUG_MODE:
    from PIL import Image
    # Ensure this is the correct import for your particular screen 
    from waveshare_epd import epd7in5_V2

CURRENT_FRAME = 'grab.jpg'

# if videos size matches your particular screen  (epd.width, epd.height) generate_frame will be faster
WIDTH = 800
HEIGHT = 480 

class SlowMoviePlayer:
    def __init__(self, data):
        self.smdata = data

        if not DEBUG_MODE:
            # Ensure this is the correct driver for your particular screen 
            self.epd = epd7in5_V2.EPD()
            # Initialise and clear the screen 
            self.epd.init()
            #epd.Clear()

    def generate_frame(self, in_filename, out_filename, time, width=WIDTH, height=HEIGHT): 
        (
            ffmpeg
            .input(in_filename, ss=time)
            .filter('scale', width, height, force_original_aspect_ratio=1)
            .filter('pad', width, height, -1, -1)
            .output(out_filename, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

    def play(self):
        while True: 
            start_time = time.time()
            if self.smdata.movieFile:
                try:
                    # Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it 
                    self.generate_frame(self.smdata.movieFile, CURRENT_FRAME, self.smdata.currentTimeMs)
                    ellapsed_generate = time.time() - start_time
                    start_time = time.time()

                    if not DEBUG_MODE:
                        # Open grab.jpg in PIL
                        pil_im = Image.open(CURRENT_FRAME)
                        # Dither the image into a 1 bit bitmap (Just zeros and ones)
                        pil_im = pil_im.convert(mode='1',dither=Image.FLOYDSTEINBERG)
                        # display the image 
                        self.epd.display(self.epd.getbuffer(pil_im))

                except ffmpeg.Error as e:
                    logging.error("Could not read movie '{}': {}".format(self.smdata.movieFile, e))
                except:
                    logging.error("Could not process frame")

            ellapsed = time.time() - start_time

            logging.info('Movie:{} - {} - Frame {} of {} - Extracted:{:.1f} - Displayed:{:.1f}'
                .format(
                    self.smdata.movie if self.smdata.movieFile else None, 
                    self.smdata.currentTimeHuman,
                    self.smdata.currentFrame, 
                    self.smdata.movieFrames, 
                    ellapsed_generate, 
                    ellapsed
                ))

            time.sleep(self.smdata.delay)
            #epd.init()

            self.smdata.incrementFrame()

    def exit(self):
        logging.info("Clear screen")

        if not DEBUG_MODE:
            self.epd.Clear()
            self.epd.sleep()
