# Setting Up Komodo & Deploying Your First "Hello World" Container

Welcome to your learning journey with **Komodo**! Komodo is a powerful, centralized platform that helps you build, deploy, and manage your containerized applications (Docker/Podman) across multiple servers.

In this tutorial, we will:
1. Set up the Komodo management platform locally.
2. Log into the Komodo dashboard.
3. Deploy a basic "Hello World" container using Komodo's interface.

---

## Prerequisites
Before you start, ensure you have the following installed on your machine:
- [Docker](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)

---

## Step 1: Download the Komodo Setup Files

Komodo provides official Docker Compose files to make installation easy. For this tutorial, we will use the MongoDB-backed configuration.

Open your terminal, create a new directory for Komodo, and download the necessary files:

```bash
mkdir komodo
cd komodo

# Download the Compose file
curl -o mongo.compose.yaml https://raw.githubusercontent.com/moghtech/komodo/main/compose/mongo.compose.yaml

# Download the environment variables file
curl -o compose.env https://raw.githubusercontent.com/moghtech/komodo/main/compose/compose.env
```

## Step 2: Customize Your Environment (Optional)

The `compose.env` file contains configuration defaults. By default, it creates an admin user with the following credentials:
- **Username:** `admin`
- **Password:** `changeme`

You can open `compose.env` in a text editor to update these values (look for `KOMODO_INIT_ADMIN_USERNAME` and `KOMODO_INIT_ADMIN_PASSWORD`), along with the secure database credentials, before starting.

## Step 3: Launch Komodo

With the files in place, start the Komodo stack by running:

```bash
docker compose -p komodo -f mongo.compose.yaml --env-file compose.env up -d
```

Docker will download the MongoDB, Komodo Core, and Komodo Periphery agent images and spin them up. The `-d` flag runs everything in the background.

## Step 4: Access the Komodo Dashboard

Once the containers are running, access the Komodo UI:
1. Open your web browser and navigate to `http://localhost:9120` (or replace `localhost` with your server's IP address if you are working remotely).
2. Log in using the default admin credentials (`admin` / `changeme`, unless you changed them in step 2).

You are now in the centralized command center for your self-hosted apps!

## Step 5: Deploy a "Hello World" Application

Now that Komodo is set up, let's deploy our first container via the UI. We'll use the `traefik/whoami` image, a tiny web server that prints out OS information and HTTP request details—the perfect "Hello World" app for Docker.

1. In the Komodo dashboard sidebar, click on **Deployments** or **Stacks** (depending on the current UI version).
2. Click **Create New**.
3. Choose the option to define your deployment using **Docker Compose** or via **UI**. Let's use a simple Compose setup.
4. Name your stack: `hello-world-stack`
5. In the Compose editor text box, paste the following:

```yaml
services:
  hello-world:
    image: traefik/whoami
    ports:
      - "8080:80"
```

6. Select your local server (which should already be connected via the Periphery agent on your machine) and hit **Deploy**.

## Step 6: Verify Your Deployment

Komodo will instruct the Periphery agent to pull the `traefik/whoami` image and spin it up on your machine.

Once the status indicates the container is running:
1. Open a new tab in your web browser.
2. Go to `http://localhost:8080`.

You should see plain text output listing your hostname, IPs, and HTTP headers. 

**Congratulations!** 🎉 You've successfully set up your very own centralized hosting management space using Komodo and deployed your first container. From here, you can start scaling up by connecting more servers, configuring automated updates from Git, and migrating your existing home lab apps to your new setup.