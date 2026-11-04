#!/bin/bash
# Builds the JavaScript adventure game's Linux program, site/scriptoria. Run it in WSL through build-scriptoria.ps1.
#
# The game is JavaScript, and it needs an engine to run it. QuickJS (by Fabrice Bellard and Charlie Gordon, MIT licence) is
# a small one, written in C. Its compiler, qjsc, turns the game's modules into bytecode inside a C file, and gcc compiles
# that with QuickJS itself into one program, statically linked, so that it needs nothing installed and doesn't mind which
# Linux it finds. Nothing else is needed but gcc, which comes with the g++ the C++ game's build uses.
#
# QuickJS's source is kept as the very file that was downloaded, checked here against its fingerprint, and unpacked
# fresh in a temporary folder for each build. To move to a newer one, download it from https://bellard.org/quickjs/ to
# javascript/build/quickjs/ and change these two lines:
VERSION=2026-06-04
SHA256=b376e839b322978313d929fd20663b11ba58b75df5a46c126dd19ea2fa70ad2a
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
archive="$root/javascript/build/quickjs/quickjs-$VERSION.tar.xz"
echo "$SHA256  $archive" | sha256sum --check --quiet

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
tar -xJf "$archive" -C "$work"
engine="$work/quickjs-$VERSION"
cp "$root"/javascript/Scriptoria/*.js "$work/"

flags=(-O2 -fwrapv -w -D_GNU_SOURCE "-DCONFIG_VERSION=\"$VERSION\"")
parts=(quickjs dtoa libregexp libunicode cutils quickjs-libc)
libraries=(-lm -ldl -lpthread)

cd "$engine"
objects=()
for part in "${parts[@]}"; do
  gcc "${flags[@]}" -c "$part.c" -o "$part.o"
  objects+=("$engine/$part.o")
done
gcc "${flags[@]}" '-DCONFIG_CC="gcc"' '-DCONFIG_PREFIX="/usr/local"' -c qjsc.c -o qjsc.o
gcc qjsc.o "${objects[@]}" "${libraries[@]}" -o qjsc

cd "$work"
"$engine/qjsc" -e -m -o scriptoria.c main-quickjs.js
gcc "${flags[@]}" "-I$engine" -c scriptoria.c -o scriptoria.o
# (The linker warns about dlopen in a static program. That's harmless: it's how QuickJS would load a C library, which the
# game never asks it to.)
gcc -static -s scriptoria.o "${objects[@]}" "${libraries[@]}" -o scriptoria

cp scriptoria "$root/site/scriptoria"
ls -l "$root/site/scriptoria"
