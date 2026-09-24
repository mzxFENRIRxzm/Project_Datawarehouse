"""Create a private .env once; optionally retain credentials of this running stack."""
import argparse
import base64
import secrets
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--use-running-credentials', action='store_true')
    args = parser.parse_args()
    target = ROOT / '.env'
    if target.exists():
        print('.env already exists; kept unchanged.')
        return
    values = dict(line.split('=', 1) for line in (ROOT / '.env.example').read_text().splitlines()
                  if line.strip() and not line.startswith('#'))
    for key in ('POSTGRES_PASSWORD', 'SUPERSET_SECRET_KEY', 'SUPERSET_ADMIN_PASSWORD',
                'DJANGO_SECRET_KEY', 'LAKEHOUSE_MINIO_PASSWORD'):
        values[key] = secrets.token_hex(32)
    values['AIRFLOW_FERNET_KEY'] = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    values['AIRFLOW__CORE__EXECUTOR'] = 'LocalExecutor'
    if args.use_running_credentials:
        for container, mapping in [
            ('suphasan-postgres', {'POSTGRES_USER': 'POSTGRES_USER', 'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD', 'POSTGRES_DB': 'POSTGRES_DB'}),
            ('suphasan-lakehouse-minio', {'MINIO_ROOT_USER': 'LAKEHOUSE_MINIO_USER', 'MINIO_ROOT_PASSWORD': 'LAKEHOUSE_MINIO_PASSWORD'})]:
            inspected = json.loads(subprocess.check_output(['docker', 'inspect', container]))[0]
            env = dict(item.split('=', 1) for item in inspected['Config']['Env'])
            values.update({dest: env[src] for src, dest in mapping.items()})
    with target.open('x', encoding='utf-8') as f:
        f.write('\n'.join(f'{key}={value}' for key, value in values.items()) + '\n')
    print('Created .env; secrets are stored locally and were not printed.')


if __name__ == '__main__':
    main()
