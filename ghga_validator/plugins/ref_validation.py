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

from typing import Any, Dict, List, Optional, Union

from linkml_runtime.utils.schemaview import ClassDefinition, SchemaView, SlotDefinition
from linkml_validator.models import ValidationMessage, ValidationResult
from linkml_validator.plugins.base import BasePlugin
from linkml_validator.utils import camelcase_to_sentencecase, snakecase_to_sentencecase

# pylint: disable=too-many-arguments,too-many-locals


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
        valid = True

        messages = self.validate_json(obj, target_class, obj, target_class, "")
        if len(messages) > 0:
            valid = False

        result = ValidationResult(
            plugin_name=self.NAME, valid=valid, validation_messages=messages
        )
        return result

    def get_id_list(
        self, obj: Dict, root: str, class_name: str, id_slot_name: str
    ) -> List[str]:
        """
        Get the list of all identifiers for the inlined objects

        Args:
            obj: The object to validate
            root: The root class name
            class_name: The name of the class used in range
            id_slot_name: The identifier slot in the range class

        Returns:
            List[str]: A list of all identifiers for the inlined objects

        """
        id_list = []
        for field, value in obj.items():
            slot_def = self.get_slot_def(root, field)
            if slot_def:
                range_class = slot_def.range
                if range_class != class_name:
                    continue
                if isinstance(value, list):
                    id_list = [x[id_slot_name] for x in value]
                else:
                    id_list = [value[id_slot_name]]
        return id_list

    def get_class_def(self, class_name) -> ClassDefinition:
        """
        Get class definition.

        Args:
            class_name: class name

        Returns:
            ClassDefinition: class definition

        """
        formatted_class_name = camelcase_to_sentencecase(class_name)
        return self.schemaview.get_class(formatted_class_name)

    def get_slot_def(self, class_name: str, slot_name: str) -> SlotDefinition:
        """
        Get slot definition.

        Args:
            slot_name: slot name

        Returns:
            SlotDefinition: class definition

        """
        formatted_slot_name = snakecase_to_sentencecase(slot_name)
        class_def = self.get_class_def(class_name)
        slot_usage = class_def.slot_usage
        if formatted_slot_name in slot_usage:
            return slot_usage[formatted_slot_name]
        return self.schemaview.get_slot(formatted_slot_name)

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

    def to_list(self, value: Any) -> List[Dict]:
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

    def validate_json(
        self,
        object_to_validate: Dict,
        target_class: str,
        json_object: Dict,
        root_class: str,
        path: str,
    ) -> ValidationMessage:
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
                for elem in self.to_list(value):
                    validation_msgs = self.validate_json(
                        elem,
                        range_class,
                        json_object,
                        root_class,
                        path + "->" + field,
                    )
                    if len(validation_msgs) > 0:
                        messages.extend(validation_msgs)
            else:
                id_slot = self.schemaview.get_identifier_slot(range_class)
                id_list = self.get_id_list(
                    json_object, target_class, range_class, id_slot.name
                )
                non_match = self.find_missing_refs(value, id_list)
                if len(non_match) == 0:
                    continue
                message = ValidationMessage(
                    severity="Error",
                    message="Unknown references in "
                    + f"{path}->{field} ({self.non_match_as_string(non_match)})",
                    field=id_slot.name,
                    value=str(value),
                )
                messages.append(message)
        return messages
