import torch
import numpy as np
import collections
from nltk import word_tokenize
from transformers import AutoTokenizer, AutoModel, BertTokenizer, BertModel
from evaluate import load
from numpy.linalg import norm
import os

folder_path = os.path.dirname(__file__)
rouge = load(f"{folder_path}/rouge.py")

tokenizer = None
model = None

def rouge_score(predictions, references):
    return rouge.compute(predictions = predictions, references = references)

def f1_score(reference, candidate):
    ref_tokens = set(word_tokenize(reference.lower()))
    cand_tokens = set(word_tokenize(candidate.lower()))
    
    common = collections.Counter(ref_tokens) & collections.Counter(cand_tokens)
    num_same = sum(common.values())
    if len(ref_tokens) == 0 or len(cand_tokens) == 0:
        return int(ref_tokens == cand_tokens)
    if num_same == 0:
        return 0
    precision = 1.0 * num_same / len(cand_tokens)
    recall = 1.0 * num_same / len(ref_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    
    return f1

def cos_sim(vector1, vector2):
    return (np.dot(vector1, vector2) / (norm(vector1)*norm(vector2)))   

def bert_score(reference, candidate, model_name, return_similarity_matrix = False):
    global tokenizer, model
    if tokenizer is None or model is None:
        model_path = f'{os.path.dirname(folder_path)}/local_models/{model_name}'
        tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path = model_path, max_length=512, truncation=True)
        model = AutoModel.from_pretrained(pretrained_model_name_or_path= model_path)
    # Tokenize the input text
    ref_tokens = tokenizer(reference, return_tensors="pt", add_special_tokens=False, truncation=True, max_length=512)
    can_tokens = tokenizer(candidate, return_tensors="pt", add_special_tokens=False, truncation=True, max_length=512)
    
    # Get the BERT embeddings
    model.eval()
    with torch.no_grad():
        ref_outputs = model(**ref_tokens)
        ref_embeddings = ref_outputs.last_hidden_state[0]
        
        can_outputs = model(**can_tokens)
        can_embeddings = can_outputs.last_hidden_state[0]
        
    # Compute cosine similarities
    cosine_similarities = np.zeros((can_embeddings.shape[0], ref_embeddings.shape[0]))
    for i, c in enumerate(can_embeddings):
        for j, r in enumerate(ref_embeddings):
            cosine_similarities[i, j] = cos_sim(c, r)
            
    # Align cosine similarities
    max_similarities = cosine_similarities.max(axis=1)
    
    # Average similarity scores
    bertscore = max_similarities.mean()
    
    if return_similarity_matrix:
        return bertscore, cosine_similarities
    else:
        return bertscore
    
# Contextual embeddings often result in BERTScores that fall within a very tight range
# (e.g. roberta-large is most often observed between 0.92 and 1) 
# Follows the simple linear transformation suggested by the BERTScore authors:
# https://github.com/Tiiiger/bert_score/blob/master/journal/rescale_baseline.md
# Note that the baseline numebrs provided in their repo are for precision/recall/F1 score -
# for this computed BERT score, we can choose a lower bound based on our observed values.
# For roberta-large, 0.9 might be a reasonable lower bound. We can floor the normalization at 0
# to always return a score >= 0.
def rescale_bertscore_by_baseline(score: float, base: float):
    normalized_score = (score - base) / (1 - base)
    return normalized_score if normalized_score > 0 else 0
