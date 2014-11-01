
import dateutil.tz
import dateutil.parser
import yaml

try:
    from yaml import CLoader as YAML_Loader
except ImportError:
    from yaml import Loader as YAML_Loader

def time_constructor(loader, node):
    return dateutil.parser.parse(node.value)

YAML_Loader.add_constructor( "tag:yaml.org,2002:timestamp",
                             time_constructor )

def load(file_path):
    with open(file_path, 'r') as f:
        return yaml.load(f, Loader = YAML_Loader)
