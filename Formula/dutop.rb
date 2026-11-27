class Dutop < Formula
  desc "Big folders, big files, and complete disk usage in two ranked panels"
  homepage "https://github.com/JuanFontes/dutop"
  version "0.1.0-beta.1"
  license "MIT"

  on_macos do
    depends_on macos: :ventura
    on_arm do
      url "https://github.com/JuanFontes/dutop/releases/download/v0.1.0-beta.1/dutop-0.1.0-beta.1-aarch64-apple-darwin.tar.gz"
      sha256 "38490cb7c78173d68164c359641d39af4ae7f17d9c74db9ab04584d5ff891cfe"
    end
    on_intel do
      url "https://github.com/JuanFontes/dutop/releases/download/v0.1.0-beta.1/dutop-0.1.0-beta.1-x86_64-apple-darwin.tar.gz"
      sha256 "8023c0df816a41e58eac3265d022f0b38d57ddb2d998bc31106f3431c3803595"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/JuanFontes/dutop/releases/download/v0.1.0-beta.1/dutop-0.1.0-beta.1-aarch64-unknown-linux-musl.tar.gz"
      sha256 "032b6552ff46b17ce10318408e4b0d6a6f73b52599c41643fcd8fb252d0833ec"
    end
    on_intel do
      url "https://github.com/JuanFontes/dutop/releases/download/v0.1.0-beta.1/dutop-0.1.0-beta.1-x86_64-unknown-linux-musl.tar.gz"
      sha256 "0e438974aa9a460c6f39874a51a155016a9f55ac577b269b83fa45c6c49369b7"
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
