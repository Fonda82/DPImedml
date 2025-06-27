#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput --settings=dpimedml.settings_production

# Run database migrations
python manage.py migrate --settings=dpimedml.settings_production

# Create demo data for Mali healthcare system
echo "Creating Mali healthcare demo data..."
python manage.py enhanced_mali_demo_data --settings=dpimedml.settings_production

# Link demo users for proper login functionality
echo "Linking demo users..."
python manage.py link_demo_users --settings=dpimedml.settings_production

# Create superuser for admin access (optional, for demo purposes)
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@dpimedml.com', 'admin123') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell --settings=dpimedml.settings_production

echo "Build completed successfully!" 