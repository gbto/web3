docker-start:
	docker run \
    -it \
    --rm \
    -v ${PWD}:/app \
    -v /app/node_modules \
    -p 3001:3000 \
    -e CHOKIDAR_USEPOLLING=true \
	solana-first-app:latest

docker-compose-start:
	 docker-compose up -d --build
