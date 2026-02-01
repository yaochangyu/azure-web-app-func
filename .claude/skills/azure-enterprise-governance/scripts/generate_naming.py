#!/usr/bin/env python3
"""
Azure Resource Naming Generator

Interactive tool to help users generate Azure resource naming schemes
following Microsoft Cloud Adoption Framework standards.

Usage:
    python generate_naming.py
    python generate_naming.py --quick --org yao --workload lab --env dev
"""

import argparse
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class NamingScheme:
    """Generated naming scheme."""
    organization: str
    workload: str
    environment: str
    scenario: str
    resources: List[str]


RESOURCE_TYPES = {
    '1': {'name': 'Web App', 'abbreviation': 'app', 'plan': 'asp'},
    '2': {'name': 'Function App', 'abbreviation': 'func', 'plan': 'asp'},
    '3': {'name': 'SQL Database', 'abbreviation': 'sqldb', 'server': 'sql'},
    '4': {'name': 'Cosmos DB', 'abbreviation': 'cosmos'},
    '5': {'name': 'Key Vault', 'abbreviation': 'kv'},
    '6': {'name': 'Application Insights', 'abbreviation': 'appi'},
    '7': {'name': 'Storage Account', 'abbreviation': 'st'},
    '8': {'name': 'Virtual Network', 'abbreviation': 'vnet'},
    '9': {'name': 'Network Security Group', 'abbreviation': 'nsg'},
}

SCENARIOS = {
    '1': {
        'name': '實驗/學習環境 (Lab)',
        'workload': 'lab',
        'description': '個人學習、技術實驗、POC',
        'suggested_resources': ['1', '2', '5', '6']
    },
    '2': {
        'name': '單一應用部署 (Simple)',
        'workload': 'app',
        'description': '單一 Web 應用、簡單架構',
        'suggested_resources': ['1', '3', '5', '6']
    },
    '3': {
        'name': '微服務架構 (Microservices)',
        'workload': 'services',
        'description': '多個獨立服務、容器化',
        'suggested_resources': ['2', '3', '4', '5', '6']
    },
    '4': {
        'name': '多租戶 SaaS (Multi-tenant)',
        'workload': 'platform',
        'description': 'SaaS 平台、多客戶',
        'suggested_resources': ['1', '4', '5', '6']
    }
}

ENVIRONMENTS = {
    'dev': 'Development (開發環境)',
    'test': 'Testing (測試環境)',
    'stg': 'Staging (預備環境)',
    'prod': 'Production (生產環境)',
    'sandbox': 'Sandbox (沙箱環境)',
    'demo': 'Demo (展示環境)'
}


class NamingGenerator:
    """Azure resource naming generator."""

    def __init__(self):
        self.scheme: Optional[NamingScheme] = None

    def run_interactive(self):
        """Run interactive questionnaire."""
        print("\n" + "=" * 50)
        print("  Azure 資源命名生成器")
        print("  遵循 Microsoft Cloud Adoption Framework")
        print("=" * 50 + "\n")

        # Question 1: Organization
        organization = self._ask_organization()

        # Question 2: Scenario
        scenario = self._ask_scenario()

        # Question 3: Environment
        environment = self._ask_environment()

        # Question 4: Resources
        resources = self._ask_resources(scenario)

        # Generate naming scheme
        workload = SCENARIOS[scenario]['workload']
        self.scheme = NamingScheme(
            organization=organization,
            workload=workload,
            environment=environment,
            scenario=SCENARIOS[scenario]['name'],
            resources=resources
        )

        # Display results
        self._display_naming_scheme()
        self._generate_deployment_commands()

    def _ask_organization(self) -> str:
        """Ask for organization name."""
        while True:
            org = input("\n問題 1: 您的組織/名稱是什麼？(2-6 字元，小寫)\n> ").strip().lower()
            if 2 <= len(org) <= 6 and org.isalnum():
                return org
            print("❌ 請輸入 2-6 個字元的英文或數字")

    def _ask_scenario(self) -> str:
        """Ask for deployment scenario."""
        print("\n問題 2: 這是什麼類型的環境？")
        for key, scenario in SCENARIOS.items():
            print(f"  {key}. {scenario['name']}")
            print(f"     {scenario['description']}")

        while True:
            choice = input("> ").strip()
            if choice in SCENARIOS:
                return choice
            print("❌ 請選擇 1-4")

    def _ask_environment(self) -> str:
        """Ask for environment."""
        print("\n問題 3: 環境名稱？")
        for key, desc in ENVIRONMENTS.items():
            print(f"  {key:8} - {desc}")

        while True:
            env = input("> ").strip().lower()
            if env in ENVIRONMENTS:
                return env
            print("❌ 請選擇有效的環境名稱")

    def _ask_resources(self, scenario: str) -> List[str]:
        """Ask for resources to deploy."""
        print("\n問題 4: 您需要哪些資源？(多選，用逗號分隔)")
        print("建議：", end=" ")
        suggested = SCENARIOS[scenario]['suggested_resources']
        print(", ".join([f"{s}={RESOURCE_TYPES[s]['name']}" for s in suggested]))
        print()

        for key, resource in RESOURCE_TYPES.items():
            marker = "✓" if key in suggested else " "
            print(f"  [{marker}] {key}. {resource['name']}")

        while True:
            choices = input("> ").strip().split(',')
            choices = [c.strip() for c in choices if c.strip()]

            if all(c in RESOURCE_TYPES for c in choices):
                return choices
            print("❌ 請輸入有效的選項（例如: 1,2,5,6）")

    def _display_naming_scheme(self):
        """Display generated naming scheme."""
        if not self.scheme:
            return

        print("\n" + "━" * 60)
        print("  生成的命名方案")
        print("━" * 60)

        # Resource Group
        rg_name = f"rg-{self.scheme.organization}-{self.scheme.workload}-{self.scheme.environment}"
        print(f"\n📦 資源群組:")
        print(f"  {rg_name}")

        # Resources
        categories = {
            '計算資源': [],
            '資料資源': [],
            '安全資源': [],
            '監控資源': [],
            '網路資源': [],
            '儲存資源': []
        }

        for resource_id in self.scheme.resources:
            resource = RESOURCE_TYPES[resource_id]
            abbr = resource['abbreviation']

            if abbr in ['app', 'func']:
                # Compute resources need plan
                plan_name = f"asp-{self.scheme.organization}-{self.scheme.workload}-{self.scheme.environment}"
                app_name = f"{abbr}-{self.scheme.organization}-{self.scheme.workload}-{self.scheme.environment}"
                categories['計算資源'].append(plan_name)
                categories['計算資源'].append(app_name)
            elif abbr in ['sqldb', 'cosmos']:
                # Data resources
                if abbr == 'sqldb':
                    server_name = f"sql-{self.scheme.organization}-{self.scheme.workload}-{self.scheme.environment}"
                    db_name = f"sqldb-{self.scheme.organization}-{self.scheme.workload}-{self.scheme.environment}"
                    categories['資料資源'].append(server_name)
                    categories['資料資源'].append(db_name)
                else:
                    name = f"{abbr}-{self.scheme.organization}-{self.scheme.workload}-{self.scheme.environment}"
                    categories['資料資源'].append(name)
            elif abbr == 'kv':
                # Security resources - shared
                name = f"kv-{self.scheme.organization}-{self.scheme.environment}"
                categories['安全資源'].append(name)
            elif abbr == 'appi':
                # Monitoring resources - shared
                name = f"appi-{self.scheme.organization}-{self.scheme.environment}"
                categories['監控資源'].append(name)
            elif abbr == 'st':
                # Storage - no hyphens
                name = f"st{self.scheme.organization}{self.scheme.environment}001"
                categories['儲存資源'].append(name)
            elif abbr in ['vnet', 'nsg']:
                # Network resources
                name = f"{abbr}-{self.scheme.organization}-{self.scheme.workload}-{self.scheme.environment}"
                categories['網路資源'].append(name)

        # Print by category
        for category, resources in categories.items():
            if resources:
                # Remove duplicates while preserving order
                unique_resources = list(dict.fromkeys(resources))
                print(f"\n{category}:")
                for resource in unique_resources:
                    print(f"  {resource}")

        print("\n" + "━" * 60)

    def _generate_deployment_commands(self):
        """Generate Azure CLI deployment commands."""
        if not self.scheme:
            return

        print("\n🚀 部署命令：\n")
        rg_name = f"rg-{self.scheme.organization}-{self.scheme.workload}-{self.scheme.environment}"

        commands = []

        # Resource Group
        commands.append(f"# 建立資源群組")
        commands.append(f"az group create \\")
        commands.append(f"  --name {rg_name} \\")
        commands.append(f"  --location centralus \\")
        commands.append(f"  --tags environment={self.scheme.environment} owner={self.scheme.organization}\n")

        # Resources
        for resource_id in self.scheme.resources:
            resource = RESOURCE_TYPES[resource_id]
            abbr = resource['abbreviation']

            if abbr == 'app':
                plan_name = f"asp-{self.scheme.organization}-{self.scheme.workload}-{self.scheme.environment}"
                app_name = f"app-{self.scheme.organization}-{self.scheme.workload}-{self.scheme.environment}"
                
                commands.append(f"# Web App")
                commands.append(f"az appservice plan create \\")
                commands.append(f"  --name {plan_name} \\")
                commands.append(f"  --resource-group {rg_name} \\")
                commands.append(f"  --sku B1 --is-linux\n")
                
                commands.append(f"az webapp create \\")
                commands.append(f"  --name {app_name} \\")
                commands.append(f"  --resource-group {rg_name} \\")
                commands.append(f"  --plan {plan_name} \\")
                commands.append(f"  --runtime \"DOTNET|10.0\"\n")

            elif abbr == 'kv':
                kv_name = f"kv-{self.scheme.organization}-{self.scheme.environment}"
                commands.append(f"# Key Vault")
                commands.append(f"az keyvault create \\")
                commands.append(f"  --name {kv_name} \\")
                commands.append(f"  --resource-group {rg_name} \\")
                commands.append(f"  --location centralus\n")

        # Print commands
        for cmd in commands:
            print(cmd)

        # Save to file
        filename = f"deploy-{rg_name}.sh"
        with open(filename, 'w') as f:
            f.write("#!/bin/bash\n\n")
            f.write("# Azure 資源部署腳本\n")
            f.write(f"# 生成時間: $(date)\n\n")
            for cmd in commands:
                f.write(cmd + "\n")

        print(f"\n💾 部署腳本已儲存到: {filename}")
        print(f"執行: chmod +x {filename} && ./{filename}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Azure 資源命名生成器'
    )
    parser.add_argument('--quick', action='store_true',
                       help='快速模式（需搭配其他參數）')
    parser.add_argument('--org', type=str,
                       help='組織名稱')
    parser.add_argument('--workload', type=str,
                       help='工作負載名稱')
    parser.add_argument('--env', type=str, choices=list(ENVIRONMENTS.keys()),
                       help='環境名稱')

    args = parser.parse_args()

    generator = NamingGenerator()

    if args.quick and args.org and args.workload and args.env:
        # Quick mode
        generator.scheme = NamingScheme(
            organization=args.org,
            workload=args.workload,
            environment=args.env,
            scenario='Quick',
            resources=['1', '5', '6']  # Default: Web App, Key Vault, AppInsights
        )
        generator._display_naming_scheme()
        generator._generate_deployment_commands()
    else:
        # Interactive mode
        generator.run_interactive()


if __name__ == '__main__':
    main()
