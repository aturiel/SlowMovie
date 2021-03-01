#!/usr/bin/env python3
import os, time, random
import ffmpeg
import argparse
import json
import re
import logging

from smframes import generate_frame

#If your movie is 30 frames per second, then a frame is 1/30th of a second, or 33.33 milliseconds
#If your movie is 24 frames per second, then a frame is 1/24th of a second, or 41.66 milliseconds
FRAME_CONSTANT = 41.666666

# Data file to store player info
DATA_FILE = 'slowmovie.json'

# Ensure this is the correct path to your video folder 
viddir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Videos/')
framesdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Frames/')

CURRENT_FRAME = 'current.jpg'

class SlowMovieData:
    __random: bool = False
    __delay: int = 60
    __increment: int = 4
    __movie: str = ''
    __movies: {} = {}

    __skipNextIncrement = False

    def __init__(self):
        self.__load()
        self.__parseArgs()
        
        if not self.updateMovies():
            quit()

    @property
    def random(self):
        return self.__random

    @property
    def delay(self):
        return self.__delay

    @property
    def increment(self):
        return self.__increment

    @property
    def movie(self):
        return self.__movie

    #@movie.setter
    #def movie(self, value):
    #    self.__movie = value

    @property
    def frameDir(self):
        if not os.path.exists(framesdir):
            os.makedirs(framesdir)
        return framesdir;

    @property
    def currentFrameImage(self):
        return self.frameDir + CURRENT_FRAME

    @property
    def movieFile(self):
        """get current movie video file"""
        if self.__movie in self.__movies:
            videoFile = viddir + self.__movie
            if os.path.isfile(videoFile):
                return videoFile

        return None

    @property
    def movieFrames(self):
        """get total frames for current movie"""
        return self.__movies[self.__movie]['totalFrames']

    @property 
    def currentTimeMs(self):
        return self.__getTimeMs(self.currentFrame)

    def __getTimeMs(self, frame):
        return "%dms"%(float(frame)*FRAME_CONSTANT)

    @property 
    def currentTimeHuman(self):
        return self.__getTimeHuman(self.currentFrame)

    def __getTimeHuman(self, frame):
        """Get human time from frame."""
        millis = (float(frame)*FRAME_CONSTANT)

        microseconds = (millis%1000)
        seconds=(millis/1000)%60
        minutes=(millis/(1000*60))%60
        hours=(millis/(1000*60*60))%24
        microseconds = int(microseconds)
        seconds = int(seconds)
        minutes = int(minutes)
        hours = int(hours)

        return "{:02d}:{:02d}:{:02d}.{:03d}".format(hours, minutes, seconds, microseconds) 

    def __getFrameFromTime(self, time_str):
        """Get frame from human time."""
        try:
            if time_str.find('.') < 0:
                time_str += '.500'

            hours, minutes, seconds, microseconds = re.split(':|\.',time_str)
            totalSeconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
            millis = totalSeconds*1000+int(microseconds)
            return int(millis/FRAME_CONSTANT)
        except Exception as err:
            logging.error("Could get frame from {} >>> {}".format(time_str, err))
            return  None

    @property
    def currentFrame(self):
        """get current frame for current movie"""
        if self.__random:
            return random.randint(0,self.movieFrames)
        else: 
            if self.__movie in self.__movies:
                frame = self.__movies[self.__movie]['currentFrame']
                frame = frame if frame and type(frame) == int else 0
                return frame
            else:
                return None

    @currentFrame.setter
    def __currentFrame(self, frame):
        """set current frame for current movie"""
        self.__setCurrentFrame(self.__movie, frame)

    def __setCurrentFrame(self, movie, frame):
        """set current frame for indicated movie"""
        if movie in self.__movies:
            frame = frame if frame and type(frame) == int else 0
            self.__movies[movie]['currentFrame'] = frame
            self.__movies[movie]['currentTime'] = self.__getTimeHuman(frame)

    def incrementFrame(self):
        """select next frame to display"""
        if self.__skipNextIncrement:
            self.__skipNextIncrement = False
            return

        if not self.__random:
            currentPosition = self.currentFrame + self.__increment

            # change to next video if needed
            if currentPosition >= self.movieFrames:
                self.__nextMovie();
            else:
                self.__currentFrame = currentPosition
        
        self.__save()

    def __nextMovie(self):
        """select next movie to play"""
        self.__currentFrame = 0

        keys = list(self.__movies.keys())

        if len(keys) > 0:
            try: 
                self.__movie = keys[keys.index(self.__movie) + 1] 
            except (ValueError, IndexError): 
                self.__movie = keys[0]
        else:
            self.__movie = ''

    def __configFromDict(self, dict):
        """all settings to json object"""
        self.__delay = dict['delay']
        self.__increment = dict['increment']
        self.__random = dict['random']
        self.__movie = dict['movie']
        self.__movies = dict['movies']

    def configToDict(self):
        """all settings to json"""
        dict = {}
        dict['delay'] = self.__delay
        dict['increment'] =  self.__increment
        dict['random'] =  self.__random
        dict['movie'] =  self.__movie 
        dict['movies'] = self.__movies

        return dict

    def __save(self):
        """save config to DATA_FILE in json format"""
        try:
            f = open(DATA_FILE, 'w', encoding='utf-8')
        except OSError as err:
            logging.error("Could not save {} >>> {}".format(DATA_FILE, err))
            return False

        with f:
            json.dump(self.configToDict(), f, ensure_ascii=False, indent=4)

        return True

    def __load(self):
        """load config from json DATA_FILE"""
        try:
            f = open(DATA_FILE, 'r', encoding='utf-8')
        except OSError as err:
            logging.error("Could not load {} >>> {}".format(DATA_FILE, err))
            return False

        with f:
            try:
                self.__configFromDict(json.load(f))

            except ValueError as err:
                logging.error("Could not load {} >>> {}".format(DATA_FILE, err))
                return False
        return True

    def getJson(self):
        """get config in a json object"""
        return json.dumps(self.configToDict(), ensure_ascii=False)

    def __setJson(self, json_str):
        """update all settings from json"""
        try:
            self.__configFromDict(json.loads(json_str))
            return True
        except ValueError as e:
            logging.error("Could not parse json settings >>> {}".format(e))
            return False

    def setFormData(self, vars):
        """update from internal web form"""
        retValue = False
        try:
            if not 'random' in vars and self.__random:
                self.__random = False
                retValue = True

            for key in vars:
                if key == 'increment':
                    self.__increment = int(vars[key][0])
                    retValue = True

                elif key == 'delay':
                    self.__delay = int(vars[key][0])
                    retValue = True

                elif key == 'random' and not self.__random:
                    self.__random = True
                    retValue = True

                elif key == 'movie':
                    if vars[key][0] in self.__movies:
                        self.__movie = vars[key][0]
                        self.__skipNextIncrement = True
                        retValue = True

                elif key.startswith('current_') and vars[key][0]:
                    name =  key[8:];
                    frame = self.__getFrameFromTime(vars[key][0])
                    # if param is frame
                    #frame = int(vars[key][0])
                    self.__setCurrentFrame(name, frame)
                    retValue = True

                else:
                    logging.info("Could not parse post variable: {}:{}".format(key, vars[key]))

        except ValueError as e:
            logging.error("Could not parse form data >>> {}".format(vars))

        if retValue:
            self.__save()

        return retValue

    def setConfig(self, json_str):
        """update player settings in json format {'random' : boolean, 'delay' : int, 'increment' : int}"""
        try:
            config = json.loads(json_str)
            if 'random' in config:
                self.__random = True if config['random'] else False
                retValue = True

            if 'delay' in config:
                self.__delay = int(config['delay'])
                retValue = True
                
            if 'increment' in config:
                self.__increment = int(config['increment'])
                retValue = True

        except ValueError as e:
            logging.error("Could not parse json config >>> {}".format(e))

        if retValue:
            self.__save()

        return retValue

    def setCurrentMovie(self, json_str):
        """Update current movie info in json format {'name': str, 'frame': int, 'time': str}"""
        try:
            new_movie = json.loads(json_str)

            # if we have human time and not frame
            if 'time' in new_movie and not 'frame' in new_movie:
                frame = self.__getFrameFromTime(new_movie['time'])
                if frame:
                    new_movie['frame'] = frame

            if 'name' in new_movie and new_movie['name'] in self.__movies.keys():
                name = new_movie['name']
                self.__movie = name

            if 'frame' in new_movie and new_movie['frame'] <= self.movieFrames:
                self.__currentFrame = new_movie['frame']
                self.__skipNextIncrement = True
                
            self.__save()
            return True

        except ValueError as e:
            logging.error("Could not parse movie data >>> {}".format(e))
        
        return False

    def setFavorite(self, json_str):
        """set frame as favorite if only "id" currentFrame will be used"""
        try:
            favorite = json.loads(json_str)


            if 'id' in favorite and favorite['id']:
                # if we have human time and not frame
                if 'time' in favorite and not 'frame' in favorite:
                    frame = self.__getFrameFromTime(favorite['time'])
                    if frame:
                        favorite['frame'] = frame

                if 'name' in favorite:
                    favName = favorite['name'] 
                else:
                    favName = self.__movie

                if 'frame' in favorite:
                    frame = favorite['frame']
                else:
                    frame = self.currentFrame

                if favName in self.__movies.keys() and frame <= self.__movies[favName]['totalFrames']:
                    return self.__addFavorite(favName, frame, favorite['id'])

        except ValueError as e:
            logging.error("Could not parse favorite >>> {}".format(e))
        
        return False

    def __addFavorite(self, name, frame, id):
        logging.info("Set as favorite {} {}".format(name, frame))

        if not 'favorites' in self.__movies[name]:
            self.__movies[name]['favorites'] = {}
        
        # frame name

        img = name.split('.')[0] + "_" + str(frame) + ".jpg"
        self.__movies[name]['favorites'][id] = {
            'frame': frame,
            'time': self.__getTimeHuman(frame),
            'img': img
        }

        # generate fav frame
        try:
            generate_frame(viddir + name, self.frameDir + img, self.__getTimeMs(frame))
        except Exception as ex:
            logging.error("Could not process frame {} for {} >>> {}".format(frame, name, ex))

        self.__save()
        return True

    def __check_mp4(self, value):
        if not value.endswith('.mp4'):
            raise argparse.ArgumentTypeError("%s should be an .mp4 file" % value)
        return value

    def __parseArgs(self):
        parser = argparse.ArgumentParser(description='SlowMovie Settings')
        parser.add_argument('-r', '--random', default=self.__random, 
            help="Random mode: chooses a random frame every refresh.")
        parser.add_argument('-d', '--delay',  default=self.__delay, 
            help="Delay between screen updates, in seconds.")
        parser.add_argument('-i', '--inc',  default=self.__increment, 
            help="Number of frames skipped between screen updates.")
        parser.add_argument('-f', '--file', type=self.__check_mp4,
            help="Add a filename to start playing a specific film. Otherwise will pick a random file, and will move to another film randomly afterwards.")
        parser.add_argument('-s', '--start',  
            help="Start at a specific frame.")
        args = parser.parse_args()

        self.__delay = int(args.delay)
        self.__increment = int(args.inc)
        self.__random = args.random
        if args.file: 
            self.__movie = args.file

    def updateMovies(self):
        movieList = []

        logging.info("**************** processing Movies")
        # update videos available 
        for file in os.listdir(viddir):
            if not file.startswith('.'):
                movieList.append(file)

                try:
                    # Check how many frames are in the movie  and save for future use
                    start_time = time.time()
                    frameCount = int(ffmpeg.probe(viddir + file)['streams'][0]['nb_frames'])
                    ellapsed = time.time() - start_time

                    if file in self.__movies:
                        self.__movies[file]['totalFrames'] = frameCount;
                        self.__movies[file]['totalTime'] = self.__getTimeHuman(frameCount)

                    else :
                        self.__movies[file] = {
                            'totalFrames': frameCount, 
                            'totalTime': self.__getTimeHuman(frameCount),
                        }
                        self.__setCurrentFrame(file, 0)

                    logging.info(" * %s - Duration:%s - Frames:%d - Calculated in %.1f secs." %(
                        file, 
                        self.__movies[file]['totalTime'],
                        self.__movies[file]['totalFrames'],
                        ellapsed
                    ))

                except ffmpeg.Error as e:
                    logging.error("Could not read movie '{}' >>> {}".format(file, e))
        
        if not movieList:
            self.__movies = {}
            self.__movie = ''
            logging.error("No movies :-( please copy some MP4 in {}".format(viddir))
            return False

        for movie in list(self.__movies.keys()):
            if not movie in movieList:
                del self.__movies[movie]
                logging.info("Delete non existing movie info {}".format(movie))

        # check if current movie is valid
        if self.__movie == '' or not self.__movie in self.__movies.keys():
            try:
                logging.info("Current movie '{}' not valid".format(self.__movie))
                selectedMovie = random.choice(list(self.__movies))
                self.__movie = selectedMovie
                logging.info("Updated current movie '{}'".format(self.__movie))
            except IndexError as e:
                logging.error("Cannot choose from empty movie list >>> {}".format(e))

        self.__save()
        return True



