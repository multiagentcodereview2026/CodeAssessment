# AWS EC2 demo deployment

This deployment runs the frontend, API, PostgreSQL, and isolated language
runners on one Ubuntu EC2 instance. It is suitable for a supervised project
demo. The execution engine mounts the host Docker socket, so use a dedicated
instance and do not expose ports 8000, 8001, or 5432 to the internet.

## 1. Launch the instance

Use these EC2 settings:

- Ubuntu Server 24.04 LTS, 64-bit x86
- `t3.small` recommended (2 GiB RAM); `t3.micro` can be slow even with swap
- 30 GiB gp3 storage
- Create or select an SSH key pair and keep its `.pem` file private

Inbound security-group rules:

| Type | Port | Source |
| --- | ---: | --- |
| SSH | 22 | My IP |
| HTTP | 80 | Anywhere IPv4 (`0.0.0.0/0`) |
| HTTPS | 443 | Anywhere IPv4 (`0.0.0.0/0`), only when HTTPS is configured |

Do not add public rules for 8000, 8001, or 5432.

## 2. Connect and deploy

On the computer containing the key:

```bash
chmod 400 "/path/to/project-key.pem"
ssh -i "/path/to/project-key.pem" ubuntu@EC2_PUBLIC_IP
```

On the EC2 instance:

```bash
git clone https://github.com/multiagentcodereview2026/CodeAssessment.git
cd CodeAssessment
chmod +x scripts/setup_aws_free_tier.sh
./scripts/setup_aws_free_tier.sh
```

The script creates private database and JWT secrets, installs Docker when
needed, creates `backend/.env`, pulls every language runtime, builds the stack,
and waits for the application health check.

Open `http://EC2_PUBLIC_IP` after the script reports success.

## 3. Optional AI feedback

AI feedback is optional. On the instance, edit `backend/.env` and set your own
Groq key. Never paste the key into chat or commit it to Git.

```bash
nano backend/.env
sudo docker compose up -d --force-recreate backend
```

Check that the key is present without printing it:

```bash
sudo docker compose exec -T backend python -c "from config.settings import settings; print(bool(settings.GROQ_API_KEY))"
```

## 4. Verify the deployment

```bash
sudo docker compose ps
curl --fail http://127.0.0.1/health
curl --fail http://127.0.0.1:8000/health
sudo docker compose exec -T execution-engine python -c "import json,urllib.request; payload=json.dumps({'code':'print(sum(map(int,input().split())))','language':'python','test_cases':[{'id':'deploy-smoke','input':'3 5','expected_output':'8'}]}).encode(); request=urllib.request.Request('http://127.0.0.1:8001/execute',data=payload,headers={'Content-Type':'application/json'}); result=json.load(urllib.request.urlopen(request,timeout=30)); assert result['status']=='ACCEPTED', result; print('Execution smoke test passed')"
```

All four application containers should be running, and the backend,
execution-engine, and PostgreSQL containers should report healthy.

## 5. Update the deployed application

```bash
cd ~/CodeAssessment
git pull --ff-only
sudo docker compose up -d --build
sudo docker compose ps
```

## 6. Preserve data

Stopping the stack without `-v` preserves PostgreSQL data:

```bash
sudo docker compose down
```

Create a database backup before upgrades:

```bash
mkdir -p backups
sudo docker compose exec -T postgres pg_dump -U codeassessment codeassessment > "backups/codeassessment-$(date +%Y%m%d-%H%M%S).sql"
```

Do not run `docker compose down -v` unless the stored database is intentionally
being deleted.

## 7. Add HTTPS later

A stable HTTPS deployment needs a domain name pointing to the instance (or an
Elastic IP) and a TLS reverse proxy such as Caddy or an AWS load balancer. Keep
port 80 available until certificate setup is complete, then use the exact HTTPS
origin for `CORS_ALLOW_ORIGINS`.
