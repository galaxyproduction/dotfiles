# Hunter Wilkins dotfiles
To install dotfiles, install `stow` and necessary dependencies

Then run
```
git clone https://github.com/galaxyproduction/dotfiles.git .dotfiles
cd .dotfiles
stow [dotfiles to install]
```
## Dependencies
- zsh
    - zsh-syntax-hightlighing
    - auto-jump
    - zsh-autosuggestions
    - [starship](https://starship.rs/)
    - nerd fonts
- git
    - gpg2
    - Create gpg key
    - `cp git/.config/git/example_config git/.config/git/config`
    - Change user key id in config to new gpg key id