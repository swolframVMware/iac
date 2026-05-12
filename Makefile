.PHONY: help install-deps install-deps-dev install-deps-docs compile-deps compile-deps-dev compile-deps-docs compile-deps-all upgrade-deps upgrade-deps-dev upgrade-deps-docs upgrade-deps-all sync-deps build install uninstall list-modules test-sanity clean dev dev-clean format lint check fix docs-install docs-compile docs-upgrade docs-serve docs-serve-live docs-build docs-uninstall docs-patch-template

COLLECTION := broadcom.vcf
VENV_PATH := .venv
PYTHON := $(VENV_PATH)/bin/python3
PIP := $(VENV_PATH)/bin/pip
ANSIBLE_GALAXY := $(VENV_PATH)/bin/ansible-galaxy
ANSIBLE_DOC := $(VENV_PATH)/bin/ansible-doc
ANSIBLE_TEST := $(VENV_PATH)/bin/ansible-test
RUFF := $(VENV_PATH)/bin/ruff
MKDOCS := $(VENV_PATH)/bin/mkdocs
REQUIREMENTS := requirements.txt
REQUIREMENTS_DEV := test-requirements.txt
REQUIREMENTS_IN := requirements.in
REQUIREMENTS_DEV_IN := test-requirements.in
REQUIREMENTS_DOCS := docs-requirements.txt
REQUIREMENTS_DOCS_IN := docs-requirements.in
PROJECT_PATH := .
COLLECTIONS_ROOT := $(PROJECT_PATH)/collections
COLLECTION_PATH := $(COLLECTIONS_ROOT)/ansible_collections/$(subst .,/,$(COLLECTION))
NAMESPACE_PATH := $(patsubst %/,%,$(dir $(COLLECTION_PATH)))
DEV_COLLECTIONS_ROOT := $(HOME)/.ansible/dev_collections
DEV_COLLECTION_PATH := $(DEV_COLLECTIONS_ROOT)/ansible_collections/$(subst .,/,$(COLLECTION))
DEV_NAMESPACE_PATH := $(patsubst %/,%,$(dir $(DEV_COLLECTION_PATH)))

help:
	@echo "Available targets:"
	@echo ""
	@echo "Environment:"
	@echo "  venv                 - Create virtual environment."
	@echo ""
	@echo "Dependencies:"
	@echo "  install-deps         - Install dependencies."
	@echo "  install-deps-dev     - Install development dependencies."
	@echo "  install-deps-docs    - Install documentation dependencies."
	@echo "  sync-deps            - Sync environment to exact dependency versions."
	@echo "  compile-deps   	  - Compile dependencies from requirements.in file."
	@echo "  compile-deps-dev     - Compile development dependencies from test-requirements.in file."
	@echo "  compile-deps-docs    - Compile documentation dependencies from docs-requirements.in."
	@echo "  compile-deps-all     - Compile all dependency *requirements.in files."
	@echo "  upgrade-deps         - Upgrade all dependencies to latest versions."
	@echo "  upgrade-deps-dev     - Upgrade all development dependencies to latest versions."
	@echo "  upgrade-deps-docs    - Upgrade documentation dependencies to latest versions."
	@echo "  upgrade-deps-all     - Upgrade all dependencies to latest versions."
	@echo ""
	@echo "Development:"
	@echo "  build                - Build the collection."
	@echo "  install              - Install the collection."
	@echo "  uninstall            - Uninstall the collection."
	@echo "  list-modules         - List collection modules."
	@echo "  clean                - Remove the collection artifacts."
	@echo "  dev                  - Set up development symlink (no build/install needed)."
	@echo "  dev-clean            - Remove development symlink and ansible.cfg."
	@echo "  format               - Format with ruff."
	@echo "  lint                 - Lint with ruff."
	@echo "  check                - Check format and lint with ruff (no changes)."
	@echo "  fix                  - Auto-fix issues with ruff."
	@echo ""
	@echo "Documentation:"
	@echo "  docs-install         - Install documentation dependencies."
	@echo "  docs-serve           - Serve documentation locally."
	@echo "  docs-serve-live      - Serve documentation with live reload."
	@echo "  docs-build           - Build documentation."
	@echo "  docs-uninstall       - Uninstall documentation dependencies."
	@echo "  docs-patch-template  - Patch mkdocs-ansible-collection jinja template."
	@echo ""

install-deps:
	@echo "→ Installing dependencies from $(REQUIREMENTS)..."
	$(PIP) install -r $(PROJECT_PATH)/$(REQUIREMENTS)
	@echo "✓ Dependencies installed."

install-deps-dev:
	@echo "→ Installing development dependencies from $(REQUIREMENTS_DEV)..."
	$(PIP) install -r $(PROJECT_PATH)/$(REQUIREMENTS_DEV)
	@echo "✓ Development dependencies installed."

install-deps-docs:
	@echo "→ Installing documentation dependencies from $(REQUIREMENTS_DOCS)..."
	$(PIP) install -r $(PROJECT_PATH)/$(REQUIREMENTS_DOCS)
	@echo "✓ Documentation dependencies installed."

sync-deps:
	@echo "→ Syncing environment to exact dependency versions..."
	cd $(PROJECT_PATH) && pip-sync $(REQUIREMENTS_DEV)
	@echo "✓ Environment synced."

compile-deps:
	@echo "→ Compiling $(REQUIREMENTS) from $(REQUIREMENTS_IN)..."
	cd $(PROJECT_PATH) && pip-compile $(REQUIREMENTS_IN) --output-file=$(REQUIREMENTS) --resolver=backtracking
	@echo "✓ Created $(PROJECT_PATH)/$(REQUIREMENTS)."

compile-deps-dev:
	@echo "→ Compiling $(REQUIREMENTS_DEV) from $(REQUIREMENTS_DEV_IN)..."
	cd $(PROJECT_PATH) && pip-compile $(REQUIREMENTS_DEV_IN) --output-file=$(REQUIREMENTS_DEV) --resolver=backtracking
	@echo "✓ Created $(PROJECT_PATH)/$(REQUIREMENTS_DEV)."

compile-deps-docs:
	@echo "→ Compiling $(REQUIREMENTS_DOCS) from $(REQUIREMENTS_DOCS_IN)..."
	cd $(PROJECT_PATH) && pip-compile $(REQUIREMENTS_DOCS_IN) --output-file=$(REQUIREMENTS_DOCS) --resolver=backtracking
	@echo "✓ Created $(PROJECT_PATH)/$(REQUIREMENTS_DOCS)."

compile-deps-all: compile-deps compile-deps-dev
	@echo "✓ All dependency requirements compiled.".

upgrade-deps:
	@echo "→ Upgrading dependencies..."
	cd $(PROJECT_PATH) && pip-compile $(REQUIREMENTS_IN) --output-file=$(REQUIREMENTS) --upgrade --resolver=backtracking
	@echo "✓ Dependencies upgraded."

upgrade-deps-dev:
	@echo "→ Upgrading development dependencies..."
	cd $(PROJECT_PATH) && pip-compile $(REQUIREMENTS_DEV_IN) --output-file=$(REQUIREMENTS_DEV) --upgrade --resolver=backtracking
	@echo "✓ Development dependencies upgraded."

upgrade-deps-docs:
	@echo "→ Upgrading documentation dependencies..."
	cd $(PROJECT_PATH) && pip-compile $(REQUIREMENTS_DOCS_IN) --output-file=$(REQUIREMENTS_DOCS) --upgrade --resolver=backtracking
	@echo "✓ Documentation dependencies upgraded."

upgrade-deps-all: upgrade-deps upgrade-deps-dev upgrade-deps-docs
	@echo "✓ All dependencies upgraded."

build: clean
	@echo "→ Building collection $(COLLECTION)..."
	$(ANSIBLE_GALAXY) collection build --force

install:
	@echo "→ Installing $(COLLECTION)..."
	@$(ANSIBLE_GALAXY) collection install . -p $(COLLECTIONS_ROOT) --force
	@echo "✓ Installed collection."

uninstall:
	@echo "→ Checking for $(COLLECTION)..."
	@if [ -d $(COLLECTION_PATH) ]; then \
		echo "→ Removing $(COLLECTION)..."; \
		rm -rf $(COLLECTION_PATH); \
		rmdir $(NAMESPACE_PATH) 2>/dev/null || true; \
		rmdir $(COLLECTIONS_ROOT)/ansible_collections 2>/dev/null || true; \
		echo "✓ Collection removed from $(COLLECTIONS_ROOT)/"; \
	else \
		echo "ℹ Collection $(COLLECTION) is not installed."; \
	fi

list-modules:
	@echo "→ Listing modules in collection $(COLLECTION)..."
	$(ANSIBLE_DOC) -l $(COLLECTION)

test-sanity: uninstall install
	@echo "→ Running ansible-test sanity (skipping import tests)..."
	@cd $(COLLECTION_PATH) && \
		$(ANSIBLE_TEST) sanity --docker default -v --skip-test import
	@echo "✓ Sanity tests completed."

clean:
	@echo "→ Removing collection artifacts..."
	@TARBALLS=$$(ls $(subst .,-, $(COLLECTION))-*.tar.gz 2>/dev/null); \
	if [ -n "$$TARBALLS" ]; then \
		echo "→ Removing $$TARBALLS..."; \
		rm -f $(subst .,-, $(COLLECTION))-*.tar.gz; \
	fi
	@echo "→ Removing cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@if ls $(subst .,-, $(COLLECTION))-*.tar.gz 1> /dev/null 2>&1; then \
		echo "✗ Failed to remove tarball."; \
		exit 1; \
	else \
		echo "✓ Collection artifacts removed."; \
	fi

dev:
	@echo "→ Setting up development environment for $(COLLECTION)..."
	@mkdir -p $(DEV_NAMESPACE_PATH)
	@rm -f $(DEV_COLLECTION_PATH)
	@ln -sfn $(abspath $(PROJECT_PATH)) $(DEV_COLLECTION_PATH)
	@[ -L "$(COLLECTION_PATH)" ] && rm -f "$(COLLECTION_PATH)" || true
	@rmdir "$(NAMESPACE_PATH)" 2>/dev/null || true
	@rmdir "$(COLLECTIONS_ROOT)/ansible_collections" 2>/dev/null || true
	@printf '[defaults]\ncollections_path = ~/.ansible/dev_collections:~/.ansible/collections\n' > ansible.cfg
	@printf '#!/usr/bin/env bash\n# Source this file when ansible.cfg is ignored (e.g., WSL/Windows mounts).\n# Usage: source dev-env.sh\nexport ANSIBLE_COLLECTIONS_PATH=~/.ansible/dev_collections:~/.ansible/collections\n' > dev-env.sh
	@echo "✓ Development environment ready."
	@echo "  Symlink: $(DEV_COLLECTION_PATH) -> $(abspath $(PROJECT_PATH))"
	@echo "  Edit files directly - no rebuild or reinstall needed."
	@echo ""
	@echo "  If ansible.cfg is ignored (world-writable directory warning), run:"
	@echo "    source dev-env.sh"

dev-clean:
	@echo "→ Removing development environment..."
	@rm -f $(DEV_COLLECTION_PATH)
	@rmdir $(DEV_NAMESPACE_PATH) 2>/dev/null || true
	@rmdir $(DEV_COLLECTIONS_ROOT)/ansible_collections 2>/dev/null || true
	@rmdir $(DEV_COLLECTIONS_ROOT) 2>/dev/null || true
	@rm -f ansible.cfg
	@rm -f dev-env.sh
	@echo "✓ Development environment removed."

format:
	@echo "→ Format with ruff..."
	$(RUFF) format $(PROJECT_PATH)
	@echo "✓ Format completed."

lint:
	@echo "→ Lint with ruff..."
	$(RUFF) check $(PROJECT_PATH)
	@echo "✓ Linting completed."

check:
	@echo "→ Checking format and linting with ruff (no changes)..."
	$(RUFF) format --check $(PROJECT_PATH)
	$(RUFF) check $(PROJECT_PATH)
	@echo "✓ All checks passed."

fix:
	@echo "→ Auto-fixing issues with ruff..."
	ruff check --fix $(PROJECT_PATH)
	ruff format $(PROJECT_PATH)
	@echo "✓ Auto-fixes applied, if any."

docs-serve: docs-patch-template
	@echo "→ Starting MkDocs server..."
	$(MKDOCS) serve

docs-serve-live: install docs-patch-template
	@echo "→ Starting MkDocs server with live reload..."
	$(MKDOCS) serve --livereload -w ./

docs-build: install docs-patch-template
	@echo "→ Building documentation..."
	$(MKDOCS) build
	@echo "✓ Documentation built."

docs-deploy: docs-build docs-patch-template
	@echo "→ Deploying documentation to GitHub Pages..."
	$(MKDOCS) gh-deploy
	@echo "✓ Documentation deployed."

docs-patch-template:
	@echo "→ Patching plugin_list.md.jinja template..."
	@TEMPLATE_FILE=.venv/lib/python3.12/site-packages/mkdocs_ansible_collection/templates/plugin_list.md.jinja; \
	if [ -f "$$TEMPLATE_FILE" ]; then \
	  sed -i.bak \
	  's|{{- plugin_data\['"'"'doc'"'"'\]\['"'"'short_description'"'"'\] \| default('"'"'--'"'"') }}|{%- if plugin_data.get('"'"'doc'"'"') and plugin_data['"'"'doc'"'"'].get('"'"'short_description'"'"') -%}\n{{ plugin_data['"'"'doc'"'"']['"'"'short_description'"'"'] }}\n{%- else -%}\n--\n{%- endif %} \||g' \
	  "$$TEMPLATE_FILE" && \
	  echo "✓ Template patched successfully."; \
	else \
	  echo "✗ Template file not found."; \
	  exit 1; \
	fi
