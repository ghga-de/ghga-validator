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

from typing import Optional

from linkml_runtime.utils.schemaview import SchemaView

from ghga_validator.core.models import ValidationReport
from ghga_validator.plugins.core_plugin import ValidationPlugin
from ghga_validator.plugins.utils import discover_plugins


class Validator:
    """
    Validator of data against a given LinkML schema.

    Args:
        schema: Virtual LinkML schema (SchemaView)
        plugins: List of plugins for validation

    """

    def __init__(self, schema: SchemaView, plugins: Optional[list[str]]) -> None:
        self._schema = schema
        self._plugins: list[ValidationPlugin] = []
        if plugins:
            self.load_plugins(plugins)

    def validate(self, data: dict, target_class: str) -> ValidationReport:
        """
        Validate an object.

        Args:
            data: The object to validate
            target_class: The type of object

        Returns:
            ValidationReport: A validation report that summarizes the validation

        """
        validation_results = []
        valid = True
        for plugin in self._plugins:
            validation_result = plugin.validate(data=data, target_class=target_class)
            validation_results.append(validation_result)
            if not validation_result.valid:
                valid = False
        validation_report = ValidationReport(
            object=data,
            type=target_class,
            valid=valid,
            validation_results=validation_results,
        )
        return validation_report

    def load_plugins(self, plugins: list[str]):
        """Load the list of plugins"""
        discovered_plugins = discover_plugins(ValidationPlugin)
        for plugin_name in plugins:
            if plugin_name in discovered_plugins:
                plugin_class = discovered_plugins[plugin_name]
                self._plugins.append(plugin_class(schema=self._schema))
            else:
                raise ModuleNotFoundError(f"Plugin '{plugin_name}' not found")
