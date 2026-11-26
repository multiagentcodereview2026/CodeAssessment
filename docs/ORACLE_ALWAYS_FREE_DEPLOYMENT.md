# Oracle Cloud Always Free deployment

This option keeps the project online on an Always Free virtual machine, so
there is no request-time cold start. Oracle can reclaim an Always Free instance
that it classifies as idle, and free Ampere capacity is not always available.
Keep database backups outside the VM.

## 1. Create an Always Free VM

In Oracle Cloud Console, open **Compute → Instances → Create instance** and use:

- Name: `codeassessment`
- Image: Ubuntu 24.04, ARM64
- Shape: `VM.Standard.A1.Flex` marked **Always Free eligible**
- OCPUs: `2`
- Memory: `12 GB`
- Boot volume: `47 GB` (minimum)
- Networking: public subnet with **Assign a public IPv4 address** enabled
- SSH key: download Oracle's generated private key or upload your public key

Do not select resources unless the console marks them **Always Free eligible**.

## 2. Configure ingress rules

Open the instance's VCN, public subnet, and default security list. Add stateful
TCP ingress rules:

| Destination port | Source CIDR | Purpose |
| ---: | --- | --- |
| 22 | Your current public IP followed by `/32` | SSH administration |
| 80 | `0.0.0.0/0` | Web application |

Do not open ports 8000, 8001, or 5432. Port 443 is needed only after HTTPS is
configured.

Ubuntu may also have a host firewall. If port 80 is still blocked after adding
the Oracle rule, connect through SSH and run:

```bash
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent
sudo iptables -I INPUT 1 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo netfilter-persistent save
```

## 3. Connect from the Mac

```bash
chmod 400 "/path/to/oracle-private-key.key"
ssh -i "/path/to/oracle-private-key.key" ubuntu@ORACLE_PUBLIC_IP
```

## 4. Deploy the application

Run these commands inside the Oracle VM:

```bash
git clone https://github.com/multiagentcodereview2026/CodeAssessment.git
cd CodeAssessment
chmod +x scripts/setup_aws_free_tier.sh scripts/setup_oracle_always_free.sh
./scripts/setup_oracle_always_free.sh
```

The script creates random PostgreSQL and JWT secrets, installs Docker, creates
4 GB of swap, pulls ARM64 language runtimes, builds the stack, and waits for
the health check. Open `http://ORACLE_PUBLIC_IP` after it succeeds.

## 5. Enable optional AI feedback

The platform works without an AI key by using deterministic fallback feedback.
To enable Groq, edit the ignored server file and recreate only the backend:

```bash
nano backend/.env
sudo docker compose up -d --force-recreate backend
```

Set `GROQ_API_KEY` in that file. Never commit or paste the key into chat.

## 6. Verify

```bash
sudo docker compose ps
curl --fail http://127.0.0.1/health
sudo docker compose exec -T execution-engine python -c "import json,urllib.request; payload=json.dumps({'code':'print(sum(map(int,input().split())))','language':'python','test_cases':[{'id':'deploy-smoke','input':'3 5','expected_output':'8'}]}).encode(); request=urllib.request.Request('http://127.0.0.1:8001/execute',data=payload,headers={'Content-Type':'application/json'}); result=json.load(urllib.request.urlopen(request,timeout=30)); assert result['status']=='ACCEPTED', result; print('Execution smoke test passed')"
```

## 7. Back up PostgreSQL

```bash
cd ~/CodeAssessment
mkdir -p backups
sudo docker compose exec -T postgres pg_dump -U codeassessment codeassessment > "backups/codeassessment-$(date +%Y%m%d-%H%M%S).sql"
```

Download backups to another computer periodically. Do not use
`docker compose down -v`, because `-v` deletes the database volume.
