
import yaml

try:
    from yaml import CLoader as YAML_Loader
except ImportError:
    from yaml import Loader as YAML_Loader

def load(file_path):
    with open(file_path, 'r') as f:
        return yaml.load(f, Loader = YAML_Loader)
