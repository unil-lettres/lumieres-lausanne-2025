# Front-end build targets for Lumières Lausanne

# Node/npm check
check-node:
	@which node > /dev/null || (echo "Error: Node.js is not installed" && exit 1)
	@which npm > /dev/null || (echo "Error: npm is not installed" && exit 1)

# Install dependencies
npm-install: check-node  ## Install npm dependencies
	npm install

# Development build
npm-dev: check-node  ## Run Vite dev server
	npm run dev

# Production build
npm-build: check-node  ## Build production assets
	npm run build

# Preview production build
npm-preview: check-node  ## Preview production build
	npm run preview

# Lint JavaScript
npm-lint-js: check-node  ## Lint JavaScript files
	npm run lint:js

# Lint CSS
npm-lint-css: check-node  ## Lint CSS files
	npm run lint:css

# Format code
npm-format: check-node  ## Format code with Prettier
	npm run format

# Clean build artifacts
npm-clean:  ## Clean npm build artifacts
	rm -rf app/static/dist
	rm -rf node_modules

.PHONY: check-node npm-install npm-dev npm-build npm-preview npm-lint-js npm-lint-css npm-format npm-clean
