import os
import shutil
import secrets
import base64
from pathlib import Path

def generate_secrets(env_content):
    """Generate secure random keys for the environment variables."""
    # Django secret key
    django_key = secrets.token_urlsafe(50)
    
    # Superset secret key
    superset_key = secrets.token_urlsafe(42)
    
    # Airflow fernet key (32-byte url-safe base64 encoded)
    fernet_key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    
    # Replace in content
    env_content = env_content.replace('changeme_django_secret_key', django_key)
    env_content = env_content.replace('changeme_superset_secret_key_minimum_42_characters_long', superset_key)
    env_content = env_content.replace('changeme_fernet_key', fernet_key)
    
    # Replace passwords with secure ones for production (optional, keeping default for now)
    # env_content = env_content.replace('changeme_pg_password', secrets.token_urlsafe(16))
    # env_content = env_content.replace('changeme_ch_password', secrets.token_urlsafe(16))
    
    return env_content

def main():
    base_dir = Path(__file__).parent.absolute()
    parent_dir = base_dir.parent
    app_dir = base_dir / 'app'
    
    print("🚀 Starting Suphasan Data Warehouse Setup...")
    
    # 1. Setup Environment Variables
    env_example = base_dir / '.env.example'
    env_file = base_dir / '.env'
    
    if not env_file.exists():
        if env_example.exists():
            print("📝 Creating .env file from .env.example with secure keys...")
            with open(env_example, 'r', encoding='utf-8') as f:
                content = f.read()
            
            content = generate_secrets(content)
            
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ .env file created successfully.")
        else:
            print("❌ .env.example not found!")
    else:
        print("ℹ️ .env file already exists. Skipping generation.")

    # 2. Copy Django Application Code
    print("📦 Copying Django application code into app directory...")
    
    django_dirs_to_copy = ['suphasan', 'sale', 'inventory', 'marketing', 'logistics', 'analytics', 'static', 'templates', 'dashboard']
    django_files_to_copy = ['manage.py', 'main.py']
    
    for item in django_dirs_to_copy:
        src = parent_dir / item
        dst = app_dir / item
        if src.exists() and src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"  - Copied directory: {item}")
            
    for item in django_files_to_copy:
        src = parent_dir / item
        dst = app_dir / item
        if src.exists() and src.is_file():
            shutil.copy2(src, dst)
            print(f"  - Copied file: {item}")

    # 3. Create required directories
    print("📁 Ensuring required directories exist...")
    dirs_to_create = [
        base_dir / 'postgres' / 'init',
        base_dir / 'dags' / 'sql' / 'bronze',
        base_dir / 'dags' / 'sql' / 'silver',
        base_dir / 'dags' / 'sql' / 'gold',
        base_dir / 'superset',
        base_dir / 'nginx',
        base_dir / 'docs',
        base_dir / 'logs'
    ]
    
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)
        
    print("✅ Directory structure verified.")
    
    print("\n" + "="*50)
    print("🎉 Setup completed successfully!")
    print("="*50)
    print("\nNext steps:")
    print("1. Review the .env file and update passwords if necessary.")
    print("2. Run the following command to start the entire data warehouse stack:")
    print("\n   docker compose up -d\n")
    print("3. Monitor the startup process:")
    print("\n   docker compose logs -f\n")

if __name__ == '__main__':
    main()
