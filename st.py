import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server
from gpiozero import Servo
import socket

import base64
PIN = 17


PAGE="""
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Document</title>
</head>
<body>
	<style>
		.button {
			width: 124px;
			height: 60px;
			background: #036FF1;
			border-radius: 15px;
			padding: 18px 50px;
		}
		button {
			border: none;
			outline: none;
			background-color: transparent;
		}
		.camera {
			display: block;
			margin: 0 auto;
		}
        .img{
            margin: 100px;
        }
		.buttons {
			margin: 50px auto;
			display: flex;
			justify-content: center;
			align-items: center;
		}
	</style>
	<div class="camera">
		<img class="camera" src="stream.mjpg"/>
        <h1> Трансляция данных с камеры </h1>
       <iframe src="https://drive.google.com/file/d/1xvDxcezlg08aOrQiT1dtWY9iaK4N-Vck/preview" width="640" height="480" ></iframe>
    

        
    
        
	</div>
        
         <h1> График данных с лидара </h1></div>

</body>
</html>"""

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        elif self.path == "lidar_gr4.png":
                            f=open(curdir + sep + self.path)
                            self.send_response(200)
                            self.send_header('Content-type','image/png')
                            self.end_headers()
                            self.wfile.write(f.read())
                            f.close()
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()


