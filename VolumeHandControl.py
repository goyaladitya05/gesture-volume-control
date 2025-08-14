import cv2
import numpy as np
import mediapipe as mp
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import time

# Init Pycaw (Windows volume control)
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

# Volume range
volRange = volume.GetVolumeRange()  # (min, max, step)
minVol, maxVol = volRange[0], volRange[1]

# Mediapipe
mpHands = mp.solutions.hands
hands = mpHands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mpDraw = mp.solutions.drawing_utils

# Camera
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)
ptime=0
volBar = 400
volPer = 0

while True:
    success, img = cap.read()
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            # Get landmark positions
            lmList = []
            for id, lm in enumerate(handLms.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append((id, cx, cy))

            if lmList:
                # Thumb tip (4), Index tip (8)
                x1, y1 = lmList[4][1], lmList[4][2]
                x2, y2 = lmList[8][1], lmList[8][2]
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                # Draw circles & line
                cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
                cv2.circle(img, (x2, y2), 10, (255, 0, 255), cv2.FILLED)
                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
                cv2.circle(img, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

                # Distance
                length = math.hypot(x2 - x1, y2 - y1)

                # Map distance to volume range
                vol = np.interp(length, [20, 200], [minVol, maxVol])
                volBar = np.interp(length, [20, 200], [400, 150])
                volPer = np.interp(length, [20, 200], [0, 100])

                volume.SetMasterVolumeLevel(vol, None)

            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)

    # Draw volume bar
    cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 255, 0), cv2.FILLED)
    cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 3)
    cv2.imshow("Img", img)

    cTime = time.time()
    fps = 1 / (cTime - ptime) if ptime != 0 else 0
    ptime = cTime

    cv2.putText(img, f'FPS: {int(fps)}', (20, 70),
                cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 2)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
