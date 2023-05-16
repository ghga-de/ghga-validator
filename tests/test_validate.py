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

import os
from pathlib import Path

from ghga_validator import BASE_DIR
from ghga_validator.cli import validate_json
from ghga_validator.core.validation import get_target_class


def test_ref_validation():
    """Test the validation plugin"""
    schema = BASE_DIR / "example_data" / "example_schema.yaml"
    file = BASE_DIR / "example_data" / "example_data.json"
    report = BASE_DIR / "example_data" / "tmp.json"
    target_class = get_target_class(str(Path(schema).resolve()))

    assert validate_json(file, schema, report, str(target_class)) is True

    if os.path.exists(report):
        os.remove(report)