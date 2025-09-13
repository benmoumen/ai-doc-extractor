# Dynamic Schema Storage

This directory contains user-created document schemas in JSON format.

## File Naming Convention
Format: `{schema_id}_v{version}.json`

## Examples
- `custom_national_id_v1.0.0.json` - Custom national ID schema, version 1.0.0
- `custom_passport_v2.1.0.json` - Custom passport schema, version 2.1.0
- `business_license_v1.0.0.json` - Business license schema, version 1.0.0

## Schema Structure
Each JSON file contains:
- Schema metadata (id, name, description, category, version)
- Field definitions with validation rules
- Cross-field validation rules
- Versioning information

This directory is managed by the Schema Management UI Extension.