# Builds the VB.NET adventure game (vbnet\Visualia) twice:
#   - for the server: site\visualia, one self-contained Linux program that needs nothing installed
#     (deploy-site.sh installs it beside app.py);
#   - for this PC: vbnet\build\win\visualia.exe, used by tools\local_test_site.py and the checks.
# Run it after changing anything in vbnet\Visualia. The Linux build needs Microsoft's Linux runtime
# packages, which .NET keeps in this PC's NuGet cache once downloaded.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$project = Join-Path $root "vbnet\Visualia"

dotnet publish $project -c Release -r win-x64 --no-self-contained -o (Join-Path $root "vbnet\build\win") --nologo -v q
if ($LASTEXITCODE) { throw "The Windows build failed" }

$linux = Join-Path $root "vbnet\build\linux"
dotnet publish $project -c Release -r linux-x64 --self-contained -p:PublishSingleFile=true -p:PublishTrimmed=true -o $linux --nologo -v q
if ($LASTEXITCODE) { throw "The Linux build failed" }
Copy-Item (Join-Path $linux "visualia") (Join-Path $root "site\visualia") -Force

"site\visualia: {0:N1} MB" -f ((Get-Item (Join-Path $root "site\visualia")).Length / 1MB)
