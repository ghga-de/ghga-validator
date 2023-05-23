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

"""Utils for LinkML schema"""

from typing import Optional

from linkml.utils.datautils import infer_root_class
from linkml_runtime.utils.schemaview import ClassDefinition, SchemaView, SlotDefinition


def get_class_def(schema_view, class_name) -> ClassDefinition:
    """
    Get class definition.

    Args:
        schema_view (SchemaView): virtual schema representation
        class_name: class name

    Returns:
        ClassDefinition: class definition

    """
    return schema_view.get_class(class_name)


def get_slot_def(schema_view, class_name: str, slot_name: str) -> SlotDefinition:
    """
    Get slot definition inside a class.

    Args:
        schema_view (SchemaView): virtual schema representation
        class_name: name of the class which contains the slot
        slot_name: slot name

    Returns:
        SlotDefinition: slot definition

    """
    class_def = get_class_def(schema_view, class_name)
    slot_usage = class_def.slot_usage
    if slot_name in slot_usage:
        return slot_usage[slot_name]
    return schema_view.get_slot(slot_name)


def get_range_class(schema_view, slot_def: SlotDefinition) -> Optional[str]:
    """Return the range class for a slot

    Args:
        schema_view (SchemaView): virtual schema representation
        slot_def (SlotDefinition): Slot Definition

    Returns:
        Optional[str]: Range class for a slot
    """
    all_classes_name = schema_view.all_classes().keys()
    if slot_def:
        range_class = slot_def.range
        if range_class in all_classes_name:
            return range_class
    return None


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
