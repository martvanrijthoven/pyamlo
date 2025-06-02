# Simple CNN Training with PyTorch Lightning and pyamlo

This is a minimal example showing how to train a CNN with PyTorch Lightning where everything is defined in the YAML configuration using pyamlo's object instantiation and function calling features.

## Files
- `main.yml` - Main configuration that includes other configs and starts training
- `data.yml` - Data transforms, datasets, and dataloaders configuration
- `model.yml` - Model definition and Lightning wrapper configuration
- `simple_cnn.py` - Minimal Lightning module wrapper
- `config.yml` - Original monolithic config (kept for reference)

## Key Features Demonstrated
- **Object Instantiation**: All PyTorch/Lightning objects defined in YAML with `!@`
- **Function Calling**: Training started directly from config with `!@pyamlo.call`
- **Variable Interpolation**: Reusing transforms and datasets with `${...}`
- **Automatic Downloads**: MNIST dataset downloaded automatically
- **Path Management**: Python path setup handled in config

## Run
```bash
cd examples/simple_cnn
PYTHONPATH=. python -m pyamlo main.yml
```

The config defines everything AND starts training:
- Torchvision transforms and datasets
- PyTorch DataLoaders  
- MobileNetV2 model from torchvision
- Lightning Trainer
- **Training execution** with `!@pyamlo.call`

Training starts automatically when the config is loaded - no separate script needed!
