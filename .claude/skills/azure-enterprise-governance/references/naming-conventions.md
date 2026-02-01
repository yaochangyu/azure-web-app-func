# Azure Resource Naming Conventions

Official standards based on [Microsoft Cloud Adoption Framework (CAF)](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/resource-naming) and industry best practices.

## Standard Naming Format

```
<resource-type>-<organization>-<workload>-<environment>-<location>-<instance>
```

### Components Definition

- **resource-type** (1-3 chars): Abbreviation indicating Azure service type
- **organization** (2-6 chars): Organization, department, or project name
- **workload** (2-8 chars): Workload or application identifier
- **environment** (3-4 chars): Environment designation (dev, test, stg, prod)
- **location** (2-3 chars, optional): Azure region abbreviation
- **instance** (1-3 digits, optional): Sequential number for multiple instances

### Naming Examples

**Web API Application - Development Environment:**
```
rg-yao-webapi-dev              # Resource Group
asp-yao-webapi-dev             # App Service Plan
app-yao-webapi-dev             # Web App
sqldb-yao-webapi-dev           # SQL Database
kv-yao-dev                      # Key Vault
appi-yao-webapi-dev            # Application Insights
nsg-yao-webapi-dev             # Network Security Group
```

**Multi-Tenant SaaS - Production Environment with Region:**
```
rg-acme-saas-prod-eus-001      # Resource Group (East US)
asp-acme-saas-prod-eus-001     # App Service Plan
app-acme-saas-prod-eus-001     # Web App
sqldb-acme-saas-prod-eus-001   # SQL Database
cosmos-acme-saas-prod-001      # Cosmos DB (global)
kv-acme-prod                   # Key Vault
```

**Microservices Architecture - Multiple Services:**
```
# User Service
rg-mycompany-users-prod        # Resource Group
func-mycompany-users-prod      # Function App
cosmos-mycompany-users-prod    # Cosmos DB
kv-mycompany-prod              # Shared Key Vault

# Order Service
func-mycompany-orders-prod     # Function App
sqldb-mycompany-orders-prod    # SQL Database
queue-mycompany-orders-prod    # Storage Queue
```

## Resource Type Abbreviations

### Microsoft Official Abbreviations

Based on [Microsoft CAF Resource Abbreviations](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/resource-abbreviations)

#### Compute

| Service | Abbreviation | Resource Name Example |
|---------|--------------|----------------------|
| App Service Plan | `asp` or `plan` | asp-myapp-prod |
| App Service / Web App | `app` | app-myapp-prod |
| App Service Environment | `ase` | ase-myapp-prod |
| Function App | `func` | func-myapp-prod |
| Container Instance | `ci` | ci-myapp-prod |
| Container Registry | `cr` | crmyappprod |
| Azure Kubernetes Service | `aks` | aks-myapp-prod |
| Service Fabric Cluster | `sf` | sf-myapp-prod |
| Virtual Machine | `vm` | vm-myapp-prod-001 |

#### Storage & Data

| Service | Abbreviation | Resource Name Example | Notes |
|---------|--------------|----------------------|-------|
| Storage Account | `st` | stmyappprod001 | No hyphens allowed |
| Azure Data Lake | `datalake` or `adls` | adls-myapp-prod | Minimum 3 chars |
| Azure Cosmos DB | `cosmos` | cosmos-myapp-prod | Global service |
| Azure SQL Database | `sqldb` | sqldb-myapp-prod | |
| SQL Server | `sql` | sql-myapp-prod | |
| SQL Server Database | `sqldb` | sqldb-myapp-prod | |
| MySQL Database | `mysql` | mysql-myapp-prod | |
| PostgreSQL Database | `psql` | psql-myapp-prod | |
| MariaDB Database | `mariadb` | mariadb-myapp-prod | |
| Synapse Analytics | `syn` | syn-myapp-prod | |
| Azure Cache for Redis | `redis` | redis-myapp-prod | |

#### Networking

| Service | Abbreviation | Resource Name Example |
|---------|--------------|----------------------|
| Virtual Network | `vnet` | vnet-myapp-prod |
| Subnet | `snet` | snet-myapp-prod-001 |
| Network Interface | `nic` | nic-myapp-prod-001 |
| Network Security Group | `nsg` | nsg-myapp-prod |
| Application Security Group | `asg` | asg-myapp-prod |
| Public IP | `pip` | pip-myapp-prod-001 |
| NAT Gateway | `nat` | nat-myapp-prod |
| Load Balancer (Internal) | `lbi` | lbi-myapp-prod |
| Load Balancer (Public) | `lbp` | lbp-myapp-prod |
| Application Gateway | `agw` | agw-myapp-prod |
| Azure Firewall | `afw` | afw-myapp-prod |
| VPN Gateway | `vpn` | vpn-myapp-prod |
| ExpressRoute Circuit | `erc` | erc-myapp-prod |
| Front Door | `fd` | fd-myapp-prod |
| CDN Endpoint | `cdn` | cdn-myapp-prod |
| Private Endpoint | `pep` | pep-myapp-prod-001 |
| Private Link Service | `pls` | pls-myapp-prod |

#### Security & Identity

| Service | Abbreviation | Resource Name Example |
|---------|--------------|----------------------|
| Key Vault | `kv` | kv-myapp-prod |
| Azure AD | `aad` | N/A (tenant-based) |
| Managed Identity | `mi` | mi-myapp-prod |
| Azure Bastion | `bas` | bas-myapp-prod |

#### Monitoring & Management

| Service | Abbreviation | Resource Name Example |
|---------|--------------|----------------------|
| Application Insights | `appi` | appi-myapp-prod |
| Log Analytics Workspace | `log` | log-myapp-prod |
| Event Hub | `evh` | evh-myapp-prod |
| Event Grid Topic | `egt` | egt-myapp-prod |
| Service Bus Namespace | `sb` | sb-myapp-prod |
| API Management | `apim` | apim-myapp-prod |
| Azure Monitor | `mon` | N/A (service-based) |
| Azure Advisor | `adv` | N/A (service-based) |
| Azure Backup | `bak` | bak-myapp-prod |
| Recovery Services Vault | `rsv` | rsv-myapp-prod |

#### Management & Governance

| Service | Abbreviation | Resource Name Example |
|---------|--------------|----------------------|
| Resource Group | `rg` | rg-myapp-prod |
| Subscription | `sub` | N/A (not named) |
| Management Group | `mg` | mg-myapp-prod |
| Policy Assignment | `pol` | pol-myapp-prod |
| Blueprint | `bp` | bp-myapp-prod |

## Environment Abbreviations

### Standard Environments

| Environment | Abbreviation | Characteristics |
|------------|--------------|-----------------|
| Development | `dev` | Developers, unstable, no compliance requirements |
| Testing | `test` | QA team, functional testing |
| Staging | `stg` | Production-like, UAT, final validation |
| Production | `prod` | Live traffic, high availability, compliance critical |
| Sandbox | `sandbox` | Experimentation, no production constraints |
| Demo | `demo` | Sales/marketing demonstrations |

### Extended Environment Variations

```
dev    - Development (unstable, active development)
dev-qa - Development-QA (QA testing in dev environment)
int    - Integration (internal integration testing)
test   - Testing (formal QA testing)
stg    - Staging (production-like, UAT)
stg-dr - Staging (disaster recovery testing)
prod   - Production (live, critical)
prod-dr - Production (disaster recovery/failover)
dr     - Disaster Recovery (passive, ready for failover)
```

## Region Abbreviations

### Azure Global Regions

| Region | Abbreviation | Alternative |
|--------|--------------|-------------|
| East US | `eus` | us-east |
| East US 2 | `eus2` | us-east2 |
| Central US | `cus` | us-central |
| West US | `wus` | us-west |
| West US 2 | `wus2` | us-west2 |
| North Central US | `ncus` | us-north |
| South Central US | `scus` | us-south |
| Canada Central | `cc` | ca-central |
| Canada East | `ce` | ca-east |
| North Europe | `ne` | eu-north |
| West Europe | `we` | eu-west |
| UK South | `uks` | uk-south |
| UK West | `ukw` | uk-west |
| Southeast Asia | `sea` | asia-southeast |
| East Asia | `ea` | asia-east |
| Australia East | `ause` | au-east |
| Australia Southeast | `ausese` | au-southeast |
| Japan East | `jpe` | jp-east |
| Japan West | `jpw` | jp-west |
| South Africa North | `san` | za-north |
| UAE North | `uan` | ae-north |
| India Central | `ic` | in-central |
| India West | `iw` | in-west |
| South India | `si` | in-south |
| Germany West Central | `gwc` | de-west |
| Brazil South | `brs` | br-south |

## Naming Constraints & Rules

### Per-Resource-Type Constraints

#### Storage Account
- **Length**: 3-24 characters
- **Allowed**: Lowercase letters and numbers only
- **Unique**: Must be globally unique across all Azure
- **Pattern**: `st[organization][environment]001`
- **Examples**: `stmyappprod001`, `styaodev001`
- **⚠️ Important**: NO HYPHENS allowed

#### Web App / Function App
- **Length**: 1-60 characters
- **Allowed**: Letters, numbers, hyphens
- **Unique**: Must be globally unique (becomes subdomain)
- **Pattern**: `app-[org]-[workload]-[env]`
- **URL**: `https://{app-name}.azurewebsites.net`
- **Examples**: `app-myapp-prod`, `func-processor-dev`

#### SQL Database Server
- **Length**: 1-63 characters
- **Allowed**: Lowercase letters, numbers, hyphens
- **Unique**: Must be globally unique
- **Pattern**: `sql-[org]-[workload]-[env]`
- **Examples**: `sql-myapp-prod`, `sql-yao-webapi-dev`

#### Cosmos DB Account
- **Length**: 3-44 characters
- **Allowed**: Lowercase letters, numbers, hyphens
- **Unique**: Must be globally unique
- **Pattern**: `cosmos-[org]-[workload]-[env]`
- **Examples**: `cosmos-myapp-prod`, `cosmos-yao-saas-dev`

#### Key Vault
- **Length**: 3-24 characters
- **Allowed**: Letters, numbers, hyphens
- **Unique**: Within resource group
- **Pattern**: `kv-[org]-[env]`
- **Examples**: `kv-myapp-prod`, `kv-yao-dev`

#### Application Insights
- **Length**: 1-260 characters
- **Allowed**: Letters, numbers, hyphens, underscores, periods, parentheses
- **Unique**: Within resource group
- **Pattern**: `appi-[org]-[workload]-[env]`
- **Examples**: `appi-myapp-prod`, `appi-yao-webapi-dev`

#### Resource Group
- **Length**: 1-90 characters
- **Allowed**: Letters, numbers, hyphens, underscores, periods
- **Unique**: Within subscription
- **Pattern**: `rg-[org]-[workload]-[env]`
- **Examples**: `rg-myapp-prod`, `rg-yao-webapi-dev`

#### Virtual Network / NSG
- **Length**: 2-64 characters
- **Allowed**: Letters, numbers, hyphens, underscores, periods
- **Unique**: Within resource group
- **Pattern**: `vnet-[org]-[env]`, `nsg-[org]-[purpose]-[env]`
- **Examples**: `vnet-myapp-prod`, `nsg-myapp-web-prod`

## Multi-Tenant Naming Patterns

### Pattern 1: Tenant-First Hierarchy (SaaS)

Useful for platforms serving multiple customers/tenants.

```
Subscription (per customer)
├── rg-[org]-[tenant-id]-prod
│   ├── asp-[org]-[tenant-id]-prod
│   ├── app-[org]-[tenant-id]-prod
│   ├── sqldb-[org]-[tenant-id]-prod
│   └── kv-[org]-tenant-[tenant-id]-prod

Resource Naming:
- Tenant A: rg-acme-tenant-001-prod
- Tenant B: rg-acme-tenant-002-prod
```

**When to use**: Each tenant needs complete isolation, custom compliance requirements, or billing per tenant.

### Pattern 2: Shared Infrastructure with Tenant Isolation

Shared resources with data isolation.

```
Subscription (single shared)
├── rg-[org]-shared-prod (shared resources)
│   ├── asp-[org]-prod (shared app plan)
│   ├── app-[org]-api-prod (main API)
│   ├── cosmos-[org]-[tenant-id]-prod (tenant data in shared cosmos)
│   ├── kv-[org]-prod (shared secrets)
│   └── appi-[org]-prod (shared monitoring)

Database Naming:
- Tenant A data: Database or Container named "tenant-001"
- Tenant B data: Database or Container named "tenant-002"
```

**When to use**: Multiple tenants share infrastructure but need data isolation, cost-effective for many small tenants.

### Pattern 3: Environment Segregation with Multi-Tenancy

Separate environments per tenant.

```
Subscription (per environment)
├── Development Subscription
│   └── rg-[org]-[tenant-id]-dev
│   
├── Production Subscription
│   ├── rg-[org]-[tenant-id]-prod (tenant A)
│   └── rg-[org]-[tenant-id]-prod (tenant B)
```

**When to use**: Enterprise scenarios requiring strict dev/prod separation and tenant isolation.

## Compliance-Friendly Naming

### Name Searchability & Auditing

Design names to support Azure Policy and compliance tooling:

```
Good (Auditable):
- rg-acme-webapi-prod        # Clear org, workload, env
- app-acme-webapi-prod       # Hierarchical, filterable
- sqldb-acme-orders-prod     # Business-meaningful

Poor (Hard to audit):
- rg-project-one             # Ambiguous environment
- App1Production             # Inconsistent format
- myapp-database-2024        # No org/workload indicators
```

### Azure Policy Naming Rules

Example policy to enforce naming:

```json
{
  "effect": "deny",
  "condition": {
    "not": {
      "match": "[resourceName]",
      "pattern": "^[a-z]+-[a-z]+-[a-z]+-[a-z]+$"
    }
  }
}
```

## Naming Validation Checklist

Before deploying resources, verify:

- [ ] Resource type abbreviation matches Microsoft CAF standard
- [ ] Organization/project identifier is consistent across resources
- [ ] Environment (`dev`, `test`, `stg`, `prod`) is clearly indicated
- [ ] Resource names follow per-resource constraints (length, characters)
- [ ] Globally unique names (Storage, SQL, App Service) are unique
- [ ] Naming pattern is consistent across resource group
- [ ] Names are lowercase (except where allowed)
- [ ] Hyphens used correctly (no hyphens in storage account names)
- [ ] Multi-instance resources have sequential numbers (`-001`, `-002`)
- [ ] Resource group name indicates purpose and environment
- [ ] Key Vault name indicates it's central security store
- [ ] Monitoring resources grouped by workload

## Automated Validation

See `scripts/validate_naming.py` for automated checking of:
- Naming convention compliance
- Constraint violations
- Format consistency
- Uniqueness verification
