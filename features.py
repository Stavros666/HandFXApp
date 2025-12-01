# features.py
import math

def clamp01(x): return max(0.0, min(1.0, x))

class EMA:
    def __init__(self, beta=0.5):
        self.beta = beta
        self.y = None
    def __call__(self, x):
        if self.y is None: self.y = x
        self.y = self.beta * x + (1 - self.beta) * self.y
        return self.y

class HysteresisToggle:
    def __init__(self, ton=0.25, toff=0.35):
        self.ton, self.toff = ton, toff
        self.state = False
    def update(self, val):
        if not self.state and val < self.ton: self.state = True
        elif self.state and val > self.toff: self.state = False
        return self.state

def compute_features(landmarks):
 
    xs = [p.x for p in landmarks]
    ys = [p.y for p in landmarks]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    hand_w = max(maxx - minx, 1e-6)

    # center
    cx = (minx + maxx) * 0.5
    cy = (miny + maxy) * 0.5

    # tips indices
    tips = [4, 8, 12, 16, 20]
    spread = 0.0
    for i in tips:
        dx = (landmarks[i].x - cx) / hand_w
        dy = (landmarks[i].y - cy) / hand_w
        spread += math.hypot(dx, dy)
    spread = clamp01(spread / len(tips))  # περίπου [0..1+]

    # pinch index–thumb
    THUMB_TIP, INDEX_TIP = 4, 8
    dx = (landmarks[INDEX_TIP].x - landmarks[THUMB_TIP].x) / hand_w
    dy = (landmarks[INDEX_TIP].y - landmarks[THUMB_TIP].y) / hand_w
    pinch = clamp01(math.hypot(dx, dy))   

    # height (invert y)
    WRIST = 0
    height = clamp01(1.0 - landmarks[WRIST].y)

    return height, spread, pinch

def energy_metric(prev_tip, tip, beta=0.6):
    dx = tip.x - prev_tip.x
    dy = tip.y - prev_tip.y
    v = math.hypot(dx, dy)

    return beta * v
