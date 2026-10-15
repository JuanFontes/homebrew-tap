"""Press real Tab keys against the installed Homebrew completion and executable."""

import os
import pty
import select
import shlex
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

CLI = Path(os.environ["CLI"]).absolute()
COMPLETION = Path(os.environ["COMPLETION_DIR"]) / "_curlimp"


class InstalledCompletion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The engine catalog is independent of the Rust completion dispatcher.
        profiles = subprocess.check_output([str(CLI), "--list-profiles"], text=True).splitlines()
        cls.prefix, cls.match = next(
            (profile[:-1], profile)
            for profile in profiles
            if len(profile) > 1 and sum(p.startswith(profile[:-1]) for p in profiles) == 1
        )
        cls.chrome = sorted(profile for profile in profiles if profile.startswith("chrom"))

    def start_shell(self, *, before_install=False, menu=False):
        temporary = tempfile.TemporaryDirectory(prefix="curlimp-homebrew-zsh-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        completion_dir = self.root if before_install else COMPLETION.parent
        pid, self.fd = pty.fork()
        if pid == 0:
            os.environ.update(HOME=str(self.root), ZDOTDIR=str(self.root), TERM="xterm")
            os.environ.pop("FPATH", None)
            os.chdir(self.root)
            os.execv(shutil.which("zsh"), ["zsh", "-f", "-i"])

        def stop():
            os.close(self.fd)
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            os.waitpid(pid, 0)

        self.addCleanup(stop)
        self.drain()
        setup = (
            f"path=({shlex.quote(str(CLI.parent))} $path); "
            f"fpath=({shlex.quote(str(completion_dir))} $fpath); "
            "zmodload zsh/complist; autoload -Uz compinit; compinit -D; "
            "PROMPT='ready> '; RPROMPT=''; LISTMAX=0; "
            "capture_buffer() { print -rn -- $'\\x1eBUFFER:'; "
            "print -rn -- $BUFFER; print -r -- $'\\x1f'; BUFFER=''; zle redisplay; }; "
            "zle -N capture_buffer; bindkey '^X' capture_buffer; "
        )
        if menu:
            setup += "zstyle ':completion:*:curlimp:*' menu yes select; "
        self.run_command(setup)

    def drain(self, timeout=0.15):
        data = b""
        while select.select([self.fd], [], [], timeout)[0]:
            try:
                data += os.read(self.fd, 65536)
            except OSError:
                break
            timeout = 0.03
        return data

    def until(self, marker):
        data = b""
        deadline = time.monotonic() + 10
        while marker not in data and time.monotonic() < deadline:
            data += self.drain()
        self.assertIn(marker, data, data.decode(errors="replace"))
        return data

    def run_command(self, command):
        os.write(self.fd, (command + " printf '\\x1eREADY\\x1f\\n'\n").encode())
        self.until(b"\x1eREADY\x1f")
        self.drain()

    def buffer_after(self, keys, *, accept_menu=False):
        os.write(self.fd, keys)
        screen = self.drain(timeout=1)
        if accept_menu:
            os.write(self.fd, b"\r")
            screen += self.drain()
        os.write(self.fd, b"\x18")
        screen += self.until(b"\x1eBUFFER:")
        if b"\x1f" not in screen.split(b"\x1eBUFFER:", 1)[1]:
            screen += self.until(b"\x1f")
        buffer = screen.split(b"\x1eBUFFER:", 1)[1].split(b"\x1f", 1)[0].decode()
        return buffer, screen

    def test_installed_file_completes_a_unique_profile(self):
        self.start_shell()
        buffer, _ = self.buffer_after(f"curlimp {self.prefix}\t".encode())
        self.assertEqual(buffer, f"curlimp {self.match} ")

    def test_menu_lists_matching_browsers_and_keeps_the_command_in_the_editor(self):
        self.start_shell(menu=True)
        buffer, screen = self.buffer_after(b"curlimp chrom\t", accept_menu=True)
        self.assertGreater(len(self.chrome), 1)
        self.assertIn(self.chrome[0].encode(), screen)
        self.assertIn(self.chrome[-1].encode(), screen)
        self.assertEqual(buffer, f"curlimp {self.chrome[0]} ")

    def test_existing_session_needs_registration_after_installation(self):
        self.start_shell(before_install=True)
        shutil.copy2(COMPLETION, self.root / "_curlimp")
        buffer, _ = self.buffer_after(f"curlimp {self.prefix}\t".encode())
        self.assertEqual(buffer, f"curlimp {self.prefix}")
        self.run_command("source <(curlimp --completions zsh);")
        buffer, _ = self.buffer_after(f"curlimp {self.prefix}\t".encode())
        self.assertEqual(buffer, f"curlimp {self.match} ")


if __name__ == "__main__":
    unittest.main(verbosity=2)
