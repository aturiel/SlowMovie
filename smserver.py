#!/usr/bin/env python3
"""
Very simple HTTP server in python for logging requests
Usage::
    ./server.py [<port>]

    https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7
    https://gist.github.com/rudzaytsev/c5b287bf25deaddc7eda

"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import logging
import threading
import signal
import sys

from smdata import SlowMovieData
from smplayer import SlowMoviePlayer, CURRENT_FRAME

smData = None

class S(BaseHTTPRequestHandler):
    def _set_response(self, response = 200):
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

            logging.info("GET [{}] >>> {}".format(self.path, json_str))

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

        else:
            logging.error("GET [{}] ERROR \nHeaders:\n{}".format(self.path, self.headers))
            self._set_response(400)
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
        #    if smData.setJson(post_data):
        #        response = 200

        if response == 200:
            logging.info("POST Path [{}] OK []".format(self.path, post_data))
        else:
            logging.error("POST Path [{}] ERROR \nHeaders:\n{}\nBody:\n{}\n"
                .format(self.path, self.headers, post_data))

        self._set_response(response)
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

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

class SlowMovieServer:
    def signal_handler(self,signal, frame):
        print('You pressed Ctrl+C!')

        logging.info('Stopping server...')
        self.httpd.server_close()

        logging.info('Stopping player...')
        self.smPlayer.exit()

        sys.exit(0)

    def __start_server(self, port=8080):
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
            target=self.__start_server,
            args=(smData.getPort(),))
        daemon.setDaemon(True) # Set as a daemon so it will be killed once the main thread is dead.
        daemon.start()

        self.smPlayer = SlowMoviePlayer(smData)
        self.smPlayer.play()

if __name__ == '__main__':
    SlowMovieServer();
