$headers = @{
  'Authorization' = 'token ITsadi@1256'
  'Accept' = 'application/vnd.github.v3+json'
}

$body = @{
  'name' = 'AI-Resume-Enhancer'
  'description' = 'AI Resume Analyzer and Enhancer'
  'private' = $false
} | ConvertTo-Json

try {
  $response = Invoke-RestMethod -Uri 'https://api.github.com/user/repos' -Method Post -Headers $headers -Body $body
  Write-Host "Repository created successfully!"
  Write-Host "Repository URL: $($response.clone_url)"
  Write-Host "HTML URL: $($response.html_url)"
} catch {
  Write-Host "Error creating repository: $($_.Exception.Message)"
}
