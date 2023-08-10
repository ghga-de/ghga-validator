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

"""Plugin for validating the back references"""

from collections import defaultdict
from numbers import Number
from typing import Dict, List, Union

from ghga_validator.core.models import ValidationMessage, ValidationResult
from ghga_validator.linkml.object_iterator import ObjectIterator
from ghga_validator.plugins.base import BasePlugin
from ghga_validator.schema_utils import get_range_class
from ghga_validator.utils import path_as_string


# pylint: disable=too-many-locals
class BackRefValidationPlugin(BasePlugin):
    """
    Plugin to check whether the identifier of the objects are references from other objects.

    Args:
        schema: Path or URL to schema YAML
        kwargs: Additional arguments that are used to instantiate the plugin

    """

    NAME = "BackRefValidationPlugin"

    def process(self, obj: Dict, **kwargs) -> ValidationResult:
        """
        Perform validation on an object.

        Args:
            obj: The object to validate
            kwargs: Additional arguments that are used for processing

        Returns:
            ValidationResult: A validation result that describes the outcome of validation

        """
        target_class = kwargs["target_class"]

        all_class_refs = self.get_all_class_refs(obj, target_class)
        messages = self.validate_refs(obj, target_class, all_class_refs)

        valid = len(messages) == 0

        result = ValidationResult(
            plugin_name=self.NAME, valid=valid, validation_messages=messages
        )
        return result

    def get_all_class_refs(self, obj: Dict, target_class: str) -> Dict[str, List[str]]:
        """Get all lists of identifies of inlined objects organized by class name

        Args:
            obj (Dict): The object to be parsed
            target_class (str): Target class

        Returns:
            Dict[class_name, List[str]]: The dictionary containing the lists of
            references by the class name
        """
        all_refs: Dict[str, List[str]] = defaultdict(list)

        for class_name, _, data, _ in ObjectIterator(self.schema, obj, target_class):
            for field, value in data.items():
                slot_def = self.schema.induced_slot(field, class_name)
                range_class = get_range_class(self.schema, slot_def)
                if range_class and not self.schema.is_inlined(slot_def):
                    new_refs = self.find_missing_refs(value, all_refs[range_class])
                    all_refs[range_class].extend(new_refs)
        return all_refs

    def validate_refs(
        self,
        object_to_validate: Dict,
        target_class: str,
        all_class_refs: Dict,
    ) -> List[ValidationMessage]:
        """
        Validate non inlined reference fields in the JSON data

        Args:
            object_to_validate: input data
            target_class: parent class in the schema
            all_class_refs: pre-computed dictionary containing all identifiers ordered by class

        Returns:
            List[ValidationMessage]: List of validation messages

        """
        messages = []

        excluded_from_ref = self.get_excluded_from_ref()

        for class_name, identifier, data, path in ObjectIterator(
            self.schema, object_to_validate, target_class
        ):
            if (
                class_name not in excluded_from_ref
                and identifier not in all_class_refs[class_name]
            ):
                message = ValidationMessage(
                    message="Unused object identifier " + str(identifier),
                    field=f"{path_as_string(path)}",
                    value=data,
                )
                messages.append(message)
        return messages

    def find_missing_refs(
        self,
        ref_value: Union[List[Union[Number, str]], Union[Number, str]],
        id_list: List,
    ) -> List:
        """
        Search for missing references

        Returns:
            List: List of missing references
        """
        if not isinstance(ref_value, list):
            return [ref_value] if ref_value not in id_list else []
        return [x for x in ref_value if x not in id_list]

    def get_excluded_from_ref(
        self,
    ) -> List:
        """
        Search for classes which are not referenced from other classes in schema
        or should ignored during reference validation

        Returns:
            List: List of class names
        """
        ref_classes = []
        excluded_from_ref = []
        all_classes = self.schema.all_classes()
        for class_name, class_def in all_classes.items():
            slots = class_def.slots
            for slot_name in slots:
                slot_def = self.schema.induced_slot(slot_name, class_name)
                range_class = get_range_class(self.schema, slot_def)
                if range_class and not self.schema.is_inlined(slot_def):
                    ref_classes.append(range_class)
            if "exclude_from_ref" in class_def.in_subset:
                excluded_from_ref.append(class_name)

        return [
            x
            for x in all_classes.keys()
            if x not in ref_classes or x in excluded_from_ref
        ]
