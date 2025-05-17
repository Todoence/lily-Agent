===========================
Lily Agent - Quick Start Guide
===========================

Thank you for downloading Lily Agent!

This is a FastAPI-based application. Follow the steps below to run it locally.
Demo video: https://www.youtube.com/watch?v=zpdn_4kstuM
---------------------------
📦 How to Run (Step-by-Step)
---------------------------

!WARNING: Please do not share .evn to anybody, the API keys will be deleted later!

1. Make sure you have Python 3.12.9 installed.

2. Open your terminal or command prompt and navigate to the project folder:
   > cd path/to/unzipped-folder

3. (Optional but recommended) Create a virtual environment:
   > python -m venv venv
   > source venv/bin/activate       [Mac/Linux]
   > venv\Scripts\activate          [Windows]

4. Install all required dependencies:
   > pip install -r requirements.txt

5. Start the development server:
   > uvicorn main:app --reload

7. Open your browser and go to:
   > http://127.0.0.1:8000

8. DEBUG_MODE
    > For quick demo, go to .env and set DEBUG_MODE=True, only outreach will use real API
    > For real case, set DEBUG_MODE=False, every step will call APIs to run, it may take 5-10 mins to get all results done.

9. Use case
    >Enter the company url that you are working on, for example, Lead Generation & Outreach for Dupont Tedlar
    >https://www.dupont.com/brands/tedlar.html
---------------------------
📚 API Documentation
---------------------------
FastAPI provides interactive docs at:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc:      http://127.0.0.1:8000/redoc

---------------------------
🛠 Troubleshooting
---------------------------
- Make sure Python and pip are in your PATH.
- If you see "ModuleNotFoundError", double-check your `pip install` step.
- If port 8000 is in use, change it by editing the run command:
  > uvicorn main:app --port 8001 --reload

---------------------------
📁 Files & Structure
---------------------------
- main.py .................. FastAPI entry point
- database.py .................. DB  operation entry point
- requirements.txt ......... Python dependencies
- .env  ...... Environment variables
- static/ .................. JS, CSS assets
- templates/ ............... HTML templates
- data/ .................... Data files

Enjoy building! 🚀
