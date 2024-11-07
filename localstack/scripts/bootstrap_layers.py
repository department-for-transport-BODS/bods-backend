import os
from pathlib import Path
from cfn_tools import load_yaml, ODict
import logging
from sys import stdout
from distutils.dir_util import copy_tree

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
stream_handler = logging.StreamHandler(stdout)
stream_handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
logger.addHandler(stream_handler)


class SamTemplate:
    def __init__(self, file):
        with open(file, "r") as sam_template_file:
            logger.info(f"Parsing template {file}")
            self.sam_template = load_yaml(sam_template_file)
            self.handle_resources()
            for function in self.functions:
                for ref in function.layer_refs:
                    if ref in self.layers:
                        logger.info(
                            f"Updating function build for {function.name} with layer {ref}"
                        )
                        copy_tree(
                            f".aws-sam/build/{ref}/python",
                            f".aws-sam/build/{function.name}",
                            update=1,
                        )

    def handle_resources(self):
        logger.debug("Finding Resources")
        self.functions = []
        self.layers = []
        for resource, resource_values in self.sam_template["Resources"].items():
            if resource_values["Type"] == "AWS::Serverless::Function":
                logger.debug(f"Found function {resource}")
                self.functions.append(Function(resource, resource_values))
            elif resource_values["Type"] == "AWS::Serverless::LayerVersion":
                logger.debug(f"Found layer {resource}")
                self.layers.append(resource)


class Function:
    def __init__(self, name, values):
        self.name = name
        self.values = dict(values)
        self.properties = dict(self.values.get("Properties", {}))
        self.handle_layers()

    def handle_layers(self):
        logger.debug(f"Looking for layers associated with function {self.name}")
        self.layer_refs = []
        layers_construct = self.properties.get("Layers", None)
        list_of_potential_layers = []
        if isinstance(layers_construct, ODict):
            if_values = layers_construct.get("Fn::If", [])
            if len(if_values) > 0:
                potential_layers = if_values[1]
                if potential_layers:
                    list_of_potential_layers = potential_layers[:1]
            else:
                logger.debug(f"No layers found for function {self.name}")
        for layer in list_of_potential_layers:
            if isinstance(layer, ODict):
                logger.debug(f"Found layer {layer.get('Ref')} for function {self.name}")
                self.layer_refs.append(layer.get("Ref"))
            else:
                logger.debug(f"Found layer {layer} for function {self.name}")
                self.layer_refs.append(layer)

if __name__ == "__main__":
    template_path = Path(os.getcwd()) / "template.yaml"
    template = SamTemplate(template_path) # this should be the template.yaml in the top level directory