# gesture_sender_twohands.py
import time, math
import cv2, mediapipe as mp
from pythonosc.udp_client import SimpleUDPClient


def clamp01(x): return max(0.0, min(1.0, x))

class EMA:
    def __init__(self, beta=0.5): self.beta, self.y = beta, None
    def __call__(self, x):
        if self.y is None: self.y = x
        self.y = self.beta * x + (1 - self.beta) * self.y
        return self.y

class HysteresisToggle:
    def __init__(self, ton=0.25, toff=0.35):
        self.ton, self.toff, self.state = ton, toff, False
    def update(self, val):
        if not self.state and val < self.ton: self.state = True
        elif self.state and val > self.toff: self.state = False
        return self.state

def log_map01_to_range(x, lo, hi):
    x = clamp01(x); return math.exp(math.log(lo) + x * math.log(hi/lo))
def lin_map01_to_range(x, lo, hi):
    x = clamp01(x); return lo + x*(hi-lo)

# 21 landmarks (normalized [0..1] )
def compute_features(landmarks):
    xs = [p.x for p in landmarks]; ys = [p.y for p in landmarks]
    minx, maxx = min(xs), max(xs); miny, maxy = min(ys), max(ys)
    hand_w = max(maxx - minx, 1e-6)
    cx = 0.5*(minx + maxx); cy = 0.5*(miny + maxy)

    tips = [4, 8, 12, 16, 20]
    spread = 0.0
    for i in tips:
        dx = (landmarks[i].x - cx) / hand_w
        dy = (landmarks[i].y - cy) / hand_w
        spread += math.hypot(dx, dy)
    spread = clamp01(spread / len(tips))

    THUMB_TIP, INDEX_TIP, WRIST = 4, 8, 0
    dx = (landmarks[INDEX_TIP].x - landmarks[THUMB_TIP].x) / hand_w
    dy = (landmarks[INDEX_TIP].y - landmarks[THUMB_TIP].y) / hand_w
    pinch = clamp01(math.hypot(dx, dy))  

    height = clamp01(1.0 - landmarks[WRIST].y)  # panw=1, katw=0
    wrist_xy = (landmarks[WRIST].x, landmarks[WRIST].y)

    return height, spread, pinch, wrist_xy

# Rythmiseis
OSC_IP, OSC_PORT = "127.0.0.1", 9000
CONTROL_RATE_HZ = 100

# Ranges
CUTOFF_MIN, CUTOFF_MAX = 200.0, 8000.0
Q_MIN, Q_MAX = 0.5, 10.0
DTIME_MIN_MS, DTIME_MAX_MS = 20.0, 800.0
DFEED_MIN, DFEED_MAX = 0.0, 0.95
REV_MIX_MIN, REV_MIX_MAX = 0.0, 1.0
DRIVE_MIN, DRIVE_MAX = 0.0, 1.0

#Main
def main():
    client = SimpleUDPClient(OSC_IP, OSC_PORT)

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    hands = mp_hands.Hands(
        static_image_mode=False,
        model_complexity=1,
        max_num_hands=2,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    )

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError("Δεν ανοίγει η κάμερα")

    # EMA per signal
    ema_cutoff = EMA(0.5)
    ema_Q_right = EMA(0.5)
    ema_rev_left = EMA(0.5)
    ema_fb_right = EMA(0.5)
    ema_dtime_left = EMA(0.5)
    ema_drive_right = EMA(0.5)

    # Hysteresis gia pinches 
    pinchR_toggle = HysteresisToggle(0.25, 0.35)
    pinchL_toggle = HysteresisToggle(0.25, 0.35)

    last_send = 0.0
    try:
        while True:
            ok, frame = cap.read()
            if not ok: break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = hands.process(rgb)

            #  handedness
            left, right = None, None
            if res.multi_hand_landmarks and res.multi_handedness:
                for lm, hd in zip(res.multi_hand_landmarks, res.multi_handedness):
                    label = hd.classification[0].label  # "Left" ή "Right"
                    if label == "Left" and left is None:
                        left = lm.landmark
                    elif label == "Right" and right is None:
                        right = lm.landmark

            # Otan uparxoun xeria
            cutoff_norm = None
            Q_right = rev_left = fb_right = dtime_left = drive_right = None

            # Apostash karpwn -> cutoff (prepei na exoume kai ta dyo)
            if left is not None and right is not None:
                _, _, _, wristL = compute_features(left)
                _, _, _, wristR = compute_features(right)
                dx = wristR[0] - wristL[0]
                dy = wristR[1] - wristL[1]
                dist = math.hypot(dx, dy)  #  (normalized space)
               
                dist = max(0.0, min(0.6, dist))
                cutoff_norm = dist / 0.6  # 0..1

            # Deksi xerii: spread -> Q, pinch -> feedback, height -> drive
            if right is not None:
                hR, spreadR, pinchR, _ = compute_features(right)
                Q_right = lin_map01_to_range(spreadR, Q_MIN, Q_MAX)
                # feedback: 1 - pinch
                fb_val = lin_map01_to_range(1.0 - pinchR, DFEED_MIN, DFEED_MAX)
                fb_right = fb_val
                # drive:ypsos xeriou 
                drive_right = lin_map01_to_range(hR, DRIVE_MIN, DRIVE_MAX)
            
                _ = pinchR_toggle.update(pinchR)  

            # Aristero xeri: spread -> reverb mix, pinch -> delay time
            if left is not None:
                hL, spreadL, pinchL, _ = compute_features(left)
                rev_left = lin_map01_to_range(spreadL, REV_MIX_MIN, REV_MIX_MAX)
                # delay time: 1 - pinch 
                dtime_left = lin_map01_to_range(1.0 - pinchL, DTIME_MIN_MS, DTIME_MAX_MS)
                _ = pinchL_toggle.update(pinchL)

            # Smoothing + send
            now = time.time()
            if now - last_send >= 1.0 / CONTROL_RATE_HZ:
                if cutoff_norm is not None:
                    cutoff = log_map01_to_range(ema_cutoff(cutoff_norm), CUTOFF_MIN, CUTOFF_MAX)
                    client.send_message("/param/cutoff", float(cutoff))

                if Q_right is not None:
                    client.send_message("/param/res", float(ema_Q_right(Q_right)))

                if rev_left is not None:
                    client.send_message("/param/reverb/mix", float(ema_rev_left(rev_left)))

                if fb_right is not None:
                    client.send_message("/param/delay/feedback", float(ema_fb_right(fb_right)))

                if dtime_left is not None:
                    client.send_message("/param/delay/time", float(ema_dtime_left(dtime_left)))

                if drive_right is not None:
                    client.send_message("/param/dist/drive", float(ema_drive_right(drive_right)))

                # Debug overlay
                txt = []
                if cutoff_norm is not None: txt.append(f"cutoff={int(cutoff)}Hz")
                if Q_right is not None:     txt.append(f"Q={ema_Q_right.y:.2f}")
                if rev_left is not None:    txt.append(f"revMix={ema_rev_left.y:.2f}")
                if fb_right is not None:    txt.append(f"fb={ema_fb_right.y:.2f}")
                if dtime_left is not None:  txt.append(f"dTime={int(ema_dtime_left.y)}ms")
                if drive_right is not None: txt.append(f"drive={ema_drive_right.y:.2f}")
                if txt:
                    cv2.putText(frame, "  ".join(txt), (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

                last_send = now

            #  landmarks
            if res.multi_hand_landmarks:
                for lm in res.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)

            cv2.imshow("Gesture Sender (2 hands)", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    finally:
        hands.close()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
