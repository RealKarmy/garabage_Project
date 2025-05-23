#!/bin/bash

echo "Setting up Egyptian Donation Platform..."

# Create project directory
mkdir -p donation_platform
cd donation_platform

# Create frontend directory
mkdir -p frontend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install Flask==2.3.3 Flask-CORS==4.0.0 python-dotenv==1.0.0

echo "Project setup complete!"
echo "Now copy the files to their respective locations:"
echo "- app.py -> donation_platform/"
echo "- requirements.txt -> donation_platform/"
echo "- frontend/index.html -> donation_platform/frontend/"
echo "- frontend/styles.css -> donation_platform/frontend/"
echo "- frontend/script.js -> donation_platform/frontend/"
echo ""
echo "To run the application:"
echo "1. cd donation_platform"
echo "2. source venv/bin/activate"
echo "3. python app.py"
echo "4. Open http://localhost:5000 in your browser"