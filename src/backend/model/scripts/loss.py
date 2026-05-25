import torch
class TripletLoss(torch.nn.Module):
    def __init__(self, base_margin=0.1, positive_irrelevance=0, account_for_positive=True):
        super().__init__()
        self.base_margin = base_margin
        self.positive_irrelevance = positive_irrelevance
        self.account_for_positive = account_for_positive

    def forward(self, sims, irrelevance_levels):
        sims_difference = sims.unsqueeze(1) - sims.unsqueeze(2)
        irrelevance_levels_difference = irrelevance_levels.unsqueeze(1) - irrelevance_levels.unsqueeze(2)
        margin = self.base_margin * irrelevance_levels_difference
        loss =  torch.clamp( sims_difference + margin, min=0)

        weight = torch.ones_like(loss).masked_fill(irrelevance_levels_difference <= 0, 0.0)
        if self.account_for_positive:
            weight = weight.masked_fill( 
                irrelevance_levels.unsqueeze(2) != self.positive_irrelevance, 
                0.0  
            )

        loss = loss * weight
        
        return loss.sum(2).sum(1).mean()