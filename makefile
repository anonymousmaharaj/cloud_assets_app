venv:
	python -m venv venv
	source venv/bin/activate
	pip install --upgrade pip

corevenv: venv
	pip install -r requirements/base.txt

testvenv: venv
	pip install -r requirements/test.txt

devvenv: venv
	pip install -r requirements/dev.txt

lint: devvenv
	flake8 --exit-zero

test: testvenv
	pytest

postgres:
	docker run -p 5432:5432 --name='postgres' --network="bridge" -e POSTGRES_PASSWORD=${DB_PASSWORD} -e POSTGRES_USER=${DB_USER} -d postgres:12.8

dockerconnect:
	docker network connect bridge-network postgres
	docker network connect bridge-network test

dockerkill:
	docker kill postgres
	docker rm postgres

dockertag:
	docker tag af-internship_web ${ECR_WEB}
	docker tag af-internship_nginx ${ECR_NGINX}

dockercomposebuild:
	docker-compose build