# PyTorch Ignite Integration Guide

PYAMLO makes PyTorch Ignite configurations modular and reusable. This guide shows a complete MNIST CNN example using the selector pattern.

## Complete Example

**run_modular.yml**
```yaml
# Configuration selection
dataset_name: mnist
model_name: cnn

# Load modular components
include!:
  - ./devices/auto.yml 
  - ./datasets/selector.yml
  - ./models/selector.yml
  - ./trainers/selector.yml
  - ./evaluators/selector.yml

# Training settings
epochs: 1

# Train model
train_result: !$@trainer.run
  start_msg: "Starting training..."
  finish_msg: "Training completed!"
  data: ${train_loader}
  max_epochs: ${epochs}

# Evaluate model
eval_result: !$@evaluator.run
  start_msg: "Running evaluation..."
  finish_msg: "Evaluation completed!"
  data: ${val_loader}

# Display results
results_msg: !@pprint.pprint ${evaluator.state.metrics}
```

## Components

**devices/auto.yml**
```yaml
cuda: !@torch.cuda.is_available
device: !@torch.device
  type: "${'cuda' if cuda else 'cpu'}"
```

**datasets/selector.yml**
```yaml
dataset_name: mnist
train_dataset, val_dataset: !include_from ./${dataset_name}.yml

train_loader: !@torch.utils.data.DataLoader
  dataset: ${train_dataset}
  batch_size: 64
  shuffle: true

val_loader: !@torch.utils.data.DataLoader
  dataset: ${val_dataset}
  batch_size: 64
  shuffle: false
```

**datasets/mnist.yml**
```yaml
transform: !@torchvision.transforms.Compose
  transforms:
    - !@torchvision.transforms.ToTensor
    - !@torchvision.transforms.Normalize
      mean: [0.1307]
      std: [0.3081]

train_dataset: !@torchvision.datasets.MNIST
  root: "./data"
  train: true
  download: true
  transform: ${transform}

val_dataset: !@torchvision.datasets.MNIST
  root: "./data"
  train: false
  download: true
  transform: ${transform}
```

**models/selector.yml**
```yaml
model_name: cnn
model: !include_from ./${model_name}.yml
model: !$@model.to ${device}
```

**models/cnn.yml**
```yaml
model: !@torch.nn.Sequential
  - !@torch.nn.Conv2d
    in_channels: 1
    out_channels: 32
    kernel_size: 3
    padding: 1
  - !@torch.nn.ReLU
  - !@torch.nn.MaxPool2d
    kernel_size: 2
  - !@torch.nn.Conv2d
    in_channels: 32
    out_channels: 64
    kernel_size: 3
    padding: 1
  - !@torch.nn.ReLU
  - !@torch.nn.MaxPool2d
    kernel_size: 2
  - !@torch.nn.Flatten
  - !@torch.nn.Linear
    in_features: 3136
    out_features: 128
  - !@torch.nn.ReLU
  - !@torch.nn.Dropout
    p: 0.5
  - !@torch.nn.Linear
    in_features: 128
    out_features: 10
```

**trainers/selector.yml** 
```yaml
lr: 0.001
optimizer: !@torch.optim.Adam
  params: !$@model.parameters
  lr: ${lr}

loss_fn: !@torch.nn.CrossEntropyLoss

trainer: !@ignite.engine.create_supervised_trainer
  model: ${model}
  optimizer: ${optimizer}
  loss_fn: ${loss_fn}
  device: ${device}
```

**evaluators/selector.yml**
```yaml
evaluator: !@ignite.engine.create_supervised_evaluator
  model: ${model}
  metrics:
    accuracy: !@ignite.metrics.Accuracy
    loss: !@ignite.metrics.Loss ${loss_fn}
  device: ${device}
```

## Running

```bash
cd examples/ignite

# Basic training
python -m pyamlo run_modular.yml

# With overrides
python -m pyamlo run_modular.yml pyamlo.model_name=resnet pyamlo.lr=0.01
```
