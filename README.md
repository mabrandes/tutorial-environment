# Sample application for tutorials

This repository contains the environment for completing the tutorials at [grafana.com/tutorials](https://grafana.com/tutorials).

Link to Tutorial: https://grafana.com/tutorials/grafana-fundamentals/?utm_source=grafana_gettingstarted

## Prequisites

You will need to have the following installed locally to complete this workshop:

- [Docker](https://docs.docker.com/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)

NOTE: If you're running Docker for Desktop for macOS or Windows, Docker Compose is already included in your installation.

## Login

To log in browse to [localhost:3000](http://localhost:3000).

NOTE:
To facilitate the demo, **login has been disabled**, and anonymous access is granted admin privileges. For security reasons, we advise keeping login enabled in your Grafana instance.

If you want to follow the tutorial with login enabled, you can comment the following lines of the [docker-compose file](docker-compose.yml)


      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin 
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_BASIC_ENABLED=false


Once login is enabled, the default username and password is `admin:admin`

## Running

To start the sample application and the supporting services:

```
docker-compose up -d
```
## Explanation docker-compose.yml

🌟 Top-level metadata

```
version: "3"
```

Declares which version of the Compose file format to use. Version 3 is commonly used and works well with Docker Swarm & modern Docker.

🌐 Networks

```
networks:
  grafana:
```

Defines a custom network named grafana. All services using this network can communicate with each other directly by service name (e.g., grafana:3000).

💾 Volumes

```
volumes:
  app_data: {}
```

Defines a named volume app_data. Used for persistent storage, shared logs, or configuration files. Docker manages this volume outside the container's lifecycle.

🧩 Services
🟢 prometheus

```
prometheus:
  image: prom/prometheus:v2.49.0
  volumes:
    - ./prometheus/:/etc/prometheus/
  command:
    - "--config.file=/etc/prometheus/prometheus.yml"
    - "--storage.tsdb.path=/prometheus"
  ports:
    - 9090:9090
  networks:
    - grafana
```

- Runs Prometheus monitoring tool. 
- Maps local ./prometheus/ directory to /etc/prometheus/ inside container for config. 
- Runs custom start command to specify config file and data path. Exposes port 9090 → you can access it at http://host:9090.

🟠 loki
```
loki:
  image: grafana/loki:2.9.0
  ports:
    - 3100:3100
  command: -config.file=/etc/loki/local-config.yaml
  networks:
    - grafana
```
- Runs Loki, a log aggregation system by Grafana.
- Exposes port 3100 (API endpoint for logs).
- Uses local config /etc/loki/local-config.yaml.

🔵 promtail
```
promtail:
  image: grafana/promtail:2.0.0
  volumes:
    - app_data:/var/log
  networks:
    - grafana
```

- Runs Promtail, which collects logs and ships them to Loki.
- Mounts the shared app_data volume → reads logs from /var/log.

🟡 grafana

```
grafana:
  image: grafana/grafana:12.0.1
  ports:
    - 3000:3000
  networks:
    - grafana
  environment:
    - "GF_DEFAULT_APP_MODE=development"
    - "GF_LOG_LEVEL=debug"
    - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
    - GF_AUTH_ANONYMOUS_ENABLED=true
    - GF_AUTH_BASIC_ENABLED=false
  volumes:
    - ./grafana/provisioning/datasources:/etc/grafana/provisioning/datasources
```
- Runs Grafana UI on port 3000.
- Disables login (anonymous mode enabled with admin role).
- Mounts local datasource config (./grafana/provisioning/datasources) to auto-provision data sources.
- Logs set to debug for troubleshooting.

🟢 app
```
app:
  build: ./app
  ports:
    - 8081:80
  volumes:
    - app_data:/var/log
  networks:
    - grafana
```
- Builds custom application from ./app directory (Dockerfile expected there).
- Exposes container's port 80 to host port 8081.
- Uses app_data volume to store logs.

🟢 db
```
db:
  image: grafana/tns-db:latest
  ports:
    - 8082:80
  networks:
    - grafana
```
- Runs a database service (image: grafana/tns-db:latest).
- Exposes container port 80 to host port 8082.

# volumes

| What you wrote                   | What it means            | Where on Windows?                                |
|---------------------------------|--------------------------|-------------------------------------------------|
| `./something:/path/in/container` | Local folder mount       | Directly in your filesystem (relative or absolute) |
| `my_volume:/path/in/container`  | Docker named volume      | Stored inside Docker's internal disk, not browsable |


💡 Key points

-  All services share one network (grafana), allowing easy internal communication by service names.
-  app_data volume is shared → Promtail can read logs from app container.
- Grafana is set up to run without login for easy local testing.
- Prometheus and Loki collect and provide metrics and logs, which you can visualize in Grafana.
- You can access each service on your local machine via the mapped ports.

## Access URLs example
| Service    | Local URL                |
|-------------|--------------------------|
| **Grafana**   | [http://localhost:3000](http://localhost:3000) |
| **Prometheus** | [http://localhost:9090](http://localhost:9090) |
| **Loki (API)** | [http://localhost:3100](http://localhost:3100) |
| **App**        | [http://localhost:8081](http://localhost:8081) |
| **DB**         | [http://localhost:8082](http://localhost:8082) |
| **DB postgresql**| [http://localhost:5433](http://localhost:5433) |
| **App2**         | [http://localhost:8083/](http://localhost:8083/) |
| **API**         | [http://localhost:8084/](http://localhost:8084/) |
| **DB Tables**| [http://localhost:8084/tables](http://localhost:8084/tables) |
| **DB Tables name**| [http://localhost:8084/query/your_table_name](http://localhost:8084/query/your_table_name) |



## 📦 Where images come from

| Service   | Where image comes from                                                                 |
|-------------|-------------------------------------------------------------------------------------|
| **prometheus** | Docker Hub (`prom/prometheus`)                                  |
| **loki**       | Docker Hub (`grafana/loki`)                                       |
| **promtail**   | Docker Hub (`grafana/promtail`)                                   |
| **grafana**    | Docker Hub (`grafana/grafana`)                                   |
| **db**         | Docker Hub (or custom if `grafana/tns-db` is private, but probably Docker Hub) |
| **app**        | Built locally from `./app`  