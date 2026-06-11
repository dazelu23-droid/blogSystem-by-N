# Deploy to Cloudflare Workers + D1 (see SKILL.md)
# Prerequisites: Node.js 18+, npx wrangler login

Set-Location $PSScriptRoot

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js/npm required. Install from https://nodejs.org/"
    exit 1
}

npm install

$dbJson = npx wrangler d1 create simple-blog-db 2>&1 | Out-String
if ($dbJson -match '"database_id":\s*"([a-f0-9-]+)"') {
    $dbId = $Matches[1]
    $config = Get-Content wrangler.jsonc -Raw
    $config = $config -replace "PLACEHOLDER", $dbId
    Set-Content wrangler.jsonc $config -NoNewline
    Write-Host "Updated wrangler.jsonc with database_id: $dbId"
}

npx wrangler d1 execute simple-blog-db --remote --file=schema.sql -y
npx wrangler deploy

Write-Host "Upload SECRET_KEY secret:"
python -c "import secrets; print(secrets.token_hex(32))" | npx wrangler secret put SECRET_KEY

Write-Host "Done! Visit the URL printed above."
