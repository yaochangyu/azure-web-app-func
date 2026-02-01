#!/usr/bin/env python3
"""
Azure Resource Naming Validation Script

Validates Azure resource names against Microsoft Cloud Adoption Framework (CAF) standards.
Checks for naming convention compliance, constraint violations, and consistency.

Usage:
    python validate_naming.py --resource-group mygroup --check-all
    python validate_naming.py --resource-group mygroup --report violations.json
    python validate_naming.py --resource-group mygroup --type webapp
"""

import json
import re
import sys
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class ResourceNamingRule:
    """Definition of naming rules for a resource type."""
    resource_type: str
    abbreviation: str
    min_length: int
    max_length: int
    allowed_chars: str
    globally_unique: bool
    description: str
    example: str


# Microsoft CAF Resource Naming Rules
NAMING_RULES = {
    'Microsoft.Storage/storageAccounts': ResourceNamingRule(
        resource_type='Storage Account',
        abbreviation='st',
        min_length=3,
        max_length=24,
        allowed_chars='lowercase letters and numbers only',
        globally_unique=True,
        description='No hyphens allowed. Must be 3-24 chars, all lowercase/numbers.',
        example='stmyappprod001'
    ),
    'Microsoft.Web/sites': ResourceNamingRule(
        resource_type='Web App / Function App',
        abbreviation='app/func',
        min_length=1,
        max_length=60,
        allowed_chars='letters, numbers, hyphens',
        globally_unique=True,
        description='Becomes public DNS name. Example: myapp.azurewebsites.net',
        example='app-myapp-prod'
    ),
    'Microsoft.Web/serverfarms': ResourceNamingRule(
        resource_type='App Service Plan',
        abbreviation='asp/plan',
        min_length=1,
        max_length=40,
        allowed_chars='letters, numbers, hyphens',
        globally_unique=False,
        description='Unique within resource group.',
        example='asp-myapp-prod'
    ),
    'Microsoft.Sql/servers': ResourceNamingRule(
        resource_type='SQL Server',
        abbreviation='sql',
        min_length=1,
        max_length=63,
        allowed_chars='lowercase letters, numbers, hyphens',
        globally_unique=True,
        description='Becomes public DNS name. Must be lowercase.',
        example='sql-myapp-prod'
    ),
    'Microsoft.Sql/servers/databases': ResourceNamingRule(
        resource_type='SQL Database',
        abbreviation='sqldb',
        min_length=1,
        max_length=128,
        allowed_chars='letters, numbers, hyphens, underscores',
        globally_unique=False,
        description='Unique within server.',
        example='sqldb-myapp-prod'
    ),
    'Microsoft.DocumentDB/databaseAccounts': ResourceNamingRule(
        resource_type='Cosmos DB',
        abbreviation='cosmos',
        min_length=3,
        max_length=44,
        allowed_chars='lowercase letters, numbers, hyphens',
        globally_unique=True,
        description='Becomes public DNS name.',
        example='cosmos-myapp-prod'
    ),
    'Microsoft.KeyVault/vaults': ResourceNamingRule(
        resource_type='Key Vault',
        abbreviation='kv',
        min_length=3,
        max_length=24,
        allowed_chars='letters, numbers, hyphens',
        globally_unique=False,
        description='Unique within resource group.',
        example='kv-myapp-prod'
    ),
    'Microsoft.Insights/components': ResourceNamingRule(
        resource_type='Application Insights',
        abbreviation='appi',
        min_length=1,
        max_length=260,
        allowed_chars='letters, numbers, hyphens, underscores, periods, parentheses',
        globally_unique=False,
        description='Unique within resource group.',
        example='appi-myapp-prod'
    ),
    'Microsoft.Network/virtualNetworks': ResourceNamingRule(
        resource_type='Virtual Network',
        abbreviation='vnet',
        min_length=2,
        max_length=64,
        allowed_chars='letters, numbers, hyphens, underscores, periods',
        globally_unique=False,
        description='Unique within resource group.',
        example='vnet-myapp-prod'
    ),
    'Microsoft.Network/networkSecurityGroups': ResourceNamingRule(
        resource_type='Network Security Group',
        abbreviation='nsg',
        min_length=1,
        max_length=80,
        allowed_chars='letters, numbers, hyphens, underscores, periods',
        globally_unique=False,
        description='Unique within resource group.',
        example='nsg-myapp-web-prod'
    ),
    'Microsoft.Cache/redis': ResourceNamingRule(
        resource_type='Azure Cache for Redis',
        abbreviation='redis',
        min_length=1,
        max_length=63,
        allowed_chars='lowercase letters, numbers, hyphens',
        globally_unique=True,
        description='Must be lowercase.',
        example='redis-myapp-prod'
    ),
}

# Environment standards
VALID_ENVIRONMENTS = ['dev', 'test', 'stg', 'prod', 'sandbox', 'demo', 'dr']

# Common abbreviations
COMMON_ABBREVIATIONS = {
    'asp': 'App Service Plan',
    'plan': 'App Service Plan',
    'app': 'App Service / Web App',
    'func': 'Function App',
    'st': 'Storage Account',
    'sqldb': 'SQL Database',
    'sql': 'SQL Server',
    'cosmos': 'Cosmos DB',
    'kv': 'Key Vault',
    'appi': 'Application Insights',
    'vnet': 'Virtual Network',
    'nsg': 'Network Security Group',
    'rg': 'Resource Group',
    'redis': 'Azure Cache for Redis',
}


@dataclass
class ValidationError:
    """Represents a naming validation error."""
    resource_name: str
    resource_type: str
    severity: str  # 'error' or 'warning'
    issue: str
    fix: str


class NamingValidator:
    """Validates Azure resource naming conventions."""

    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def validate_name(self, resource_name: str, resource_type: str) -> Tuple[bool, List[str]]:
        """
        Validate a single resource name.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Get naming rules for this resource type
        if resource_type not in NAMING_RULES:
            issues.append(f"Unknown resource type: {resource_type}")
            return False, issues

        rule = NAMING_RULES[resource_type]

        # Check length
        if len(resource_name) < rule.min_length:
            issues.append(f"Name too short (min {rule.min_length} chars): '{resource_name}'")
        elif len(resource_name) > rule.max_length:
            issues.append(f"Name too long (max {rule.max_length} chars): '{resource_name}'")

        # Check allowed characters
        if self._has_invalid_characters(resource_name, rule):
            issues.append(f"Contains invalid characters. Allowed: {rule.allowed_chars}")

        # Check naming pattern
        pattern_issues = self._check_naming_pattern(resource_name)
        issues.extend(pattern_issues)

        return len(issues) == 0, issues

    def _has_invalid_characters(self, name: str, rule: ResourceNamingRule) -> bool:
        """Check if name contains invalid characters based on rule."""
        if 'lowercase' in rule.allowed_chars and 'letters and numbers only' in rule.allowed_chars:
            # Storage account: only lowercase and numbers
            return not re.match(r'^[a-z0-9]+$', name)
        elif 'lowercase' in rule.allowed_chars:
            # Must be lowercase: letters, numbers, hyphens
            return not re.match(r'^[a-z0-9-]+$', name)
        # Default: allow more characters
        return False

    def _check_naming_pattern(self, name: str) -> List[str]:
        """Check if name follows standard CAF pattern."""
        issues = []

        # Check for common issues
        if '_' in name and 'nsg' not in name and 'kv' not in name:
            issues.append("Underscores discouraged. Use hyphens instead.")

        if name != name.lower() and not any(c.isdigit() for c in name):
            issues.append("Should be lowercase (except storage accounts and SQL servers).")

        # Check if pattern looks reasonable (e.g., has hyphens for separation)
        parts = name.split('-')
        if len(parts) < 2:
            issues.append("Name appears too simple. Consider pattern: type-org-workload-env")

        # Check for common mistakes
        if 'production' in name.lower():
            issues.append("Use 'prod' abbreviation instead of 'production'")
        if 'development' in name.lower():
            issues.append("Use 'dev' abbreviation instead of 'development'")

        return issues

    def validate_resource_group(self, resources: List[Dict]) -> Dict[str, any]:
        """Validate naming consistency across a resource group."""
        summary = {
            'total_resources': len(resources),
            'valid': 0,
            'invalid': 0,
            'warnings': 0,
            'errors': []
        }

        for resource in resources:
            name = resource.get('name', '')
            resource_type = resource.get('type', '')

            is_valid, issues = self.validate_name(name, resource_type)

            if is_valid:
                summary['valid'] += 1
            else:
                summary['invalid'] += 1
                summary['errors'].append({
                    'name': name,
                    'type': resource_type,
                    'issues': issues
                })

        return summary

    def generate_report(self) -> Dict:
        """Generate comprehensive validation report."""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'errors': [asdict(e) for e in self.errors],
            'warnings': [asdict(w) for w in self.warnings],
        }


def get_azure_resources(resource_group: str, resource_type: Optional[str] = None) -> List[Dict]:
    """Fetch Azure resources from resource group."""
    try:
        cmd = ['az', 'resource', 'list', '--resource-group', resource_group, '--output', 'json']
        
        if resource_type:
            cmd.extend(['--resource-type', resource_type])

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"Error fetching resources: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Validate Azure resource naming against CAF standards'
    )
    parser.add_argument('--resource-group', '-g', required=True,
                       help='Azure resource group name')
    parser.add_argument('--type', '-t', type=str,
                       help='Filter by resource type (e.g., Microsoft.Storage/storageAccounts)')
    parser.add_argument('--check-all', action='store_true',
                       help='Check all resources')
    parser.add_argument('--report', '-r', type=str,
                       help='Output report to JSON file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    print(f"Validating resources in resource group: {args.resource_group}")

    # Fetch resources
    resources = get_azure_resources(args.resource_group, args.type)
    print(f"Found {len(resources)} resources\n")

    # Validate
    validator = NamingValidator()
    summary = validator.validate_resource_group(resources)

    # Print results
    print(f"Validation Summary:")
    print(f"  Total Resources: {summary['total_resources']}")
    print(f"  Valid: {summary['valid']}")
    print(f"  Invalid: {summary['invalid']}")
    print()

    if summary['errors']:
        print("Issues Found:")
        for error in summary['errors']:
            print(f"\n  ❌ {error['name']} ({error['type']})")
            for issue in error['issues']:
                print(f"     - {issue}")

    # Generate report if requested
    if args.report:
        report = {
            'timestamp': datetime.now().isoformat(),
            'resource_group': args.resource_group,
            'summary': summary,
        }
        with open(args.report, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to {args.report}")

    # Exit with appropriate code
    sys.exit(0 if summary['invalid'] == 0 else 1)


if __name__ == '__main__':
    main()
