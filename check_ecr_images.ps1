# Script to check what images/tags exist in ECR

$AWS_ACCOUNT_ID = "083738448444"
$AWS_REGION = "us-east-1"
$ECR_REPOSITORY_NAME = "portfolio-streamlit"

Write-Host "=== Checking ECR Repository ===" -ForegroundColor Cyan
Write-Host ""

# Check if repository exists
Write-Host "Checking repository..." -ForegroundColor Yellow
$repo = aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR - Repository does not exist!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Creating repository..." -ForegroundColor Yellow
    aws ecr create-repository --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION
    Write-Host "Repository created!" -ForegroundColor Green
} else {
    Write-Host "OK - Repository exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "Checking for images..." -ForegroundColor Yellow

# List images in repository
$images = aws ecr describe-images --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION 2>&1

if ($LASTEXITCODE -eq 0) {
    $imageData = $images | ConvertFrom-Json
    
    if ($imageData.imageDetails.Count -eq 0) {
        Write-Host "WARNING - No images found in repository!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "You need to push an image first. Options:" -ForegroundColor Yellow
        Write-Host "1. Use GitHub Actions workflow (recommended)" -ForegroundColor White
        Write-Host "2. Use build_then_push.ps1 script" -ForegroundColor White
        Write-Host "3. Use push_with_buildx.ps1 script" -ForegroundColor White
    } else {
        Write-Host "Found $($imageData.imageDetails.Count) image(s):" -ForegroundColor Green
        Write-Host ""
        
        foreach ($image in $imageData.imageDetails) {
            $tags = if ($image.imageTags) { $image.imageTags -join ", " } else { "(untagged)" }
            Write-Host "  Image: $tags" -ForegroundColor White
            Write-Host "    Pushed: $($image.imagePushedAt)" -ForegroundColor Gray
            Write-Host "    Size: $([math]::Round($image.imageSizeBytes / 1MB, 2)) MB" -ForegroundColor Gray
            Write-Host ""
        }
        
        Write-Host "Available tags for App Runner:" -ForegroundColor Cyan
        foreach ($image in $imageData.imageDetails) {
            if ($image.imageTags) {
                foreach ($tag in $image.imageTags) {
                    Write-Host "  - $tag" -ForegroundColor Green
                }
            }
        }
    }
} else {
    Write-Host "ERROR - Could not list images" -ForegroundColor Red
    Write-Host $images -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Repository URI: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}" -ForegroundColor White

