"""
Keras utilities for PYAMLO examples.
"""
import tensorflow as tf

class MNISTDataset:
    """MNIST dataset class for PYAMLO."""
    
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
    
    def __repr__(self):
        return f"MNISTDataset(num_classes={self.get_num_classes()}, input_shape={self.get_input_shape()})"
