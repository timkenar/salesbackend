
# 🚀 Django Backend – Automated CI/CD Deployment

![GitHub branch check runs](https://img.shields.io/github/check-runs/chepkenertimothy/salesbackend/main?logo=github)
![GitHub last commit](https://img.shields.io/github/last-commit/chepkenertimothy/salesbackend?color=blue)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/chepkenertimothy/salesbackend/deploy.yml?label=Deployment&logo=githubactions&color=brightgreen)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## 🧩 Overview

This project uses **GitHub Actions CI/CD** to automate deployment of the **SalesBackend Django app** to a live **VPS** running Ubuntu, Gunicorn, and Nginx.

Whenever code is pushed to the `main` branch, GitHub automatically:
1. Connects to the VPS via SSH  
2. Pulls the latest code  
3. Installs dependencies  
4. Runs database migrations  
5. Collects static files  
6. Restarts Gunicorn and Nginx  

---

## ✅ Achievements

- Configured **Django production environment**
- Set up **Gunicorn** and **Nginx** on the VPS
- Installed **SSL with Let’s Encrypt**
- Created a **systemd service** for app management
- Implemented **GitHub Actions CI/CD** for zero-downtime deployment
- Enabled **automated static and media handling**

---

## 🏗️ Deployment Architecture

```text
GitHub → GitHub Actions → SSH → VPS
                                     ├── Gunicorn (Django WSGI Server)
                                     ├── Nginx (Reverse Proxy + SSL)
                                     └── Systemd (Service Manager)
````

---

## ⚙️ GitHub Actions Workflow

📂 **File:** `.github/workflows/deploy.yml`

```yaml
name: 🚀 Deploy to VPS

on:
  push:
    branches:
      - main  # Trigger deployment on push to main branch

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up SSH
        uses: webfactory/ssh-agent@v0.9.0
        with:
          ssh-private-key: ${{ secrets.VPS_SSH_KEY }}

      - name: Deploy to VPS
        run: |
          ssh -o StrictHostKeyChecking=no root@(VPS IP Address) << 'EOF'
            echo "🚀 Starting deployment on VPS..."

            cd your/project/path || exit 1

            echo "📦 Pulling latest code..."
            git fetch origin main
            git reset --hard origin/main

            echo "🐍 Activating virtual environment..."
            source /root/root/env/bin/activate

            echo "📦 Installing dependencies..."
            pip install --upgrade pip
            pip install -r requirements.txt

            echo "🧱 Applying database migrations..."
            python manage.py migrate --noinput

            echo "🎨 Collecting static files..."
            python manage.py collectstatic --noinput

            echo "🔄 Restarting services..."
            systemctl restart salesbackend
            systemctl restart nginx

            echo "✅ Deployment completed successfully!"
          EOF
```

---

## 🔐 SSH Authentication Setup

To allow GitHub to connect securely to your VPS, we used **SSH key-based authentication**.

### 1. Generate a dedicated SSH key (locally or on VPS)

```bash
ssh-keygen -t ed25519 -C "github-cicd"
```

This creates:

* Private key: `~/.ssh/github_cicd`
* Public key: `~/.ssh/github_cicd.pub`

---

### 2. Add the public key to your VPS

```bash
cat ~/.ssh/github_cicd.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

---

### 3. Add the private key to GitHub Secrets

1. Go to your GitHub repository →
   **Settings → Secrets and variables → Actions**

2. Click **New repository secret**

3. Add:

   * **Name:** `VPS_SSH_KEY`
   * **Value:** *Contents of your private SSH key (`~/.ssh/github_cicd`)*

---

## 🧰 VPS Configuration Recap

### 🧠 Gunicorn systemd service

📄 `/etc/systemd/system/salesbackend.service`

```ini
[Unit]
Description=Gunicorn service for Django SalesBackend
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=your/project/path
ExecStart=/root/root/env/bin/gunicorn --workers 3 --bind unix:your/project/path/salesbackend.sock salesbackend.wsgi:application

[Install]
WantedBy=multi-user.target
```

---

### 🌐 Nginx configuration

📄 `/etc/nginx/sites-available/salesbackend`

```nginx
server {
    server_name api.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias your/project/path/staticfiles/;
    }

    location /media/ {
        alias your/project/path/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:your/project/path/salesbackend.sock;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}
```

---

## 🧪 Testing the Pipeline

1. Commit and push your changes:

   ```bash
   git add .
   git commit -m "Test deployment via GitHub Actions"
   git push origin main
   ```

2. Go to your **GitHub repo → Actions tab** and monitor the deployment job.

3. Once complete, check your live site:
   🔗 **[https://api.yourdomain.com](https://api.yourdomain.com]**

---

## 🧯 Troubleshooting Guide

| Problem                         | Cause                    | Solution                                                         |
| ------------------------------- | ------------------------ | ---------------------------------------------------------------- |
| `Permission denied (publickey)` | Wrong SSH key            | Ensure the public key is added to `/root/.ssh/authorized_keys`   |
| `502 Bad Gateway`               | Gunicorn not running     | Restart with `sudo systemctl restart salesbackend`               |
| `DisallowedHost`                | Missing domain in Django | Add the domain to `ALLOWED_HOSTS` in `.env`                      |
| `collectstatic` error           | File permission issue    | Ensure `/staticfiles` is owned by the same user running Gunicorn |

---

## 📘 Summary

| Component           | Description               |
| ------------------- | ------------------------- |
| **CI/CD Tool**      | GitHub Actions            |
| **Server OS**       | Ubuntu (VPS)              |
| **Web Server**      | Nginx                     |
| **App Server**      | Gunicorn                  |
| **Language**        | Python 3.12               |
| **Framework**       | Django 5.x                |
| **SSL**             | Let’s Encrypt             |
| **Branch**          | `main`                    |
| **Trigger**         | Push to main branch       |
| **Deployment Path** | `your/project/path` |

---

## 🌟 Future Enhancements

* Add **test & lint** stages before deployment
* Use a **non-root deploy user** for better security
* Implement **zero-downtime rolling updates**
* Add **Slack notifications** for deployment status

---

## 🏁 Deployment in Action

✅ **Every push to `main` automatically deploys your Django app to your VPS.**
🔗 Live site: [https://api.yourdomain.com](https://api.yourdomain.com)

---

🛠 **Maintained by:** [Timothy Chepkener](mailto:chepkenertimothy@gmail.com)
📅 **Last Updated:** November 2025
📄 **License:** MIT

```

