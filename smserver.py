#!/usr/bin/env python3
"""
Very simple HTTP server in python for logging requests
Usage::
    ./server.py [<port>]

    https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7
    https://gist.github.com/rudzaytsev/c5b287bf25deaddc7eda

"""
import os, sys, signal, threading, socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import jinja2 
import logging
import re

from system_info import getSystemInfo
from smdata import SlowMovieData
from smplayer import SlowMoviePlayer

smData = None
smPlayer = None
class S(BaseHTTPRequestHandler):
    def __set_response(self, response = 200):
        self.send_response(response)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):

        if self.path == '/settings':
            json_str = smData.getJson()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json_str.encode(encoding='utf_8'))

            #logging.info("GET [{}] >>> {}".format(self.path, json_str))

        elif self.path == '/system':
            json_str = getSystemInfo()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json_str.encode(encoding='utf_8'))

        elif self.path.startswith('/frame/'):
            try:
                substring = re.search("/frame/(.*?)\?dummy=", self.path)
                if( substring):
                    name = substring.group(1)
                else:
                    name = self.path[7:]

                file_data = self.__retrieve_image(smData.frameDir + name)
                file_data_len = len(file_data)

            except Exception as ex:
                logging.error("GET frame [{}] >>> {}".format(name, ex))
                self.send_error(404)
                self.end_headers()
                self.wfile.write("File not found")
                return
            else:
                #logging.info("GET [{}] >>> image of {} bytes".format(self.path, file_data_len))
                self.send_response(200)
                self.send_header("Accept-Ranges","bytes")
                self.send_header("Content-Disposition","attachment")
                self.send_header("Content-Length",file_data_len)
                self.send_header('Content-type', 'image/jpeg')
                self.end_headers()
                self.wfile.write(file_data)

        elif self.path == '/':
            try:
                #logging.info("homepage")
                self.__set_response()
                rawBytes = self._getHomePage().encode("utf-8")
                self.wfile.write(rawBytes)
            except Exception as ex:
                logging.error("GET homepage [{}] >>> {}".format(name, ex))
                self.send_error(404)
                self.end_headers()
                self.wfile.write("File not found")
                return

        else:
            logging.error(self.__remove_empty_lines(
                "GET [{}] ERROR Headers >>> \n{}".format(self.path, self.headers)
            ))
            self.__set_response(400)
            self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length).decode('utf-8') # <--- Gets the data itself
        response = 400

        if self.path == '/movie':
            if smData.setCurrentMovie(post_data):
                response = 200

        elif self.path == '/movies':
            if smData.updateMovies():
                response = 200

        elif self.path == '/favorite':
            if smData.setFavorite(post_data):
                response = 200

        elif self.path == '/config':
            #inc, delay, random
            if smData.setConfig(post_data):
                response = 200

        #elif self.path == '/settings':
            # to deprecate
        #    if smData.__setJson(post_data):
        #        response = 200
        
        elif self.path.startswith('/form/'):
            logging.info(self.path)
            postvars = parse_qs(post_data,keep_blank_values=1)
            if self.path == '/form/general':
                smData.setFormGeneral(postvars)
            else: # '/form/movies'
                smData.setFormMovies(postvars)
            self.send_response(301)
            self.send_header('Location','/')
            self.end_headers()
            self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))
            return


        if response == 200:
            logging.info("POST OK [{}]".format(post_data))
        else:
            logging.error(self.__remove_empty_lines(
                "POST [{}] ERROR Headers >>>\n{}\nBody >>>\n{}"
                .format(self.path, self.headers, post_data)
            ))

        self.send_response(response)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

    def __remove_empty_lines(self, text):
        return os.linesep.join([s for s in text.splitlines() if s])

    def __retrieve_image(self,image_path):
        try:
            file = open(image_path,"rb")
        except IOError as ioerr:
            #logging.error("File not found >>> {}".format(ioerr));
            raise
        else:
            file_data = file.read()
            file.close()
        return file_data
    
    def _getHomePage(self):
        templateLoader = jinja2.FileSystemLoader(searchpath="./")
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template("./templates/homepage.jinja")
        outputText = template.render({'smData':smData.configToDict(), 'smPlayer':smPlayer.currentFrameData})  # this is where to put args to the template renderer
        return outputText

class SlowMovieServer:
    def signal_handler(self,signal, frame):
        print('You pressed Ctrl+C!')

        logging.info('Stopping server...')
        self.httpd.server_close()

        logging.info('Stopping player...')
        self.smPlayer.exit()

        sys.exit(0)

    def __start_server(self, port=9998):
        server_address = ('', port)
        self.httpd = HTTPServer(server_address, S)

        hostname= socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        logging.info('Server starting at http://%s:%d...'%(local_ip,port))

        self.httpd.serve_forever()

    def __start_player(self):
        smPlayer.play()

    def __init__(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        print('Press Ctrl+C to exit')

        logging.basicConfig(level=logging.INFO)

        logging.info("Slow Movie Player")
        logging.info(getSystemInfo())

        global smData, smPlayer
        smData = SlowMovieData()
        smPlayer = SlowMoviePlayer(smData)

        daemon = threading.Thread(
            name='daemon_server',
            target=self.__start_server,
            args=())
        daemon.setDaemon(True) # Set as a daemon so it will be killed once the main thread is dead.
        daemon.start()

        thread = threading.Thread(
            name='thread_player',
            target=self.__start_player,
            args=())
        thread.start()
        #smPlayer = SlowMoviePlayer(smData)
        #smPlayer.play()

if __name__ == '__main__':
    SlowMovieServer();
