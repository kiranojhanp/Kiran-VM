# Production Self-Hosting on Ubuntu with Komodo, Docker, Caddy, and Cloudflare

This guide walks you through building a hardened, production-ready self-hosting environment from a fresh Ubuntu 24.04 server. Every layer is configured with security and reliability in mind.

**Stack:**
- **Ubuntu 24.04 LTS** — hardened host OS
- **Docker & Docker Compose** — containerization
- **Komodo** — centralized deployment dashboard (UI-based Stacks)
- **Caddy** — reverse proxy with automatic HTTPS via Cloudflare DNS
- **Cloudflare** — DNS, CDN, DDoS protection, WAF

## Prerequisites
- A fresh Ubuntu 24.04 LTS server with root SSH access
- A domain managed by Cloudflare
- Your local machine's SSH public key ready to copy

---

## Step 1: Initial Server Setup

### 1.1 Update the System
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Create a Non-Root Sudo User
Never run your server day-to-day as root.
```bash
sudo adduser deploy
sudo usermod -aG sudo deploy
```
Copy your SSH public key to the new user before proceeding:
```bash
# Run this from your local machine
ssh-copy-id deploy@<your_server_ip>
```
Then verify you can SSH in as `deploy` before closing your root session.

### 1.3 Harden SSH
Edit `/etc/ssh/sshd_config` and set the following:
```
Port 2222
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication no
X11Forwarding no
MaxAuthTries 3
MaxSessions 2
UsePAM yes
```
Validate and restart:
```bash
sudo sshd -t
sudo systemctl restart ssh
```

### 1.4 Configure the Firewall (UFW)
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 2222/tcp   # Custom SSH port
sudo ufw allow 80/tcp     # HTTP (required for Caddy)
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable
sudo ufw status verbose
```
> **Note:** Port 9120 (Komodo) does NOT need to be opened. We will access it securely via the Caddy reverse proxy.

### 1.5 Install and Configure Fail2Ban
Fail2Ban automatically bans IPs that repeatedly fail authentication.
```bash
sudo apt install fail2ban -y
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
```
Edit `/etc/fail2ban/jail.local` and update the `[sshd]` section:
```ini
[sshd]
enabled  = true
port     = 2222
maxretry = 3
bantime  = 3600
findtime = 600
```
Enable and start:
```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 1.6 Enable Automatic Security Updates
```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

### 1.7 Kernel and Network Hardening
Add the following to `/etc/sysctl.conf`:
```ini
# Prevent IP spoofing
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Disable IP source routing
net.ipv4.conf.all.accept_source_route = 0

# Enable SYN flood protection
net.ipv4.tcp_syncookies = 1

# Log suspicious packets
net.ipv4.conf.all.log_martians = 1

# Disable ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0

# Ignore broadcast pings
net.ipv4.icmp_echo_ignore_broadcasts = 1
```
Apply immediately:
```bash
sudo sysctl -p
```

### 1.8 Secure Shared Memory
Add to `/etc/fstab`:
```
tmpfs /run/shm tmpfs defaults,noexec,nosuid 0 0
```

### 1.9 Configure Swap
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```
Make it permanent by adding to `/etc/fstab`:
```
/swapfile swap swap defaults 0 0
```

### 1.10 Install Monitoring Tools
```bash
sudo apt install htop iotop nethogs auditd audispd-plugins -y
sudo systemctl enable auditd && sudo systemctl start auditd
```

### 1.11 Verify AppArmor
AppArmor provides mandatory access control and is enabled by default on Ubuntu.
```bash
sudo systemctl status apparmor
sudo aa-status
```

### 1.12 Set Timezone
```bash
sudo timedatectl set-timezone America/Chicago  # Set to your timezone
```

### 1.13 Reboot and Verify
```bash
sudo reboot
```
After reboot, SSH back in on your new port (`ssh -p 2222 deploy@<your_server_ip>`) and verify all services are running:
```bash
sudo systemctl status fail2ban ufw auditd apparmor
```

---

## Step 2: Install Docker and Docker Compose

Follow the [official Docker installation for Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

Add your user to the `docker` group so you can run Docker without `sudo`:
```bash
sudo usermod -aG docker deploy
newgrp docker
```

Verify both are working:
```bash
docker --version
docker compose version
```

---

## Step 3: Install and Launch Komodo

Komodo is your centralized deployment dashboard. It runs as a Docker stack on your server and manages all other containers through its Periphery agent.

### 3.1 Download Komodo Setup Files
```bash
mkdir ~/komodo && cd ~/komodo
curl -o mongo.compose.yaml https://raw.githubusercontent.com/moghtech/komodo/main/compose/mongo.compose.yaml
curl -o compose.env https://raw.githubusercontent.com/moghtech/komodo/main/compose/compose.env
```

### 3.2 Configure Credentials
Edit `compose.env` and set strong values for at least:
```env
KOMODO_INIT_ADMIN_USERNAME=your_admin_username
KOMODO_INIT_ADMIN_PASSWORD=a_strong_password_here
```
Also update the MongoDB credentials in the same file.

### 3.3 Launch Komodo
```bash
docker compose -p komodo -f mongo.compose.yaml --env-file compose.env up -d
```
Komodo Core (port 9120) and the Periphery agent are now running. You can temporarily access the dashboard at `http://<your_server_ip>:9120` to confirm it is alive before we proxy it.

---

## Step 4: Configure Cloudflare

### 4.1 Configure DNS Records
Log into the Cloudflare Dashboard and go to your domain's **DNS** settings.

For every subdomain you intend to host, create a proxied `A` record:

| Type | Name     | IPv4 Address      | Proxy Status |
|------|----------|-------------------|--------------|
| A    | komodo   | `<your_server_ip>`| Proxied (ON) |
| A    | app      | `<your_server_ip>`| Proxied (ON) |

The orange cloud (Proxied) hides your server's real IP and routes traffic through Cloudflare's network for DDoS protection and WAF.

### 4.2 Set SSL/TLS Mode to Full (Strict)
Go to **SSL/TLS** -> **Overview** and set the encryption mode to **Full (Strict)**.

This is critical. Caddy will provision a valid certificate on your server. "Full (Strict)" ensures Cloudflare validates this certificate, providing genuine end-to-end encryption. Any other mode is insecure or will cause redirect loops.

### 4.3 Generate a Cloudflare API Token
When Cloudflare's proxy is enabled, Caddy cannot use its standard HTTP challenge to obtain SSL certificates. Instead, we use the Cloudflare DNS challenge, which requires an API token.

1. Go to **My Profile** -> **API Tokens** -> **Create Token**.
2. Select the **Edit zone DNS** template.
3. Under **Zone Resources**, select your specific domain.
4. Click **Continue to summary** -> **Create Token**.
5. **Save the token securely.** It is only shown once.

### 4.4 (Optional) Harden with Cloudflare WAF Rules
Under **Security** -> **WAF** -> **Custom rules**, you can add rules such as:
- Block traffic not originating from Cloudflare IP ranges.
- Block known bad bots.
- Rate-limit aggressive crawlers.

---

## Step 5: Deploy Caddy via Komodo Stack

Caddy is managed just like any other application — deployed through Komodo's Stacks UI. We use the `slothcroissant/caddy-cloudflaredns` image which ships with the Cloudflare DNS module pre-built.

### 5.1 Create the Caddyfile on the Server
Caddy reads its config from a file on the host, mounted into the container.
```bash
sudo mkdir -p /etc/caddy
sudo nano /etc/caddy/Caddyfile
```
Start with the Komodo dashboard entry:
```caddyfile
komodo.yourdomain.com {
    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
    }
    reverse_proxy localhost:9120
}
```
Save and close.

### 5.2 Create the Caddy Stack in Komodo
1. Log into your Komodo dashboard at `http://<your_server_ip>:9120`.
2. Go to **Stacks** -> **Create New**.
3. Name the stack `caddy`.
4. Paste the following compose configuration:
```yaml
services:
  caddy:
    image: slothcroissant/caddy-cloudflaredns:latest
    container_name: caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    environment:
      - CLOUDFLARE_API_TOKEN=your_cloudflare_api_token_here
    volumes:
      - /etc/caddy/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
      - caddy-config:/config
    network_mode: "host"

volumes:
  caddy-data:
  caddy-config:
```
> Replace `your_cloudflare_api_token_here` with the token from Step 4.3. For production, store it as a secret in Komodo's environment variable management rather than hardcoding it.

5. Select your server and click **Deploy**.

Once the container starts, Caddy will automatically request a certificate from Let's Encrypt using the Cloudflare DNS challenge. In 30-60 seconds your Komodo dashboard will be securely available at `https://komodo.yourdomain.com`.

### 5.3 Lock Down the Komodo Port
Now that Komodo is accessible via HTTPS through Caddy, block direct access to port 9120:
```bash
sudo ufw deny 9120/tcp
```

---

## Step 6: Deploying Applications

Every new application follows the same repeatable workflow: create a Stack in Komodo, add a Cloudflare DNS record, and update the Caddyfile.

### 6.1 Example: Deploy a "Hello World" App

**In Komodo:**
1. Go to **Stacks** -> **Create New**.
2. Name the stack `hello-world`.
3. Paste:
```yaml
services:
  whoami:
    image: traefik/whoami
    restart: unless-stopped
    ports:
      - "8080:80"
```
4. Select your server and click **Deploy**.

**In Cloudflare:**
- Add a Proxied `A` record: `app` -> `<your_server_ip>`.

**Update the Caddyfile** on your server:
```bash
sudo nano /etc/caddy/Caddyfile
```
```caddyfile
komodo.yourdomain.com {
    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
    }
    reverse_proxy localhost:9120
}

app.yourdomain.com {
    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
    }
    reverse_proxy localhost:8080
}
```
**Reload Caddy** (zero downtime):
```bash
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

Your app is now live at `https://app.yourdomain.com`.

### 6.2 Adding More Apps

The pattern for every new app is:
1. **Komodo:** Create a new Stack, expose a host port (e.g. `8081:80`).
2. **Cloudflare:** Add a Proxied `A` record for the new subdomain.
3. **Caddyfile:** Add a new block pointing to the host port.
4. **Reload Caddy.**

---

## Step 7: Ongoing Maintenance

### Updating a Stack
In Komodo, navigate to the Stack, pull the latest image, and redeploy — all from the UI without touching the server.

### Monitoring Logs
View real-time container logs directly in the Komodo dashboard under each Stack's **Logs** tab.

### Updating the Server
Unattended upgrades handle security patches automatically. For full system upgrades:
```bash
sudo apt update && sudo apt upgrade -y
```

### Monitoring Intrusion Attempts
Check Fail2Ban status and banned IPs:
```bash
sudo fail2ban-client status sshd
```
Check audit logs:
```bash
sudo ausearch -m avc --start today
```

---

## Architecture Summary

```
Internet
   │
   ▼
Cloudflare (CDN, DDoS, WAF, Proxied DNS)
   │  HTTPS
   ▼
Caddy (Docker, host network, port 80/443)
   │  Automatic TLS via Cloudflare DNS challenge
   ├── komodo.yourdomain.com  ──► localhost:9120 (Komodo)
   ├── app.yourdomain.com     ──► localhost:8080 (Hello World)
   └── ...                    ──► localhost:XXXX (Future apps)
   
Komodo Dashboard
   └── Manages all Docker Stacks via Periphery agent
```

**Security layers:**
- Cloudflare proxy hides your server IP
- UFW blocks all ports except 22 (SSH), 80, 443
- Fail2Ban bans brute-force SSH attempts
- SSH root login and password auth disabled
- Caddy enforces HTTPS for all services
- Cloudflare Full (Strict) TLS ensures end-to-end encryption
