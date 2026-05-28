# devcontainer.mk is sub makefile about devcontainer commands.
#
# Authors:
#   - Xavier Beheydt <xavier.beheydt@gmail.com>

# Available presets: tmux-neovim, vscode
PRESET ?= tmux-neovim

DEVCONTAINER_CONFIG = .devcontainer/$(PRESET)/devcontainer.json
DEVCONTAINER_COMPOSE = .devcontainer/$(PRESET)/docker-compose.dev.yml

DEVCONTAINER_EXEC_CMD ?= nvim .

.PHONY: devcontainer/exec
devcontainer/exec:  ## Exec a command in the devcontainer (PRESET=tmux-neovim|vscode, CMD=nvim .)
	devcontainer exec --workspace-folder . --config $(DEVCONTAINER_CONFIG) -- $(DEVCONTAINER_EXEC_CMD)

.PHONY: devcontainer/build
devcontainer/build:  ## Build the devcontainer image (PRESET=tmux-neovim|vscode)
	devcontainer build --workspace-folder . --config $(DEVCONTAINER_CONFIG)

.PHONY: devcontainer/up
devcontainer/up:  ## Start the devcontainer (PRESET=tmux-neovim|vscode)
	devcontainer up --workspace-folder . --config $(DEVCONTAINER_CONFIG)

.PHONY: devcontainer/stop
devcontainer/stop:  ## Stop the devcontainer services (PRESET=tmux-neovim|vscode)
	docker compose -f $(DEVCONTAINER_COMPOSE) -f docker-compose.yml stop

.PHONY: devcontainer/down
devcontainer/down:  ## Stop and remove the devcontainer services and volumes (PRESET=tmux-neovim|vscode)
	docker compose -f $(DEVCONTAINER_COMPOSE) -f docker-compose.yml down -v
