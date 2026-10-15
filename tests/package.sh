#!/usr/bin/env bash
# Run only on disposable CI machines: this installs and removes the formula.
set -euo pipefail

formula=juanfontes/tap/curlimp
install_log="$(mktemp)"
trap 'rm -f "$install_log"' EXIT
brew install "$formula" | tee "$install_log"
grep -Fq 'source <(curlimp --completions zsh)' "$install_log"
installed_prefix="$(brew --prefix "$formula")"
installed_keg="$(cd "$installed_prefix" && pwd -P)"
brew_prefix="$(brew --prefix)"
brew test "$formula"

if [ "$(uname -s)" = Darwin ]; then
  archive="$(brew --cache "$formula")"
  unpacked="$(mktemp -d)"
  tar -xzf "$archive" -C "$unpacked"
  bundles=("$unpacked"/*)
  test "${#bundles[@]}" -eq 1
  cmp "${bundles[0]}/curlimp" "$installed_keg/libexec/curlimp"
  codesign --verify --strict "$installed_keg/libexec/curlimp"
  for library in "$installed_keg"/libexec/lib/*.dylib; do
    cmp "${bundles[0]}/lib/$(basename "$library")" "$library"
    codesign --verify --strict "$library"
  done
fi

test -x "$brew_prefix/bin/curlimp"
"$brew_prefix/bin/curlimp" --version
profiles="$("$brew_prefix/bin/curlimp" --complete-profiles chrome1)"
test -n "$profiles"
while IFS= read -r profile; do
  case "$profile" in
    chrome1*) ;;
    *) echo "Unexpected completion: $profile" >&2; exit 1 ;;
  esac
done <<< "$profiles"

completion="$brew_prefix/share/zsh/site-functions/_curlimp"
test -f "$completion"
# macOS has Zsh; Linux still verifies the installed completion and Rust backend.
if command -v zsh >/dev/null 2>&1; then
  CLI="$brew_prefix/bin/curlimp" COMPLETION_DIR="$brew_prefix/share/zsh/site-functions" \
    python3 tests/zsh_completion.py
fi

# Exercise TLS and the bundled certificate setup as well as the local HTTP test.
code="$("$brew_prefix/bin/curlimp" -sS --fail --max-time 30 \
  -o /dev/null -w '%{http_code}' https://httpbin.org/status/200)"
test "$code" = 200

brew uninstall "$formula"
test ! -e "$installed_prefix"
test ! -e "$installed_keg"
test ! -L "$brew_prefix/bin/curlimp"
test ! -e "$brew_prefix/bin/curlimp"
test ! -L "$completion"
test ! -e "$completion"
test ! -e "$brew_prefix/opt/curlimp"
test ! -L "$brew_prefix/opt/curlimp"
test -z "$(brew list --formula --versions curlimp)"
echo 'Verified install, HTTP/TLS, profiles, completion, and clean uninstall.'
