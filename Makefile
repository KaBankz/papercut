.PHONY: build clean help dev install

# Build metadata - Single source of truth from pyproject.toml and git
PROJECT_NAME := $(shell grep '^name = ' pyproject.toml | cut -d'"' -f2)
VERSION := $(shell grep '^version = ' pyproject.toml | cut -d'"' -f2)
DESCRIPTION := $(shell grep '^description = ' pyproject.toml | cut -d'"' -f2)
LICENSE := $(shell grep '^license = ' pyproject.toml | cut -d'"' -f2)
AUTHORS := $(shell grep '^authors = ' pyproject.toml | sed -E 's/.*name = "([^"]*)".*email = "([^"]*)".*/\1 <\2>/' || echo "Unknown")
BUILD_DATE := $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")
VCS_REF := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Image configuration
IMAGE_NAME := $(PROJECT_NAME)
CONTAINER_NAME := $(PROJECT_NAME)
IMAGE_TAG := latest
REGISTRY := ghcr.io/kabankz

# Convert git remote URL to HTTPS format (handles both SSH and HTTPS)
# git@github.com:user/repo.git → https://github.com/user/repo
# https://github.com/user/repo.git → https://github.com/user/repo
VCS_URL := $(shell git config --get remote.origin.url 2>/dev/null | \
	sed -E 's|^git@github\.com:|https://github.com/|' | \
	sed -E 's|^git@gitlab\.com:|https://gitlab.com/|' | \
	sed 's/\.git$$//')

# Auto-generate title from project name (replace dashes with spaces, capitalize each word)
TITLE := $(shell echo $(PROJECT_NAME) | tr '-' ' ' | awk '{for(i=1;i<=NF;i++) $$i=toupper(substr($$i,1,1)) tolower(substr($$i,2))}1')

# Full image name
FULL_IMAGE_NAME := $(if $(REGISTRY),$(REGISTRY)/$(IMAGE_NAME),$(IMAGE_NAME))

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

dev: ## Run development server with auto-reload
	uv run uvicorn main:app --reload

clean: ## Clean up python environment
	rm -rdf .venv
	find . | grep -E "(__pycache__|\.pyc$$)" | xargs rm -rf
	@echo "✅ Python environment cleaned!"

build: ## Build the Docker image with OCI labels
	@echo "Building $(FULL_IMAGE_NAME):$(IMAGE_TAG)..."
	@echo "  Title: $(TITLE)"
	@echo "  Description: $(DESCRIPTION)"
	@echo "  Version: $(VERSION)"
	@echo "  Authors: $(AUTHORS)"
	@echo "  License: $(LICENSE)"
	@echo "  Build Date: $(BUILD_DATE)"
	@echo "  Git Commit: $(VCS_REF)"
	@echo "  Git Remote: $(VCS_URL)"
	@echo "Generating .dockerignore from .gitignore..."
	@cp .gitignore .dockerignore
	docker build \
		--build-arg TITLE="$(TITLE)" \
		--build-arg DESCRIPTION="$(DESCRIPTION)" \
		--build-arg VERSION=$(VERSION) \
		--build-arg AUTHORS="$(AUTHORS)" \
		--build-arg LICENSE=$(LICENSE) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg VCS_REF=$(VCS_REF) \
		--build-arg VCS_URL=$(VCS_URL) \
		-t $(FULL_IMAGE_NAME):$(IMAGE_TAG) \
		-t $(FULL_IMAGE_NAME):$(VERSION) \
		.
	@rm -f .dockerignore
	@echo "✅ Build complete!"
