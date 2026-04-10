Set-Location -Path $PSScriptRoot
Start-Process -FilePath "python" -ArgumentList "main.py --launcher" -WindowStyle Normal
