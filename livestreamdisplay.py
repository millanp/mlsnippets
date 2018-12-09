import numpy
import cv2
import time
import subprocess as sp
import json
from threading import Thread

# cap = cv.VideoCapture("https://58cc2dce193dd.streamlock.net/live/23_E_Madison_EW.stream/chunklist_w233633407.m3u8")

# while True:
#     ret, img = cap.read()

#     if not ret:
#         time.sleep(0.01)
#         print('.')
#         continue

#     cv.imshow('img', img)
#     if cv.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv.destroyAllWindows()

class HLSVideoStream:
    def __init__(self, src):
        # initialize the video camera stream and read the first frame
        # from the stream

        # initialize the variable used to indicate if the thread should
        # be stopped
        self.stopped = False

        FFMPEG_BIN = "ffmpeg"

        metadata = {}

        while "streams" not in metadata.keys():
            
            print('ERROR: Could not access stream. Trying again.')

            info = sp.Popen(["ffprobe", 
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams", src],
            stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
            out, err = info.communicate(b"ffprobe -v quiet -print_format json -show_format -show_streams http://52.91.28.88:8080/hls/live.m3u8")

            metadata = json.loads(out.decode('utf-8'))
            time.sleep(5)


        print('SUCCESS: Retrieved stream metadata.')

        # [print('%s --> %s' % (str(k), str(v)) for k,v in metadata['streams'][0])]
        print(metadata["streams"][0])

        # TODO: Figure out why this is 1 and not 0
        self.WIDTH = metadata["streams"][1]["width"]
        self.HEIGHT = metadata["streams"][1]["height"]

        self.pipe = sp.Popen([ FFMPEG_BIN, "-i", src,
                 "-loglevel", "quiet", # no text output
                 "-an",   # disable audio
                 "-f", "image2pipe",
                 "-pix_fmt", "bgr24",
                 "-vcodec", "rawvideo", "-"],
                 stdin = sp.PIPE, stdout = sp.PIPE)
        print('WIDTH: ', self.WIDTH)

        raw_image = self.pipe.stdout.read(self.WIDTH*self.HEIGHT*3) # read 432*240*3 bytes (= 1 frame)
        self.frame =  numpy.fromstring(raw_image, dtype='uint8').reshape((self.HEIGHT,self.WIDTH,3))
        self.grabbed = self.frame is not None


    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        # if the thread indicator variable is set, stop the thread

        while True:
            if self.stopped:
                return

            raw_image = self.pipe.stdout.read(self.WIDTH*self.HEIGHT*3) # read 432*240*3 bytes (= 1 frame)
            self.frame =  numpy.fromstring(raw_image, dtype='uint8').reshape((self.HEIGHT,self.WIDTH,3))
            self.grabbed = self.frame is not None

    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True

def main():
    stream = HLSVideoStream(src="https://58cc2dce193dd.streamlock.net/live/Boren_Seneca_NS.stream/chunklist_w1390393416.m3u8").start()
    print('hi')

    while True:
        frame = stream.read()
        output_rgb = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow('Video', output_rgb)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

if __name__ == '__main__':
    main()