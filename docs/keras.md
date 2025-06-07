# Keras Integration Guide

This guide demonstrates how to use PYAMLO with TensorFlow/Keras for deep learning projects. PYAMLO's modular configuration system makes it easy to manage complex machine learning workflows with clean, reusable components.

## Quick Start

### Basic Training Configuration

```yaml
# train.yml
# Configuration selection
dataset_name: mnist
model_name: cnn
optimizer_name: adam

# Load configurations
dataset: !include_at datasets/${dataset_name}.yml
model: !include_at models/${model_name}.yml

# Training parameters
batch_size: 32
epochs: 1
validation_split: 0.1

# Compile model
compile_step: !@pyamlo.call
  calling: ${model.compile}
  optimizer: ${optimizer_name}
  loss: "sparse_categorical_crossentropy"
  metrics: ["accuracy"]

# Print model summary
summary_step: !@pyamlo.call
  calling: ${model.summary}

# Train the model
history: !@pyamlo.call
  calling: ${model.fit}
  x: ${dataset.x_train}
  y: ${dataset.y_train}
  batch_size: ${batch_size}
  epochs: ${epochs}
  validation_split: ${validation_split}
  verbose: 1

# Evaluate on test set
test_results: !@pyamlo.call
  calling: ${model.evaluate}
  x: ${dataset.x_test}
  y: ${dataset.y_test}
  verbose: 0

# Print results
final_message: !@print "Training completed! Check history and test_results for details."
```

## Modular Components

### Dataset Configuration

**datasets/mnist.yml**
```yaml
# MNIST Dataset Configuration
dataset: !@keras_utils.MNISTDataset
_num_classes: 10
_input_shape: [28, 28, 1]
```

**keras_utils.py**
```python
import tensorflow as tf

class MNISTDataset:
    """MNIST dataset class for PYAMLO."""
    
    def __init__(self):
        (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
        
        # Normalize pixel values
        self.x_train = tf.cast(x_train, tf.float32) / 255.0
        self.x_test = tf.cast(x_test, tf.float32) / 255.0

        # Add channel dimension for CNN
        self.x_train = tf.expand_dims(self.x_train, axis=-1)
        self.x_test = tf.expand_dims(self.x_test, axis=-1)

        self.y_train = tf.cast(y_train, tf.int32)
        self.y_test = tf.cast(y_test, tf.int32)

        self.num_classes = 10
        self.input_shape = (28, 28, 1)
    
    def __repr__(self):
        return f"MNISTDataset(num_classes={self.num_classes}, input_shape={self.input_shape})"
```

### Model Configuration

**models/cnn.yml**
```yaml
# CNN Model Configuration using direct Keras layers
model: !@tensorflow.keras.Sequential
  layers:
    - !@tensorflow.keras.layers.Conv2D
        filters: 32
        kernel_size: [3, 3]
        activation: "relu"
        input_shape: [28, 28, 1]
    - !@tensorflow.keras.layers.MaxPooling2D
        pool_size: [2, 2]
    - !@tensorflow.keras.layers.Conv2D
        filters: 64
        kernel_size: [3, 3]
        activation: "relu"
    - !@tensorflow.keras.layers.MaxPooling2D
        pool_size: [2, 2]
    - !@tensorflow.keras.layers.Conv2D
        filters: 64
        kernel_size: [3, 3]
        activation: "relu"
    - !@tensorflow.keras.layers.Flatten
    - !@tensorflow.keras.layers.Dense
        units: 64
        activation: "relu"
    - !@tensorflow.keras.layers.Dropout
        rate: 0.5
    - !@tensorflow.keras.layers.Dense
        units: 10
        activation: "softmax"
```

## Key Features

### Single Key Include Pattern

The current implementation uses a clean single-key include pattern:

```yaml
# Load complete dataset object
dataset: !include_at datasets/mnist.yml

# Load complete model object  
model: !include_at models/cnn.yml

# Access dataset properties through the dataset object
x: ${dataset.x_train}
y: ${dataset.y_train}
```

### Private Metadata with `_` Prefix

PYAMLO's `!include_at` validation allows keys starting with underscore (`_`) to be included without validation errors. This is perfect for metadata:

```yaml
# datasets/mnist.yml can contain private metadata
dataset: !include_at datasets/mnist.yml
# File contains: dataset, _num_classes, _input_shape

# These private keys don't cause validation errors
# but aren't directly used in the main configuration
```

### Direct Keras Layer Configuration

Models are built using direct Keras layer instantiation in YAML:

```yaml
model: !@tensorflow.keras.Sequential
  layers:
    - !@tensorflow.keras.layers.Conv2D
        filters: 32
        kernel_size: [3, 3]
        activation: "relu"
        input_shape: [28, 28, 1]
    # ... more layers
```

### String-Based Optimizers

For simplicity, use string-based optimizers directly in the compile step:

```yaml
# Clean and simple
compile_step: !@pyamlo.call
  calling: ${model.compile}
  optimizer: "adam"  # Direct string reference
  loss: "sparse_categorical_crossentropy"
  metrics: ["accuracy"]
```

## Advanced Examples

### Custom Training with Callbacks

```yaml
# advanced_train.yml
dataset: !include_at datasets/mnist.yml
model: !include_at models/cnn.yml

# Custom callbacks
callbacks:
  - !@tensorflow.keras.callbacks.EarlyStopping
      monitor: "val_loss"
      patience: 3
      restore_best_weights: true
  
  - !@tensorflow.keras.callbacks.ReduceLROnPlateau
      monitor: "val_loss"
      factor: 0.5
      patience: 2

# Compile with custom optimizer object
compile_step: !@pyamlo.call
  calling: ${model.compile}
  optimizer: !@tensorflow.keras.optimizers.Adam
    learning_rate: 0.001
  loss: "sparse_categorical_crossentropy"
  metrics: ["accuracy"]

# Training with callbacks and validation data
history: !@pyamlo.call
  calling: ${model.fit}
  x: ${dataset.x_train}
  y: ${dataset.y_train}
  validation_data: [${dataset.x_test}, ${dataset.y_test}]
  epochs: 50
  batch_size: 32
  callbacks: ${callbacks}
  verbose: 1
```

### Multiple Dataset Selection

```yaml
# multi_dataset.yml
dataset_name: mnist  # Switch between mnist, cifar10, etc.

dataset: !include_at datasets/${dataset_name}.yml
model: !include_at models/cnn.yml

# Rest of configuration...
```

## Best Practices

### 1. Use Dataset Classes
- Create dataset classes that handle loading and preprocessing
- Include private metadata (`_num_classes`, `_input_shape`) for reference
- Keep data access clean through object properties

### 2. Direct Layer Configuration
- Use direct Keras layer instantiation in YAML for transparency
- Specify all layer parameters explicitly in configuration
- Avoid complex utility functions when simple YAML works

### 3. String Optimizers for Simplicity
- Use string-based optimizers (`"adam"`, `"sgd"`) for basic cases
- Only use object-based optimizers when you need specific parameters
- Keep compilation simple and readable

### 4. Modular Design
- Separate datasets, models into different files
- Use consistent naming patterns (`dataset_name`, `model_name`)
- Make configurations easily switchable with variables

### 5. Validation-Friendly Structure
- Design configurations to work with PYAMLO's key validation
- Use single-key includes (`dataset: !include_at ...`)
- Prefix internal metadata with underscore

## Running Your Configuration

```bash
# Run from the examples/keras directory
cd examples/keras
PYTHONPATH=. python -m pyamlo train.yml
```

Or in Python:
```python
import os
from pyamlo import load_config

# Change to keras examples directory
os.chdir('examples/keras')

# Load and execute configuration
config = load_config('train.yml')

# Access results
print(f"Final test accuracy: {config['test_results'][1]:.4f}")
print(f"Training history keys: {config['history'].history.keys()}")
```

## Error Handling

Common issues and solutions:

### Validation Errors
```
IncludeError: File 'datasets/mnist.yml' contains unexpected keys: ['extra_key']
```
**Solution**: Ensure included files only contain expected keys or prefix with `_`

### Import Errors
```
AttributeError: module 'keras_utils' has no attribute 'MNISTDataset'
```
**Solution**: Ensure `keras_utils.py` is in the correct directory and `PYTHONPATH` is set

### Shape Mismatches
```
ValueError: Input shape incompatible with layer
```
**Solution**: Verify that dataset preprocessing matches model input expectations

### TensorFlow Import Issues
```
ModuleNotFoundError: No module named 'tensorflow'
```
**Solution**: Install TensorFlow: `pip install tensorflow`

## Example Output

When running the basic example, you should see output like:
```
Model: "sequential"
_________________________________________________________________
 Layer (type)                Output Shape              Param #   
=================================================================
 conv2d (Conv2D)             (None, 26, 26, 32)       320       
 max_pooling2d (MaxPooling2  (None, 13, 13, 32)       0         
 ...
=================================================================
Total params: 93,322
Trainable params: 93,322
Non-trainable params: 0

1875/1875 [==============================] - 45s 24ms/step - loss: 0.1234 - accuracy: 0.9647 - val_loss: 0.0567 - val_accuracy: 0.9823
313/313 [==============================] - 2s 6ms/step - loss: 0.0521 - accuracy: 0.9847
Training completed! Check history and test_results for details.
```

This guide provides a complete foundation for using PYAMLO with Keras, emphasizing the clean, modular approach used in the current implementation.
