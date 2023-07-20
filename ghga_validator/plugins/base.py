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

"""Plugin Core Class"""

from abc import ABC, abstractmethod
from typing import Dict

from ghga_validator.core.models import ValidationResult


class BasePlugin(ABC):
    """
    Plugin Core Class

    Args:
        schema: Virtual LinkML schema (SchemaView)
        kwargs: Additional arguments that are used to instantiate the plugin

    """

    NAME = "BasePlugin"

    def __init__(self, schema) -> None:
        """
        Initialize the plugin with the given schema YAML.

        Args:
            schema: Virtual LinkML schema (SchemaView)
            kwargs: Additional arguments that are used to instantiate the plugin

        """
        self.schema = schema

    @abstractmethod
    def process(self, obj: Dict, **kwargs) -> ValidationResult:
        """
        Run one or more operations on the given object and return
        the results.

        Args:
            obj: The object to process
            kwargs: Additional arguments that are used for processing

        """
        ...
