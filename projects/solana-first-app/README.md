# SOLANA APP

This projects contains the front-end application of the Solana decentralized application deployed on Solana network.

To run the app in a container, build a run the image with:

```
docker build -t solana-first-app:latest .

docker run \
    -it \
    --rm \
    -v ${PWD}:/app \
    -v /app/node_modules \
    -p 3001:3000 \
    -e CHOKIDAR_USEPOLLING=true \
```
