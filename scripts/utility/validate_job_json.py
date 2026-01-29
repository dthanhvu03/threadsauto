#!/usr/bin/env python3
"""
Script validate JSON file theo schema.

Usage:
    python scripts/validate_job_json.py <json_file> [--schema schemas/job_schema.json]
"""

import sys
import json
import argparse
from pathlib import Path

# Setup path using common utility
from scripts.common import setup_path

# Add parent directory to path (must be after importing common)
setup_path()


def validate_with_schema(json_data: dict, schema: dict) -> tuple[bool, list[str]]:
    """
    Validate JSON data với schema (simple validation, không dùng jsonschema library).
    
    Args:
        json_data: JSON data để validate
        schema: JSON schema
    
    Returns:
        (is_valid, errors)
    """
    errors = []
    
    # Check required fields
    required = schema.get('required', [])
    for field in required:
        if field not in json_data:
            errors.append(f"Missing required field: {field}")
    
    # Check properties
    properties = schema.get('properties', {})
    for field, value in json_data.items():
        if field not in properties:
            if not schema.get('additionalProperties', True):
                errors.append(f"Unknown field: {field}")
            continue
        
        prop_schema = properties[field]
        prop_type = prop_schema.get('type')
        
        # Handle union types (e.g., ["string", "null"])
        if isinstance(prop_type, list):
            if not any(_validate_type(value, t) for t in prop_type):
                errors.append(f"Field '{field}' has invalid type. Expected {prop_type}, got {type(value).__name__}")
        elif prop_type:
            if not _validate_type(value, prop_type):
                errors.append(f"Field '{field}' has invalid type. Expected {prop_type}, got {type(value).__name__}")
        
        # Check enum
        if 'enum' in prop_schema:
            if value not in prop_schema['enum']:
                errors.append(f"Field '{field}' has invalid value. Expected one of {prop_schema['enum']}, got {value}")
        
        # Check min/max length
        if prop_type == 'string':
            if 'minLength' in prop_schema and len(value) < prop_schema['minLength']:
                errors.append(f"Field '{field}' too short. Minimum {prop_schema['minLength']} chars, got {len(value)}")
            if 'maxLength' in prop_schema and len(value) > prop_schema['maxLength']:
                errors.append(f"Field '{field}' too long. Maximum {prop_schema['maxLength']} chars, got {len(value)}")
        
        # Check min/max value
        if prop_type == 'integer':
            if 'minimum' in prop_schema and value < prop_schema['minimum']:
                errors.append(f"Field '{field}' too small. Minimum {prop_schema['minimum']}, got {value}")
            if 'maximum' in prop_schema and value > prop_schema['maximum']:
                errors.append(f"Field '{field}' too large. Maximum {prop_schema['maximum']}, got {value}")
        
        # Check pattern (simple regex check)
        if 'pattern' in prop_schema:
            import re
            if not re.match(prop_schema['pattern'], str(value)):
                errors.append(f"Field '{field}' doesn't match pattern: {prop_schema['pattern']}")
    
    return len(errors) == 0, errors


def _validate_type(value: any, expected_type: str) -> bool:
    """Check if value matches expected type."""
    type_map = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'object': dict,
        'array': list,
        'null': type(None)
    }
    
    if expected_type == 'null':
        return value is None
    
    expected_python_type = type_map.get(expected_type)
    if expected_python_type is None:
        return True  # Unknown type, skip
    
    if isinstance(expected_python_type, tuple):
        return isinstance(value, expected_python_type)
    return isinstance(value, expected_python_type)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Validate JSON file theo schema"
    )
    parser.add_argument(
        'json_file',
        type=Path,
        help='JSON file để validate'
    )
    parser.add_argument(
        '--schema',
        type=Path,
        default=Path(__file__).parent.parent / 'schemas' / 'job_schema.json',
        help='Schema file (default: schemas/job_schema.json)'
    )
    
    args = parser.parse_args()
    
    # Load schema
    try:
        with open(args.schema, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except FileNotFoundError:
        print(f"❌ Schema file không tồn tại: {args.schema}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Schema file không hợp lệ: {e}")
        sys.exit(1)
    
    # Load JSON file
    try:
        with open(args.json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ JSON file không tồn tại: {args.json_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON file không hợp lệ: {e}")
        sys.exit(1)
    
    # Validate
    if isinstance(json_data, list):
        # Batch validation
        print(f"📋 Validating {len(json_data)} jobs...")
        all_valid = True
        for i, job in enumerate(json_data):
            is_valid, errors = validate_with_schema(job, schema)
            if not is_valid:
                all_valid = False
                print(f"\n❌ Job {i+1} có lỗi:")
                for error in errors:
                    print(f"   - {error}")
            else:
                print(f"✅ Job {i+1} hợp lệ")
        
        if all_valid:
            print(f"\n✅ Tất cả {len(json_data)} jobs đều hợp lệ!")
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        # Single job validation
        is_valid, errors = validate_with_schema(json_data, schema)
        
        if is_valid:
            print("✅ JSON file hợp lệ!")
            sys.exit(0)
        else:
            print("❌ JSON file có lỗi:")
            for error in errors:
                print(f"   - {error}")
            sys.exit(1)


if __name__ == "__main__":
    main()

