# https://github.com/nianlonggu/Local-Citation-Recommendation/blob/main/src/rerank/model.py
import torch
import torch.nn
import torch.nn.functional as F

from transformers import AutoModel

class Scorer(torch.nn.Module):
    def __init__(self, bert_model_path, vocab_size, embed_dim = 768):
        super().__init__()
        self.bert_model = AutoModel.from_pretrained(bert_model_path)
        self.bert_model.resize_token_embeddings(vocab_size)
        self.ln_score = torch.nn.Linear(embed_dim, 1)

    def forward(self, inputs):
        net = self.bert_model(**inputs)[0]
        net = net[ :, 0, : ].contiguous()
        score = F.sigmoid(self.ln_score(F.relu(net))).squeeze(1)
        
        return score[1]    