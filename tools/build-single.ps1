$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$html = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $root "index.html")
$css = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $root "css/style.css")
$scripts = @(
  "js/cards.js",
  "js/rules.js",
  "js/storage.js",
  "js/game.js",
  "js/renderer.js",
  "js/interactions.js",
  "js/main.js"
) | ForEach-Object { Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $root $_) }
$html = $html -replace '<link rel="stylesheet" href="css/style.css">', "<style>`n$css`n</style>"
$html = $html -replace '(?m)^\s*<script defer src="js/[^\"]+"></script>\s*$', ''
$bundle = [string]::Join("`n", $scripts)
$html = $html -replace '</body>', "<script>`n$bundle`n</script>`n</body>"
[System.IO.File]::WriteAllText((Join-Path $root "solitaire.html"), $html, [System.Text.UTF8Encoding]::new($false))
Write-Output "Generated solitaire.html"
