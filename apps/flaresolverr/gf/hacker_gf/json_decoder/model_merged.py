import torch
import os
import numpy as np
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import TrainingArguments

def merged_linear(sd_a:dict, sd_b:dict, alpha:float)->dict:
    merged = {}
    for key in sd_a:
        pa,pb = sd_a[key].float(), sd_b[key].float()
        merged[key] = ((1 - alpha) * pa + alpha * pb).to(sd_a[key].dtype)
    return merged

