import pytesseract
import numpy as np
from difflib import SequenceMatcher
import math
import cv2

# Common reversal pairs (expand as needed)
REVERSAL_PAIRS = {
    'b': 'd', 'd': 'b',
    'p': 'q', 'q': 'p',
    'm': 'w', 'w': 'm',
    'n': 'u', 'u': 'n',
    's': 'z', 'z': 's',
    'k':'ʞ','y':'γ',
    'h':'ɥ'
}

def get_ocr_words_with_boxes(image_cv):
    """
    Returns list of words with bounding boxes and text from pytesseract.image_to_data
    Each item: {"word": text, "box": (x, y, w, h)}
    """
    # Use RGB for pytesseract if needed
    img_rgb = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
    data = pytesseract.image_to_data(img_rgb, output_type=pytesseract.Output.DICT)
    words = []
    n = len(data['text'])
    for i in range(n):
        txt = data['text'][i].strip()
        if txt == "":
            continue
        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        words.append({"word": txt, "box": (x, y, w, h)})
    return words

def align_words(expected_words, ocr_words):
    """
    Align two word lists returning mapping from OCR index -> expected index.
    Uses SequenceMatcher on joined lists for a tolerant alignment.
    Returns list of tuples (ocr_idx, expected_idx) for mapped pairs.
    """
    # lower-case both lists
    exp = [w.lower() for w in expected_words]
    ocr = [w.lower() for w in ocr_words]

    # We will align by best matching sequence of words using a greedy sliding approach:
    # Use SequenceMatcher on strings of words joined by space to get opcodes
    sm = SequenceMatcher(None, " ".join(exp), " ".join(ocr))
    # Build char offsets to word index mapping is complex; instead do word-level alignment simpler:
    # fallback: pair best-matching words by order (safe for short sentences)
    mapping = {}
    minlen = min(len(exp), len(ocr))
    # naive alignment by index (works for short similar strings); for robust alignment you can implement LCS
    for i in range(len(ocr)):
        # choose expected index nearest by position
        j = int(round(i * (len(exp) / max(len(ocr),1))))
        if j >= len(exp):
            j = len(exp)-1
        mapping[i] = j
    return mapping  # dict: ocr_idx -> expected_idx

def infer_reversed_letters_from_vit(expected_sentence, ocr_text, vit_results, image_cv):
    """
    Infers which expected letters are reversed based on ViT reversal boxes + OCR char boxes.
    Returns a clean list like ['p', 'y', 'b'].
    """
    import pytesseract
    import cv2
    import numpy as np

    if not vit_results:
        return []

    # Convert to RGB (pytesseract expects RGB)
    img_rgb = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
    h, w, _ = img_rgb.shape

    # Get character-level bounding boxes from pytesseract
    boxes_str = pytesseract.image_to_boxes(img_rgb)
    char_boxes = []
    for b in boxes_str.strip().splitlines():
        parts = b.split()
        if len(parts) >= 5:
            char, x1, y1, x2, y2 = parts[:5]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            # pytesseract gives y from bottom-left, convert to OpenCV coords
            y1c = h - y2
            y2c = h - y1
            char_boxes.append({"char": char.lower(), "box": (x1, y1c, x2 - x1, y2c - y1c)})

    reversed_letters = []

    # Match each ViT reversal box to nearest OCR character box
    for res in vit_results:
        if res.get("label") != "Reversal":
            continue

        bx, by, bw, bh = res["box"]
        bcx, bcy = bx + bw / 2, by + bh / 2

        best_char = None
        best_dist = 1e9
        for cb in char_boxes:
            cx, cy, cw, ch = cb["box"]
            ccx, ccy = cx + cw / 2, cy + ch / 2
            dist = abs(bcx - ccx) + 2 * abs(bcy - ccy)  # weight vertical distance higher
            if dist < best_dist:
                best_dist = dist
                best_char = cb["char"]

        if best_char and best_char.isalpha():
            reversed_letters.append(best_char)

    # Clean up duplicates
    reversed_letters = list(dict.fromkeys(reversed_letters))

    print("✅ Inferred reversed letters:", reversed_letters)
    return reversed_letters

