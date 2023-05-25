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

from linkml_runtime.utils.schemaview import SchemaView, SlotDefinition
from linkml_validator.models import SeverityEnum, ValidationMessage, ValidationResult
from linkml_validator.plugins.base import BasePlugin

from ghga_validator.linkml.object_iterator import ObjectIterator
from ghga_validator.utils import path_as_string


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

        all_class_ids = self.get_all_class_ids(obj, target_class)
        messages = self.validate_refs(obj, target_class, all_class_ids)

        valid = len(messages) == 0

        result = ValidationResult(
            plugin_name=self.NAME, valid=valid, validation_messages=messages
        )
        return result

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

    def get_all_class_ids(self, obj: Dict, target_class: str) -> Dict[str, List[str]]:
        """Get all lists of identifies of inlined objects organized by class name

        Args:
            obj (Dict): The object to be parsed
            target_class (str): Target class

        Returns:
            Dict[class_name, List[str]]: The dictionary containing the lists of
            identifiers by the class name
        """
        all_ids = {}

        for class_name, identifier, _, _ in ObjectIterator(
            self.schemaview, obj, target_class
        ):
            if class_name not in all_ids:
                all_ids[class_name] = [identifier]
            else:
                all_ids[class_name].append(identifier)

        return all_ids

    def validate_refs(
        self,
        object_to_validate: Dict,
        target_class: str,
        all_class_ids: Dict,
    ) -> List[ValidationMessage]:
        """
        Validate non inlined reference fields in the JSON data

        Args:
            object_to_validate: input data
            target_class: parent class in the schema
            all_class_ids: pre-computed dictionary containing all identifiers ordered by class

        Returns:
            List[ValidationMessage]: List of validation messages

        """
        messages = []

        for class_name, _, data, path in ObjectIterator(
            self.schemaview, object_to_validate, target_class
        ):
            for field, value in data.items():
                slot_def = self.schemaview.induced_slot(field, class_name)
                range_class = self.get_range_class(slot_def)
                if range_class and not self.schemaview.is_inlined(slot_def):
                    non_match = self.find_missing_refs(
                        value, all_class_ids[range_class]
                    )
                    if len(non_match) == 0:
                        continue
                    message = ValidationMessage(
                        severity=SeverityEnum.error,
                        message="Unknown references "
                        + f"({self.non_match_as_string(non_match)})",
                        field=f"{path_as_string(path)}.{field}",
                        value=value,
                    )
                    messages.append(message)
        return messages

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
