import os
import json
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import traceback

# Import our parsers
from regex_parser import RegexResumeParser
from fixed_pyresparser import FixedResumeParser

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_result_for_display(data, parser_name):
    """Format parser results for better display in HTML"""
    if not data:
        return {"error": f"{parser_name} failed to extract data"}
    
    formatted = {
        "parser_name": parser_name,
        "success": True,
        "data": {}
    }
    
    for key, value in data.items():
        if value is None:
            formatted["data"][key] = "Not found"
        elif isinstance(value, list):
            if not value:
                formatted["data"][key] = "Not found"
            elif len(value) > 10:  # Limit display to first 10 items
                formatted["data"][key] = value[:10] + [f"... and {len(value)-10} more"]
            else:
                formatted["data"][key] = value
        elif isinstance(value, dict):
            # Handle nested dictionaries (like experience)
            formatted["data"][key] = value
        else:
            formatted["data"][key] = str(value)
    
    return formatted

@app.route('/')
def index():
    """Main page with file upload form"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process with both parsers"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload PDF, DOCX, or DOC files only.')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Secure the filename
            filename = secure_filename(file.filename)
            
            # Save uploaded file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process with both parsers
            results = {
                "filename": filename,
                "file_size": os.path.getsize(file_path),
                "parsers": {}
            }
            
            # Parser 1: Regex-based parser
            try:
                regex_parser = RegexResumeParser()
                regex_data = regex_parser.extract_resume_data(file_path)
                results["parsers"]["regex"] = format_result_for_display(regex_data, "Regex Parser")
            except Exception as e:
                results["parsers"]["regex"] = {
                    "parser_name": "Regex Parser",
                    "success": False,
                    "error": str(e)
                }
            
            # Parser 2: spaCy/NLTK-based parser
            try:
                spacy_parser = FixedResumeParser(file_path)
                spacy_data = spacy_parser.get_extracted_data()
                results["parsers"]["spacy"] = format_result_for_display(spacy_data, "spaCy + NLTK Parser")
            except Exception as e:
                results["parsers"]["spacy"] = {
                    "parser_name": "spaCy + NLTK Parser",
                    "success": False,
                    "error": str(e)
                }
            
            # Clean up uploaded file
            try:
                os.remove(file_path)
            except:
                pass  # Ignore cleanup errors
            
            return render_template('results.html', results=results)
    
    except Exception as e:
        flash(f'Error processing file: {str(e)}')
        return redirect(url_for('index'))

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """API endpoint for programmatic access"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Process with both parsers
        results = {}
        
        try:
            regex_parser = RegexResumeParser()
            results['regex_parser'] = regex_parser.extract_resume_data(file_path)
        except Exception as e:
            results['regex_parser'] = {'error': str(e)}
        
        try:
            spacy_parser = FixedResumeParser(file_path)
            results['spacy_parser'] = spacy_parser.get_extracted_data()
        except Exception as e:
            results['spacy_parser'] = {'error': str(e)}
        
        # Clean up
        try:
            os.remove(file_path)
        except:
            pass
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/about')
def about():
    """About page explaining the parsers"""
    return render_template('about.html')

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash("File is too large. Maximum size is 16MB.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)