# Builds the ASP.NET adventure game (aspnet\Razoria) twice:
#   - for the server: site\razoria, one self-contained Linux program that needs nothing installed
#     (deploy-site.sh installs it beside app.py);
#   - for this PC: aspnet\build\win\razoria.exe, used by tools\local_test_site.py and the checks.
# Run it after changing anything in aspnet\Razoria. The Linux build needs Microsoft's Linux runtime
# packages, which .NET keeps in this PC's NuGet cache once downloaded.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$project = Join-Path $root "aspnet\Razoria"

dotnet publish $project -c Release -r win-x64 --no-self-contained -o (Join-Path $root "aspnet\build\win") --nologo -v q
if ($LASTEXITCODE) { throw "The Windows build failed" }

$linux = Join-Path $root "aspnet\build\linux"
dotnet publish $project -c Release -r linux-x64 --self-contained -p:PublishSingleFile=true -p:PublishTrimmed=true -o $linux --nologo -v q
if ($LASTEXITCODE) { throw "The Linux build failed" }
Copy-Item (Join-Path $linux "razoria") (Join-Path $root "site\razoria") -Force

"site\razoria: {0:N1} MB" -f ((Get-Item (Join-Path $root "site\razoria")).Length / 1MB)
