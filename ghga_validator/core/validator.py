# Copyright 2021 - 2023 Universität Tübingen, DKFZ, EMBL, and Universität zu Köln
# for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Validator of data against a given LinkML schema."""

from typing import Dict, List, Optional

from linkml_runtime.utils.schemaview import SchemaView

from ghga_validator.core.models import ValidationReport
from ghga_validator.plugins.base import BasePlugin


class Validator:
    """
    Validator of data against a given LinkML schema.

    Args:
        schema: Virtual LinkML schema (SchemaView)
        plugins: List of plugins for validation

    """

    def __init__(self, schema: SchemaView, plugins: Optional[List]) -> None:
        self._schema = schema
        self.load_plugins(plugins)

    def validate(self, obj: Dict, target_class: str, **kwargs) -> ValidationReport:
        """
        Validate an object.

        Args:
            obj: The object to validate
            target_class: The type of object
            kwargs: Any additional arguments

        Returns:
            ValidationReport: A validation report that summarizes the validation

        """
        validation_results = []
        valid = True
        for plugin in self._plugins:
            validation_result = plugin.process(
                obj=obj, target_class=target_class, **kwargs
            )
            validation_results.append(validation_result)
            if not validation_result.valid:
                valid = False
        if "exclude_object" in kwargs and kwargs["exclude_object"]:
            object_for_report = None
        else:
            object_for_report = obj
        validation_report = ValidationReport(
            object=object_for_report,
            type=target_class,
            valid=valid,
            validation_results=validation_results,
        )
        return validation_report

    def load_plugins(self, plugins: Optional[List]):
        """
        Load plugins for validation

        Args:
            plugins: The list of plugins to be loaded
        """
        self._plugins = []
        if plugins:
            for plugin in plugins:
                plugin_class = plugin["plugin_class"]
                plugin_args = {}
                if "args" in plugin:
                    plugin_args = plugin["args"]
                if not issubclass(plugin_class, BasePlugin):
                    raise TypeError(f"{plugin_class} must inherit from {BasePlugin}")
                instance = plugin_class(schema=self._schema, **plugin_args)
                self._plugins.append(instance)
