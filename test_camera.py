import cv2
cap = cv2.VideoCapture(0)
if not cap.isOpened(): raise RuntimeError("Δεν ανοίγει η κάμερα")
while True:
    ok, frame = cap.read()
    if not ok: break
    cv2.putText(frame, "Camera OK", (20,40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2)
    cv2.imshow("Camera", frame)
    if cv2.waitKey(1) & 0xFF == 27: break  # ESC
cap.release(); cv2.destroyAllWindows()