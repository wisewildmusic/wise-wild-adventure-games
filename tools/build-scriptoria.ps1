# Builds the JavaScript adventure game's program for the server, site\scriptoria, with gcc in WSL (see build-scriptoria.sh,
# which does the work). Run it after changing anything in javascript\Scriptoria, then run check-js-questions.py.
# (On this PC there's nothing to build: tools\local_test_site.py runs the source with Node.js.)
# To get gcc, as for the C++ game (done on this PC on 2026-11-04):
#     wsl -d Ubuntu -u root -- bash -c "apt-get update && apt-get install -y --no-install-recommends g++"
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
wsl -d Ubuntu --cd $root -- bash tools/build-scriptoria.sh
if ($LASTEXITCODE) { throw "The Linux build failed" }
"site\scriptoria: {0:N1} MB" -f ((Get-Item (Join-Path $root "site\scriptoria")).Length / 1MB)
