import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
drawer   = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)


cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  
if not cap.isOpened():
    raise RuntimeError("Δεν ανοίγει η κάμερα")

try:
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)

        if res.multi_hand_landmarks:
            for lm in res.multi_hand_landmarks:
                drawer.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)

        cv2.imshow("MediaPipe Hands", frame)
        if cv2.waitKey(1) & 0xFF == 27:  
            break
finally:
    hands.close()
    cap.release()
    cv2.destroyAllWindows()
