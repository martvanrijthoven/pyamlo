"""
Very simple Lightning module wrapper for torchvision models.
"""
import torch
import torch.nn.functional as F
import lightning.pytorch as pl


class LightningModel(pl.LightningModule):
    def __init__(self, model, lr=0.001):
        super().__init__()
        self.model = model
        self.lr = lr
        
        # Modify first layer for MNIST (1 channel instead of 3)
        if hasattr(model, 'features') and len(model.features) > 0:
            # For MobileNet - first layer is features[0][0]
            first_layer = model.features[0]
            if hasattr(first_layer, '0'):  # Sequential layer
                old_conv = first_layer[0]
                first_layer[0] = torch.nn.Conv2d(
                    1, old_conv.out_channels, 
                    kernel_size=old_conv.kernel_size,
                    stride=old_conv.stride, 
                    padding=old_conv.padding,
                    bias=old_conv.bias is not None
                )
    
    def forward(self, x):
        return self.model(x)
    
    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = F.cross_entropy(logits, y)
        self.log('train_loss', loss)
        return loss
    
    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = F.cross_entropy(logits, y)
        acc = (logits.argmax(dim=1) == y).float().mean()
        self.log('val_loss', loss)
        self.log('val_acc', acc)
    
    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.lr)
