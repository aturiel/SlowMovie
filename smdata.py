#!/usr/bin/env python3
import os, time, random
import ffmpeg
import argparse
import json
import logging

# Data file to store player info
DATA_FILE = 'slowmovie.data'

# Ensure this is the correct path to your video folder 
viddir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Videos/')

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
            logging.error("No movies :-( pleaee copy some MP4 in {}".format(viddir))
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
        return self.__movies[self.__movie]['frames']

    @property
    def currentFrame(self):
        """get current frame for current movie"""
        if self.__random:
            return random.randint(0,self.movieFrames)
        else: 
            if self.__movie in self.__movies:
                return self.__movies[self.__movie]['currentFrame']
            else:
                return None

    @currentFrame.setter
    def __currentFrame(self, frame):
        """set current frame for current movie"""
        self.__movies[self.__movie]['currentFrame'] = frame

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

    def __loadFromDict(self, dict):
        """all settings to json object"""
        self.__delay = dict['delay']
        self.__increment = dict['increment']
        self.__random = dict['random']
        self.__movie = dict['movie']
        self.__movies = dict['movies']

    def __saveToDict(self):
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
            logging.error("Could not save {}: {}".format(DATA_FILE, err))
            return False

        with f:
            json.dump(self.__saveToDict(), f, ensure_ascii=False, indent=4)

        return True

    def __load(self):
        """load config from json DATA_FILE"""
        try:
            f = open(DATA_FILE, 'r', encoding='utf-8')
        except OSError as err:
            logging.error("Could not load {}: {}".format(DATA_FILE, err))
            return False

        with f:
            try:
                x, y = json.load(f)
                self.__loadFromDict(self, json.load(f))

            except ValueError as err:
                logging.error("Could not load {}: {}".format(DATA_FILE, err))
                return False
        return True

    def getJson(self):
        """get config in a json object"""
        return json.dumps(self.__saveToDict(), ensure_ascii=False)

    def __setJson(self, json_str):
        """update all settings from json"""
        try:
            self.__loadFromDict(self, json.loads(json_str))
            return True
        except ValueError as e:
            logging.error("Could not parse json settings: {}".format(e))
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
                    if vars[key][0] in self.__movies.keys():
                        self.__movie = vars[key][0]
                        if 'frame' in vars and vars['frame'][0] <= self.movieFrames:
                            self.__currentFrame = vars['frame'][0]
                            self.__skipNextIncrement = True
                    retValue = True

                else:
                    logging.info("Could not parse post variable: {}:{}".format(key, vars[key]))

        except ValueError as e:
            logging.error("Could not parse form data: {}".format(vars))

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
            logging.error("Could not parse json config: {}".format(e))

        if retValue:
            self.__save()

        return retValue

    def setCurrentMovie(self, json_str):
        """Update current movie info in json format {'name' : str, 'frame': int}"""
        try:
            new_movie = json.loads(json_str)

            if 'name' in new_movie and new_movie['name'] in self.__movies.keys():
                name = new_movie['name']
                self.__movie = name

                if 'frame' in new_movie and new_movie['frame'] <= self.movieFrames:
                    self.__currentFrame = new_movie['frame']
                    self.__skipNextIncrement = True
                
                self.__save()
                return True

        except ValueError as e:
            logging.error("Could not parse movie data: {}".format(e))
        
        return False

    def setFavorite(self, json_str):
        """set frame as favorite if only "id" currentFrame will be used"""
        try:
            favorite = json.loads(json_str)

            if 'id' in favorite:
                if 'name' in favorite and 'frame' in favorite:
                    favName = favorite['name'] 
                    if favName in self.__movies.keys():
                        if favorite['frame'] <= self.__movies[favName]['frames']:
                            return self._addFavorite(favName, favorite['frame'], favorite['id'])
                else:
                    return self._addFavorite(self.__movie, self.currentFrame, favorite['id'])

        except ValueError as e:
            logging.error("Could not parse favorite: {}".format(e))
        
        return False

    def _addFavorite(self, name, frame, id):
        logging.info("Set as favorite {} {}".format(name, frame))

        if not 'favorites' in self.__movies[name]:
            self.__movies[name]['favorites'] = {}
        
        #TODO check for errors
        self.__movies[name]['favorites'][id] = frame

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

        # update videos available 
        for file in os.listdir(viddir):
            if not file.startswith('.'):
                movieList.append(file)

                if not file in self.__movies:
                    try:
                        # Check how many frames are in the movie  and save for future use
                        start_time = time.time()
                        frameCount = int(ffmpeg.probe(viddir + file)['streams'][0]['nb_frames'])
                        ellapsed = time.time() - start_time
                        print(" * There are %d frames in %s. Calculated in %.1f secs." %(frameCount, file, ellapsed))

                        self.__movies[file] = {'frames': frameCount, 'currentFrame': 0}
                    except ffmpeg.Error as e:
                        logging.error("Could not read movie '{}': {}".format(file, e))
        
        if not movieList:
            self.__movies = {}
            self.__movie = ''
            return False

        for movie in list(self.__movies.keys()):
            if not movie in movieList:
                del self.__movies[movie]

        # check if current movie is valid
        if self.__movie == '' or not self.__movie in self.__movies.keys():
            try:
                selectedMovie = random.choice(list(self.__movies))
                self.__movie = selectedMovie
            except IndexError as e:
                logging.error("Cannot choose from empty movie list {}".format(e))

        self.__save()
        return True



