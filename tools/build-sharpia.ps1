# Builds the C# adventure game (csharp\Sharpia) twice:
#   - for the server: site\sharpia, one self-contained Linux program that needs nothing installed
#     (deploy-site.sh installs it beside app.py);
#   - for this PC: csharp\build\win\sharpia.exe, used by tools\local_test_site.py and the checks.
# Run it after changing anything in csharp\Sharpia. The Linux build needs Microsoft's Linux runtime
# packages, which .NET keeps in this PC's NuGet cache once downloaded.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$project = Join-Path $root "csharp\Sharpia"

dotnet publish $project -c Release -r win-x64 --no-self-contained -o (Join-Path $root "csharp\build\win") --nologo -v q
if ($LASTEXITCODE) { throw "The Windows build failed" }

$linux = Join-Path $root "csharp\build\linux"
dotnet publish $project -c Release -r linux-x64 --self-contained -p:PublishSingleFile=true -p:PublishTrimmed=true -o $linux --nologo -v q
if ($LASTEXITCODE) { throw "The Linux build failed" }
Copy-Item (Join-Path $linux "sharpia") (Join-Path $root "site\sharpia") -Force

"site\sharpia: {0:N1} MB" -f ((Get-Item (Join-Path $root "site\sharpia")).Length / 1MB)
