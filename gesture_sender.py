# gesture_sender.py
import time, math
import cv2, mediapipe as mp
from pythonosc.udp_client import SimpleUDPClient
from features import EMA, HysteresisToggle, compute_features, clamp01


OSC_IP   = "127.0.0.1"
OSC_PORT = 9000
CONTROL_RATE_HZ = 100         
BETA_CONT = 0.5              
PINCH_ON, PINCH_OFF = 0.25, 0.35

CUTOFF_MIN, CUTOFF_MAX = 200.0, 8000.0
Q_MIN, Q_MAX = 0.5, 10.0
DFEED_MIN, DFEED_MAX = 0.0, 0.95
MIX_MIN, MIX_MAX = 0.0, 1.0

def log_map01_to_range(x, lo, hi):
    x = clamp01(x)
    return math.exp(math.log(lo) + x * math.log(hi/lo))

def lin_map01_to_range(x, lo, hi):
    x = clamp01(x)
    return lo + x*(hi-lo)

def main():
    client = SimpleUDPClient(OSC_IP, OSC_PORT)

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
    static_image_mode=False,
    model_complexity=1,            
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

    drawer = mp.solutions.drawing_utils

    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError("Δεν ανοίγει η κάμερα")

    # EMA 
    ema_height = EMA(BETA_CONT)
    ema_spread = EMA(BETA_CONT)
    ema_pinch  = EMA(BETA_CONT)
    ema_energy = EMA(0.6)

    # Hysteresis 
    pinch_toggle = HysteresisToggle(PINCH_ON, PINCH_OFF)

    last_send = 0.0
    try:
        while True:
            ok, frame = cap.read()
            if not ok: break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = hands.process(rgb)

            if res.multi_hand_landmarks:
                lms = res.multi_hand_landmarks[0].landmark 
                height, spread, pinch = compute_features(lms)

                # smooth
                height_s = ema_height(height)
                spread_s = ema_spread(spread)
                pinch_s  = ema_pinch(pinch)

                #  index_tip
                idx_tip = lms[8]
                energy_s = ema_energy(abs(idx_tip.x) + abs(idx_tip.y))  # proxy 

                # mapping
                cutoff = log_map01_to_range(height_s, CUTOFF_MIN, CUTOFF_MAX)
                q      = lin_map01_to_range(spread_s, Q_MIN, Q_MAX)
                dfeed  = lin_map01_to_range(min(1.0, energy_s*4.0), DFEED_MIN, DFEED_MAX)

                # pinch→mix
                mix_cont = 1.0 - pinch_s
                mix_snap = 1.0 if pinch_toggle.update(pinch_s) else mix_cont
                mix     = max(MIX_MIN, min(MIX_MAX, mix_snap))

                # 100Hz
                now = time.time()
                if now - last_send >= 1.0/CONTROL_RATE_HZ:
                    client.send_message("/param/cutoff", float(cutoff))
                    client.send_message("/param/res",    float(q))
                    client.send_message("/param/delay/feedback", float(dfeed))
                    client.send_message("/param/mix",    float(mix))
                    last_send = now

                # debug draw
                drawer.draw_landmarks(frame, res.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS)
                cv2.putText(frame, f"cutoff={int(cutoff)}Hz  Q={q:.2f}  fb={dfeed:.2f}  mix={mix:.2f}",
                            (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

            cv2.imshow("Gesture Sender", frame)
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break
    finally:
        hands.close()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
