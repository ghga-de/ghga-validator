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

import importlib
import pkgutil
from typing import Dict, List, Optional

from linkml_runtime.utils.schemaview import SchemaView

import ghga_validator.plugins as plugin_package
from ghga_validator.core.models import ValidationReport
from ghga_validator.plugins.core_plugin import ValidationPlugin


class Validator:
    """
    Validator of data against a given LinkML schema.

    Args:
        schema: Virtual LinkML schema (SchemaView)
        plugins: List of plugins for validation

    """

    def __init__(self, schema: SchemaView, plugins: Optional[List[str]]) -> None:
        self._schema = schema
        self._plugins = self.load_plugins(plugins)

    def validate(self, data: Dict, target_class: str) -> ValidationReport:
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
        for _, plugin in self._plugins.items():
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

    def load_plugins(self, plugins: Optional[List[str]]) -> Dict:
        """
        Load the list of plugins
        """
        if not plugins:
            return {}
        discovered_plugins = {}
        for _, module_name, _ in pkgutil.iter_modules(plugin_package.__path__):
            try:
                module = importlib.import_module(
                    f"{plugin_package.__name__}.{module_name}"
                )
                for name, cls in module.__dict__.items():
                    if (
                        isinstance(cls, type)
                        and issubclass(cls, ValidationPlugin)
                        and cls.__name__ in plugins
                    ):
                        discovered_plugins[name] = cls(schema=self._schema)
            except ImportError as err:
                print(f"Error loading module '{module_name}': {err}")
        return discovered_plugins
