# Docker & Docker Compose Tutorial

This guide provides an introduction to Docker and Docker Compose, explaining what they are and how to use them effectively for containerizing applications. It synthesizes practical guidance for beginners to learn and practice multi-container deployments.

---

## 1. What are Docker and Docker Compose?

**Docker** is a platform for building, running, and managing containers. A container is a standard unit of software that packages up code and all its dependencies so the application runs quickly and reliably from one computing environment to another. 

**Docker Compose** is a specialized tool used alongside Docker to define and run multi-container applications. While Docker commands work great for single containers, deploying complex applications (like a web server, a database, and a caching system) via single commands can become messy and error-prone. Docker Compose solves this by using a simple YAML configuration file (`docker-compose.yml`) to orchestrate everything at once.

### Why Use Docker Compose?
- **Infrastructure as Code:** Defines your whole app stack in a single readable `.yml` file.
- **Reproducibility:** Say goodbye to "it works on my machine." Anyone with your compose file can spin up the exact same environment.
- **Easy Orchestration:** Spin up, stop, and destroy interconnected services with single, simple commands.
- **Automatic Networking:** Compose automatically creates a default network, allowing containers to communicate with each other easily using their service names.

---

## 2. Prerequisites

To follow this tutorial, you will need:
1. A terminal/command line interface.
2. [Docker installed](https://docs.docker.com/get-docker/) on your machine.
3. [Docker Compose installed](https://docs.docker.com/compose/install/) (Note: Docker Desktop includes Compose automatically).

You can verify your installation by running:
```bash
docker --version
docker compose version
```
*(Note: Older installations use `docker-compose`, while newer versions use the `docker compose` plugin syntax).*

---

## 3. Core Concepts of `docker-compose.yml`

A Docker Compose file usually has the following primary elements:
- **`version`**: The Compose specification version (e.g., `"3.8"`). 
- **`services`**: The containers that make up your application (e.g., `web`, `database`, `redis`).
- **`image` / `build`**: The source of the container. You can use an existing image from Docker Hub (like `nginx:latest`) or build a local `Dockerfile`.
- **`ports`**: Maps ports from the host machine to the container (e.g., `"8080:80"` maps host port 8080 to container port 80).
- **`volumes`**: Persistent data storage. Mounts host directories or Docker-managed volumes to retain data even when containers are destroyed.
- **`environment`**: Passes environment variables to the container (like database passwords).
- **`depends_on`**: Sets the startup order so a web app doesn't start before its database is ready.

---

## 4. Step-by-Step Example: Multi-Container Application

Let's create a practical multi-container application. We will set up a simple architecture featuring a web application and a Redis cache database. 

### Step 4.1: Create your project directory
Open your terminal and create a folder for this project:
```bash
mkdir my-compose-app
cd my-compose-app
```

### Step 4.2: Create the `docker-compose.yml` file
Create a file named `docker-compose.yml` and paste the following configuration:

```yaml
version: "3.8"

services:
  # Service 1: The Redis Database
  redis_cache:
    container_name: "my_redis"
    image: "redis:alpine"
    ports:
      - "6379:6379"
    restart: always

  # Service 2: A simple web server (using Nginx)
  web_server:
    container_name: "my_nginx"
    image: "nginx:latest"
    ports:
      - "8080:80"
    volumes:
      - "./html:/usr/share/nginx/html"
    depends_on:
      - redis_cache
    restart: unless-stopped
```

### Step 4.3: Add some local content (Bind Mount)
Notice the `volumes` section under `web_server`. It maps a local `./html` folder to the container. Let's create that:

```bash
mkdir html
echo "<h1>Hello from Docker Compose!</h1>" > html/index.html
```

### Step 4.4: Run your Application
Now, run the stack in **detached mode** (in the background):

```bash
docker compose up -d
```

Docker will automatically pull the Nginx and Redis images, create a default network linking them, and start the containers. 

### Step 4.5: Verify it works
Open your web browser and navigate to: `http://localhost:8080`
You should see your "Hello from Docker Compose!" message.

---

## 5. Essential Docker Compose Commands

Once your application is running, you can manage it from the terminal using the following commands (always run these in the same directory as your `docker-compose.yml` file):

- **`docker compose up -d`**: Builds, (re)creates, starts, and attaches to containers for a service, running them in the background.
- **`docker compose ps`**: Lists all running containers associated with your Compose file.
- **`docker compose logs`**: Displays log output from services. You can view logs for a specific service using `docker compose logs [service_name]` (e.g., `docker compose logs web_server`).
- **`docker compose stop`**: Stops running containers without destroying them or their data.
- **`docker compose start`**: Starts existing, stopped containers.
- **`docker compose restart`**: Restarts the containers.
- **`docker compose down`**: Stops containers and **removes** containers, networks, volumes, and images created by `up`. (Note: use `docker compose down -v` to also destroy named volumes and erase persistent data).
- **`docker compose pull`**: Pulls the latest versions of the images defined in your file.

---

## 6. Next Steps & Best Practices

1. **Environment Variables (.env):** Never hardcode sensitive passwords into your `.yml` file. Instead, use a `.env` file and reference variables using `${VAR_NAME}` in your Compose file.
2. **Explicit Networking:** While default networks are easy, explicitly defining custom networks in the `networks:` block provides better control and security.
3. **Scaling:** You can run multiple instances of a container for load balancing testing using the scale flag: `docker compose up --scale web_server=3 -d`.

By mastering Docker Compose, you lay a foundational stone for handling larger orchestrated environments and moving towards robust Infrastructure as Code.