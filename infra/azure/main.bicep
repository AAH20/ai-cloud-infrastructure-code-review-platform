@description('Globally unique deployment prefix')
@minLength(3)
param prefix string
@description('Azure region')
param location string = resourceGroup().location
@allowed(['dev', 'prod'])
param environment string = 'dev'

var storageName = take('st${uniqueString(resourceGroup().id)}${replace(prefix, '-', '')}', 24)
var workspaceName = '${prefix}-logs'
var appEnvironmentName = '${prefix}-cae'

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  properties: { retentionInDays: environment == 'prod' ? 90 : 30 }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource appEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: appEnvironmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: workspace.properties.customerId
        sharedKey: workspace.listKeys().primarySharedKey
      }
    }
  }
}

output logAnalyticsWorkspaceId string = workspace.id
output storageAccountId string = storage.id
output containerAppsEnvironmentId string = appEnvironment.id
