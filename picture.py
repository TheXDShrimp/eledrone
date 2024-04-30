import cv2, time
import numpy as np
from djitellopy import Tello

tello = Tello()
tello.connect()
tello.streamon()
print("init complete")


frame_read = tello.get_frame_read()
# time.sleep(5)

tello.takeoff()

# CVT COLOR IS ESSENTIAL TO REVERSE THE COLOR VALUES AROUND
# otherwise, your image will be in BGR format, so you will look like a smurf.
frame = cv2.cvtColor(frame_read.frame, cv2.COLOR_BGR2RGB)
cv2.imshow("Tello", frame)
cv2.waitkey(1)
cv2.destroyAllWindows()
cv2.imwrite("picture.png", frame)

tello.land()
tello.streamoff()