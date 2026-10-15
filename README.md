# Homebrew tap

[![CI](https://github.com/JuanFontes/homebrew-tap/actions/workflows/ci.yml/badge.svg)](https://github.com/JuanFontes/homebrew-tap/actions/workflows/ci.yml)
[![Release updates](https://github.com/JuanFontes/homebrew-tap/actions/workflows/update.yml/badge.svg)](https://github.com/JuanFontes/homebrew-tap/actions/workflows/update.yml)

Install [Curlimp](https://github.com/JuanFontes/curlimp), an HTTP client with browser profiles, familiar curl-style commands, and response exports.

## Install

With [Homebrew](https://brew.sh/) already installed:

```sh
brew install juanfontes/tap/curlimp
curlimp --version
curlimp -sS -I https://httpbin.org/status/200
curlimp firefox147 -sS -i https://httpbin.org/status/418
```

The fully qualified command adds this tap and installs Curlimp. No separate `brew tap` command is needed.

| Platform | Package | CI validation |
| --- | --- | --- |
| macOS Apple Silicon | ARM64, experimental | macOS 15 |
| Linux Intel / AMD | amd64 | Ubuntu 24.04 |
| Linux ARM64 | arm64 | Ubuntu 24.04 ARM |
| macOS Intel / Windows | Not available through this tap | — |

The formula downloads the corresponding **published native release**, verifies its SHA-256 checksum, and keeps its bundled libraries and notices. It does not compile the Rust CLI or native engine during installation. macOS requires Ventura or later; the package is ad-hoc signed, not notarized. This is a project-maintained tap, separate from `homebrew/core`.

## Zsh completion

The formula installs the completion file into Homebrew's standard Zsh directory. If your shell already loads Homebrew completions, start a new shell and try typing `curlimp chrome1` followed by Tab.

**Installed from a terminal that is still open?** That session has not registered the new completion yet. Open a new tab, or register it immediately in the current Zsh session:

```zsh
source <(curlimp --completions zsh)
zstyle ':completion:*:curlimp:*' menu yes select
```

This assumes your shell already initialized completion with `compinit`. The second line enables the selection menu for Curlimp. Without that setting, Zsh may complete only the shared prefix on the first Tab (`chrom` becomes `chrome`); press Tab again to see the versions. For a unique match, `curlimp chrome15` + Tab inserts `chrome150`. To keep the menu preference, add the `zstyle` line to `~/.zshrc`.

Otherwise, add this to `~/.zshrc` **before any existing `compinit` call**, or use the full block if you do not have one:

```zsh
fpath=("$(brew --prefix)/share/zsh/site-functions" $fpath)
autoload -Uz compinit
compinit
```

You do not need to source `curlimp --completions zsh` separately. The installer does not modify shell configuration files. See the [completion guide](https://juanfontes.github.io/curlimp/docs/completion/) for profile filtering and shell setup.

## Upgrade

```sh
brew update
brew upgrade curlimp
```

## Uninstall

```sh
brew uninstall curlimp
```

Homebrew removes the installed package, executable link, and managed completion file. It does not delete response files you created, edit your shell configuration, remove the tap, or clear Homebrew's download cache. To remove this tap as well:

```sh
brew untap juanfontes/tap
```

CI checks installation, local HTTP, HTTPS, profile completion, and removal of the package and links on all three supported architectures. Runners with Zsh also press real Tab keys in a pseudo-terminal to test the installed completion, menu selection, and registration in a session opened before installation.

## Release maintenance

The **Update Curlimp** workflow checks the latest stable release of [`JuanFontes/curlimp`](https://github.com/JuanFontes/curlimp/releases) hourly. GitHub may delay scheduled jobs or disable them after repository inactivity; maintainers can also run the workflow manually. Enable **verify_current** to verify the current release and exercise the candidate-testing pipeline without making a version change.

For a new version, the workflow:

1. Rejects draft, prerelease, incomplete, malformed, or older releases.
2. Downloads all three archives and verifies their sizes and hashes against both GitHub's asset digests and `SHA256SUMS`.
3. Runs formula style checks and installation, usage, and uninstall tests on native macOS ARM64, Linux amd64, and Linux arm64 runners.
4. Commits the exact tested formula only after every platform passes. A concurrent change to `main` makes the push fail safely; the next run starts from the new commit.

The workflow uses this repository's `GITHUB_TOKEN`; no cross-repository write credential is needed. Token-created commits do not trigger a second CI run: the candidate has already passed the same package checks before publication. Dependabot proposes Action and lint-tool updates; those still go through CI.

Local maintainer checks, without installing Curlimp:

```sh
python3 -m unittest discover -s tests -v
ruby -c Formula/curlimp.rb
python3 scripts/update_formula.py --verify-current
```

`tests/package.sh` installs and uninstalls Curlimp and is intended for disposable CI runners.

## Links and license

- [Curlimp documentation](https://juanfontes.github.io/curlimp/)
- [Curlimp source and releases](https://github.com/JuanFontes/curlimp)
- [Report a packaging problem](https://github.com/JuanFontes/homebrew-tap/issues)

Tap code is MIT-licensed. The installed native packages retain their component licenses, attribution notices, and provenance files under the formula's `libexec` directory.
