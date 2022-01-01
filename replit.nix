{ pkgs }: {
  deps = [
    pkgs.python39
    pkgs.python39Packages.discordpy
    pkgs.python39Packages.aiosqlite
    pkgs.python39Packages.roman
  ];
}
