.PHONY : build, start, end, clear, clear_all, lock, quality, tests

# Target to build the Docker image
build:
	@echo "Starting the build of the Docker image..."
	@docker build --progress=plain -t scientific_crawler .

# Target to start the Docker service - success
success_start:
	@echo "Starting Scientific crawler service..."
	@docker run --network host --name scientific_crawler_service -e JOURNAL_NUMBER=3 -e JOURNAL_YEAR=2022 scientific_crawler

# Target to start the Docker service - fail because the journal does not have download link
fail_start:
	@echo "Starting Scientific crawler service..."
	@docker run --network host --name scientific_crawler_service scientific_crawler

# Target to stop Docker service
end:
	@echo "Stopping Scientific crawler service..."
	@docker kill scientific_crawler_service

# Target to remove all Docker containers
clear:
	@echo "Removing Docker container..."
	@docker rm scientific_crawler_service

# Target to remove all Docker containers
clear_all:
	@echo "Removing all Docker containers..."
	@docker rm -f $$(docker ps -a -q) || true

# Target to invoke the poetry lock process
lock:
	@echo "Starting the lock process..."
	@python3 -m pip install -q poetry==1.8.3
	@poetry lock

# Target to invoke the quality process
quality:
	@echo "Starting the quality process..."
	@poetry install --with dev
	@poetry run pre-commit install
	@poetry run pre-commit run --all-files

# Target to invoke the testing process
tests:
	@echo "Starting the tests process..."
	@poetry install --with dev
	@poetry run pytest --cov=. --cov-fail-under=70
