## PDF Tool Application

This application provides a web interface for merging and splitting PDF files.

![Project Demo](uploads/ss.png)

### Features
- **Merge PDFs**: Combine multiple PDF files into a single document.
- **Split PDF**: Split a single PDF file into individual pages.
- **CAPTCHA Validation**: Prevents spam and ensures bot protection.

### Prerequisites
- Python 3.7+

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/draprar/flask-pdf-tools_pdfy.git
   cd flask-pdf-tools_pdfy
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate # For Linux/MacOS
   venv\Scripts\activate  # For Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following keys:
   ```
   FLASK_ENV=development
   SECRET_KEY=your_secret_key_here
   MAX_CONTENT_LENGTH=16777216
   UPLOAD_FOLDER=uploads
   ALLOWED_EXTENSIONS=pdf
   ```

5. Create the `uploads` directory:
   ```bash
   mkdir uploads
   ```

### Running the Application
1. Start the Flask application:
   ```bash
   flask run
   ```

2. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

### Configuration
- Modify `MAX_CONTENT_LENGTH` in the `.env` file to set the maximum file size for uploads.
- Update `SECRET_KEY` to a strong, unique key for session security.

### Testing
To run tests:
```bash
pytest
```

### License
This project is licensed under the MIT License. See the LICENSE file for details.
