# Dependencies
# zsh-syntax-hightlighing
# autojump
# zsh-autosuggestions
# starship prompt

# Enable colors and change prompt
autoload -U colors && colors
PS1="%B%{$fg[red]%}[%{$fg[yellow]%}%n%{$fg[green]%}@%{$fg[blue]%}%M %{$fg[magenta]%}%~%{$fg[red]%}]%{$reset_color%}$%b "

path+=('$HOME/.local/bin')

colorscript -r
# Start starship
eval "$(starship init zsh)"

# Custom variables
EDITOR=vim

# History
HISTSIZE=10000
SAVEHIST=10000
HISTFILE=~/.cache/zshhistory
setopt appendhistory
setopt HIST_SAVE_NO_DUPS 

# Basic auto/tab complete
autoload -U compinit

zstyle ':completion:*' menu select
zmodload zsh/complist
compinit
_comp_options+=(globdots) # include hidden files

# Custom Bindings
bindkey '^ ' autosuggest-accept

# Load aliases
[ -f "$HOME/.config/zsh/aliasrc" ] && source "$HOME/.config/zsh/aliasrc"

# Load zsh plugins
source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh 2>/dev/null
source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh 2>/dev/null
source /usr/share/autojump/autojump.zsh 2>/dev/null
