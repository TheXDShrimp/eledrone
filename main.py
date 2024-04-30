import time, cv2, os, math
from threading import Thread
from ultralytics import YOLO


model = YOLO("yolov8s.pt")
print("YOLO Model Loaded")

# Initialize Global Variables
FPS = 30
DELAY = 3 # 3 second initial delay
CLASS_LABELS = {0: "person", 2: "car", 39: "bottle", 67: "cell phone"}





def getYoloSpeed(model, picture) -> float:
    start = time.process_time()
    model(picture)
    return time.process_time() - start
DELAY = math.floor(getYoloSpeed(model, cv2.imread("picture.png")) + DELAY)
print("Delay of", DELAY, "seconds calculated")
time.sleep(1) # allow runner to read the print statement


class BoundBox:
    def __init__(self, xmin, ymin, height, width, confidence=None, class_id=None, class_label=None):
        self.xmin = xmin
        self.ymin = ymin
        self.height = height
        self.width = width
        self.confidence = confidence
        self.class_id = class_id
        self.class_label = class_label
        
    def __init__(self, dic: dict):
        self.xmin = dic["x"]
        self.ymin = dic["y"]
        self.height = dic["h"]
        self.width = dic["w"]
        self.confidence = dic["confidence"]
        self.class_id = dic["class"]
        self.class_label = CLASS_LABELS[self.class_id] if self.class_id in CLASS_LABELS else None

    def get_label(self):
        return self.class_label

    def get_confidence(self):
        return self.confidence

    def get_coordinates(self):
        return (self.xmin, self.ymin, self.xmin + self.width, self.ymin + self.height)

    def __repr__(self):
        return "({:.2f}, {:.2f}, {:.2f}, {:.2f}: {})".format(self.xmin, self.ymin, self.xmin + self.width, self.ymin + self.height, self.class_label)

def parseBoxesToList(model_result):
    boxes = model_result[0].boxes
    parse = list()
    for i in range(len(boxes)):
        xy = boxes[i].xyxy[0].tolist()
        parse.append({'x': xy[0], 'y': xy[1], 'w': xy[2], 'h': xy[3],
                    'confidence': float(boxes.conf[i]), 'class': int(boxes.cls[i])})
    return parse

def toBBList(boxx):
    return [BoundBox(i) for i in boxx]














from djitellopy import Tello

tello = Tello()

try:
    tello.connect()
except Exception as e:
    print(e)
    print("Tello not connected")
    exit()
keepRecording = True
tello.streamon()
time.sleep(1)
print("Tello Init Complete")

frame_read = tello.get_frame_read()
frame_queue = list()
print("Streaming variables created")





curFrameIndex = 0
def videoDisplay():
    # this thread will be started 3-5 (DELAY) seconds after capture to ensure frames are able to be processed in due time.
    # "oh but sonny this is so janky!"
    # womp womp this is my project not yours
    
    # this is the ONLY method that modifies curFrameIndex!!!
    global curFrameIndex, frame_queue, keepRecording
    
    # wait until there are DELAY seconds worth of frames to start
    while (len(frame_queue) < DELAY * FPS) and keepRecording:
        time.sleep(1)
    
    while curFrameIndex < len(frame_queue):
        frame = frame_queue[curFrameIndex]
        curFrameIndex += 1
        try:
            # show the frame
            cv2.imshow("Tello", frame)
            cv2.waitKey(1)
            # print("Showing frame", curFrameIndex)
        finally:
            pass
        
        time.sleep(1 / FPS)
    cv2.destroyAllWindows()
    print("Display done")
    return

def videoCapture():
    # this thread gets each frame from the drone and appends it to the frame_queue
    # possible issues would be this thread not getting enough frames or getting too many frames
    
    global keepRecording
    
    while keepRecording:
        frame_queue.append(cv2.cvtColor(frame_read.frame, cv2.COLOR_BGR2RGB))
        # print("Added frame", len(frame_queue), "to queue.")
        time.sleep(1 / FPS)
    return


def videoProcess():
    global keepRecording, frame_queue, curFrameIndex
    
    lastFrameInd = 0
    while keepRecording:
        if len(frame_queue) == 0:
            time.sleep(1)
            continue
        
        frameInd = len(frame_queue) - 1    
        frame = frame_queue[frameInd]
        # process frame here
        print("Processing frame", curFrameIndex)
        
        # change verbose to False to remove YOLO statements.
        result = toBBList((modelresult := parseBoxesToList(model(frame, verbose=True))))
        print(result)
        
        # draw boxes on the frame and label them
        for box in result:
            if box.get_confidence() < 0.2:
                continue
            
            # do it for every frame between the 2 processes.
            xmin, ymin, xmax, ymax = (w := [int(_) for _ in box.get_coordinates()])
            for i in range(lastFrameInd, frameInd):
                cv2.rectangle(frame_queue[i], (xmin, ymin), (xmax, ymax), (255, 0, 0), 2)
                cv2.putText(frame_queue[i], str(box.get_label()), ((xmin + xmax) // 2, (ymin + ymax) // 2), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)
                cv2.putText(frame_queue[i], str(box.get_confidence()), (xmin + 50, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        lastFrameInd = frameInd
    return




capture = Thread(target=videoCapture)
display = Thread(target=videoDisplay)
processing = Thread(target=videoProcess)

start = lambda x: [x[1].start(), print(x[0], "started")]
start(("Capture", capture))
start(("Display", display))
start(("Processing", processing))


# NOTE: there are no time.sleep() statements here. Those statements block the thread from 
#       accepting "ok" messages from the drone (i think), since it crashes every time I add a time.sleep() statement.

tello.takeoff()
# tello.move_back(100)
tello.rotate_clockwise(360)
tello.land()

keepRecording = False
tello.streamoff()

[print() for _ in range(10)]
print("STREAMING DONE")
print(len(frame_queue), curFrameIndex)
[print() for _ in range(10)]


capture.join()
display.join()
processing.join()