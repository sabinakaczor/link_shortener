up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose up -d --build

test:
	docker-compose exec web pytest
