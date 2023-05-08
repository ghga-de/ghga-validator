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

from typing import Dict, List, Optional, Union

from linkml.utils.datautils import infer_root_class
from linkml_runtime.utils.schemaview import SchemaView
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
    schema: str, target_class: Optional[str], obj: Dict, plugins: List[Dict]
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
        obj, target_class, exclude_object=True, truncate_message=True
    )
    return report


def get_target_class(schema: str) -> Optional[str]:
    """
    Infer the root class from schema
    Args:
        schema (str): YAML schema as the string

    Returns:
        class name for root class, if found in the scheme
    """
    with open(schema, "r", encoding="utf8") as file:
        input_schema = file.read()
        return infer_root_class(SchemaView(input_schema))


def to_list(value: Union[Dict, List[Dict]]) -> List[Dict]:
    """
    If an value is not an instance of List of objects, transform to it
    """
    list_of_values = []
    if not isinstance(value, list):
        list_of_values = [value]
    else:
        list_of_values = value
    if len(list_of_values) == 0:
        return []
    if not isinstance(list_of_values[0], dict):
        return []
    return list_of_values


def merge_dicts_of_list(
    dict1: Dict[str, List], dict2: Dict[str, List]
) -> Dict[str, List]:
    """Merge two dictionaries which values are lists. Each list in the output dictionary
    is the union of the lists for a key in the source dictionaries

    Args:
        dict1, dict2 (Dict[str, List]): dictionaries to be merged

    Returns:
        Dict[str, List]: Output dictionary
    """
    output_dict = dict1
    for key in dict2:
        if key in output_dict:
            output_dict[key].extend(dict2[key])
        else:
            output_dict[key] = dict2[key]
    return output_dict
