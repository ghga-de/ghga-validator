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

"""Validation utilities"""

from typing import Dict, List

from linkml_validator.models import ValidationReport
from linkml_validator.validator import Validator


def get_validator(schema: str, plugins: List[Dict]) -> Validator:
    """
    Get an instance of Validator.
    Args:
        schema: The schema YAML
        plugins: A list of plugins to use
    Returns:
        Validator: An instance of Validator
    """
    validator = Validator(schema, plugins=plugins)
    return validator


def validate(
    schema: str, obj: Dict, obj_type: str, plugins: List[Dict]
) -> ValidationReport:
    """
    Validate an object of a particular type against a given schema.
    Args:
        schema: The URL or path to the schema YAML
        obj: The object to validate
        obj_type: The object type (schema type)
    """
    validator = get_validator(schema=schema, plugins=plugins)
    report = validator.validate(
        obj, target_class=obj_type, exclude_object=True, truncate_message=True
    )
    return report
