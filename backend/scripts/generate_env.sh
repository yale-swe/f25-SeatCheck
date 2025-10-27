
# helper: generate a strong SECRET_KEY and write a local .env (ignored by git)
# usage: run from backend/ directory: ./scripts/generate_env.sh

set -euo pipefail

# generate a 48-byte URL-safe secret
SECRET=$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)
#write it to local env file
cat > .env <<EOF
# Local environment (generated). This file is gitignored; do NOT commit.
secret_key=${SECRET}
session_cookie_name=seatcheck_session
session_expire_minutes=1440

# CAS auth (use the real CAS for integration testing)
cas_base_url=https://secure.its.yale.edu/cas
frontend_url=http://localhost:3000

EOF

echo ".env created in $(pwd)/.env (SECRET_KEY set). File is gitignored by default."
