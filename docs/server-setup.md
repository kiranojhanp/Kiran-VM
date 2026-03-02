# How to Set Up and Harden a New Ubuntu 24.04 Server

*Based on the comprehensive security guide by Paul Hoke.*

Launching a new Virtual Machine (VM) is exciting, but a default installation is rarely secure enough for production. Whether you are hosting a web app, a database, or a personal project, security should be your first priority.

In this guide, we will walk through the essential steps to initialize, configure, and harden a fresh Ubuntu 24.04 LTS server. 

## Prerequisites
- A fresh instance of Ubuntu 24.04 (LTS).
- Access to your terminal.
- Root password or an SSH key provided by your cloud provider.
- `vim` or `nano` for editing files.
- A backup method to access your server if SSH fails (console access via cloud provider).

**⚠️ IMPORTANT:** Keep a backup console/terminal session open until you verify all changes work correctly. This prevents lockout.

---

## Step 1: Update the System

Before configuring anything, ensure your system repositories and installed packages are up to date. This patches known vulnerabilities immediately.

```bash
sudo apt update && sudo apt upgrade -y
```

**Verification:**
```bash
sudo apt list --upgradable
```
*Should return: “All packages are up to date.”*

---

## Step 2: Create a New Sudo User

Running your server as root is dangerous. If the root account is compromised, the attacker has full control. We will create a standard user with `sudo` privileges for daily tasks.

Replace `username` with your preferred name:

```bash
sudo adduser username
```

Follow the prompts to set a password. Next, add this user to the sudo group:

```bash
sudo usermod -aG sudo username
```

**Verification:**
```bash
groups username
```
*Should show “sudo” in the list of groups.*

**Action: Keep your current root session open. Open a NEW terminal and test logging in as the new user before proceeding.**

---

## Step 3: Secure SSH Access

SSH is the most common attack vector for servers. We will disable password authentication, disable root login entirely, and optionally change the default SSH port.

### 1. Set up SSH Keys
If you haven’t already added your local machine’s public key to the server, do so now. On your local machine:

```bash
ssh-copy-id username@your_server_ip
```

**Test the SSH key login:**
```bash
ssh username@your_server_ip
```
**🚨 CRITICAL: Do not proceed until you can successfully log in with SSH keys!**

### 2. Harden the SSH Configuration
Back on your server, open the SSH configuration file:

```bash
sudo vi /etc/ssh/sshd_config
```

Find the following settings and modify them to match the values below. You may need to uncomment them (remove the `#`):

```text
PermitRootLogin no  
PasswordAuthentication no  
PubkeyAuthentication yes  
ChallengeResponseAuthentication no  
UsePAM yes  
X11Forwarding no  
MaxAuthTries 3  
MaxSessions 2  
Port 2222  # Optional: Change from default 22
```

Save the file.

**Test the SSH configuration for syntax errors:**
```bash
sudo sshd -t
```

**If no errors, restart the SSH service:**
```bash
sudo systemctl restart ssh
```

**Verification:**
In your NEW terminal session (keep the old one open!), test SSH login:
```bash
ssh username@your_server_ip -p 2222 # Use new port if changed
```

Verify root login is disabled:
```bash
ssh root@your_server_ip # Should be denied
```

---

## Step 4: Configure the Firewall (UFW)

Ubuntu ships with UFW (Uncomplicated Firewall). We want to deny all incoming traffic by default and only allow specific services.

```bash
# Set default policies  
sudo ufw default deny incoming  
sudo ufw default allow outgoing  
  
# Allow SSH connections (use your custom port if changed)  
sudo ufw allow 2222/tcp  # Or "sudo ufw allow OpenSSH" for port 22  
  
# (Optional) Allow HTTP/HTTPS if this is a web server  
sudo ufw allow 80/tcp  
sudo ufw allow 443/tcp  
  
# Enable the firewall  
sudo ufw enable
```

**Verification:**
```bash
sudo ufw status verbose
```
*Should show your allowed ports and “Status: active”.*

---

## Step 5: Install Fail2Ban

Fail2Ban is an intrusion prevention software that scans log files for malicious behavior (like repeated failed login attempts) and temporarily bans the offending IP addresses.

Install it via apt:
```bash
sudo apt install fail2ban -y
```

Create a local configuration file to prevent your settings from being overwritten during updates:
```bash
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
```

Edit the local configuration:
```bash
sudo vi /etc/fail2ban/jail.local
```

Find the `[sshd]` section and modify/add these settings:
```ini
[sshd]  
enabled = true  
port = 2222  # Match your SSH port  
filter = sshd  
logpath = /var/log/auth.log  
maxretry = 3  
bantime = 3600  # 1 hour  
findtime = 600  # 10 minutes
```

Restart the service:
```bash
sudo systemctl restart fail2ban  
sudo systemctl enable fail2ban
```

**Verification:**
```bash
sudo fail2ban-client status  
sudo fail2ban-client status sshd
```

---

## Step 6: Enable Automatic Security Updates

You don’t want to manually check for critical security patches every day. Ubuntu can handle this automatically.

```bash
sudo apt install unattended-upgrades -y  
sudo dpkg-reconfigure --priority=low unattended-upgrades
```
*When prompted, select Yes to enable automatic updates.*

**Verification:**
```bash
cat /etc/apt/apt.conf.d/20auto-upgrades
```
*The file should show automatic updates enabled.*

---

## Step 7: Install and Configure Audit Logging

Audit logging helps track security events and potential breaches.

```bash
sudo apt install auditd audispd-plugins -y
```

Enable and start the service:
```bash
sudo systemctl enable auditd  
sudo systemctl start auditd
```

**Verification:**
```bash
sudo systemctl status auditd
```

---

## Step 8: Verify AppArmor Status

Ubuntu 24.04 ships with AppArmor enabled by default. Verify it is running:

```bash
sudo systemctl status apparmor  
sudo aa-status
```
*You should see profiles loaded and in enforce mode.*

---

## Step 9: Secure Shared Memory

Shared memory (`/run/shm`) can be used in an attack against a running service. We can secure it by modifying the filesystem table.

Open the fstab file:
```bash
sudo vi /etc/fstab
```

Add the following line to the bottom of the file:
```text
tmpfs /run/shm tmpfs defaults,noexec,nosuid 0 0
```

Apply the changes immediately without rebooting:
```bash
sudo mount -o remount /run/shm
```

**Verification:**
```bash
mount | grep /run/shm
```
*Should show noexec,nosuid options.*

---

## Step 10: Network Hardening with Sysctl

Tweak kernel parameters to prevent common network-based attacks like IP spoofing and Man-in-the-Middle (MITM) attacks.

Open the sysctl configuration file:
```bash
sudo vi /etc/sysctl.conf
```

Scroll through the file and uncomment (or add) the following lines:

```ini
# IP Spoofing protection  
net.ipv4.conf.all.rp_filter = 1  
net.ipv4.conf.default.rp_filter = 1  
  
# Ignore ICMP broadcast requests  
net.ipv4.icmp_echo_ignore_broadcasts = 1  
  
# Disable source packet routing  
net.ipv4.conf.all.accept_source_route = 0  
net.ipv6.conf.all.accept_source_route = 0  
net.ipv4.conf.default.accept_source_route = 0  
net.ipv6.conf.default.accept_source_route = 0  
  
# Block SYN attacks  
net.ipv4.tcp_syncookies = 1  
net.ipv4.tcp_max_syn_backlog = 2048  
net.ipv4.tcp_synack_retries = 2  
net.ipv4.tcp_syn_retries = 5  
  
# Log Martians  
net.ipv4.conf.all.log_martians = 1  
net.ipv4.icmp_ignore_bogus_error_responses = 1  
  
# Ignore ICMP redirects  
net.ipv4.conf.all.accept_redirects = 0  
net.ipv6.conf.all.accept_redirects = 0  
  
# Ignore send redirects  
net.ipv4.conf.all.send_redirects = 0
```

Load the new settings:
```bash
sudo sysctl -p
```

**Verification:**
```bash
sudo sysctl net.ipv4.tcp_syncookies
```
*Should return: `net.ipv4.tcp_syncookies = 1`*

---

## Step 11: Configure Swap Space (Optional)

Many VMs do not have swap configured by default. Add swap to prevent out-of-memory issues:

```bash
# Create 2GB swap file  
sudo fallocate -l 2G /swapfile  
sudo chmod 600 /swapfile  
sudo mkswap /swapfile  
sudo swapon /swapfile  
  
# Make it permanent  
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**Verification:**
```bash
sudo swapon --show  
free -h
```

---

## Step 12: Configure Local Timezone (Optional)

To change the timezone to US Central on Ubuntu, you can use the `timedatectl` command:

```bash
sudo timedatectl set-timezone America/Chicago
```

**Verification:**
After running that command, you can verify the change by running:
```bash
date
```
*or*
```bash
timedatectl
```

---

## Step 13: Install Basic Monitoring Tools (Optional)

Install tools to monitor your server health:

```bash
sudo apt install htop iotop nethogs -y
```
- **htop** — Interactive process viewer
- **iotop** — Disk I/O monitoring
- **nethogs** — Network bandwidth monitoring

---

## Step 14: Reboot and Final Verification

Reboot to ensure all changes persist across restarts:

```bash
sudo reboot
```

After reboot, verify all services are running:
```bash
sudo systemctl status ssh  
sudo systemctl status fail2ban  
sudo systemctl status auditd  
sudo ufw status  
sudo aa-status
```