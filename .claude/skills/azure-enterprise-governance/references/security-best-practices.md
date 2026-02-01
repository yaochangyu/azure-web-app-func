# Azure Security Best Practices & Compliance Framework

Enterprise-grade security architecture based on [Microsoft Security Best Practices](https://learn.microsoft.com/security/), [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework/), and [Zero Trust Architecture](https://learn.microsoft.com/security/zero-trust/).

## Zero Trust Security Principles

Zero Trust assumes all access is a potential threat and requires verification at every stage.

### Core Principles

1. **Verify Explicitly**
   - Use all available data for authentication and authorization
   - Require Multi-Factor Authentication (MFA)
   - Use conditional access policies based on user, device, location
   - Verify device health and compliance status

2. **Assume Breach**
   - Design systems assuming attackers already have access
   - Implement defense in depth (multiple security layers)
   - Minimize blast radius with network segmentation
   - Enable rapid detection and response

3. **Secure Every Access Point**
   - Protect identities with strong authentication
   - Secure devices and applications
   - Encrypt all data (in transit and at rest)
   - Apply least privilege access controls

## Identity & Access Management (IAM)

### Authentication Hierarchy (Best to Worst)

#### 1. Managed Identity ✅ **RECOMMENDED**

Eliminates credential management entirely. Azure automatically manages secrets.

```csharp
// .NET Example - Managed Identity
var credential = new DefaultAzureCredential();
var blobClient = new BlobServiceClient(
    new Uri("https://mystorageaccount.blob.core.windows.net"),
    credential
);
```

```javascript
// Node.js Example - Managed Identity
const { DefaultAzureCredential } = require('@azure/identity');
const { BlobServiceClient } = require('@azure/storage-blob');

const credential = new DefaultAzureCredential();
const blobServiceClient = new BlobServiceClient(
  'https://mystorageaccount.blob.core.windows.net',
  credential
);
```

**Advantages:**
- No credential management needed
- Automatic rotation of credentials
- Audit trail of service access
- No secrets in code, configuration files, or pipelines
- Works across Azure services seamlessly

**When to use:**
- Service-to-service communication (App Service → Storage)
- Function App accessing databases
- Container Apps accessing Key Vault
- Anywhere inside Azure

#### 2. Azure Key Vault with Managed Identity

Use managed identity to fetch secrets from Key Vault (not embedding secrets).

```csharp
// Fetch secret from Key Vault using managed identity
var credential = new DefaultAzureCredential();
var client = new SecretClient(
    new Uri("https://myvault.vault.azure.net/"),
    credential
);
KeyVaultSecret secret = await client.GetSecretAsync("MySecret");
```

**When to use:**
- Storing connection strings, API keys, passwords
- Sharing secrets across multiple services
- External API credentials
- Database admin passwords

#### 3. Azure AD / Entra ID Service Principal (with Client Secret)

Use only if managed identity is unavailable (external tools, on-premises).

```bash
# Only use if managed identity not available
az login --service-principal \
  -u <app-id> \
  -p <secret> \
  --tenant <tenant-id>
```

⚠️ **Requires credential rotation strategy**

#### 4. ❌ **AVOID: Shared Credentials / Connection Strings**

- Hard-coded passwords in code
- Credentials in configuration files
- Shared credentials (multiple people knowing same password)
- Credentials in environment variables without protection

### Role-Based Access Control (RBAC)

#### Built-in Roles (Use These First)

| Role | Use Case | Scope |
|------|----------|-------|
| `Owner` | Full management, including access | Any |
| `Contributor` | Full management, no access control | Any |
| `Reader` | View only | Any |
| `Storage Account Contributor` | Manage storage accounts | Storage |
| `Storage Blob Data Owner` | Read/write/delete blobs | Storage |
| `Storage Blob Data Reader` | Read blobs only | Storage |
| `Cosmos DB Account Reader` | Read CosmosDB | Cosmos |
| `SQL DB Contributor` | Manage SQL databases | SQL |
| `Key Vault Administrator` | Full KV access | Key Vault |
| `Key Vault Secrets User` | Read secrets only | Key Vault |
| `App Service Contributor` | Manage App Service | App Service |

#### Principle of Least Privilege (PoLP)

**❌ Bad:**
```bash
# Assigning Owner to production service
az role assignment create \
  --assignee <service-principal> \
  --role Owner \
  --scope /subscriptions/{subscriptionId}
```

**✅ Good:**
```bash
# Assign minimal required role to specific resource
az role assignment create \
  --assignee <service-principal> \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/providers/Microsoft.Storage/storageAccounts/{storageAccountName}/blobServices/default/containers/{containerName}
```

#### Role Assignment Pattern

```
User/Service → Scope (Resource Group, Subscription, Resource)
              ↓
         Built-in Role
              ↓
         Conditional Access Policies
```

### Access Reviews & Auditing

```bash
# List all role assignments in resource group
az role assignment list --resource-group mygroup --output table

# List all role assignments for specific user
az role assignment list --assignee user@example.com --output table

# Export RBAC configuration for audit
az role assignment list --scope /subscriptions/{subscriptionId} \
  --output json > rbac-audit-$(date +%Y%m%d).json
```

## Network Security

### Network Architecture Pattern

```
┌─────────────────────────────────────────────────────────┐
│                    Internet                              │
└──────────────────────┬──────────────────────────────────┘
                       ↓
        ┌──────────────────────────────┐
        │   Azure Front Door / WAF      │ (DDoS, WAF rules)
        └──────────────┬───────────────┘
                       ↓
        ┌──────────────────────────────┐
        │    Application Gateway       │ (SSL termination)
        └──────────────┬───────────────┘
                       ↓
        ┌──────────────────────────────┐
        │    Virtual Network (VNet)    │
        ├──────────────────────────────┤
        │ NSG - Allow 443 only         │
        └──────────────┬───────────────┘
                       ↓
        ┌──────────────────────────────┐
        │     Public Subnets           │
        │ ├─ App Service (multi-tenant)│
        │ └─ App Gateway               │
        └──────────────┬───────────────┘
                       ↓
        ┌──────────────────────────────┐
        │    Private Subnets           │
        │ ├─ VMs, Container Instances  │
        │ ├─ App Service Environment   │
        │ └─ Private Endpoints         │
        └──────────────┬───────────────┘
                       ↓
        ┌──────────────────────────────┐
        │    Database / Storage        │
        │ (Private Endpoints only)     │
        └──────────────────────────────┘
```

### Network Security Group (NSG) Rules

**Principle:** Default deny, explicitly allow.

#### ✅ Good NSG Configuration

```bash
# Create NSG
az network nsg create --resource-group mygroup --name nsg-myapp

# Allow HTTPS inbound only
az network nsg rule create \
  --resource-group mygroup \
  --nsg-name nsg-myapp \
  --name allow-https \
  --protocol tcp \
  --direction Inbound \
  --access Allow \
  --priority 100 \
  --source-address-prefixes Internet \
  --destination-port-ranges 443

# Allow HTTP inbound (for redirect to HTTPS)
az network nsg rule create \
  --resource-group mygroup \
  --nsg-name nsg-myapp \
  --name allow-http \
  --protocol tcp \
  --direction Inbound \
  --access Allow \
  --priority 110 \
  --source-address-prefixes Internet \
  --destination-port-ranges 80

# Block everything else (implicit)
```

#### ❌ Dangerous NSG Configuration

```bash
# ❌ NEVER: Allow all inbound
--source-address-prefixes "*"
--destination-port-ranges "*"

# ❌ NEVER: Allow SSH/RDP from internet
--source-address-prefixes Internet
--destination-port-ranges 22  # SSH
--destination-port-ranges 3389 # RDP
```

### Private Endpoints & VNet Integration

#### When to Use Private Endpoints

**Private Endpoints for sensitive services:**
- SQL Database
- Storage Account (Blobs, Queues, Tables)
- Cosmos DB
- Key Vault
- Azure Container Registry
- Azure Cognitive Services

```bash
# Create private endpoint for SQL Database
az network private-endpoint create \
  --resource-group mygroup \
  --name pep-sqldb-myapp \
  --vnet-name vnet-myapp \
  --subnet subnet-private \
  --private-connection-resource-id /subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/providers/Microsoft.Sql/servers/{serverName} \
  --group-ids sqlServer \
  --connection-name conn-sqldb
```

## Data Protection

### Encryption in Transit

**Enforce HTTPS only:**

```bash
# Configure web app to use HTTPS only
az webapp update \
  --resource-group mygroup \
  --name myapp \
  --https-only true

# Enforce minimum TLS 1.2
az webapp config set \
  --resource-group mygroup \
  --name myapp \
  --min-tls-version 1.2
```

**API Communication:**

```csharp
// Enforce HTTPS in code
using var handler = new HttpClientHandler();
handler.ServerCertificateCustomValidationCallback = (msg, cert, chain, errors) => {
    // In production, validate certificate properly
    return errors == SslPolicyErrors.None;
};

using var client = new HttpClient(handler);
```

### Encryption at Rest

#### Storage Account
```bash
# Enable encryption with customer-managed keys
az storage account update \
  --resource-group mygroup \
  --name mystorageaccount \
  --encryption-services blob table queue \
  --key-source Microsoft.Keyvault \
  --key-vault-uri https://myvault.vault.azure.net
```

#### SQL Database
```bash
# Enable Transparent Data Encryption (TDE)
az sql db tde set \
  --resource-group mygroup \
  --server myserver \
  --database mydb \
  --status Enabled
```

#### Cosmos DB
```bash
# Enable encryption with customer-managed keys
# (Requires Azure Resource Manager template)
```

## Secrets Management

### ✅ Correct: Use Key Vault with Managed Identity

```csharp
// Application fetches secrets at runtime using managed identity
var credential = new DefaultAzureCredential();
var client = new SecretClient(new Uri("https://myvault.vault.azure.net/"), credential);

// Get secret when needed
KeyVaultSecret secret = await client.GetSecretAsync("DatabasePassword");
string password = secret.Value;
```

### ❌ Incorrect: Hard-coded Secrets

```csharp
// ❌ NEVER hardcode secrets
const string password = "MySecurePassword123!";
var connectionString = $"Server=myserver;Password={password}";

// ❌ NEVER store in config files
appsettings.json:
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=myserver;Password=MySecurePassword123!"
  }
}

// ❌ NEVER pass in environment variables without protection
export DATABASE_PASSWORD="MySecurePassword123!"
```

### Key Rotation Strategy

```bash
# Create secret version in Key Vault
az keyvault secret set \
  --vault-name myvault \
  --name DatabasePassword \
  --value "NewSecurePassword456!"

# Application automatically uses latest version
# Old connections gracefully transition
```

## Compliance Frameworks

### NIST Cybersecurity Framework (CSF) Alignment

| NIST Function | Azure Control | Configuration |
|---------------|---------------|---------------|
| **Identify** | Microsoft Defender for Cloud | Asset inventory, vulnerability assessment |
| **Protect** | Azure Policy, RBAC | Access controls, encryption |
| **Detect** | Azure Monitor, Security Center | Logging, alerting, anomaly detection |
| **Respond** | Azure Sentinel | Incident response, automation |
| **Recover** | Azure Backup, Site Recovery | Business continuity, disaster recovery |

### SOC 2 Compliance Checklist

#### Trust Service Criteria (TSC)

- [ ] **CC1**: Risk management process documented and implemented
- [ ] **CC2**: Board oversight of security program
- [ ] **CC3**: Management defines security objectives
- [ ] **CC4**: Infrastructure security policies documented
- [ ] **CC5**: Access control policies and enforcement
- [ ] **CC6**: Logical access enforced for systems
- [ ] **CC7**: Data classified and retention policies defined
- [ ] **CC8**: Encryption configured for data at rest/transit
- [ ] **CC9**: Change management procedures documented
- [ ] **C03**: Encryption keys managed securely
- [ ] **A1**: Infrastructure monitoring and logging
- [ ] **A2**: Audit logs retained for sufficient period
- [ ] **A3**: Response procedures for security events
- [ ] **S1**: Availability of system components
- [ ] **S2**: Redundancy and failover procedures
- [ ] **S3**: System capacity and performance monitored

**Azure Services Supporting SOC 2:**
- Microsoft Defender for Cloud
- Azure Policy
- Azure Monitor
- Azure Backup
- Azure Site Recovery
- Key Vault
- Network Security Groups

### PCI-DSS Compliance Checklist

For applications processing credit cards:

- [ ] Firewall protection (NSG, Application Gateway)
- [ ] No default passwords (managed identity, Key Vault)
- [ ] Encrypted cardholder data (TDE, BYOK)
- [ ] Encrypted data in transit (TLS 1.2+)
- [ ] Network segmentation (subnets, NSGs)
- [ ] Regular security updates (patch management)
- [ ] Access control (RBAC, least privilege)
- [ ] Vulnerability testing (Microsoft Defender)
- [ ] Security logging and monitoring (Sentinel)
- [ ] Information security policy (Azure Policy)

### HIPAA Compliance Checklist

For healthcare applications:

- [ ] Risk assessment completed
- [ ] Encryption at rest and in transit
- [ ] Access controls and audit logging
- [ ] Breach notification procedures
- [ ] Data integrity controls
- [ ] Business associate agreements (BAA)
- [ ] Backup and disaster recovery
- [ ] Workforce security training
- [ ] Facility access controls
- [ ] Audit logs retained for 6 years

## Security Assessment Checklist

### Before Production Deployment

**Identity & Access:**
- [ ] Managed identities used for service-to-service auth
- [ ] No credentials hard-coded in code or config
- [ ] All secrets stored in Key Vault
- [ ] RBAC follows principle of least privilege
- [ ] MFA enabled for human users
- [ ] Service principals use certificates (not secrets)
- [ ] Regular access reviews scheduled

**Network Security:**
- [ ] Virtual Network segmented (public/private subnets)
- [ ] NSGs configured with explicit allow rules
- [ ] Private endpoints used for data services
- [ ] DDoS protection enabled (Front Door, WAF)
- [ ] SSL/TLS 1.2+ enforced
- [ ] No public endpoints for data services

**Data Protection:**
- [ ] Encryption at rest enabled (TDE, BYOK, CMK)
- [ ] Encryption in transit enforced (HTTPS only)
- [ ] Data classification policy defined
- [ ] Backup strategy implemented
- [ ] Disaster recovery procedures documented

**Application Security:**
- [ ] Input validation implemented
- [ ] Output encoding applied
- [ ] SQL injection prevention (parameterized queries)
- [ ] CORS policies restricted
- [ ] Security headers configured
- [ ] Dependency scanning enabled
- [ ] SAST/DAST performed

**Monitoring & Logging:**
- [ ] Application Insights enabled
- [ ] Log Analytics configured
- [ ] Audit logging enabled
- [ ] Security alerts configured
- [ ] Incident response procedures documented
- [ ] Regular security reviews scheduled

**Compliance:**
- [ ] Compliance framework selected
- [ ] Audit trail requirements met
- [ ] Documentation complete
- [ ] Third-party assessment scheduled

## Common Security Misconfigurations

| Misconfiguration | Impact | Fix |
|------------------|--------|-----|
| Storage account public access | Data breach | Disable public access, use private endpoints |
| Unencrypted data in transit | Man-in-the-middle attack | Enforce HTTPS, TLS 1.2+ |
| Hard-coded secrets | Credential compromise | Move to Key Vault + Managed Identity |
| Overly permissive RBAC | Privilege escalation | Use principle of least privilege |
| No network segmentation | Lateral movement | Implement VNets, subnets, NSGs |
| Disabled audit logging | No visibility | Enable logging, retention |
| Default database passwords | Easy compromise | Use managed identities, Key Vault |
| No MFA on admin accounts | Account takeover | Enforce MFA |
| Outdated TLS versions | Cryptographic attacks | Enforce TLS 1.2+ |
| No backup strategy | Data loss | Implement automated backups |

## Security Tools & Services

### Microsoft Defender for Cloud

Unified security management across Azure:

```bash
# Enable Microsoft Defender for Cloud
az security setting list --output table
az security setting update --setting-name MCAS --value True
```

### Azure Policy

Enforce compliance at scale:

```json
{
  "mode": "all",
  "policyRule": {
    "if": {
      "field": "type",
      "equals": "Microsoft.Storage/storageAccounts"
    },
    "then": {
      "effect": "deny",
      "details": {
        "condition": {
          "field": "Microsoft.Storage/storageAccounts/supportsHttpsTrafficOnly",
          "equals": false
        }
      }
    }
  }
}
```

### Azure Sentinel

Security information and event management (SIEM):

```bash
# Connect data sources
az sentinel data-connector create \
  --resource-group mygroup \
  --workspace-name myworkspace \
  --name AzureActivityConnector \
  --kind AzureActivity
```

## Security Validation Scripts

See `scripts/security_audit.py` for automated checks:
- Managed identity usage
- Encryption configuration
- Network isolation
- RBAC assignments
- Secret management
- Compliance alignment
