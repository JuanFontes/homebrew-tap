class Curlimp < Formula
  desc "HTTP client with browser profiles and response exports"
  homepage "https://juanfontes.github.io/curlimp/"
  version "0.5.1"
  license "MIT"

  on_macos do
    depends_on arch: :arm64
    depends_on macos: :ventura

    on_arm do
      url "https://github.com/JuanFontes/curlimp/releases/download/v0.5.1/curlimp-0.5.1-macos-arm64.tar.gz"
      sha256 "f3b8be54cf694e21a51021b788231c0dd3b1c64c354fc73be49a2e8ba8c41074"
    end
  end

  on_linux do
    on_intel do
      url "https://github.com/JuanFontes/curlimp/releases/download/v0.5.1/curlimp-0.5.1-linux-amd64.tar.gz"
      sha256 "fe949b33e69fff43d782b5d86b4e5da66ee0829046f4d19e62a963c71f47a1bf"
    end
    on_arm do
      url "https://github.com/JuanFontes/curlimp/releases/download/v0.5.1/curlimp-0.5.1-linux-arm64.tar.gz"
      sha256 "2a0b631b7069922d656091e440ac56308c3a3bceb31eb8abdee38a691efaca2b"
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
