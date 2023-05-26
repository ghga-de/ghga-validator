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

"""Utils"""

from typing import Dict, List, Union


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


def path_as_string(error_path: List) -> str:
    """Convert the path to the error in JSON to string format
    Args:
        error_path (List): path to the error in JSON
    Returns:
        str: string representation of the error path
    """
    path_str = ".".join(str(elem) for elem in error_path)
    return path_str
