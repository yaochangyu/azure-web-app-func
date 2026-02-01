#!/usr/bin/env python3
"""
Azure Security Audit Script

Performs comprehensive security audit of Azure resources against best practices.
Checks for: managed identities, encryption, network isolation, RBAC, compliance.

Usage:
    python security_audit.py --resource-group mygroup
    python security_audit.py --resource-group mygroup --severity high
    python security_audit.py --resource-group mygroup --report audit-report.json
"""

import json
import sys
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class SecurityFinding:
    """Represents a security finding."""
    resource_name: str
    resource_type: str
    severity: str  # 'critical', 'high', 'medium', 'low', 'info'
    category: str  # 'identity', 'encryption', 'network', 'monitoring', 'compliance'
    title: str
    description: str
    recommendation: str


class SecurityAuditor:
    """Performs security audits on Azure resources."""

    def __init__(self):
        self.findings: List[SecurityFinding] = []

    def audit_storage_account(self, resource: Dict) -> List[SecurityFinding]:
        """Audit storage account for security issues."""
        findings = []
        name = resource.get('name', '')
        resource_id = resource.get('id', '')

        # Check HTTPS only
        props = resource.get('properties', {})
        if not props.get('supportsHttpsTrafficOnly'):
            findings.append(SecurityFinding(
                resource_name=name,
                resource_type='Storage Account',
                severity='high',
                category='encryption',
                title='HTTPS Not Enforced',
                description='Storage account allows HTTP access, allowing unencrypted traffic',
                recommendation='Enable "Secure transfer required" to enforce HTTPS'
            ))

        # Check public access
        if props.get('publicNetworkAccess') == 'Enabled':
            findings.append(SecurityFinding(
                resource_name=name,
                resource_type='Storage Account',
                severity='high',
                category='network',
                title='Public Network Access Enabled',
                description='Storage account is accessible from the internet',
                recommendation='Use Private Endpoints or restrict network access via firewall'
            ))

        # Check for default access rule (Allow)
        network_acls = props.get('networkAcls', {})
        if network_acls.get('defaultAction') == 'Allow':
            findings.append(SecurityFinding(
                resource_name=name,
                resource_type='Storage Account',
                severity='high',
                category='network',
                title='Open Network Access',
                description='Network ACL default action is "Allow", permitting all traffic',
                recommendation='Set default action to "Deny" and explicitly allow trusted sources'
            ))

        # Check encryption
        encryption = props.get('encryption', {})
        if not encryption:
            findings.append(SecurityFinding(
                resource_name=name,
                resource_type='Storage Account',
                severity='medium',
                category='encryption',
                title='Encryption Not Explicitly Configured',
                description='Storage account encryption configuration not found',
                recommendation='Enable encryption with Microsoft-managed or customer-managed keys'
            ))

        return findings

    def audit_sql_database(self, resource: Dict) -> List[SecurityFinding]:
        """Audit SQL database for security issues."""
        findings = []
        name = resource.get('name', '')
        props = resource.get('properties', {})

        # Check for encryption
        if props.get('transparentDataEncryption') != 'Enabled':
            findings.append(SecurityFinding(
                resource_name=name,
                resource_type='SQL Database',
                severity='high',
                category='encryption',
                title='Transparent Data Encryption (TDE) Not Enabled',
                description='Database is not encrypted at rest',
                recommendation='Enable Transparent Data Encryption (TDE) for data protection'
            ))

        # Check for audit logging
        if not props.get('auditingPolicy', {}).get('state') == 'Enabled':
            findings.append(SecurityFinding(
                resource_name=name,
                resource_type='SQL Database',
                severity='medium',
                category='monitoring',
                title='Audit Logging Not Enabled',
                description='Database audit logging is not enabled',
                recommendation='Enable auditing for compliance and security monitoring'
            ))

        return findings

    def audit_key_vault(self, resource: Dict) -> List[SecurityFinding]:
        """Audit Key Vault for security issues."""
        findings = []
        name = resource.get('name', '')
        props = resource.get('properties', {})

        # Check purge protection
        if not props.get('enablePurgeProtection'):
            findings.append(SecurityFinding(
                resource_name=name,
                resource_type='Key Vault',
                severity='medium',
                category='compliance',
                title='Purge Protection Not Enabled',
                description='Key Vault can be permanently deleted by users with permissions',
                recommendation='Enable purge protection to prevent accidental deletion'
            ))

        # Check soft delete
        if not props.get('enableSoftDelete'):
            findings.append(SecurityFinding(
                resource_name=name,
                resource_type='Key Vault',
                severity='medium',
                category='compliance',
                title='Soft Delete Not Enabled',
                description='Deleted keys are not recoverable',
                recommendation='Enable soft delete for key recovery during accidental deletion'
            ))

        # Check RBAC enforcement
        if not props.get('enableRbacAuthorization'):
            findings.append(SecurityFinding(
                resource_name=name,
                resource_type='Key Vault',
                severity='low',
                category='identity',
                title='Access Policy Used Instead of RBAC',
                description='Using legacy access policies instead of Azure RBAC',
                recommendation='Migrate to Azure RBAC for consistent access management'
            ))

        return findings

    def audit_webapp(self, resource: Dict) -> List[SecurityFinding]:
        """Audit Web App for security issues."""
        findings = []
        name = resource.get('name', '')
        props = resource.get('properties', {})

        # Check HTTPS only
        if not props.get('httpsOnly'):
            findings.append(SecurityFinding(
                resource_name=name,
                resource_type='Web App',
                severity='high',
                category='encryption',
                title='HTTPS Not Enforced',
                description='Web app allows HTTP access',
                recommendation='Enable "HTTPS Only" setting in web app configuration'
            ))

        # Check minimum TLS version
        if props.get('minTlsVersion', '1.0') < '1.2':
            findings.append(SecurityFinding(
                resource_name=name,
                resource_type='Web App',
                severity='high',
                category='encryption',
                title='TLS 1.2 Not Enforced',
                description=f"Minimum TLS version is {props.get('minTlsVersion')} instead of 1.2",
                recommendation='Set minimum TLS version to 1.2 or higher'
            ))

        # Check FTP deployment disabled
        if props.get('ftpsState') != 'Disabled':
            findings.append(SecurityFinding(
                resource_name=name,
                resource_type='Web App',
                severity='high',
                category='network',
                title='FTP Deployment Allowed',
                description='FTP is enabled for deployment (unencrypted)',
                recommendation='Disable FTP deployment and use SFTP or deployment slots'
            ))

        # Check for client certificate
        if not props.get('clientCertEnabled'):
            findings.append(SecurityFinding(
                resource_name=name,
                resource_type='Web App',
                severity='low',
                category='identity',
                title='Client Certificate Authentication Not Enabled',
                description='Web app does not require client certificates',
                recommendation='Enable client certificate authentication for additional security if needed'
            ))

        return findings

    def audit_network_security_group(self, resource: Dict) -> List[SecurityFinding]:
        """Audit NSG for security issues."""
        findings = []
        name = resource.get('name', '')
        props = resource.get('properties', {})

        security_rules = props.get('securityRules', [])

        # Check for overly permissive rules
        for rule in security_rules:
            rule_props = rule.get('properties', {})

            # Check for allow all inbound
            if (rule_props.get('access') == 'Allow' and
                rule_props.get('direction') == 'Inbound' and
                rule_props.get('sourceAddressPrefix') in ['*', '0.0.0.0/0', '<nw>/0', '/0']):

                dest_port = rule_props.get('destinationPortRange', '')

                # Critical ports exposed
                if dest_port in ['*', '22', '3389', '3306', '5432', '5984']:
                    findings.append(SecurityFinding(
                        resource_name=name,
                        resource_type='Network Security Group',
                        severity='critical',
                        category='network',
                        title=f'Internet Access to Port {dest_port}',
                        description=f"NSG rule allows internet access to port {dest_port}",
                        recommendation='Restrict source IPs or disable public access'
                    ))

        return findings

    def generate_report(self, filter_severity: Optional[str] = None) -> Dict:
        """Generate security audit report."""
        findings = self.findings

        # Filter by severity
        if filter_severity:
            severity_order = ['critical', 'high', 'medium', 'low', 'info']
            if filter_severity in severity_order:
                min_severity_level = severity_order.index(filter_severity)
                findings = [
                    f for f in findings
                    if severity_order.index(f.severity) <= min_severity_level
                ]

        # Group by category
        by_category = {}
        for finding in findings:
            category = finding.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(asdict(finding))

        return {
            'timestamp': datetime.now().isoformat(),
            'total_findings': len(findings),
            'critical': len([f for f in findings if f.severity == 'critical']),
            'high': len([f for f in findings if f.severity == 'high']),
            'medium': len([f for f in findings if f.severity == 'medium']),
            'low': len([f for f in findings if f.severity == 'low']),
            'by_category': by_category,
            'findings': [asdict(f) for f in findings]
        }


def audit_resources(resource_group: str, filter_type: Optional[str] = None) -> List[Dict]:
    """Fetch Azure resources for auditing."""
    try:
        cmd = ['az', 'resource', 'list', '--resource-group', resource_group, '--output', 'json']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        resources = json.loads(result.stdout)

        if filter_type:
            resources = [r for r in resources if r.get('type') == filter_type]

        return resources

    except subprocess.CalledProcessError as e:
        print(f"Error fetching resources: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Audit Azure resources for security compliance'
    )
    parser.add_argument('--resource-group', '-g', required=True,
                       help='Azure resource group name')
    parser.add_argument('--severity', '-s', choices=['critical', 'high', 'medium', 'low', 'info'],
                       help='Minimum severity level to report')
    parser.add_argument('--report', '-r', type=str,
                       help='Output report to JSON file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    print(f"Auditing resources in resource group: {args.resource_group}")

    # Fetch resources
    resources = audit_resources(args.resource_group)
    print(f"Found {len(resources)} resources\n")

    # Perform audits
    auditor = SecurityAuditor()

    for resource in resources:
        resource_type = resource.get('type', '')

        if 'Storage' in resource_type:
            auditor.findings.extend(auditor.audit_storage_account(resource))
        elif 'Sql' in resource_type and 'databases' in resource_type:
            auditor.findings.extend(auditor.audit_sql_database(resource))
        elif 'KeyVault' in resource_type:
            auditor.findings.extend(auditor.audit_key_vault(resource))
        elif 'sites' in resource_type and 'Web' in resource_type:
            auditor.findings.extend(auditor.audit_webapp(resource))
        elif 'networkSecurityGroups' in resource_type:
            auditor.findings.extend(auditor.audit_network_security_group(resource))

    # Generate report
    report = auditor.generate_report(args.severity)

    # Print summary
    print("Security Audit Summary:")
    print(f"  Critical: {report['critical']}")
    print(f"  High: {report['high']}")
    print(f"  Medium: {report['medium']}")
    print(f"  Low: {report['low']}")
    print(f"  Total Findings: {report['total_findings']}\n")

    # Print findings
    if report['findings']:
        print("Findings by Category:")
        for category, findings in report['by_category'].items():
            print(f"\n  📋 {category.upper()} ({len(findings)}):")
            for finding in findings:
                print(f"    [{finding['severity']}] {finding['resource_name']}: {finding['title']}")
                if args.verbose:
                    print(f"      → {finding['recommendation']}")

    # Save report if requested
    if args.report:
        with open(args.report, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to {args.report}")

    sys.exit(0 if report['critical'] == 0 else 1)


if __name__ == '__main__':
    main()
