# Keras Integration Guide

PYAMLO makes Keras/TensorFlow configurations modular and reusable. This guide shows a complete MNIST CNN example.

## Complete Example

**train.yml**
```yaml
# Configuration selection
dataset_name: mnist
model_name: cnn
optimizer_name: adam

# Load modular components
dataset: !include_from datasets/${dataset_name}.yml
model: !include_from models/${model_name}.yml

# Training settings
batch_size: 32
epochs: 1
validation_split: 0.1

# Compile and train
compile_step: !$@model.compile
  optimizer: ${optimizer_name}
  loss: "sparse_categorical_crossentropy"
  metrics: ["accuracy"]

history: !$@model.fit
  x: ${dataset.x_train}
  y: ${dataset.y_train}
  batch_size: ${batch_size}
  epochs: ${epochs}
  validation_split: ${validation_split}
  verbose: 1

test_results: !$@model.evaluate
  x: ${dataset.x_test}
  y: ${dataset.y_test}
  verbose: 0
```

## Components

**datasets/mnist.yml**
```yaml
dataset: !@keras_utils.MNISTDataset
```

**models/cnn.yml**
```yaml
model: !@tensorflow.keras.Sequential
  layers:
    - !@tensorflow.keras.layers.Conv2D
        filters: 32
        kernel_size: [3, 3]
        activation: "relu"
        input_shape: ${dataset.input_shape}
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
        units: ${dataset.num_classes}
        activation: "softmax"
```

**keras_utils.py**
```python
import tensorflow as tf

class MNISTDataset:
    def __init__(self):
        (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
        
        self.x_train = tf.cast(x_train, tf.float32) / 255.0
        self.x_test = tf.cast(x_test, tf.float32) / 255.0
        
        self.x_train = tf.expand_dims(self.x_train, axis=-1)
        self.x_test = tf.expand_dims(self.x_test, axis=-1)
        
        self.y_train = tf.cast(y_train, tf.int32)
        self.y_test = tf.cast(y_test, tf.int32)
        
        self.num_classes = 10
        self.input_shape = (28, 28, 1)
```

## Key Features

- **Dataset Classes**: Encapsulate data loading and preprocessing
- **Dynamic References**: Model uses `${dataset.input_shape}` and `${dataset.num_classes}`
- **String Optimizers**: Simple `optimizer: "adam"` instead of complex objects
- **Modular Design**: Separate files for datasets and models

## Running

```bash
cd examples/keras
PYTHONPATH=. python -m pyamlo train.yml
```
