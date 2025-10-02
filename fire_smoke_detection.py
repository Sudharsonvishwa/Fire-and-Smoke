import cv2
import numpy as np

def detect_fire_smoke(frame, fire_thresh=5000, smoke_thresh=5000):
    alert_msg = None
    severity = 0

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Fire detection (red + yellow)
    lower_red1 = np.array([0, 150, 150])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 150, 150])
    upper_red2 = np.array([180, 255, 255])
    red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)

    lower_yellow = np.array([20, 150, 150])
    upper_yellow = np.array([35, 255, 255])
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    fire_mask = cv2.bitwise_or(red_mask, yellow_mask)
    fire_pixels = cv2.countNonZero(fire_mask)

    # Smoke detection (gray/white)
    lower_smoke = np.array([0, 0, 180])
    upper_smoke = np.array([180, 50, 255])
    smoke_mask = cv2.inRange(hsv, lower_smoke, upper_smoke)
    smoke_pixels = cv2.countNonZero(smoke_mask)

    if fire_pixels > fire_thresh:
        alert_msg = "🔥 Fire Detected!"
        severity = 5
        cv2.putText(frame, "FIRE ALERT!", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
    elif smoke_pixels > smoke_thresh:
        alert_msg = "💨 Smoke Detected!"
        severity = 3
        cv2.putText(frame, "SMOKE ALERT!", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

    return frame, alert_msg, severity
