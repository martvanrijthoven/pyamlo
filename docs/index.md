Welcome to Yamlo
yamlo provides a way to load YAML configuration files with enhanced features like includes, merging, variable interpolation, and object instantiation. It aims to make complex configurations manageable by allowing separation of concerns and dynamic value generation.

#### Key Features:

 - Includes: Merge multiple YAML files using _includes.
 - Merging: Deep merge dictionaries, extend lists (!extend), and replace dictionaries (!patch).
 - Environment Variables: Substitute values using !env VAR_NAME or !env {var: NAME, default: ...}.
- Object Instantiation: Create Python objects or call functions directly from YAML using !@module.path.ClassName.
 - Variable Interpolation: Reference configuration values using ${path.to.value} syntax, including attributes of instantiated objects.


### Installation

```uv pip install yamlo```




### Quick Start
Given a simple YAML file config.yaml:

```yaml

app:
  name: MyWebApp
  port: 8080
  host: web.local

greeting: Hello, ${app.name}!
database_url: postgres://${app.host}:${app.port}/maindb

```

You can load and resolve it using yamlo:




```python
from yamlo import load_config
from pathlib import Path
import io

# Create a dummy file for the example
Path("config.yaml").write_text("""
app:
  name: MyWebApp
  port: 8080
  host: web.local
greeting: Hello, ${app.name}!
database_url: postgres://${app.host}:${app.port}/maindb
""")

try:
    with open("config.yaml", "r") as f:
        cfg, instances = load_config(f)

    # cfg is the fully resolved configuration dictionary
    print(cfg['greeting'])
    # Output: Hello, MyWebApp!

    print(cfg['database_url'])
    # Output: postgres://web.local:8080/maindb

    # instances dictionary would be empty in this simple case
    print(instances)
    # Output: {}

except FileNotFoundError:
    print("Error: config.yaml not found. Please create it for the Quick Start example.")
except Exception as e:
    print(f"An error occurred: {e}")

# Clean up dummy file
Path("config.yaml").unlink()

```




