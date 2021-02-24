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

import logging

from smdata import SlowMovieData
from smplayer import SlowMoviePlayer, CURRENT_FRAME

smData = None

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

        elif self.path == '/frame':
            try:
                file_data = self.__retrieve_image(CURRENT_FRAME)
                file_data_len = len(file_data)

            except Exception as ex:
                logging.error("GET [{}] >>> {}".format(self.path, ex))
                self.send_error(404)
                self.end_headers()
                self.wfile.write("File not found")
                return
            else:
                logging.info("GET [{}] >>> image of {} bytes".format(self.path, file_data_len))
                self.send_response(200)
                self.send_header("Accept-Ranges","bytes")
                self.send_header("Content-Disposition","attachment")
                self.send_header("Content-Length",file_data_len)
                self.send_header('Content-type', 'image/jpeg')
                self.end_headers()
                self.wfile.write(file_data)

        elif self.path == '/':
            logging.info("homepage")
            self.__set_response()
            self.wfile.write(self._getHomePage()
                .format(smData.getJson())
                .encode("utf-8")
            )

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
        
        elif self.path.startswith('/test'):
            logging.info("test")
            postvars = parse_qs(post_data,keep_blank_values=1)
            smData.setFormData(postvars);
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
        return  """ 
<!DOCTYPE html>
<html>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
<title>Slow Movie</title>
<body>
<header class="w3-container w3-teal">
    <h1>Slow Movie</h1>
</header>
<div class="w3-container w3-margin-top">
<form class="w3-container" action="/test" method="post" enctype="application/x-www-form-urlencoded">
    <div class="w3-row">
        <div class="w3-col s6">
            <label for="increment">Increment:</label>
        </div>
        <div class="w3-col s6">
            <label for="random">Random:</label>
            <input class="" type="checkbox" id="random" name="random" value="random"{2}>
        </div>
    </div>
            <input class="w3-input" type="number" id="increment" name="increment" value="{1}">
            <label for="delay">Delay:</label>
            <input class="w3-input" type="number" id="delay" name="delay" value="{0}">
        <label for="movies">Movie:</label>
        <select class="w3-select" id="movie" name="movie">
            <option value="Bueno_Feo_Malo.mp4">Bueno_Feo_Malo</option>
            <option value="Blade_Runner.mp4">Blade_Runner</option>
            <option value="Bullitt.mp4">Bullitt</option>
            <option value="North_by_Northwest.mp4">North_by_Northwest</option>
            <option value="Psycho.mp4">Psycho</option>
        </select>
 
    <button class="w3-btn w3-section" type="submit" >Submit</button>
</form> 
</div>
</body>
</html>
""".format(int(1), int(2), ' checked')

class SlowMovieServer:
    def signal_handler(self,signal, frame):
        print('You pressed Ctrl+C!')

        logging.info('Stopping server...')
        self.httpd.server_close()

        logging.info('Stopping player...')
        self.smPlayer.exit()

        sys.exit(0)

    def _start_server(self, port=9998):
        server_address = ('', port)
        self.httpd = HTTPServer(server_address, S)

        hostname= socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        logging.info('Server starting at http://%s:%d...'%(local_ip,port))

        self.httpd.serve_forever()

    def __init__(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        print('Press Ctrl+C to exit')

        logging.basicConfig(level=logging.INFO)

        global smData
        smData = SlowMovieData()

        daemon = threading.Thread(
            name='daemon_server',
            target=self._start_server,
            args=())
        daemon.setDaemon(True) # Set as a daemon so it will be killed once the main thread is dead.
        daemon.start()

        self.smPlayer = SlowMoviePlayer(smData)
        self.smPlayer.play()

if __name__ == '__main__':
    SlowMovieServer();
