# Backend

how to run the backend:
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Run the server:
   ```
   uvicorn main.app:app --reload
   ```
3. The server will be running at `http://localhost:8000`
4. You can access the API documentation at `http://localhost:8000/docs`
5. To run the tests:
   ```
   pytest
   ```
   