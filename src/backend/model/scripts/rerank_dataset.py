from torch.utils.data import Dataset
import numpy as np
class RerankDataset(Dataset):
    def __init__(
        self,
        corpus = [],
        paper_database = {},
        context_database = {},
        tokenizer = None,
        rerank_top_K = 500,
        max_input_length = 512,
        padding  = "max_length",
        truncation = True,
        sep_token = "<sep>",
        cit_token = "<cit>",
        is_training = True,
        n_document = 16,
        max_n_positive = 1,
    ):
        self.corpus = corpus
        self.paper_database = paper_database
        self.context_database = context_database
        self.tokenizer = tokenizer
        self.rerank_top_K = rerank_top_K
        self.max_input_length = max_input_length
        self.padding = padding
        self.truncation = truncation
        self.cit_token = cit_token
        self.sep_token = sep_token
        self.is_training = is_training
        self.n_document = n_document
        self.max_n_positive = max_n_positive

        self.irrelevance_level_for_positive = 0
        self.irrelevance_level_for_negative = 1

    def __len__(self):
        return len(self.corpus)

    def get_paper_text(self, paper_id: str) -> str:
        info = self.paper_database.get(paper_id, {})
        return info.get("title", "") + " " + info.get("abstract", "")

    def __getitem__(self, idx):
        data       = self.corpus[idx]
        context_id = data["context_id"]

        ctx          = self.context_database[context_id]
        citing_id    = ctx["citing_id"]
        context_text = ctx["masked_text"].replace("TARGETCIT", self.cit_token)
        context_text = context_text.replace("OTHERCIT", "")
        citing_text  = self.get_paper_text(citing_id)

        positive_ids     = data["positive_ids"]
        positive_ids_set = set(positive_ids)
        prefetched_ids   = data["prefetched_ids"][:self.rerank_top_K]

        negative_ids = list(
            set(prefetched_ids) - set(positive_ids + [citing_id])
        )

        if self.is_training:
            positive_id_indices = np.arange(len(positive_ids))
            np.random.shuffle(positive_id_indices)
            candidate_id_list      = [positive_ids[i] for i in positive_id_indices[:self.max_n_positive]]
            irrelevance_levels_list = [self.irrelevance_level_for_positive] * len(candidate_id_list)

            n_neg = self.n_document - len(candidate_id_list)
            if len(negative_ids) == 0:
                candidate_id_list      += [positive_ids[0]] * n_neg
                irrelevance_levels_list += [self.irrelevance_level_for_positive] * n_neg
            else:
                replace = len(negative_ids) < n_neg
                sampled = np.random.choice(len(negative_ids), n_neg, replace=replace)
                for pos in sampled:
                    irrelevance_levels_list.append(self.irrelevance_level_for_negative)
                    candidate_id_list.append(negative_ids[pos])

            irrelevance_levels_list = np.array(irrelevance_levels_list, dtype=np.float32)

        else:
            candidate_id_list = prefetched_ids
            irrelevance_levels_list = np.array([
                self.irrelevance_level_for_positive
                if cid in positive_ids_set
                else self.irrelevance_level_for_negative
                for cid in candidate_id_list
            ], dtype=np.float32)

        max_citing_tokens = int(self.max_input_length * 0.35)
        truncated_citing = " ".join(citing_text.split()[:max_citing_tokens])
        query_text = truncated_citing + self.sep_token + context_text

        query_text_list = [query_text] * len(candidate_id_list)
        candidate_text_list = [self.get_paper_text(cid) for cid in candidate_id_list]

        encoded_seqs = self.tokenizer(
            query_text_list,
            candidate_text_list,
            max_length = self.max_input_length,
            padding = self.padding,
            truncation = self.truncation,
            return_tensors = None,
        )

        for key in encoded_seqs:
            encoded_seqs[key] = np.asarray(encoded_seqs[key])

        encoded_seqs.update({
            "irrelevance_levels": irrelevance_levels_list,
            "num_positive_ids":   len(positive_ids),
        })
        return encoded_seqs
    
class RerankDatasetForTesting(Dataset):
    def __init__(
        self,
        corpus = [],
        paper_database = {},
        context_database = {},
        tokenizer = None,
        rerank_top_K = 500,
        max_input_length = 512,
        padding  = "max_length",
        truncation = True,
        sep_token = "<sep>",
        cit_token = "<cit>",
        is_training = True,
        n_document = 16,
        max_n_positive = 1,
    ):
        self.corpus = corpus
        self.paper_database = paper_database
        self.context_database = context_database
        self.tokenizer = tokenizer
        self.rerank_top_K = rerank_top_K
        self.max_input_length = max_input_length
        self.padding = padding
        self.truncation = truncation
        self.cit_token = cit_token
        self.sep_token = sep_token
        self.is_training = is_training
        self.n_document = n_document
        self.max_n_positive = max_n_positive

        self.irrelevance_level_for_positive = 0
        self.irrelevance_level_for_negative = 1

    def __len__(self):
        return len(self.corpus)

    def get_paper_text(self, paper_id: str) -> str:
        info = self.paper_database.get(paper_id, {})
        return info.get("title", "") + " " + info.get("abstract", "")

    def __getitem__(self, idx):
        data = self.corpus[idx]
        context_id = data["context_id"]

        ctx = self.context_database[context_id]
        citing_id = ctx["citing_id"]
        context_text = ctx["masked_text"].replace("TARGETCIT", self.cit_token)
        context_text = context_text.replace("OTHERCIT", "")
        citing_text = self.get_paper_text(citing_id)

        positive_ids = data["positive_ids"]
        positive_ids_set = set(positive_ids)
        prefetched_ids = data["prefetched_ids"][:self.rerank_top_K]

        negative_ids = list(
            set(prefetched_ids) - set(positive_ids + [citing_id])
        )

        if self.is_training:
            positive_id_indices = np.arange(len(positive_ids))
            np.random.shuffle(positive_id_indices)
            candidate_id_list = [positive_ids[i] for i in positive_id_indices[:self.max_n_positive]]
            irrelevance_levels_list = [self.irrelevance_level_for_positive] * len(candidate_id_list)

            n_neg = self.n_document - len(candidate_id_list)
            if len(negative_ids) == 0:
                candidate_id_list += [positive_ids[0]] * n_neg
                irrelevance_levels_list += [self.irrelevance_level_for_positive] * n_neg
            else:
                replace = len(negative_ids) < n_neg
                sampled = np.random.choice(len(negative_ids), n_neg, replace=replace)
                for pos in sampled:
                    irrelevance_levels_list.append(self.irrelevance_level_for_negative)
                    candidate_id_list.append(negative_ids[pos])

            irrelevance_levels_list = np.array(irrelevance_levels_list, dtype=np.float32)

        else:
            candidate_id_list = prefetched_ids
            missing_positives = [pid for pid in positive_ids if pid not in set(prefetched_ids)]
            candidate_id_list = missing_positives + candidate_id_list
        
            irrelevance_levels_list = np.array([
                self.irrelevance_level_for_positive
                if cid in positive_ids_set
                else self.irrelevance_level_for_negative
                for cid in candidate_id_list
            ], dtype=np.float32)

        max_citing_tokens = int(self.max_input_length * 0.35)
        truncated_citing = " ".join(citing_text.split()[:max_citing_tokens])
        query_text = truncated_citing + self.sep_token + context_text

        query_text_list = [query_text] * len(candidate_id_list)
        candidate_text_list = [self.get_paper_text(cid) for cid in candidate_id_list]

        encoded_seqs = self.tokenizer(
            query_text_list,
            candidate_text_list,
            max_length = self.max_input_length,
            padding = self.padding,
            truncation = self.truncation,
            return_tensors = None,
            return_token_type_ids=True
        )

        for key in encoded_seqs:
            encoded_seqs[key] = np.asarray(encoded_seqs[key])

        encoded_seqs.update({
            "irrelevance_levels": irrelevance_levels_list,
            "num_positive_ids": len(positive_ids),
        })
        return encoded_seqs