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

            for application_name, application in self.applications.items():
                logger.info(f"Updating functions for {application_name}")
                for function in application["functions"]:
                    for ref in function.layer_refs:
                        layer_name = ref.removesuffix("Arn")
                        if layer_name in self.layers:
                            logger.info(f"Updating function build for {function.name} with layer {layer_name}")
                            copy_tree(
                                f".aws-sam/build/{layer_name}/python",
                                f".aws-sam/build/{application_name}/{function.name}",
                                update=1,
                            )

    def handle_resources(self):
        """
        Populate resources: Applications, Functions, and Layers
        """
        logger.debug("Finding Resources")
        self.applications = {}
        self.functions = []
        self.layers = []
        for resource, resource_values in self.sam_template["Resources"].items():
            resource_type = resource_values["Type"]

            # If this is an Application, we parse the nested template to get the Functions/Layers for the Application
            if resource_type == "AWS::Serverless::Application":
                nested_template_location = resource_values.get("Properties", {}).get("Location")
                if nested_template_location and os.path.exists(nested_template_location):
                    logger.info(f"Found nested template: {nested_template_location}")
                    nested_template = SamTemplate(nested_template_location)
                    self.applications[resource] = {
                        "functions": nested_template.functions,
                    }
                else:
                    logger.warning(f"Nested template {nested_template_location} not found")

            if resource_type == "AWS::Serverless::Function":
                logger.debug(f"Found function {resource}")
                self.functions.append(Function(resource, resource_values))
            elif resource_type == "AWS::Serverless::LayerVersion":
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
        layers = self.properties.get("Layers", [])
        for layer in layers:
            if isinstance(layer, ODict):
                logger.debug(f"Found layer {layer.get('Ref')} for function {self.name}")
                self.layer_refs.append(layer.get("Ref"))
            else:
                logger.debug(f"Found layer {layer} for function {self.name}")
                self.layer_refs.append(layer)


if __name__ == "__main__":
    template_path = Path(os.getcwd()) / "template.yaml"
    template = SamTemplate(template_path)  # this should be the template.yaml in the top level directory
