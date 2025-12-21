# bert_module.py
from transformers import BertTokenizer, BertForMaskedLM
import torch

# Load pre-trained BERT model (masked language modeling)
from transformers import BertForMaskedLM, BertTokenizer

model = BertForMaskedLM.from_pretrained("bert-base-uncased", cache_dir="./models/bert/")
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased", cache_dir="./models/bert/")

def check_spelling(text: str):
    """
    Uses BERT masked language modeling to detect and suggest spelling corrections.
    Args:
        text (str): OCR extracted text from handwriting.
    Returns:
        spelling_errors (int): number of detected spelling issues
        corrections (list of dict): suggested corrections
    """

    words = text.strip().split()
    corrections = []
    spelling_errors = 0

    for i, word in enumerate(words):
        # Skip very short tokens
        if len(word) < 3:
            continue

        # Mask one word at a time
        masked_tokens = words.copy()
        masked_tokens[i] = tokenizer.mask_token
        masked_text = " ".join(masked_tokens)

        inputs = tokenizer(masked_text, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = outputs.logits

        mask_index = (inputs["input_ids"][0] == tokenizer.mask_token_id).nonzero(as_tuple=True)[0]
        predicted_ids = predictions[0, mask_index].topk(5).indices[0].tolist()
        predicted_words = [tokenizer.decode([idx]).strip() for idx in predicted_ids]

        # If original word not in top predictions → assume error
        if word.lower() not in [w.lower() for w in predicted_words]:
            spelling_errors += 1
            corrections.append({
                "word": word,
                "suggestions": predicted_words
            })

    return spelling_errors, corrections
