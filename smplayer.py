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

import os, time, sys, random 
from PIL import Image
import ffmpeg
import argparse
import logging

# Ensure this is the correct import for your particular screen 
from waveshare_epd import epd7in5_V2

CURRENT_FRAME = 'grab.jpg'

# if videos size matches your particular screen  (epd.width, epd.height)
# ... process will be faster
# epd7in5_V2 is
WIDTH = 800
HEIGHT = 480 

class SlowMoviePlayer:
    def __init__(self, data):
        self.smdata = data

        #'''
        # Ensure this is the correct driver for your particular screen 
        self.epd = epd7in5_V2.EPD()

        # Initialise and clear the screen 
        self.epd.init()
        #epd.Clear()
        #'''

    def generate_frame(self, in_filename, out_filename, frame, width=WIDTH, height=HEIGHT): 
        time = "%dms"%(frame*41.666666)
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
            frame = self.smdata.getCurrentFrame()
            videoFile = self.smdata.getMovieFile();

            start_time = time.time()
            if videoFile:
                try:
                    # Use ffmpeg to extract a frame from the movie, 
                    # ... crop it, letterbox it and save it as grab.jpg 
                    self.generate_frame(videoFile, CURRENT_FRAME, frame)
                    ellapsed_generate = time.time() - start_time

                    start_time = time.time()
                    #'''
                    # Open grab.jpg in PIL  
                    pil_im = Image.open(CURRENT_FRAME)
                    # Dither the image into a 1 bit bitmap (Just zeros and ones)
                    pil_im = pil_im.convert(mode='1',dither=Image.FLOYDSTEINBERG)
                    # display the image 
                    self.epd.display(self.epd.getbuffer(pil_im))
                    #'''
                except ffmpeg.Error as e:
                    logging.error("Could not read movie '{}': {}".format(file, e))
                except:
                    logging.error("Could not process frame")

            ellapsed = time.time() - start_time

            logging.info('Movie:{} - Frame:{} of {} - Extracted:{:.1f} - Displayed:{:.1f}'
                .format(
                    self.smdata.getMovie() if videoFile else None, 
                    frame, 
                    self.smdata.getMovieFrames(), 
                    ellapsed_generate, 
                    ellapsed
                ))

            time.sleep(self.smdata.getDelay())
            #epd.init()

            self.smdata.incrementFrame()

    def exit(self):
        logging.info("Clear screen")
    #'''
        self.epd.Clear()
        self.epd.sleep()
    #'''