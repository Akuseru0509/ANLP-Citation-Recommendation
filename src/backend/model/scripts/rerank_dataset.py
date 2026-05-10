import os
import torch
from torch.utils.data import Dataset
import numpy as np
from nltk.tokenize import sent_tokenize

class RerankDataset(Dataset):
    def  __init__(self, 
                  collection = {}, 
                  paper_database = {}, 
                  contexts = {}, 
                  tokenizer = None,
                  top_k = 50,
                  max_input_length = 512,
                  padding = "max_length",
                  truncation = True,
                  sep_token = "<sep>",
                  cit_token = "<cit>",
                  eos_token = "<eos>",
                  is_training = True,
                  n_documents = 32,
                  max_n_positive = 1
                ):
        
        self.collection = collection
        self.paper_database = paper_database
        self.contexts = contexts
        self.tokenizer = tokenizer
        self.top_k = top_k
        self.max_input_length = max_input_length
        self.padding = padding
        self.truncation = truncation
        self.sep_token = sep_token
        self.cit_token = cit_token
        self.eos_token = eos_token
        self.special_eos_token_id = self.tokenizer.convert_tokens_to_ids(self.eos_token)
        self.is_training = is_training
        self.n_documents = n_documents
        self.max_n_positive = max_n_positive

        self.irrelevance_level_for_positive = 0
        self.irrelevance_level_for_negative = 1

    def __len__(self):
        return len()