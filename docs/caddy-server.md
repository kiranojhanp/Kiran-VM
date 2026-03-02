# Deploying Web Apps with Caddy: A Beginner's Guide

Caddy is an open-source web server written in Go that simplifies the process of running and deploying web applications. It's unique for its automatic HTTPS setup, easy-to-use `Caddyfile` configuration, and minimal dependencies.

In this tutorial, we will explore:
1. Running Caddy with Docker
2. Setting up Automatic HTTPS
3. Using Caddy as a Static File Server
4. Setting up Request Logging
5. Using Caddy as a Reverse Proxy

---

## 1. Running Caddy server with Docker

The easiest way to get started with Caddy is via Docker. 

You can run a temporary foreground Caddy container just by typing:
```bash
docker run --rm -p 80:80 caddy
```
Visiting `http://localhost` in your browser will display the default "Caddy works!" page.

However, to persist configurations and SSL certificates, it's better to use **Docker Compose**. Let's create a setup.

### Step-by-Step Setup
1. Create a project folder:
```bash
mkdir caddy-tutorial && cd caddy-tutorial
```

2. Create a basic `Caddyfile`:
```caddyfile
:80 {
    root * /usr/share/caddy
    file_server
}
```

3. Create a dummy `index.html`:
```html
<!DOCTYPE html>
<html>
<body>
    <p>Hello, Caddy!</p>
</body>
</html>
```

4. Create your `docker-compose.yml`:
```yaml
version: '3'

name: caddy-tutorial

services:
  caddy:
    container_name: caddy
    image: caddy
    restart: always
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - caddy-config:/config
      - caddy-data:/data
      - ./Caddyfile:/etc/caddy/Caddyfile
      - ./index.html:/usr/share/caddy/index.html

volumes:
  caddy-config:
  caddy-data:
```

Run `docker compose up -d` to start it, and `docker compose down` to stop it.

---

## 2. Setting up Automatic HTTPS

Caddy's defining feature is automatic TLS/SSL certificate provisioning and renewal using Let's Encrypt. 

To enable this, change the `:80` in your `Caddyfile` to a real domain name that is currently pointing to your server's IP address.

**Updated Caddyfile:**
```caddyfile
your_domain_name.com {
    root * /usr/share/caddy
    file_server
}
```
When you start the server again, Caddy will automatically:
1. Contact Let's Encrypt.
2. Verify domain ownership.
3. Provision and install the certificate (stored in the persistent `/data` volume).
4. Redirect all HTTP traffic to HTTPS.

---

## 3. Using Caddy as a Static File Server (For SPAs)

If you are serving Single Page Applications (SPAs) like React or Vue, you must instruct Caddy to route all unmatched paths back to the `index.html` file so that your client-side router can handle them.

Update your `docker-compose.yml` to mount your built application folder (e.g., `./dist`) into `/usr/share/caddy`:

```yaml
    volumes:
      # ... other volumes
      - ./dist:/usr/share/caddy
```

Update your `Caddyfile` with the `try_files` directive:

```caddyfile
:80 {
    root * /usr/share/caddy
    file_server
    try_files {path} /index.html
}
```

---

## 4. Setting up Request Logging

By default, Caddy doesn't log incoming requests. You have to explicitly enable standard output logging in your `Caddyfile`:

```caddyfile
your_domain_name.com {
    root * /usr/share/caddy
    file_server
    try_files {path} /index.html
    
    log {
        output stdout
    }
}
```

After restarting the container, you can view the logs using:
```bash
docker compose logs -f
```

*(Note: Advanced users typically push these logs to a log forwarder like Vector, which can send them to aggregation services like Better Stack).*

---

## 5. Using Caddy as a Reverse Proxy

Caddy is exceptional at proxying traffic to backend services. If you have an API running locally (or inside another Docker container) on port 3000, you can serve your frontend application on the root path and reverse proxy `/api/*` requests to your backend.

Here's a `Caddyfile` demonstrating this using block handling:

```caddyfile
your_domain_name.com {
  # Forward /api requests to the backend container
  redir /api /api/

  handle_path /api/* {
    reverse_proxy backend:3000
  }

  # Fallback to serving the frontend for all other requests
  handle {
    root * /usr/share/caddy
    file_server
    try_files {path} /index.html
  }

  log {
    output stdout
  }
}
```

*Note: In Docker Compose, you can refer to the backend container by its service name (`backend:3000`).*

---

## Summary

You now have a powerful, auto-HTTPS-enabled web server! Caddy handles the heavy lifting, making it easier than ever to host static websites and reverse proxy dynamic APIs. 

For advanced configuration, check the [official Caddy Documentation](https://caddyserver.com/docs/).