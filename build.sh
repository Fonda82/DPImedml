#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Starting DPImedml Mali Healthcare System Build..."

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Collect static files for production
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --settings=dpimedml.settings_production

# Run database migrations for PostgreSQL
echo "🗄️  Running database migrations..."
python manage.py migrate --settings=dpimedml.settings_production

# Create demo superuser
echo "👤 Creating admin user..."
python manage.py shell --settings=dpimedml.settings_production << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@dpimedml.com', 'admin123')
    print("✅ Admin user created: admin/admin123")
else:
    print("✅ Admin user already exists")
EOF

# Create Mali healthcare demo data
echo "🏥 Creating comprehensive Mali healthcare demo data..."
python manage.py enhanced_mali_demo_data --settings=dpimedml.settings_production

# Link demo users for proper login functionality  
echo "🔗 Linking demo users to patient records..."
python manage.py link_demo_users --settings=dpimedml.settings_production

# Populate security and GDPR demo data
echo "🔒 Creating security and GDPR compliance demo data..."
python manage.py populate_security_demo --settings=dpimedml.settings_production

echo "🎉 Build complete! Mali healthcare demo system ready for Humanité & Inclusion tender!"
echo "📊 Demo includes: 55+ Mali patients, 18+ doctors, TDR compliance features"
echo "🔐 Login options: superadmin/demo1234, facilityAdmin/demo1234, docteur/demo1234, patient/demo1234" 