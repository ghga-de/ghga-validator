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

from typing import Dict, List

from linkml_runtime.utils.schemaview import SchemaView
from linkml_validator.models import SeverityEnum, ValidationMessage, ValidationResult
from linkml_validator.plugins.base import BasePlugin

from ghga_validator.schema_utils import get_range_class, get_slot_def
from ghga_validator.utils import to_list


# pylint: disable=too-many-locals
class UniqueValidationPlugin(BasePlugin):
    """
    Plugin to check whether the fields defined as identifier/unique key
    are unique for a class.

    Args:
        schema: Path or URL to schema YAML
        kwargs: Additional arguments that are used to instantiate the plugin

    """

    NAME = "UniqueValidationPlugin"

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

        messages = self.validate_unique_fields(obj, target_class, "")
        valid = len(messages) == 0

        result = ValidationResult(
            plugin_name=self.NAME, valid=valid, validation_messages=messages
        )
        return result

    def validate_unique_fields(
        self,
        object_to_validate: Dict,
        target_class: str,
        path: str,
    ) -> List[ValidationMessage]:
        """
        Validate non inlined reference fields in a JSON object

        Args:
            object_to_validate: input JSON object
            target_class: parent class in the schema
            path: current JSON path to a field (used to compute the validation error path)
            inlined_ids: pre-computed dictionary containing all inlined identifiers

        Returns:
            SlotDefinition: class definition

        """
        messages = []

        for field, value in object_to_validate.items():
            slot_def = get_slot_def(self.schemaview, target_class, field)
            range_class = get_range_class(self.schemaview, slot_def)
            if not range_class:
                continue
            if self.schemaview.is_inlined(slot_def):
                id_slot = self.schemaview.get_identifier_slot(range_class)
                if isinstance(value, list):
                    if id_slot:
                        id_list = [item[id_slot.name] for item in value]
                        non_unique = set(
                            elem for elem in id_list if id_list.count(elem) > 1
                        )
                        for elem in non_unique:
                            filtered_value = [
                                item for item in value if item[id_slot.name] == elem
                            ]
                            message = ValidationMessage(
                                severity=SeverityEnum.error,
                                message="Duplicate value for unique attribute "
                                + f"{range_class}({id_slot.name}): {elem}",
                                field=f"{path}{field}",
                                value=filtered_value,
                            )
                            messages.append(message)
                index = 0
                if not isinstance(value, list):
                    new_path = path + field + "."
                else:
                    new_path = path + field + ".0"
                for elem in to_list(value):
                    validation_msgs = self.validate_unique_fields(
                        elem,
                        range_class,
                        new_path,
                    )
                    if len(validation_msgs) > 0:
                        messages.extend(validation_msgs)
                    index = index + 1
                    new_path = path + field + "." + str(index)
        return messages
