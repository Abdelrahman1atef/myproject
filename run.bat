@echo off

:: Activate the virtual environment
call venv\Scripts\activate

:: Install dependencies
pip install -r requirements.txt

:: Run the application
gunicorn ramzy_app.wsgi:application --bind 0.0.0.0:8000