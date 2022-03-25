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
        * {box-sizing: border-box}

/* Add padding to containers */
.container {
  padding: 16px;
}

/* Full-width input fields */
input[type=text], input[type=password] {
  width: 100%;
  padding: 15px;
  margin: 5px 0 22px 0;
  display: inline-block;
  border: none;
  background: #f1f1f1;
}

input[type=text]:focus, input[type=password]:focus {
  background-color: #ddd;
  outline: none;
}

/* Overwrite default styles of hr */
hr {
  border: 1px solid #f1f1f1;
  margin-bottom: 25px;
}

/* Set a style for the submit/register button */
.registerbtn {
  background-color: #4CAF50;
  color: white;
  padding: 16px 20px;
  margin: 8px 0;
  border: none;
  cursor: pointer;
  width: 100%;
  opacity: 0.9;
}

.registerbtn:hover {
  opacity:1;
}

/* Add a blue text color to links */
a {
  color: dodgerblue;
}

/* Set a grey background color and center the text of the "sign in" section */
.signin {
  background-color: #f1f1f1;
  text-align: center;
}
	</style>
	<div class="camera">
<h1> Модули</h1>
<div style="float: left;">
<img src="https://thumbs.dreamstime.com/b/topographic-map-line-icon-vector-illustration-black-sign-isolated-contour-symbol-203706373.jpg" width="100"/>
  
</div>
<div style="float: left;">
<h2>Создание топографической карты</h2>
<h3>Уровень завершения миссии: 60%</h3>
<h3>Время начала миссии: 01.03.2022 17:03:24</h3>
<h3>Панируемое время конца миссии: 31.03.2022 17:03:24</h3>
</div>
<div style="float: left;">
<img src="https://thumbs.dreamstime.com/b/%D0%BB%D0%B8%D0%BD%D0%B8%D1%8F-%D0%B7%D0%BD%D0%B0%D1%87%D0%BE%D0%BA-%D0%BF%D0%BE%D1%87%D0%B2%D1%8B-%D1%85%D0%B8%D0%BC%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B0%D1%8F-%D1%85%D0%B0%D1%80%D0%B0%D0%BA%D1%82%D0%B5%D1%80%D0%BD%D0%BE%D0%B9-%D0%BF%D0%BB%D0%B0%D0%BD%D0%B0-%D0%B2-%D0%B8%D0%B7%D0%BE%D0%BB%D1%8F%D1%86%D0%B8%D0%B8-%D0%BD%D0%B0-%D0%B1%D0%B5%D0%BB%D0%BE%D0%BC-170834383.jpg" width="100"/>
</div>
<div style="float: left;">
<h2>Исследование почвы</h2>
<h3>Уровень завершения миссии: 0%</h3>
<h3>Планируемое время начала миссии: 31.03.2022 17:03:24</h3>
<h3>Планируемое время конца миссии: 08.05.2022 17:03:24</h3>
</div>
<div style="float: left;">
<img src="https://cdn-icons-png.flaticon.com/512/5375/5375452.png" width="100"/>
  
</div>
<div style="float: left;">
<h2>Исследование атмосферы</h2>
<h3>Уровень завершения миссии: 0%</h3>
<h3>Планируемое время начала миссии: 08.05.2022 17:03:24</h3>
<h3>Планируемое время конца миссии: 12.06.2022 17:03:24</h3>
</div>

  </div>

</form>
</div>

        
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
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()


