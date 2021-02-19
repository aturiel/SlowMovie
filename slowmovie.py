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

# Ensure this is the correct import for your particular screen 
from waveshare_epd import epd7in5_V2

def generate_frame(in_filename, out_filename, time, width, height):    
    (
        ffmpeg
        .input(in_filename, ss=time)
        .filter('scale', width, height, force_original_aspect_ratio=1)
        .filter('pad', width, height, -1, -1)
        .output(out_filename, vframes=1)              
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )

def check_mp4(value):
    if not value.endswith('.mp4'):
        raise argparse.ArgumentTypeError("%s should be an .mp4 file" % value)
    return value

# Ensure this is the correct path to your video folder 
viddir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Videos/')
logdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'logs/')


def save_now_playing(currentVideo):
    f = open('nowPlaying', 'w')
    f.write(currentVideo)
    f.close()    

def save_progress(currentVideo, currentPosition):
    log = open(logdir + '%s<progress'%currentVideo, 'w')
    log.write(str(currentPosition))
    log.close() 

def get_progress(currentVideo):
    log = open(logdir + '%s<progress'%currentVideo)
    for line in log:
        currentPosition = float(line)
    log.close()
    return currentPosition;

start_time = time.time()

parser = argparse.ArgumentParser(description='SlowMovie Settings')
parser.add_argument('-l', '--loop', action='store_true', 
    help="Loop mode: update one frame vs playing movie.")
parser.add_argument('-r', '--random', action='store_true', 
    help="Random mode: chooses a random frame every refresh.")
parser.add_argument('-f', '--file', type=check_mp4,
    help="Add a filename to start playing a specific film. Otherwise will pick a random file, and will move to another film randomly afterwards.")
parser.add_argument('-d', '--delay',  default=120, 
    help="Delay between screen updates, in seconds.")
parser.add_argument('-i', '--inc',  default=4, 
    help="Number of frames skipped between screen updates.")
parser.add_argument('-s', '--start',  
    help="Start at a specific frame.")
args = parser.parse_args()

frameDelay = float(args.delay)
print(" - Frame Delay = %f" %frameDelay )

increment = float(args.inc)
print(" - Increment = %f" %increment )

if args.loop:
    print(" - In loop mode")
else: 
    print (" - In single mode")

if args.random:
    print(" - In random mode")
else: 
    print (" - In play-through mode")
    
if args.file: 
    print(' - Try to start playing %s' %args.file)
else: 
    print (" - Continue playing existing file")

# Scan through video folder until you find an .mp4 file 
currentVideo = ""
videoTry = 0 
while not (currentVideo.endswith('.mp4')):
    currentVideo = os.listdir(viddir)[videoTry]
    videoTry = videoTry + 1 

# the nowPlaying file stores the current video file 
# if it exists and has a valid video, switch to that 
try: 
    f = open('nowPlaying')
    for line in f:
        currentVideo = line.strip()
    f.close()
except: 
    save_now_playing(currentVideo)

videoExists = 0 
for file in os.listdir(viddir):
    if file == currentVideo: 
        videoExists = 1

if videoExists > 0:  
    print(" * The current video is %s" %currentVideo)
elif videoExists == 0: 
    print(">>> Error, could not find video %s" %currentVideo)
    currentVideo = os.listdir(viddir)[0]
    save_now_playing(currentVideo)
    print(" * The current video is %s" %currentVideo)

movieList = []

print(" * Available movies:")
# log files store the current progress for all the videos available 
for file in os.listdir(viddir):
    if not file.startswith('.'):
        movieList.append(file)
        print("\t - %s" %file)
        try: 
            get_progress(file)
        except: 
            save_progress(file, 0)

#print(movieList)

if args.file: 
    if args.file in movieList:
        currentVideo = args.file
    else: 
        print ('>>> Error %s not found' %args.file)

print(" * The video to be processed is %s" %currentVideo)

# Ensure this is the correct driver for your particular screen 
epd = epd7in5_V2.EPD()

# Initialise and clear the screen 
epd.init()
#epd.Clear()    

currentPosition = get_progress(currentVideo)

if args.start:
    print(' * Start at frame %.0f' %float(args.start))
    currentPosition = float(args.start)

# Ensure this matches your particular screen  (epd.width, epd.height)
width = 800 
height = 480 

inputVid = viddir + currentVideo

# Check how many frames are in the movie 
start_time = time.time()
frameCount = int(ffmpeg.probe(inputVid)['streams'][0]['nb_frames'])
ellapsed = time.time() - start_time
print(" * There are %d frames in this video. Calculated in %.1f secs." %(frameCount, ellapsed))

while True: 
    if args.random:
        frame = random.randint(0,frameCount)
    else: 
        frame = currentPosition

    msTimecode = "%dms"%(frame*41.666666)
        
    # Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it as grab.jpg 
    start_time = time.time()
    generate_frame(inputVid, 'grab.jpg', msTimecode, width, height)
    ellapsed_generate = time.time() - start_time

    start_time = time.time()
    # Open grab.jpg in PIL  
    pil_im = Image.open("grab.jpg")
    # Dither the image into a 1 bit bitmap (Just zeros and ones)
    pil_im = pil_im.convert(mode='1',dither=Image.FLOYDSTEINBERG)
    # display the image 
    epd.display(epd.getbuffer(pil_im))

    ellapsed = time.time() - start_time
    print('%s // Frame %d of %d // Extracted %.1f // Displayed %.1f' %(currentVideo, frame, frameCount, ellapsed_generate, ellapsed))

    currentPosition = currentPosition + increment 
    # change to next video if needed
    if currentPosition >= frameCount:
        currentPosition = 0
        save_progress(currentVideo, currentPosition)

        thisVideo = movieList.index(currentVideo)
        if thisVideo < len(movieList)-1:
            currentVideo = movieList[thisVideo+1]
        else:
            currentVideo = movieList[0]

    save_progress(currentVideo, currentPosition)
    save_now_playing(currentVideo)

    if args.loop:
        #epd.sleep()
        time.sleep(frameDelay)
        #epd.init()
    else:
        break; 


epd.sleep()

ellapsed = time.time() - start_time
print("Total run time %.1f seconds" %ellapsed)

exit()
