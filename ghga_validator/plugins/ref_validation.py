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

"""Plugin for LinkML JSON Validator used for validating the non inline references"""

from typing import Dict, List, Optional, Union

from linkml_runtime.utils.schemaview import ClassDefinition, SchemaView, SlotDefinition
from linkml_validator.models import SeverityEnum, ValidationMessage, ValidationResult
from linkml_validator.plugins.base import BasePlugin

from ghga_validator.utils import merge_dicts_of_list, to_list


# pylint: disable=too-many-locals
class RefValidationPlugin(BasePlugin):
    """
    Plugin to check whether the values in non inline reference fields point
    to existing objects.

    Args:
        schema: Path or URL to schema YAML
        kwargs: Additional arguments that are used to instantiate the plugin

    """

    NAME = "RefValidationPlugin"

    def __init__(self, schema: str) -> None:
        super().__init__(schema)
        self.schemaview = SchemaView(schema)

    def process(self, obj: Dict, **kwargs) -> ValidationResult:
        """
        Perform validation on an object.

        Args:
            obj: The object to validate
            kwargs: Additional arguments that are used for processing

        Returns:
            ValidationResult: A validation result that describes the outcome of validation

        """
        if "target_class" not in kwargs:
            raise TypeError("'target_class' argument is required")
        target_class = kwargs["target_class"]
        messages = []

        inlined_ids = self.get_inlined_ids(obj, target_class)

        messages = self.validate_json(obj, target_class, "", inlined_ids)

        valid = len(messages) == 0

        result = ValidationResult(
            plugin_name=self.NAME, valid=valid, validation_messages=messages
        )
        return result

    def get_class_def(self, class_name) -> ClassDefinition:
        """
        Get class definition.

        Args:
            class_name: class name

        Returns:
            ClassDefinition: class definition

        """
        return self.schemaview.get_class(class_name)

    def get_slot_def(self, class_name: str, slot_name: str) -> SlotDefinition:
        """
        Get slot definition inside a class.

        Args:
            class_name: name of the class which contains the slot
            slot_name: slot name

        Returns:
            SlotDefinition: slot definition

        """
        class_def = self.get_class_def(class_name)
        slot_usage = class_def.slot_usage
        if slot_name in slot_usage:
            return slot_usage[slot_name]
        return self.schemaview.get_slot(slot_name)

    def find_missing_refs(
        self, ref_value: Union[List[str], str], id_list: List
    ) -> List:
        """
        Search for missing references

        Returns:
            List: List of missing references
        """
        if not isinstance(ref_value, list):
            value_to_check = [ref_value]
        else:
            value_to_check = ref_value
        non_match = []
        if not all(x in id_list for x in value_to_check):
            non_match = [x for x in value_to_check if x not in id_list]
        return non_match

    def non_match_as_string(self, non_match: List[str]) -> str:
        """
        Generate a validation error message for missing references

        Returns:
            str: The validation error message
        """
        if len(non_match) > 1:
            non_match_as_string = (
                "'" + "', '".join(str(x) for x in non_match) + "'" + " were unexpected"
            )
        else:
            non_match_as_string = "'" + non_match[0] + "'" + " was unexpected"
        return non_match_as_string

    def get_range_class(self, slot_def: SlotDefinition) -> Optional[str]:
        """Return the range class for a slot

        Args:
            slot_def (SlotDefinition): Slot Definition

        Returns:
            Optional[str]: Range class for a slot
        """
        all_classes_name = self.schemaview.all_classes().keys()
        if slot_def:
            range_class = slot_def.range
            if range_class in all_classes_name:
                return range_class
        return None

    def validate_json(
        self,
        object_to_validate: Dict,
        target_class: str,
        path: str,
        inlined_ids: Dict,
    ) -> List[ValidationMessage]:
        """
        Get slot definition.

        Args:
            slot_name: slot name

        Returns:
            SlotDefinition: class definition

        """
        messages = []

        for field, value in object_to_validate.items():
            slot_def = self.get_slot_def(target_class, field)
            range_class = self.get_range_class(slot_def)
            if not range_class:
                continue
            if self.schemaview.is_inlined(slot_def):
                index = 0
                if not isinstance(value, list):
                    new_path = path + field + "."
                else:
                    new_path = path + field + ".0"
                for elem in to_list(value):
                    validation_msgs = self.validate_json(
                        elem,
                        range_class,
                        new_path,
                        inlined_ids,
                    )
                    if len(validation_msgs) > 0:
                        messages.extend(validation_msgs)
                    index = index + 1
                    new_path = path + field + "." + str(index)
            else:
                if range_class in inlined_ids:
                    id_list = inlined_ids[range_class]
                else:
                    id_list = []
                non_match = self.find_missing_refs(value, id_list)
                if len(non_match) == 0:
                    continue
                message = ValidationMessage(
                    severity=SeverityEnum.error,
                    message="Unknown references "
                    + f"({self.non_match_as_string(non_match)})",
                    field=f"{path}.{field}",
                    value=value,
                )
                messages.append(message)
        return messages

    def get_inlined_ids(self, obj: Dict, target_class: str) -> Dict[str, List[str]]:
        """Get all lists of identifies of inlined objects organized by class name

        Args:
            obj (Dict): The object to be parsed
            target_class (str): Target class

        Returns:
            Dict[class_name, List[str]]: The dictionary containing the lists of
            identifiers by the class name
        """
        inlined_ids: Dict[str, List[str]] = {}
        for field, value in obj.items():
            slot_def = self.get_slot_def(target_class, field)
            range_class = self.get_range_class(slot_def)
            if not range_class:
                continue
            if self.schemaview.is_inlined(slot_def):
                id_slot = self.schemaview.get_identifier_slot(range_class)
                if isinstance(value, list):
                    if id_slot:
                        id_list = [item[id_slot.name] for item in value]
                    for item in value:
                        inlined_ids = merge_dicts_of_list(
                            inlined_ids, self.get_inlined_ids(item, range_class)
                        )
                else:
                    if id_slot:
                        id_list = [value[id_slot.name]]
                    inlined_ids = merge_dicts_of_list(
                        inlined_ids, self.get_inlined_ids(value, range_class)
                    )
                if range_class not in inlined_ids:
                    inlined_ids[range_class] = id_list
                else:
                    inlined_ids[range_class].extend(id_list)
        return inlined_ids
