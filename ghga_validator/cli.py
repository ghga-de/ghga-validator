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

"""Entrypoint of the package"""

import json
from pathlib import Path

import typer
from linkml_validator.plugins.jsonschema_validation import JsonSchemaValidationPlugin

from ghga_validator.core.utils import validate

from .plugins.ref_validation import RefValidationPlugin

cli = typer.Typer()

VALIDATION_PLUGINS = [
    {"plugin_class": RefValidationPlugin},
    {"plugin_class": JsonSchemaValidationPlugin},
]


def validate_json(file: Path, schema: Path, report: Path) -> bool:
    """
    Validate JSON object against a given schema. Store the errors to the validation report.
    Args:
        file: The URL or path to submission file
        schema: The URL or path to YAML file (submission schema)
        report: The URL or path to store the validation results
    """
    with open(file, "r", encoding="utf8") as json_file:
        submission_json = json.load(json_file)
        if submission_json is None:
            raise EOFError(f"<{file}> is empty! Nothing to validate!")
        validation_report = validate(
            str(Path(schema).resolve()),
            submission_json,
            "Submission",
            plugins=VALIDATION_PLUGINS,
        )
        if not validation_report.valid:
            with open(report, "w", encoding="utf-8") as sub:
                json.dump(
                    validation_report.dict(exclude_unset=True, exclude_none=True),
                    sub,
                    ensure_ascii=False,
                    indent=4,
                )
            return False
    return True


@cli.command()
def main(
    schema: Path = typer.Option(
        ..., help="Path to metadata schema (modelled using LinkML)"
    ),
    inputfile: Path = typer.Option(
        ..., help="Path to submission file in JSON format to be validated"
    ),
    report: Path = typer.Option(..., help="Path to resulting validation report"),
):
    """
    GHGA Validator
    """
    typer.echo("Start validating...")
    if validate_json(inputfile, schema, report):
        typer.echo(f"<{inputfile}> is valid!")
    else:
        typer.echo(
            f"<{inputfile}> is invalid! Look at <{report}> for validation report"
        )
