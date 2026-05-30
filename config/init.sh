#!/bin/bash
set -e

python3 - <<'EOF'
import os, re

with open('/etc/odoo/odoo.conf.tpl') as f:
    content = f.read()

content = re.sub(
    r'\$\{(\w+)\}',
    lambda m: os.environ.get(m.group(1), m.group(0)),
    content
)

with open('/etc/odoo/odoo.conf', 'w') as f:
    f.write(content)
EOF

exec /entrypoint.sh odoo
