# PyTorch Lightning with PYAMLO

This guide demonstrates using PyTorch Lightning with PYAMLO for MNIST digit classification, showcasing declarative ML configuration for Lightning workflows.

## Quick Start

### Prerequisites
```bash
pip install -e .[ml]  # Install PYAMLO with ML dependencies
```

### Run Example
```bash
cd examples/lightning

# Set Python path and run training
PYTHONPATH=. python -m pyamlo train.yml
```

The training will:
1. Download MNIST dataset (if not present)
2. Train a MobileNetV2 model for 1 epoch
3. Validate after each epoch
4. Save checkpoints and logs to `lightning_logs/`

!!! warning "First Run"
    The first run downloads the MNIST dataset (~9.9 MB), which may take a few moments.

## Configuration Structure

### File Organization
```
examples/lightning/
├── train.yml        # Main training configuration
├── mnist.yml        # MNIST dataset configuration
├── mobilenet.yml    # MobileNetV2 model configuration
├── simple_cnn.py    # Lightning module wrapper
└── data/           # Downloaded datasets
```

## Key Components

### Main Configuration (`train.yml`)
```yaml
# Dataset and model selection
dataset: mnist
model_name: mobilenet

# Load configurations using !include_from
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
train: !@pyamlo.call
  calling: ${trainer.fit}
  model: ${lightning_model}
  train_dataloaders: ${train_loader}
  val_dataloaders: ${val_loader}
```

### Dataset Configuration (`mnist.yml`)
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

### Model Configuration (`mobilenet.yml`)
```yaml
model: !@torchvision.models.mobilenet_v2
  num_classes: 10
```

### Lightning Module (`simple_cnn.py`)
The Lightning module wrapper adapts torchvision models for MNIST:
- Modifies first layer to accept 1-channel (grayscale) input
- Implements training and validation steps
- Configures optimizer and logging

## Usage

### Command Line Overrides
```bash
# Change learning rate
PYTHONPATH=. python -m pyamlo train.yml pyamlo.lr=0.01

# Change model
PYTHONPATH=. python -m pyamlo train.yml pyamlo.model_name=mobilenet

# Change dataset (if you have other datasets)
PYTHONPATH=. python -m pyamlo train.yml pyamlo.dataset=mnist

# Change training parameters
PYTHONPATH=. python -m pyamlo train.yml pyamlo.trainer.max_epochs=5

# Multiple overrides
PYTHONPATH=. python -m pyamlo train.yml pyamlo.lr=0.01 pyamlo.trainer.max_epochs=3
```

### Expected Output
```
Epoch 1/1: 100%|██████████| 938/938 [00:45<00:00, 20.67it/s, v_num=0]
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃        Test metric        ┃       DataLoader 0        ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│         val_acc           │    0.9820000529289246     │
│         val_loss          │    0.05834667384624481    │
└───────────────────────────┴───────────────────────────┘
```

## Lightning Features

### Built-in Capabilities
The Lightning integration automatically provides:
- **Distributed Training**: Multi-GPU and multi-node support
- **Mixed Precision**: Automatic 16-bit training
- **Checkpointing**: Model state saving and resuming  
- **Logging**: TensorBoard, Weights & Biases integration
- **Early Stopping**: Automatic training termination
- **Progress Bars**: Training progress visualization

### Advanced Configuration
```yaml
# Enhanced trainer with more features
trainer: !@lightning.pytorch.Trainer
  max_epochs: 10
  accelerator: "auto"
  devices: "auto"
  precision: "16-mixed"  # Mixed precision training
  enable_checkpointing: true
  enable_progress_bar: true
  enable_model_summary: true
  log_every_n_steps: 50
  
# Add callbacks
callbacks:
  - !@lightning.pytorch.callbacks.ModelCheckpoint
    monitor: "val_acc"
    mode: "max"
    save_top_k: 3
  - !@lightning.pytorch.callbacks.EarlyStopping
    monitor: "val_loss"
    patience: 3
    mode: "min"

# Add callbacks to trainer
trainer: !@lightning.pytorch.Trainer
  # ...existing config...
  callbacks: ${callbacks}
```

### Logging Integration
```yaml
# TensorBoard logger
tb_logger: !@lightning.pytorch.loggers.TensorBoardLogger
  save_dir: "./lightning_logs"
  name: "mnist_experiment"

# Weights & Biases logger
wandb_logger: !@lightning.pytorch.loggers.WandbLogger
  project: "mnist-classification"
  name: "mobilenet-experiment"

# Add logger to trainer
trainer: !@lightning.pytorch.Trainer
  # ...existing config...
  logger: ${tb_logger}  # or ${wandb_logger}
```

## Customization Examples

### Different Model Architectures
Create new model configuration files:

**`resnet.yml`:**
```yaml
model: !@torchvision.models.resnet18
  num_classes: 10
```

**`efficientnet.yml`:**
```yaml
model: !@torchvision.models.efficientnet_b0
  num_classes: 10
```

Then switch models:
```bash
PYTHONPATH=. python -m pyamlo train.yml pyamlo.model_name=resnet
```

### Environment Variables
```yaml
# Use environment variables for configuration
learning_rate: !env {var: LEARNING_RATE, default: 0.001}
batch_size: !env {var: BATCH_SIZE, default: 64}
max_epochs: !env {var: MAX_EPOCHS, default: 1}
```

### Conditional Configuration
```yaml
# Adapt configuration based on hardware
is_cuda_available: !@torch.cuda.is_available
batch_size: "${128 if is_cuda_available else 32}"
devices: "${'auto' if is_cuda_available else 1}"
```

## Lightning vs Ignite

| Feature | PyTorch Lightning | PyTorch Ignite |
|---------|-------------------|----------------|
| **Learning Curve** | Steeper (more opinionated) | Gentler (more flexible) |
| **Boilerplate** | Minimal | More manual setup |
| **Built-in Features** | Extensive | Manual implementation |
| **Customization** | Through Lightning modules | Direct event handling |
| **Best For** | Standard workflows | Custom training loops |

Both integrate seamlessly with PYAMLO's configuration management, allowing you to choose the right tool for your specific needs.

## Best Practices

1. **Modular Configuration**: Split datasets, models, and training configs into separate files
2. **Environment Variables**: Use `!env` for deployment-specific settings
3. **CLI Overrides**: Leverage command line overrides for experimentation
4. **Validation**: Use `!include_from` validation to ensure configuration consistency
5. **Logging**: Configure appropriate loggers for experiment tracking
6. **Callbacks**: Use Lightning callbacks for checkpointing and early stopping

The Lightning integration demonstrates PYAMLO's ability to manage complex ML frameworks through declarative configuration, making experimentation and deployment more systematic and reproducible.
