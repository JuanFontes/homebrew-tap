cask "alumia" do
  arch arm: "arm64", intel: "x64"

  version "0.1.0"
  sha256 arm:   "b7579035cfc5821acb58548181777d02e5e107378a8096b36570c7da41b54a29",
         intel: "1d86ffa7cb5502fc7002f5e06ab4c7f96d8f6a3cc1bbaa978e43f5140d50b123"

  url "https://github.com/JuanFontes/homebrew-tap/releases/download/alumia-v#{version}/Alumia-macOS-#{arch}.zip"
  name "Alumia"
  desc "IDE para aprender programação em português com execução e compilação offline"
  homepage "https://github.com/JuanFontes/homebrew-tap/releases/tag/alumia-v0.1.0"

  depends_on macos: :sonoma

  app "Alumia.app"

  caveats do
    <<~EOS
      O aplicativo usa assinatura ad hoc. O macOS pode pedir confirmação na primeira abertura.
    EOS
  end
end
