# Builds the C++ adventure game (cpp\Templaria) twice:
#   - for this PC: cpp\build\win\templaria.exe, with Microsoft's compiler (MSVC, from Visual Studio), used by
#     tools\local_test_site.py and the checks;
#   - for the server: site\templaria, with g++ in WSL, statically linked so that it's one program that needs
#     nothing installed and doesn't mind which Linux it finds (deploy-site.sh installs it beside app.py).
# Run it after changing anything in cpp\Templaria. Without g++ in WSL, it stops after the Windows build. To get g++
# (about 75 MB from Ubuntu's archive; done on this PC on 2026-11-04):
#     wsl -d Ubuntu -u root -- bash -c "apt-get update && apt-get install -y --no-install-recommends g++"
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path $root "cpp\Templaria"
$win = Join-Path $root "cpp\build\win"
$objects = Join-Path $win "obj"
New-Item -ItemType Directory -Force $objects | Out-Null

$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$vs = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vs) { throw "Visual Studio's C++ tools aren't installed" }
$vcvars = Join-Path $vs "VC\Auxiliary\Build\vcvars64.bat"

# (In a batch file, since Windows PowerShell mangles the quotes in a command this long given to cmd directly.)
$batch = Join-Path $objects "build.bat"
@"
@call "$vcvars" >nul 2>nul
@cl/nologo /std:c++20 /EHsc /O2 /W4 /permissive- /utf-8 /MT /Fe:"$win\templaria.exe" /Fo:"$objects\\" "$source\*.cpp"
"@ | Set-Content $batch -Encoding Ascii
cmd /c $batch
if ($LASTEXITCODE) { throw "The Windows build failed" }
"cpp\build\win\templaria.exe: {0:N1} MB" -f ((Get-Item (Join-Path $win "templaria.exe")).Length / 1MB)

wsl -d Ubuntu --cd $source -- which g++ | Out-Null
if ($LASTEXITCODE) {
    "No g++ in WSL, so the Linux program wasn't built (see the top of this script)."
    exit 0
}
$linux = Join-Path $root "cpp\build\linux"
New-Item -ItemType Directory -Force $linux | Out-Null
$sources = Get-ChildItem $source -Filter *.cpp | ForEach-Object { $_.Name }
wsl -d Ubuntu --cd $source -- g++ -std=c++20 -O2 -Wall -Wextra -static -s -o ../build/linux/templaria @sources
if ($LASTEXITCODE) { throw "The Linux build failed" }
Copy-Item (Join-Path $linux "templaria") (Join-Path $root "site\templaria") -Force
"site\templaria: {0:N1} MB" -f ((Get-Item (Join-Path $root "site\templaria")).Length / 1MB)
