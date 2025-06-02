# PyTorch Ignite with PYAMLO

This guide demonstrates how to use PyTorch Ignite with PYAMLO's YAML configuration system for MNIST digit classification. We'll explore both monolithic and modular configuration approaches.

## Overview

The PyTorch Ignite example showcases how PYAMLO can manage complex machine learning training pipelines through declarative YAML configuration. This approach provides:

- **Reproducibility**: Complete training configuration in version-controlled files
- **Modularity**: Split complex configurations into focused, reusable components
- **Flexibility**: Easy experimentation with different architectures and hyperparameters
- **Clarity**: Human-readable configuration that documents the entire training process

## Files Structure

```
examples/ignite/
├── data/               # MNIST dataset (auto-downloaded)
├── datasets/
│   └── mnist.yml       # Data pipeline configuration
├── devices/
│   └── auto.yml        # Device detection and configuration
├── evaluators/
│   └── supervised.yml  # Evaluation engine and metrics
├── models/
│   ├── selector.yml    # Dynamic model selection
│   └── architectures/  # Individual model definitions
│       ├── cnn.yml
│       └── resnet.yml
├── trainers/
│   └── supervised.yml  # Training engine and optimizer
├── run_modular.yml     # Modular configuration
└── run_monolithic.yml  # Monolithic configuration
```

## Quick Start

### Prerequisites

```bash
pip install -e .[ml]  # Install PYAMLO with ML dependencies
```

### Run the Monolithic Configuration

The monolithic approach puts everything in a single file:

```bash
cd examples/ignite
python -m pyamlo run_monolithic.yml
```

### Run the Modular Configuration

The modular approach splits configuration into focused components:

```bash
cd examples/ignite
python -m pyamlo run_modular.yml
```

Both configurations will:

1. Download MNIST dataset (if not already present)
2. Train a CNN model for 1 epoch
3. Evaluate on the test set
4. Display training progress and final accuracy

!!! warning "First Run"
    The first run will download the MNIST dataset (~9.9 MB), which may take a few moments depending on your internet connection.

## Configuration Approaches

### Monolithic Configuration (`run_monolithic.yml`)

The monolithic configuration demonstrates a complete training pipeline in a single file. This approach is great for:

- Quick prototyping
- Simple experiments
- Learning how the components work together
- Small projects with minimal configuration complexity

### Modular Configuration (organized by directories)

The modular approach organizes configuration into logical directories with focused files, providing several advantages:

- **Better Organization**: Related configurations are grouped together (all models in `models/`, all datasets in `datasets/`)
- **Easier Maintenance**: Changes to model architecture only require editing files in `models/`
- **Reusability**: Components can be easily shared across different experiments
- **Team Collaboration**: Multiple team members can work on different components simultaneously
- **Scalability**: Easy to add new models, datasets, or training strategies without cluttering

#### 1. Device Configuration (`devices/auto.yml`)

Automatically detects and configures the appropriate device:

```yaml
cuda: !@torch.cuda.is_available
device: !@torch.device
  type: "${'cuda' if cuda else 'cpu'}"
device_msg: !@print "Using device: ${device.type}"
```

#### 2. Data Configuration (`datasets/mnist.yml`)

Defines the complete data pipeline:

```yaml
# Data transforms for MNIST
transform: !@torchvision.transforms.Compose
  transforms:
    - !@torchvision.transforms.ToTensor
    - !@torchvision.transforms.Normalize
      mean: [0.1307]
      std: [0.3081]

# Training dataset
train_dataset: !@torchvision.datasets.MNIST
  root: './data'
  train: true
  download: true
  transform: ${transform}

# Training data loader
train_loader: !@torch.utils.data.DataLoader
  dataset: ${train_dataset}
  batch_size: 64
  shuffle: true
```


#### 3. Model Configuration (`models/selector.yml`)

Dynamically selects model architecture:

```yaml
model_name: cnn  # Default model
_model: !include ./architectures/${model_name}.yml
model: ${_model.architecture}
_model_device_setup: !@pyamlo.call
  calling: ${model.to}
  device: ${device}
```

#### 4. Trainer Configuration (`trainers/supervised.yml`)

Sets up training components and progress tracking:

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

# Progress bar for training visualization
pbar: !@ignite.handlers.ProgressBar
  persist: true

attach_pbar: !@pyamlo.call
  calling: ${pbar.attach}
  engine: ${trainer}
```

#### 5. Evaluator Configuration (`evaluators/supervised.yml`)

Defines evaluation metrics and testing:

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

#### 6. Run Configuration (`run_modular.yml`)

Main orchestration file that coordinates all components:

```yaml
# Import all configurations
include!:
  - ./devices/auto.yml 
  - ./datasets/mnist.yml
  - ./models/selector.yml
  - ./trainers/supervised.yml
  - ./evaluators/supervised.yml

epochs: 1

# Start training for 1 epoch
train_result: !@pyamlo.call
  calling: ${trainer.run}
  data: ${train_loader}
  max_epochs: ${epochs}

# Print completion message
completion_msg: !@print "Training completed!"

# Run final evaluation
eval_result: !@pyamlo.call
  calling: ${evaluator.run}
  data: ${val_loader}

results_msg: !@print "Evaluation completed! ${evaluator.state.metrics}"
```

## Model Architecture

The CNN model consists of:

1. **First Conv Block**: Conv2d(1→32) → ReLU → MaxPool2d
2. **Second Conv Block**: Conv2d(32→64) → ReLU → MaxPool2d  
3. **Classifier**: Flatten → Linear(3136→128) → ReLU → Dropout(0.5) → Linear(128→10)

**Input**: 28×28 grayscale images  
**Output**: 10-class probability distribution

## Expected Results

!!! example "Sample Output"
    After running the training, you should see output similar to:

    ```
    Using device: cuda
    Iteration: [938/938] 100%|████████████████████| [00:20<00:00]
    Training completed!
    Evaluation completed! {'accuracy': 0.9868, 'loss': 0.040337673950195316}
    ```

## Customization Examples

### Modify Training Parameters

Edit `trainers/supervised.yml` to change optimization settings:

```yaml
optimizer: !@torch.optim.SGD
  params: !@pyamlo.call ${model.parameters}
  lr: 0.01
  momentum: 0.9
```

Edit `run_modular.yml` to change training duration:

```yaml
epochs: 5  # Train for more epochs

train_result: !@pyamlo.call
  calling: ${trainer.run}
  data: ${train_loader}
  max_epochs: ${epochs}
```

### Specific Devices

Edit `devices/auto.yml` to set specific device:

```yaml
# For CPU only
device: !@torch.device
  type: "cpu"

# For CUDA (if available)  
device: !@torch.device
  type: "cuda"

# For Apple Silicon
device: !@torch.device
  type: "mps"
```

### Add More Metrics

Extend the evaluator in `evaluators/supervised.yml`:

```yaml
metrics:
  accuracy: !@ignite.metrics.Accuracy
  loss: !@ignite.metrics.Loss
    loss_fn: ${criterion}
  precision: !@ignite.metrics.Precision
  recall: !@ignite.metrics.Recall
  f1: !@ignite.metrics.Fbeta
    beta: 1

evaluator: !@ignite.engine.create_supervised_evaluator
  model: ${model}
  metrics: ${metrics}
  device: ${device}
```

### Configuration Overrides

Override configuration values from command line:

```bash
python -m pyamlo run_modular.yml pyamlo.lr=0.01 pyamlo.epochs=5
```

### Data Augmentation

Enhance the data pipeline in `datasets/mnist.yml`:

```yaml
train_transform: !@torchvision.transforms.Compose
  transforms:
    - !@torchvision.transforms.ToTensor
    - !@torchvision.transforms.RandomRotation
      degrees: 10
    - !@torchvision.transforms.RandomAffine
      degrees: 0
      translate: [0.1, 0.1]
    - !@torchvision.transforms.Normalize
      mean: [0.1307]
      std: [0.3081]
```

## Advanced Patterns

### Conditional Configuration

Use PYAMLO's expression system for conditional behavior:

```yaml
# In devices/auto.yml
is_cuda_available: !@torch.cuda.is_available
device_type: "${'cuda' if is_cuda_available else 'cpu'}"
batch_size: "${128 if is_cuda_available else 32}"  # Larger batch on GPU
```

### Dynamic Model Architecture

Create models based on configuration:

```yaml
# In model.yml
hidden_size: 128
num_classes: 10

model: !@torch.nn.Sequential
  - !@torch.nn.Flatten
  - !@torch.nn.Linear
    in_features: 784  # 28*28
    out_features: ${hidden_size}
  - !@torch.nn.ReLU
  - !@torch.nn.Dropout
    p: 0.5
  - !@torch.nn.Linear
    in_features: ${hidden_size}
    out_features: ${num_classes}
```

### Environment-Specific Configuration

Use of environment variables:

```yaml
# In trainer.yml
learning_rate: !env {var: LEARNING_RATE, default: 0.001}
batch_size: !env {var: BATCH_SIZE, default: 64}
num_epochs: !env {var: NUM_EPOCHS, default: 1}
```

## Dynamic Model Selection

PYAMLO supports dynamic model selection through parametrized includes, allowing you to easily switch between different model architectures via CLI overrides.

### Model Selector Pattern

Create a model selector that dynamically includes architecture files based on a parameter:

```yaml
# models/selector.yml
model_name: cnn  # Default model
_model: !include ./architectures/${model_name}.yml
model: ${_model.architecture}
_model_device_setup: !@pyamlo.call
  calling: ${model.to}
  device: ${device}
```

Individual architecture files contain their model definitions:

```yaml
# models/architectures/cnn.yml
architecture: !@torch.nn.Sequential
  - !@torch.nn.Conv2d [1, 32, 3, 1, 1]
  - !@torch.nn.ReLU
  - !@torch.nn.MaxPool2d [2]
  # ... more layers
```

```yaml
# models/architectures/resnet.yml
architecture: !@torch.nn.Sequential
  - !@torch.nn.Conv2d [1, 64, 7, 2, 3, false]
  - !@torch.nn.BatchNorm2d [64]
  - !@torch.nn.ReLU [true]
  # ... more layers
```

### Usage

Switch between models using CLI overrides:

```bash
# Use default CNN model
python -m pyamlo run_modular.yml

# Switch to ResNet model
python -m pyamlo run_modular.yml 'pyamlo.model_name=resnet'
```


## Best Practices

1. **Start Simple**: Begin with the monolithic configuration to understand the flow
2. **Split Gradually**: Move to modular configuration as complexity grows
3. **Name Meaningfully**: Use descriptive names for configuration keys
4. **Document Choices**: Add comments explaining hyperparameter choices
5. **Version Control**: Keep configurations in version control alongside code
6. **Test Configurations**: Validate configurations work before long training runs
7. **Use Includes Wisely**: Group related configurations together

## Next Steps

This example demonstrates the power of PYAMLO for ML configuration management. Consider exploring:

- **Different Models**: Replace the CNN with ResNet, Transformer, etc.
- **Other Datasets**: Adapt the configuration for CIFAR-10, ImageNet, etc.
- **Advanced Training**: Add learning rate scheduling, early stopping, checkpointing
- **Hyperparameter Tuning**: Use PYAMLO with hyperparameter optimization libraries
- **Production Deployment**: Create configurations for different deployment environments

The modular approach scales well to complex ML pipelines while maintaining readability and maintainability.
