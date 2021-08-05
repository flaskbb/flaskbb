.PHONY: clean install help run build
.DEFAULT_GOAL := help

help: ## Displays this help message.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)


clean: ## Remove unwanted stuff such as node_modules, etc...
	find . -name 'node_modules' -exec rm -rf {} +


run: ## Runs the webpack server which watches for changes
	npm run watch


build: ## Builds a dist bundle of the JS and CSS files
	npm run build


install: ## Installs the dependencies
	npm install
