#!/usr/bin/env python3
import os, time , random
import ffmpeg
import logging
#from types import SimpleNamespace
import argparse

import json

DATA_FILE = 'slowmovie.data'

# Ensure this is the correct path to your video folder 
viddir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Videos/')

class SlowMovieData:

    def __init__(self):
        self.serverPort = 9998
        self.skipNextIncrement = False

        if not self.__load():
            self.smConfig = {
                'random':  False,
                'delay': 60,
                'increment': 4,
                'movie': '',
                'movies': {
                }
            }

        self.__parseArgs()
        
        if not self.updateMovies():
            logging.error("No movies :-( pleaee copy some MP4 in {}".format(viddir))
            quit()

    def getDelay(self):
        return self.smConfig['delay']

    def getMovie(self):
        return self.smConfig['movie']

    def __setMovie(self, name):
        self.smConfig['movie'] = name

    def getMovieFile(self):
        if self.getMovie() in self.smConfig['movies']:
            videoFile = viddir + self.getMovie()
            if os.path.isfile(videoFile):
                return videoFile

        return None

    def getMovieFrames(self):
        return self.smConfig['movies'][self.getMovie()]['frames']

    def getCurrentFrame(self):
        if self.smConfig['random']:
            return random.randint(0,self.getMovieFrames())
        else: 
            if self.getMovie() in self.smConfig['movies']:
                return self.smConfig['movies'][self.getMovie()]['currentFrame']
            else:
                return None

    def __setCurrentFrame(self, frame):
        self.smConfig['movies'][self.getMovie()]['currentFrame'] = frame

    def incrementFrame(self):
        if self.skipNextIncrement:
            self.skipNextIncrement = False
            return

        if not self.smConfig['random']:
            currentPosition = self.getCurrentFrame() + self.smConfig['increment']

            # change to next video if needed
            if currentPosition >= self.getMovieFrames():
                self.__nextMovie();
            else:
                self.__setCurrentFrame(currentPosition)
        
        self.__save()

    def __nextMovie(self):
        self.__setCurrentFrame(0)

        keys = list(self.smConfig['movies'].keys())

        if len(keys) > 0:
            try: 
                self.__setMovie(keys[keys.index(self.getMovie()) + 1]) 
            except (ValueError, IndexError): 
                self.__setMovie(keys[0])
        else:
            self.__setMovie('')

    def __save(self):
        try:
            f = open(DATA_FILE, 'w', encoding='utf-8')
        except OSError as err:
            logging.error("Could not save {}: {}".format(DATA_FILE, err))
            return False

        with f:
            json.dump(self.smConfig, f, ensure_ascii=False, indent=4)

        return True

    def __load(self):
        try:
            f = open(DATA_FILE, 'r', encoding='utf-8')
        except OSError as err:
            logging.error("Could not load {}: {}".format(DATA_FILE, err))
            return False

        with f:
            try:
                self.smConfig = json.load(f) 
            except ValueError as err:
                logging.error("Could not load {}: {}".format(DATA_FILE, err))
                return False

        return True

    def getJson(self):
        """all settings to json"""
        return json.dumps(self.smConfig, ensure_ascii=False)

    def setJson(self, json_str):
        """update all settings from json"""
        try:
            self.smConfig = json.loads(json_str)
            return True
        except ValueError as e:
            logging.error("Could not parse settings: {}".format(e))
            return False

    def setConfig(self, json_str):
        """update: random, delay and increment settings"""
        retValue = False
        try:
            config = json.loads(json_str)
            if 'random' in config:
                self.smConfig['random'] = config['random'] 
                retValue = True

            if 'delay' in config:
                self.smConfig['delay'] = config['delay'] 
                retValue = True
                
            if 'increment' in config:
                self.smConfig['increment'] = config['increment'] 
                retValue = True

            if retValue:
                self.__save()

            return retValue
        except ValueError as e:
            logging.error("Could not parse config: {}".format(e))
            return retValue

    def setFavorite(self, json_str):
        """set frame as favorite if empty currentFrame will be used"""
        try:
            favorite = json.loads(json_str)

            if 'name' in favorite and 'frame' in favorite:
                if favorite['name'] in self.smConfig['movies'].keys():
                    if favorite['frame'] <= self.smConfig['movies'][favorite['name']]['frames']:
                        return self.__addFavorite(favorite['name'], favorite['frame'])
            else:
                return self.__addFavorite(self.getMovie(), self.getCurrentFrame())

        except ValueError as e:
            logging.error("Could not parse favorite: {}".format(e))
        
        return False

    def __addFavorite(self, name, frame):
        logging.info("Set as favorite {} {}".format(name, frame))

        if not 'favorites' in self.smConfig['movies'][name]:
            self.smConfig['movies'][name]['favorites'] = set()
        
        self.smConfig['movies'][name]['favorites'].add(frame)

        self.__save()
        return True

    def setCurrentMovie(self, json_str):
        """update current movie info"""
        try:
            new_movie = json.loads(json_str)

            if 'name' in new_movie and new_movie['name'] in self.smConfig['movies'].keys():
                name = new_movie['name']
                self.__setMovie(name)

                if 'frame' in new_movie and new_movie['frame'] <= self.getMovieFrames():
                    self.__setCurrentFrame(new_movie['frame'])
                    self.skipNextIncrement = True
                
                self.__save()
                return True

        except ValueError as e:
            logging.error("Could not parse movie data: {}".format(e))
        
        return False

    def getPort(self):
        return self.serverPort

    def check_mp4(self, value):
        if not value.endswith('.mp4'):
            raise argparse.ArgumentTypeError("%s should be an .mp4 file" % value)
        return value

    def __parseArgs(self):
        parser = argparse.ArgumentParser(description='SlowMovie Settings')
        parser.add_argument('-p', '--port', default=self.serverPort, 
            help="Random mode: chooses a random frame every refresh.")
        parser.add_argument('-r', '--random', default=self.smConfig['random'], 
            help="Random mode: chooses a random frame every refresh.")
        parser.add_argument('-d', '--delay',  default=self.smConfig['delay'], 
            help="Delay between screen updates, in seconds.")
        parser.add_argument('-i', '--inc',  default=self.smConfig['increment'], 
            help="Number of frames skipped between screen updates.")
        parser.add_argument('-f', '--file', type=self.check_mp4,
            help="Add a filename to start playing a specific film. Otherwise will pick a random file, and will move to another film randomly afterwards.")
        parser.add_argument('-s', '--start',  
            help="Start at a specific frame.")
        args = parser.parse_args()

        self.serverPort = int(args.port)
        self.smConfig['delay'] = float(args.delay)
        self.smConfig['increment'] = float(args.inc)
        self.smConfig['random'] = args.random
        if args.file: 
            self.__setMovie(args.file)

    def updateMovies(self):
        movieList = []

        # update videos available 
        for file in os.listdir(viddir):
            if not file.startswith('.'):
                movieList.append(file)

                if not file in self.smConfig['movies']:
                    try:
                        # Check how many frames are in the movie  and save for future use
                        start_time = time.time()
                        frameCount = int(ffmpeg.probe(viddir + file)['streams'][0]['nb_frames'])
                        ellapsed = time.time() - start_time
                        print(" * There are %d frames in %s. Calculated in %.1f secs." %(frameCount, file, ellapsed))

                        self.smConfig['movies'][file] = {'frames': frameCount, 'currentFrame': 0}
                    except ffmpeg.Error as e:
                        logging.error("Could not read movie '{}': {}".format(file, e))
        
        if not movieList:
            self.smConfig['movies'] = {}
            self.__setMovie('')
            return false

        for movie in list(self.smConfig['movies'].keys()):
            if not movie in movieList:
                del self.smConfig['movies'][movie]

        # check if current movie is valid
        if self.getMovie() == '' or not self.getMovie() in self.smConfig['movies'].keys():
            selectedMovie = random.choice(list(self.smConfig['movies']))
            self.__setMovie(selectedMovie)
        
        self.__save()
        return True



