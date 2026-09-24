"""Create the configured administrator once, without masking migration errors."""
import os
from superset.app import create_app
from superset import security_manager

with create_app().app_context():
    username = os.environ['SUPERSET_ADMIN_USERNAME']
    if not security_manager.find_user(username=username):
        user = security_manager.add_user(
            username=username, first_name='Admin', last_name='Suphasan',
            email=os.environ['SUPERSET_ADMIN_EMAIL'],
            role=security_manager.find_role('Admin'),
            password=os.environ['SUPERSET_ADMIN_PASSWORD'],
        )
        if not user:
            raise RuntimeError('Could not create Superset administrator')
