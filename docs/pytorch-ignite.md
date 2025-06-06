# PyTorch Ignite with PYAMLO

This guide demonstrates using PyTorch Ignite with PYAMLO for MNIST digit classification, showcasing both monolithic and modular configuration approaches.

## Overview

The PyTorch Ignite example demonstrates how PYAMLO manages complex ML training pipelines through declarative YAML configuration, providing:

- **Reproducibility**: Complete training configuration in version-controlled files
- **Modularity**: Split complex configurations into focused, reusable components
- **Flexibility**: Easy experimentation with different architectures and hyperparameters
- **Clarity**: Human-readable configuration documenting the entire training process

## Quick Start

### Prerequisites
```bash
pip install -e .[ml]  # Install PYAMLO with ML dependencies
```

### Run Examples
```bash
cd examples/ignite

# Monolithic approach - everything in one file
python -m pyamlo run_monolithic.yml

# Modular approach - split into focused components
python -m pyamlo run_modular.yml
```

Both configurations will:
1. Download MNIST dataset (if not present)
2. Train a CNN model for 1 epoch
3. Evaluate on test set
4. Display training progress and final accuracy

!!! warning "First Run"
    The first run downloads the MNIST dataset (~9.9 MB), which may take a few moments.

## Configuration Approaches

### File Structure
```
examples/ignite/
├── run_modular.yml     # Main orchestration file
├── run_monolithic.yml  # Everything in one file
├── devices/
│   └── auto.yml        # Device detection
├── datasets/
│   └── mnist.yml       # Data pipeline
├── models/
│   ├── selector.yml    # Dynamic model selection
│   └── architectures/  # Individual model definitions
├── trainers/
│   └── supervised.yml  # Training engine
└── evaluators/
    └── supervised.yml  # Evaluation metrics
```

### Monolithic Configuration
Perfect for quick prototyping and simple experiments - everything in `run_monolithic.yml`.

### Modular Configuration
Organized into logical directories with focused files, providing:
- **Better Organization**: Related configs grouped together
- **Easier Maintenance**: Changes isolated to specific components
- **Reusability**: Components shared across experiments
- **Scalability**: Easy to add new models/datasets without clutter

## Key Components

### 1. Device Configuration (`devices/auto.yml`)
Automatically detects and configures the appropriate device:
```yaml
cuda: !@torch.cuda.is_available
device: !@torch.device
  type: "${'cuda' if cuda else 'cpu'}"
device_msg: !@print "Using device: ${device.type}"
```

### 2. Data Pipeline (`datasets/mnist.yml`)
```yaml
transform: !@torchvision.transforms.Compose
  transforms:
    - !@torchvision.transforms.ToTensor
    - !@torchvision.transforms.Normalize
      mean: [0.1307]
      std: [0.3081]

train_dataset: !@torchvision.datasets.MNIST
  root: './data'
  train: true
  download: true
  transform: ${transform}

train_loader: !@torch.utils.data.DataLoader
  dataset: ${train_dataset}
  batch_size: 64
  shuffle: true
```

### 3. Model Selection (`models/selector.yml`)
Dynamically selects model architecture:
```yaml
model_name: cnn  # Default model
_model: !include ./architectures/${model_name}.yml
model: ${_model.architecture}
_model_device_setup: !@pyamlo.call
  calling: ${model.to}
  device: ${device}
```

### 4. Training Setup (`trainers/supervised.yml`)
```yaml
criterion: !@torch.nn.CrossEntropyLoss
optimizer: !@torch.optim.Adam
  params: !@pyamlo.call ${model.parameters}
  lr: 0.001

trainer: !@ignite.engine.create_supervised_trainer
  model: ${model}
  optimizer: ${optimizer}
  loss_fn: ${criterion}
  device: ${device}

pbar: !@ignite.handlers.ProgressBar
  persist: true

attach_pbar: !@pyamlo.call
  calling: ${pbar.attach}
  engine: ${trainer}
```

### 5. Evaluation Setup (`evaluators/supervised.yml`)
```yaml
metrics:
  accuracy: !@ignite.metrics.Accuracy
  loss: !@ignite.metrics.Loss
    loss_fn: ${criterion}
  precision: !@ignite.metrics.Precision
  recall: !@ignite.metrics.Recall

evaluator: !@ignite.engine.create_supervised_evaluator
  model: ${model}
  metrics: ${metrics}
  device: ${device}
```

### 6. Main Orchestration (`run_modular.yml`)
```yaml
include!:
  - ./devices/auto.yml 
  - ./datasets/mnist.yml
  - ./models/selector.yml
  - ./trainers/supervised.yml
  - ./evaluators/supervised.yml

epochs: 1
train_result: !@pyamlo.call
  calling: ${trainer.run}
  data: ${train_loader}
  max_epochs: ${epochs}

eval_result: !@pyamlo.call
  calling: ${evaluator.run}
  data: ${val_loader}

results_msg: !@pprint.pprint ${evaluator.state.metrics}
```
## Model Architecture

The CNN model consists of:
1. **First Conv Block**: Conv2d(1→32) → ReLU → MaxPool2d
2. **Second Conv Block**: Conv2d(32→64) → ReLU → MaxPool2d  
3. **Classifier**: Flatten → Linear(3136→128) → ReLU → Dropout(0.5) → Linear(128→10)

**Input**: 28×28 grayscale images | **Output**: 10-class probability distribution

## Expected Results

```
Using device: cuda
Iteration: [938/938] 100%|████████████████████| [00:20<00:00]
Training completed!
Evaluation completed! {'accuracy': 0.9868, 'loss': 0.040337673950195316}
```

## Customization Examples

### Training Parameters
**Change optimizer** in `trainers/supervised.yml`:
```yaml
optimizer: !@torch.optim.SGD
  params: !@pyamlo.call ${model.parameters}
  lr: 0.01
  momentum: 0.9
```

**Change training duration** in `run_modular.yml`:
```yaml
epochs: 5
```

### Device Selection
**Force specific device** in `devices/auto.yml`:
```yaml
device: !@torch.device
  type: "cpu"  # or "cuda" or "mps"
```

### Additional Metrics
**Extend evaluator** in `evaluators/supervised.yml`:
```yaml
metrics:
  accuracy: !@ignite.metrics.Accuracy
  loss: !@ignite.metrics.Loss
    loss_fn: ${criterion}
  f1: !@ignite.metrics.Fbeta
    beta: 1
```

### Command Line Overrides
```bash
python -m pyamlo run_modular.yml pyamlo.lr=0.01 pyamlo.epochs=5
python -m pyamlo run_modular.yml 'pyamlo.model_name=resnet'
```

## Advanced Patterns

### Dynamic Model Selection
Switch between models using CLI overrides:
```bash
# Use default CNN model
python -m pyamlo run_modular.yml

# Switch to ResNet model  
python -m pyamlo run_modular.yml 'pyamlo.model_name=resnet'
```

### Environment-Specific Configuration
```yaml
learning_rate: !env {var: LEARNING_RATE, default: 0.001}
batch_size: !env {var: BATCH_SIZE, default: 64}
num_epochs: !env {var: NUM_EPOCHS, default: 1}
```

### Conditional Configuration
```yaml
is_cuda_available: !@torch.cuda.is_available
device_type: "${'cuda' if is_cuda_available else 'cpu'}"
batch_size: "${128 if is_cuda_available else 32}"
```

## Best Practices

1. **Start Simple**: Begin with monolithic configuration to understand the flow
2. **Split Gradually**: Move to modular configuration as complexity grows
3. **Name Meaningfully**: Use descriptive names for configuration keys
4. **Version Control**: Keep configurations alongside code
5. **Test Configurations**: Validate before long training runs

This example demonstrates PYAMLO's power for ML configuration management, scaling from simple prototypes to complex pipelines while maintaining readability and maintainability.
