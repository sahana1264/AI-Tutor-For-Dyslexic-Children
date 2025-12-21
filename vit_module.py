# # vit_module.py

# import cv2
# import numpy as np
# import tensorflow as tf

# # Load trained ViT model
# vit_classifier = tf.keras.models.load_model(
#     r'C:\Users\pc\OneDrive\Desktop\Dyslexia\static\kaggle\working\best_vit_model.keras'
# )

# # Class labels and visualization colors
# LABEL_NAMES = {0: "Corrected", 1: "Normal", 2: "Reversal"}
# LABEL_COLORS = {
#     0: (0, 255, 0),   # Green = Corrected
#     1: (255, 255, 0), # Yellow = Normal
#     2: (0, 0, 255)    # Red = Reversal
# }

# def analyze_reversals(image_cv):
#     """
#     Analyze handwritten text using trained ViT model.
#     Args:
#         image_cv: BGR numpy array from cv2 (uploaded handwriting image)
#     Returns:
#         annotated_img: image with bounding boxes + labels
#         stats: dict with counts of each label
#         results: list with per-character predictions
#     """

#     # 1) Preprocess
#     gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
#     blurred = cv2.GaussianBlur(gray, (5, 5), 0)
#     _, thresh = cv2.threshold(
#         blurred, 0, 255,
#         cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
#     )

#     # 2) Find contours (potential characters)
#     contours = cv2.findContours(
#         thresh, cv2.RETR_EXTERNAL,
#         cv2.CHAIN_APPROX_SIMPLE
#     )[0]

#     bboxes = sorted(
#         (cv2.boundingRect(c) for c in contours),
#         key=lambda b: (b[1]//30, b[0])  # sort row by row
#     )

#     char_boxes, char_images = [], []
#     for x, y, w, h in bboxes:
#         if w > 5 and h > 10:  # ignore noise
#             roi = gray[y:y+h, x:x+w]
#             roi_resized = cv2.resize(roi, (128, 128)) / 255.0
#             roi_resized = roi_resized.reshape(1, 128, 128, 1)
#             char_images.append(roi_resized)
#             char_boxes.append((x, y, w, h))

#     # 3) Predict with ViT
#     annotated_img = image_cv.copy()
#     results = []
#     stats = {"Corrected": 0, "Normal": 0, "Reversal": 0}

#     if char_images:
#         char_images = np.vstack(char_images)  # batch prediction
#         preds = vit_classifier.predict(char_images, verbose=0)

#         for (box, pred) in zip(char_boxes, preds):
#             x, y, w, h = box
#             label_idx = int(np.argmax(pred))
#             label = LABEL_NAMES[label_idx]
#             confidence = float(np.max(pred))

#             # Update stats
#             stats[label] += 1

#             # Draw
#             cv2.rectangle(annotated_img, (x, y), (x+w, y+h),
#                           LABEL_COLORS[label_idx], 2)
#             cv2.putText(annotated_img, label, (x, y-5),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.4,
#                         LABEL_COLORS[label_idx], 1)

#             results.append({
#                 "box": box,
#                 "label": label,
#                 "confidence": confidence
#             })

#     return annotated_img, stats, results
import cv2
import numpy as np
import tensorflow as tf
import pytesseract

# Load trained ViT model
vit_classifier = tf.keras.models.load_model(
    r'C:\Users\pc\OneDrive\Desktop\Dyslexia\static\kaggle\working\best_vit_model.keras'
)

LABEL_NAMES = {0: "Corrected", 1: "Normal", 2: "Reversal"}
LABEL_COLORS = {
    0: (0, 255, 0),   # Green = Corrected
    1: (255, 255, 0), # Yellow = Normal
    2: (0, 0, 255)    # Red = Reversal
}

# def analyze_reversals(image_cv):
#     """
#     Analyze handwritten text using trained ViT model and identify reversed letters.
#     Returns:
#         annotated_img, stats, reversed_letters (list)
#     """

#     gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
#     blurred = cv2.GaussianBlur(gray, (5, 5), 0)
#     _, thresh = cv2.threshold(
#         blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
#     )

#     contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
#     bboxes = sorted(
#         (cv2.boundingRect(c) for c in contours),
#         key=lambda b: (b[1] // 30, b[0])
#     )

#     char_boxes, char_images = [], []
#     for x, y, w, h in bboxes:
#         if w > 5 and h > 10:
#             roi = gray[y:y+h, x:x+w]
#             roi_resized = cv2.resize(roi, (128, 128)) / 255.0
#             roi_resized = roi_resized.reshape(1, 128, 128, 1)
#             char_images.append(roi_resized)
#             char_boxes.append((x, y, w, h))

#     annotated_img = image_cv.copy()
#     stats = {"Corrected": 0, "Normal": 0, "Reversal": 0}
#     reversed_letters = []

#     if char_images:
#         char_images = np.vstack(char_images)
#         preds = vit_classifier.predict(char_images, verbose=0)

#         for (box, pred) in zip(char_boxes, preds):
#             x, y, w, h = box
#             label_idx = int(np.argmax(pred))
#             label = LABEL_NAMES[label_idx]
#             confidence = float(np.max(pred))
#             stats[label] += 1

#             # Draw bounding boxes
#             cv2.rectangle(annotated_img, (x, y), (x+w, y+h), LABEL_COLORS[label_idx], 2)
#             cv2.putText(annotated_img, label, (x, y-5),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.4, LABEL_COLORS[label_idx], 1)

#             # 🔍 Detect actual letter (OCR) if it's a reversal
#             # if label == "Reversal":
#             #     roi = gray[y:y+h, x:x+w]
#             #     ocr_letter = pytesseract.image_to_string(
#             #         roi, config='--psm 10 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz'
#             #     ).strip().lower()

#             #     if ocr_letter and ocr_letter.isalpha():
#             #         reversed_letters.append(ocr_letter)
            


#             if label == "Reversal":
#                 roi = gray[y:y+h, x:x+w]
#                 # Clean up the ROI
#                 roi = cv2.resize(roi, (64, 64))
#                 _, roi_bin = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

#                 ocr_letter = pytesseract.image_to_string(
#                     roi_bin,
#                     config='--psm 10 --oem 3 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz'
#                 ).strip().lower()

#                 print(f"OCR output for reversed region: '{ocr_letter}' at box {x,y,w,h}")

#             if ocr_letter and ocr_letter.isalpha():
#                 reversed_letters = [l[0] for l in reversed_letters if len(l) >= 1 and l[0].isalpha()]
#             print(reversed_letters)



#     return annotated_img, stats, reversed_letters
def analyze_reversals(image_cv):
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(
        blurred, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    bboxes = sorted(
        (cv2.boundingRect(c) for c in contours),
        key=lambda b: (b[1] // 30, b[0])  # left-to-right, line-by-line
    )

    char_boxes, char_images = [], []
    for x, y, w, h in bboxes:
        if w > 5 and h > 10:
            roi = gray[y:y+h, x:x+w]
            roi_resized = cv2.resize(roi, (128, 128)) / 255.0
            roi_resized = roi_resized.reshape(1, 128, 128, 1)
            char_images.append(roi_resized)
            char_boxes.append((x, y, w, h))

    annotated_img = image_cv.copy()
    stats = {"Corrected": 0, "Normal": 0, "Reversal": 0}
    results = []  # ✅ store all predictions (needed for helper alignment)
    reversed_letters = []

    if char_images:
        char_images = np.vstack(char_images)
        preds = vit_classifier.predict(char_images, verbose=0)

        for (box, pred) in zip(char_boxes, preds):
            x, y, w, h = box
            label_idx = int(np.argmax(pred))
            label = LABEL_NAMES[label_idx]
            confidence = float(np.max(pred))
            stats[label] += 1

            # Draw
            cv2.rectangle(annotated_img, (x, y), (x+w, y+h), LABEL_COLORS[label_idx], 2)
            cv2.putText(annotated_img, label, (x, y-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, LABEL_COLORS[label_idx], 1)

            results.append({"box": (x, y, w, h), "label": label, "confidence": confidence})

            # OCR for reversals
            if label == "Reversal":
                roi = gray[y:y+h, x:x+w]
                roi = cv2.resize(roi, (64, 64))
                _, roi_bin = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                ocr_letter = pytesseract.image_to_string(
                    roi_bin,
                    config='--psm 10 --oem 3 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz'
                ).strip().lower()

                print(f"OCR output for reversed region: '{ocr_letter}' at box {x,y,w,h}")

                if ocr_letter and ocr_letter.isalpha():
                    reversed_letters.append(ocr_letter)

    # Cleanup
    reversed_letters = [l[0] for l in reversed_letters if len(l) >= 1 and l[0].isalpha()]

    print("Detected reversed letters:", reversed_letters)
    return annotated_img, stats, results  # ✅ return 'results' not reversed_letters
