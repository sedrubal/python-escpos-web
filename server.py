#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python ESC/POS Webinterface
"""

from __future__ import absolute_import
from __future__ import print_function

import tornado.ioloop
import tornado.web
import tornado.websocket
import os
import json
from PIL import Image
from io import BytesIO, StringIO
import base64
from escpos.printer import Serial


APP = None


def log(msg):
    """log message"""
    print(msg)


class StartPage(tornado.web.RequestHandler):
    """
    A normal webpage providing some html, css and js, which uses websockets
    """
    def get(self):
        """the handler for get requests"""
        self.render(
            "index.html",
        )

    def data_received(self, chunk):
        """override abstract method"""
        pass


class WebSocket(tornado.websocket.WebSocketHandler):
    """
    The websocket server part
    """
    def open(self):
        """when a client connects, add this socket to list"""
        APP.clients.append(self)
        # self.send_status()
        log("WebSocket opened. {0} child(s) connected".
            format(len(APP.clients)))

    def on_message(self, message):
        """new message received"""
        try:
            msg = json.loads(message)
        except ValueError:
            log("Client sent an invalid message: {0}".format(message),
                error=True)
            return
        log(msg)
        try:
            if 'text' in msg and msg['text']:
                APP.printer.text(msg['text'])
            if 'image' in msg and msg['image']:
                open('/tmp/img.jpg', 'w').write(msg['image'])
                image = Image.open(BytesIO(base64.b64decode(msg['image'])))
                if 'image-resize' in msg and msg['image-resize']:
                    new_width = int(msg['image-resize'])
                    new_height = new_width * image.size[1] // image.size[0]
                    image = image.resize(
                        (new_width, new_height), Image.ANTIALIAS
                    )
                APP.printer.image(image)
            if 'barcode' in msg and msg['barcode'] and \
                    'barcode-type' in msg and msg['barcode-type'] in [
                        'EAN8', 'EAN16',
                    ]:
                APP.printer.barcode(msg['barcode'], bc=msg['barcode-type'])
            if 'set' in msg:
                APP.printer.set()  # reset
            if 'cut' in msg and msg['cut']:
                APP.printer.cut()
        except Exception as exc:
            self.write_message(json.dumps({
                'error': str(exc),
            }))
        else:
            self.write_message(json.dumps({
                'success': 'Successfully printed your foo',
            }))


#    def send_status(self):
#        """sends the current and next tracks to the client"""
#        self.write_message(json.dumps(APP.meta_status), binary=False)
#        log("send: {0}".format(APP.meta_status))

    def on_close(self):
        """the client of this socket leaved, remove this socket from list"""
        APP.clients.remove(self)
        log("WebSocket closed. {0} child(s) connected".
            format(len(APP.clients)))

    def data_received(self, chunk):
        """override abstract method"""
        pass


SETTINGS = {
    "template_path": os.path.join(os.path.dirname(__file__), "./templates"),
    "static_path": os.path.join(os.path.dirname(__file__), "./static"),
}


def make_app():
    """create a new application and specify the url patterns"""
    return tornado.web.Application([
        tornado.web.URLSpec(r"/ws/", WebSocket, name="websocket"),
        tornado.web.URLSpec(r"/", StartPage, name='index'),
        (r"/static/", tornado.web.StaticFileHandler,
         dict(path=SETTINGS['static_path'])),
    ], **SETTINGS)


def main():
    """the main function starts the server"""
    global APP
    APP = make_app()
    APP.clients = []  # global list of all connected websocket clients
    APP.printer = Serial('/dev/ttyUSB0', baudrate=19200)
    APP.listen('1337', '0.0.0.0')
    log('Listening on http://0.0.0.0:1337')
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
