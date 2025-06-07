# PyTorch Ignite with PYAMLO

This guide demonstrates using PyTorch Ignite with PYAMLO for MNIST digit classification, showcasing modular ML configuration management.

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

## Configuration Structure

### File Organization
```
examples/ignite/
├── run_modular.yml     # Main configuration file
├── run_monolithic.yml  # Single-file alternative
├── devices/auto.yml    # Device detection
├── datasets/
│   ├── selector.yml    # Dataset selection
│   └── mnist.yml       # MNIST configuration
├── models/
│   ├── selector.yml    # Model selection
│   ├── cnn.yml         # CNN architecture
│   └── resnet.yml      # ResNet architecture
├── trainers/selector.yml    # Training configuration
└── evaluators/selector.yml  # Evaluation setup
```

The modular approach provides better organization, easier maintenance, and component reusability.

## Key Components

The configuration uses a selector pattern for flexible component switching:

### Device Configuration
```yaml
cuda: !@torch.cuda.is_available
device: !@torch.device
  type: "${'cuda' if cuda else 'cpu'}"
```

### Dataset Selection
```yaml
dataset_name: mnist
train_dataset, val_dataset: !include_from ./${dataset_name}.yml

train_loader: !@torch.utils.data.DataLoader
  dataset: ${train_dataset}
  batch_size: 64
  shuffle: true
```

### Model Selection
```yaml
model_name: cnn
model: !include_from ./${model_name}.yml
```

### Main Configuration
```yaml
include!:
  - ./devices/auto.yml 
  - ./datasets/selector.yml
  - ./models/selector.yml
  - ./trainers/selector.yml
  - ./evaluators/selector.yml

epochs: 1
train_result: !$@trainer.run
  data: ${train_loader}
  max_epochs: ${epochs}
```
## Usage

### Command Line Overrides
```bash
# Change learning rate
python -m pyamlo run_modular.yml pyamlo.lr=0.01

# Change model
python -m pyamlo run_modular.yml pyamlo.model_name=resnet

# Multiple overrides
python -m pyamlo run_modular.yml pyamlo.lr=0.01 pyamlo.epochs=5 pyamlo.model_name=resnet
```

## Selector Pattern

The modular configuration uses a selector pattern for maximum flexibility:

```yaml
# In any selector.yml file
component_name: default_option
component: !include_from ./${component_name}.yml
```

This pattern enables:
- **Runtime selection**: Change components via CLI overrides
- **Easy extensibility**: Add new components by creating new files
- **Clean organization**: Keep related configurations together

### Advanced Usage

**Environment variables:**
```yaml
learning_rate: !env {var: LEARNING_RATE, default: 0.001}
model_name: !env {var: MODEL_NAME, default: "cnn"}
```

**Conditional configuration:**
```yaml
is_cuda_available: !@torch.cuda.is_available
batch_size: "${128 if is_cuda_available else 32}"
```
