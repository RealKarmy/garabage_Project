@echo off
echo Setting up Egyptian Donation Platform...

REM Create project directory
mkdir donation_platform
cd donation_platform

REM Create frontend directory
mkdir frontend

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
pip install Flask==2.3.3 Flask-CORS==4.0.0 python-dotenv==1.0.0

echo Project setup complete!
echo Now copy the files to their respective locations:
echo - app.py -^> donation_platform/
echo - requirements.txt -^> donation_platform/
echo - frontend/index.html -^> donation_platform/frontend/
echo - frontend/styles.css -^> donation_platform/frontend/
echo - frontend/script.js -^> donation_platform/frontend/
echo.
echo To run the application:
echo 1. cd donation_platform
echo 2. venv\Scripts\activate.bat
echo 3. python app.py
echo 4. Open http://localhost:5000 in your browser

pause