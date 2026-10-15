class Curlimp < Formula
  desc "HTTP client with browser profiles and response exports"
  homepage "https://juanfontes.github.io/curlimp/"
  version "0.5.2"
  license "MIT"

  on_macos do
    depends_on arch: :arm64
    depends_on macos: :ventura

    on_arm do
      url "https://github.com/JuanFontes/curlimp/releases/download/v0.5.2/curlimp-0.5.2-macos-arm64.tar.gz"
      sha256 "5d4b70bb7bc7507061e1b681022dfa6b309a41a7d424a7c6bae243424df0d623"
    end
  end

  on_linux do
    on_intel do
      url "https://github.com/JuanFontes/curlimp/releases/download/v0.5.2/curlimp-0.5.2-linux-amd64.tar.gz"
      sha256 "57304096dae98248f9237f1233fe8c0c743db2a53bb495ea30c21c831a351fdd"
    end
    on_arm do
      url "https://github.com/JuanFontes/curlimp/releases/download/v0.5.2/curlimp-0.5.2-linux-arm64.tar.gz"
      sha256 "0cd4b335c7058f8b33c23b64ebd25719b555cb319ca5b6e1a9110bb43463e49c"
    end
  end

  # Keep the tested native library layout, signatures, licenses, and provenance.
  preserve_rpath
  skip_clean "libexec"

  def install
    libexec.install Dir["*"]
    bin.install_symlink libexec/"curlimp"
    zsh_completion.install libexec/"completions/zsh/_curlimp"
  end

  def caveats
    <<~EOS
      Zsh profile completion is installed. If your shell already uses compinit,
      activate it in your current Zsh session with:
        source <(curlimp --completions zsh)

      Then type curlimp followed by a space and press Tab to discover browser profiles.
      For shell setup and completion tips:
        https://juanfontes.github.io/curlimp/docs/completion/
    EOS
  end

  test do
    assert_match "curlimp #{version}", shell_output("#{bin}/curlimp --version")
    assert_match "firefox147", shell_output("#{bin}/curlimp --list-profiles")
    assert_path_exists zsh_completion/"_curlimp"

    require "socket"
    server = TCPServer.new("127.0.0.1", 0)
    port = server.addr[1]
    child = fork do
      socket = server.accept
      while (line = socket.gets) && line != "\r\n"
        # Read the request headers before writing the fixture response.
      end
      body = "curlimp-homebrew\n"
      socket.write "HTTP/1.1 200 OK\r\nContent-Length: #{body.bytesize}\r\nConnection: close\r\n\r\n#{body}"
      socket.close
      server.close
    end
    begin
      assert_equal "curlimp-homebrew\n", shell_output(
        "#{bin}/curlimp --noproxy '*' -sS --fail --max-time 10 http://127.0.0.1:#{port}/status/200",
      )
    ensure
      server.close
      Process.kill("TERM", child)
      Process.wait(child)
    end
  end
end
