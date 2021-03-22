import ffmpeg
import logging

# if videos size matches your particular screen  (epd.width, epd.height) generate_frame will be faster
WIDTH = 800
HEIGHT = 480
SCREEN_ASPECT_RATIO = int((WIDTH/HEIGHT)*100)

#ffmpeg -i input.file -vf "
# scale=(iw*sar)*max(800/(iw*sar)\,480/ih):ih*max(800/(iw*sar)\,480/ih), 
# crop=800:480
# "
# -c:v mpeg4 -vtag XVID -q:v 4 -c:a libmp3lame -q:a 4 output.avi

def generate_frame(in_filename, out_filename, time, video_width, video_height): 
    video_aspect_ratio = int((video_width/video_height)*100)

    if video_aspect_ratio > SCREEN_ASPECT_RATIO:
        width = int(video_width*HEIGHT/video_height)
        height = HEIGHT
    else:
        width = WIDTH
        height = int(video_height*WIDTH/video_width)

    (
        ffmpeg
        .input(in_filename, ss=time)
        .filter('scale', width, width, force_original_aspect_ratio=1)
        .filter('crop', WIDTH, HEIGHT)
        .filter('pad', WIDTH, HEIGHT, -1, -1)
        .output(out_filename, vframes=1)
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )