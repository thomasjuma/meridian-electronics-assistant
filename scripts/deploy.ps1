param(
    [string]$Environment = "dev",   # dev | test | prod
    [string]$ProjectName = "meridian"
)
$ErrorActionPreference = "Stop"
$rootDir = Split-Path $PSScriptRoot -Parent
$backendDir = Join-Path $rootDir "backend"
$frontendDir = Join-Path $rootDir "frontend"
$lambdaPackage = Join-Path $backendDir "lambda-deployment.zip"

Write-Host "Deploying $ProjectName to $Environment ..." -ForegroundColor Green

if ($Environment -notin @("dev", "test", "prod")) {
    throw "Invalid environment '$Environment'. Allowed values: dev, test, prod."
}

# 1. Build backend Lambda package
Set-Location $rootDir
Write-Host "Preparing backend package..." -ForegroundColor Yellow
if (Test-Path (Join-Path $backendDir "deploy.py")) {
    Set-Location $backendDir
    uv run deploy.py
    Set-Location $rootDir
} else {
    Write-Host "backend/deploy.py not found. Creating lambda package from source files..." -ForegroundColor Yellow
    if (Test-Path $lambdaPackage) {
        Remove-Item $lambdaPackage -Force
    }
    Set-Location $backendDir
    Compress-Archive -Path @("app", "main.py", "pyproject.toml", "uv.lock") -DestinationPath $lambdaPackage -Force
    Set-Location $rootDir
}

# 2. Terraform workspace & apply
Set-Location terraform
$awsAccountId = aws sts get-caller-identity --query Account --output text
$awsRegion = if ($env:DEFAULT_AWS_REGION) { $env:DEFAULT_AWS_REGION } else { "us-east-1" }

terraform init -reconfigure -input=false `
  -backend-config="bucket=meridian-terraform-state-$awsAccountId" `
  -backend-config="key=$Environment/terraform.tfstate" `
  -backend-config="region=$awsRegion" `
  -backend-config="use_lockfile=true" `
  -backend-config="encrypt=true"

if (-not (terraform workspace list | Select-String $Environment)) {
    terraform workspace new $Environment
} else {
    terraform workspace select $Environment
}

if ($Environment -eq "prod") {
    terraform apply -var-file="prod.tfvars" -var="project_name=$ProjectName" -var="environment=$Environment" -auto-approve
} else {
    terraform apply -var="project_name=$ProjectName" -var="environment=$Environment" -auto-approve
}

$ApiUrl         = (terraform output -raw api_gateway_url).Trim()
$FrontendBucket = (terraform output -raw s3_frontend_bucket).Trim()
try { $CustomUrl = (terraform output -raw custom_domain_url).Trim() } catch { $CustomUrl = "" }

# 3. Build + deploy frontend
Set-Location $frontendDir

# Create environment files with deployed API URL
Write-Host "Setting API URL for production..." -ForegroundColor Yellow
$ApiBaseUrl = "$($ApiUrl.TrimEnd('/'))/api"
@"
export const environment = {
  apiBaseUrl: '$ApiBaseUrl',
};
"@ | Out-File src/environments/environment.ts -Encoding utf8
"NG_APP_API_BASE_URL=$ApiBaseUrl" | Out-File .env.production -Encoding utf8
"NG_APP_API_BASE_URL=$ApiBaseUrl" | Out-File .env -Encoding utf8

npm install
$env:NG_APP_API_BASE_URL = $ApiBaseUrl
npm run build
aws s3 sync .\dist\meridian-chat\browser "s3://$FrontendBucket/" --delete

Write-Host "Invalidating CloudFront cache..." -ForegroundColor Yellow
$DistributionId = (terraform -chdir=terraform output -raw cloudfront_distribution_id).Trim()
aws cloudfront create-invalidation --distribution-id $DistributionId --paths "/*" | Out-Null

Set-Location ..

# 4. Final summary
$CfUrl = terraform -chdir=terraform output -raw cloudfront_url
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "CloudFront URL : $CfUrl" -ForegroundColor Cyan
if ($CustomUrl) {
    Write-Host "Custom domain  : $CustomUrl" -ForegroundColor Cyan
}
Write-Host "API Gateway    : $ApiUrl" -ForegroundColor Cyan