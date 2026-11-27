class Dutop < Formula
  desc "Big folders, big files, and complete disk usage in two ranked panels"
  homepage "https://github.com/JuanFontes/dutop"
  version "0.1.0"
  license "MIT"

  on_macos do
    depends_on macos: :ventura
    on_arm do
      url "https://github.com/JuanFontes/dutop/releases/download/v0.1.0/dutop-0.1.0-aarch64-apple-darwin.tar.gz"
      sha256 "00c03f70a067007fb826d1665c0e0ca55e9ca8236d6ce648db81fa571d85db9c"
    end
    on_intel do
      url "https://github.com/JuanFontes/dutop/releases/download/v0.1.0/dutop-0.1.0-x86_64-apple-darwin.tar.gz"
      sha256 "ee4af3d0979fd0ad3683ee4556eb75b6f8f75453a97b3396bd45964e6bfea615"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/JuanFontes/dutop/releases/download/v0.1.0/dutop-0.1.0-aarch64-unknown-linux-musl.tar.gz"
      sha256 "ab559973e5475e0fa9cb7d072d391b34e75105868a1a92afbbb12fa35085f467"
    end
    on_intel do
      url "https://github.com/JuanFontes/dutop/releases/download/v0.1.0/dutop-0.1.0-x86_64-unknown-linux-musl.tar.gz"
      sha256 "220f72c6d227cb3da88fbc38755b9c6ef0efd00333634f44721425459582ae6a"
    end
  end

  def install
    bin.install "dutop"
    pkgshare.install "licenses"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/dutop --version")
    (testpath/"sample/folder").mkpath
    (testpath/"sample/folder/data").write("x" * 8192)
    (testpath/"sample/file").write("x" * 4096)
    output = shell_output("#{bin}/dutop --top 4 #{testpath}/sample")
    assert_match "FOLDERS 1 / 1", output
    assert_match "FILES 1 / 1", output
    assert_match "TOTAL", output
    assert_match "folder/", output
    assert_match "between 1 and 99", shell_output("#{bin}/dutop --top 100 2>&1", 2)
  end
end
