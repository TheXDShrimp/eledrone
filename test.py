# read picture.py

import cv2

frame = cv2.imread("picture.png")
frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

cv2.imshow("poop", frame)
cv2.waitKey(1000)