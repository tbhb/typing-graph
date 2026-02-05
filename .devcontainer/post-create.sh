#!/bin/bash
# Post-create setup for typing-graph devcontainer
set -e

# ------------------------------------------------------------------------------
# Fix permissions on volumes (created as root)
# ------------------------------------------------------------------------------
if [ -d /workspaces/typing-graph/node_modules ]; then
    sudo chown -R vscode:vscode /workspaces/typing-graph/node_modules
fi
if [ -d /workspaces/typing-graph/.venv ]; then
    sudo chown -R vscode:vscode /workspaces/typing-graph/.venv
fi

# ------------------------------------------------------------------------------
# Ensure directories exist (home volume may be empty on first run)
# ------------------------------------------------------------------------------
mkdir -p ~/.local/share/bash-completion/completions
mkdir -p ~/.zfunc

# ------------------------------------------------------------------------------
# Just completions
# ------------------------------------------------------------------------------
just --completions bash > ~/.local/share/bash-completion/completions/just
just --completions zsh > ~/.zfunc/_just

# ------------------------------------------------------------------------------
# Zsh configuration (only add if not already configured)
# ------------------------------------------------------------------------------
if ! grep -q "# typing-graph devcontainer config" ~/.zshrc 2>/dev/null; then
    cat >> ~/.zshrc << 'EOF'

# typing-graph devcontainer config
# History
HISTSIZE=10000
SAVEHIST=10000
setopt SHARE_HISTORY
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_SPACE

# Completions
fpath=(~/.zfunc $fpath)
autoload -Uz compinit && compinit

# Plugins (installed via apt)
source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

# Starship prompt
eval "$(starship init zsh)"
EOF
fi

# ------------------------------------------------------------------------------
# Bash configuration (only add if not already configured)
# ------------------------------------------------------------------------------
if ! grep -q "# typing-graph devcontainer config" ~/.bashrc 2>/dev/null; then
    cat >> ~/.bashrc << 'EOF'

# typing-graph devcontainer config
# History
HISTSIZE=10000
HISTFILESIZE=10000
HISTCONTROL=ignoreboth:erasedups
shopt -s histappend
PROMPT_COMMAND="history -a; history -c; history -r; $PROMPT_COMMAND"

# Starship prompt
eval "$(starship init bash)"
EOF
fi

# ------------------------------------------------------------------------------
# Install project dependencies
# Run directly instead of `just install` to handle non-TTY environment
# ------------------------------------------------------------------------------
pnpm install --frozen-lockfile --config.confirmModulesPurge=false
uv sync --frozen
