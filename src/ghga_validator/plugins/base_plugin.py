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

"""Base Class for Validation Plugins"""

from abc import ABC, abstractmethod

from ghga_validator.core.models import ValidationResult


class ValidationPlugin(ABC):
    """An abstract class for validation plugins"""

    def __init__(self, schema):
        """
        Initialize the plugin with the given schema.

        Args:
            schema: schema representation

        """
        self.schema = schema

    @abstractmethod
    def validate(self, data, target_class) -> ValidationResult:
        """Validate input data against the schema starting with the target class"""
