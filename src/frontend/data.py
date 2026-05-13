"""
data.py — Mock data layer for CiteSense.
Replace `mock_recommend` with a real backend call when ready.
"""

import time
import random

MOCK_PAPERS = [
    {
        "id": "p001",
        "title": "Attention Is All You Need",
        "authors": ["Vaswani, A.", "Shazeer, N.", "Parmar, N.", "Uszkoreit, J."],
        "year": 2017,
        "venue": "NeurIPS",
        "abstract": (
            "The dominant sequence transduction models are based on complex recurrent or "
            "convolutional neural networks that include an encoder and a decoder. The best "
            "performing models also connect the encoder and decoder through an attention "
            "mechanism. We propose a new simple network architecture, the Transformer, based "
            "solely on attention mechanisms, dispensing with recurrence and convolutions entirely."
        ),
        "doi": "10.48550/arXiv.1706.03762",
        "citations": 90000,
        "score": 0.97,
        "keywords": ["transformer", "attention", "nlp", "sequence"],
        "url": "https://arxiv.org/abs/1706.03762",
    },
    {
        "id": "p002",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "authors": ["Devlin, J.", "Chang, M.-W.", "Lee, K.", "Toutanova, K."],
        "year": 2019,
        "venue": "NAACL",
        "abstract": (
            "We introduce a new language representation model called BERT, which stands for "
            "Bidirectional Encoder Representations from Transformers. Unlike recent language "
            "representation models, BERT is designed to pre-train deep bidirectional "
            "representations from unlabeled text by jointly conditioning on both left and right "
            "context in all layers."
        ),
        "doi": "10.18653/v1/N19-1423",
        "citations": 50000,
        "score": 0.94,
        "keywords": ["bert", "pre-training", "language model", "nlp"],
        "url": "https://arxiv.org/abs/1810.04805",
    },
    {
        "id": "p003",
        "title": "SciBERT: A Pretrained Language Model for Scientific Text",
        "authors": ["Beltagy, I.", "Lo, K.", "Cohan, A."],
        "year": 2019,
        "venue": "EMNLP",
        "abstract": (
            "Obtaining large-scale annotated data for NLP tasks in the scientific domain is "
            "challenging and expensive. We release SciBERT, a pretrained language model based "
            "on BERT to address the lack of high-quality, large-scale labeled scientific data."
        ),
        "doi": "10.18653/v1/D19-1371",
        "citations": 3200,
        "score": 0.91,
        "keywords": ["scibert", "scientific text", "pre-training", "bert"],
        "url": "https://arxiv.org/abs/1903.10676",
    },
    {
        "id": "p004",
        "title": "A Neural Probabilistic Language Model",
        "authors": ["Bengio, Y.", "Ducharme, R.", "Vincent, P.", "Jauvin, C."],
        "year": 2003,
        "venue": "JMLR",
        "abstract": (
            "A goal of statistical language modeling is to learn the joint probability function "
            "of sequences of words in a language. This is intrinsically difficult because of the "
            "curse of dimensionality: a word sequence on which the model will be tested is likely "
            "to be different from all the training word sequences."
        ),
        "doi": "10.5555/944919.944966",
        "citations": 12000,
        "score": 0.85,
        "keywords": ["language model", "neural network", "word embeddings"],
        "url": "https://www.jmlr.org/papers/v3/bengio03a.html",
    },
    {
        "id": "p005",
        "title": "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
        "authors": ["Reimers, N.", "Gurevych, I."],
        "year": 2019,
        "venue": "EMNLP",
        "abstract": (
            "BERT and RoBERTa has set a new state-of-the-art performance on sentence-pair "
            "regression tasks like semantic textual similarity (STS). However, it requires "
            "that both sentences are fed into the network, which causes a massive computational "
            "overhead."
        ),
        "doi": "10.18653/v1/D19-1410",
        "citations": 8500,
        "score": 0.88,
        "keywords": ["sentence embeddings", "siamese", "bert", "similarity"],
        "url": "https://arxiv.org/abs/1908.10084",
    },
    {
        "id": "p006",
        "title": "Deep Residual Learning for Image Recognition",
        "authors": ["He, K.", "Zhang, X.", "Ren, S.", "Sun, J."],
        "year": 2016,
        "venue": "CVPR",
        "abstract": (
            "Deeper neural networks are more difficult to train. We present a residual learning "
            "framework to ease the training of networks that are substantially deeper than those "
            "used previously. We reformulate the layers as learning residual functions with "
            "reference to the layer inputs, instead of learning unreferenced functions."
        ),
        "doi": "10.1109/CVPR.2016.90",
        "citations": 140000,
        "score": 0.79,
        "keywords": ["resnet", "deep learning", "image recognition", "residual"],
        "url": "https://arxiv.org/abs/1512.03385",
    },
    {
        "id": "p007",
        "title": "Longformer: The Long-Document Transformer",
        "authors": ["Beltagy, I.", "Peters, M. E.", "Cohan, A."],
        "year": 2020,
        "venue": "arXiv",
        "abstract": (
            "Transformer-based models are unable to process long sequences due to their "
            "self-attention operation, which scales quadratically with the sequence length. "
            "To address this limitation, we introduce the Longformer with an attention "
            "mechanism that scales linearly with sequence length."
        ),
        "doi": "10.48550/arXiv.2004.05150",
        "citations": 4100,
        "score": 0.83,
        "keywords": ["longformer", "long document", "transformer", "attention"],
        "url": "https://arxiv.org/abs/2004.05150",
    },
    {
        "id": "p008",
        "title": "GPT-4 Technical Report",
        "authors": ["OpenAI"],
        "year": 2023,
        "venue": "arXiv",
        "abstract": (
            "We report the development of GPT-4, a large-scale, multimodal model which can "
            "accept image and text inputs and produce text outputs. Although less capable than "
            "humans in many real-world scenarios, GPT-4 exhibits human-level performance on "
            "various professional and academic benchmarks."
        ),
        "doi": "10.48550/arXiv.2303.08774",
        "citations": 9000,
        "score": 0.76,
        "keywords": ["gpt-4", "large language model", "multimodal"],
        "url": "https://arxiv.org/abs/2303.08774",
    },
    {
        "id": "p009",
        "title": "Citation Recommendation: Approaches and Datasets",
        "authors": ["Färber, M.", "Jatowt, A."],
        "year": 2020,
        "venue": "ECIR",
        "abstract": (
            "Citation recommendation is a key task in the scientific domain, helping researchers "
            "to find relevant papers. In this survey, we provide a comprehensive overview of the "
            "field, including a systematic categorization of approaches and an overview of the "
            "datasets used."
        ),
        "doi": "10.1007/978-3-030-45442-5_2",
        "citations": 320,
        "score": 0.95,
        "keywords": ["citation recommendation", "survey", "information retrieval"],
        "url": "https://link.springer.com/chapter/10.1007/978-3-030-45442-5_2",
    },
    {
        "id": "p010",
        "title": "specter: Document-level Representation Learning using Citation-informed Transformers",
        "authors": ["Cohan, A.", "Feldman, S.", "Beltagy, I.", "Downey, D.", "Weld, D."],
        "year": 2020,
        "venue": "ACL",
        "abstract": (
            "Representation learning is a critical ingredient for natural language processing "
            "systems. Recent Transformer language models like BERT learn powerful textual "
            "representations, but these models are targeted towards token and sentence-level "
            "training objectives and do not leverage document-level or relational information "
            "from co-citations."
        ),
        "doi": "10.18653/v1/2020.acl-main.207",
        "citations": 1100,
        "score": 0.93,
        "keywords": ["specter", "citation", "document embedding", "transformer"],
        "url": "https://arxiv.org/abs/2004.07180",
    },
]


def mock_recommend(query: str, year_range: tuple, top_k: int = 10) -> list[dict]:
    """Simulate a recommendation call — replace with real backend when ready."""
    time.sleep(random.uniform(0.8, 1.6))  # Simulate network latency
    results = []
    for p in MOCK_PAPERS:
        if not (year_range[0] <= p["year"] <= year_range[1]):
            continue
        jitter = random.uniform(-0.04, 0.04)
        p_copy = {**p, "score": min(1.0, max(0.0, p["score"] + jitter))}
        results.append(p_copy)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
