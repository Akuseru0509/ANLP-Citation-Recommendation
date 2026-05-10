# From https://github.com/nianlonggu/Local-Citation-Recommendation/blob/main/src/rerank/losses.py
import torch

class TripletLoss(torch.nn.Module):
    def __init__(self, base_margin = 0.1, positive_irrelevance = 0, account_for_positive = True):
        super().__init__()
        self.base_margin = base_margin
        self.positive_irrelevance = positive_irrelevance
        self.account_for_positive = account_for_positive

    def forward(self, sims, irrelevance_levels):
        sims_diffs = sims.unsqueeze(2) - sims.unsqueeze(1)
        levels_diffs = irrelevance_levels.unsqueeze(2) - irrelevance_levels.unsqueeze(1)

        margin = self.base_margin * levels_diffs
        loss = torch.clamp(sims_diffs + margin, min = 0)
        weight = torch.ones_like(loss).masked_fill(levels_diffs <= 0, 0.0)
        
        if self.account_for_positive:
            weight = torch.masked_fill(irrelevance_levels.unsqueeze(2) != self.positive_irrelevance, 0.0)

        loss = loss * weight

        return loss.sum(2).sum(1).mean()