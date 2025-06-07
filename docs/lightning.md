# PyTorch Lightning Integration Guide

PYAMLO makes PyTorch Lightning configurations modular and reusable. This guide shows a complete MNIST MobileNetV2 example.

## Complete Example

**train.yml**
```yaml
# Configuration selection
dataset: mnist
model_name: mobilenet

# Load modular components
model: !include_from ${model_name}.yml
train_dataset, val_dataset: !include_from ${dataset}.yml

# DataLoaders
train_loader: !@torch.utils.data.DataLoader
  dataset: ${train_dataset}
  batch_size: 64
  shuffle: true

val_loader: !@torch.utils.data.DataLoader
  dataset: ${val_dataset}
  batch_size: 64
  shuffle: false

# Lightning model wrapper
lightning_model: !@simple_cnn.LightningModel
  model: ${model}
  lr: 0.001

# Lightning trainer
trainer: !@lightning.pytorch.Trainer
  max_epochs: 1
  accelerator: "auto"
  devices: 1

# Start training
train: !$@trainer.fit
  model: ${lightning_model}
  train_dataloaders: ${train_loader}
  val_dataloaders: ${val_loader}
```

## Components

**mnist.yml**
```yaml
# MNIST transforms
_mnist:
  _transform: !@torchvision.transforms.Compose
    transforms:
      - !@torchvision.transforms.ToTensor
      - !@torchvision.transforms.Normalize
        mean: [0.1307]
        std: [0.3081]

# Datasets
train_dataset: !@torchvision.datasets.MNIST
  root: "./data"
  train: true
  download: true
  transform: ${_mnist._transform}

val_dataset: !@torchvision.datasets.MNIST
  root: "./data"
  train: false
  download: true
  transform: ${_mnist._transform}
```

**mobilenet.yml**
```yaml
model: !@torchvision.models.mobilenet_v2
  num_classes: 10
```

**simple_cnn.py**
```python
import lightning.pytorch as pl
import torch
import torch.nn.functional as F
import torchmetrics

class LightningModel(pl.LightningModule):
    def __init__(self, model, lr=0.001):
        super().__init__()
        self.model = model
        self.lr = lr
        self.accuracy = torchmetrics.Accuracy(task='multiclass', num_classes=10)
        
        # Modify first layer for MNIST (1 channel input)
        if hasattr(model, 'features') and hasattr(model.features[0], 'in_channels'):
            if model.features[0].in_channels == 3:
                model.features[0] = torch.nn.Conv2d(1, model.features[0].out_channels, 
                                                   kernel_size=model.features[0].kernel_size,
                                                   stride=model.features[0].stride,
                                                   padding=model.features[0].padding,
                                                   bias=model.features[0].bias is not None)
    
    def forward(self, x):
        return self.model(x)
    
    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = F.cross_entropy(logits, y)
        acc = self.accuracy(logits, y)
        self.log('train_loss', loss, prog_bar=True)
        self.log('train_acc', acc, prog_bar=True)
        return loss
    
    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = F.cross_entropy(logits, y)
        acc = self.accuracy(logits, y)
        self.log('val_loss', loss, prog_bar=True)
        self.log('val_acc', acc, prog_bar=True)
        return loss
    
    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.lr)
```

## Running

```bash
cd examples/lightning

# Basic training
PYTHONPATH=. python -m pyamlo train.yml

# With overrides
PYTHONPATH=. python -m pyamlo train.yml pyamlo.lr=0.01 pyamlo.trainer.max_epochs=5
```
