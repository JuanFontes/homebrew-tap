#!/usr/bin/env bash
# Install/uninstall check for disposable CI runners only.
set -euo pipefail
brew install juanfontes/tap/dutop
brew test juanfontes/tap/dutop
"$(brew --prefix)/bin/dutop" --help
brew uninstall dutop
test ! -e "$(brew --prefix)/bin/dutop"
