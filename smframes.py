import ffmpeg
import logging

# if videos size matches your particular screen  (epd.width, epd.height) generate_frame will be faster
WIDTH = 800
HEIGHT = 480 

def generate_frame(in_filename, out_filename, time, width=WIDTH, height=HEIGHT): 
    (
        ffmpeg
        .input(in_filename, ss=time)
        .filter('scale', width, height, force_original_aspect_ratio=1)
        .filter('pad', width, height, -1, -1)
        .output(out_filename, vframes=1)
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )