# Career Up - AI-Powered Career Development Platform

Career Up is a comprehensive AI-powered platform designed to help job seekers and professionals accelerate their career growth through intelligent resume analysis, job matching, career guidance, and interview preparation.

## Features

### 1. Resume Parser
- Upload your resume in PDF, DOC, or DOCX format
- AI-powered analysis of your skills, experience, and qualifications
- Receive a detailed resume score and feedback on structure
- Get actionable suggestions to improve resume quality

### 2. Job Matcher
- Find relevant job opportunities based on your resume and skills
- Customizable job search by position or field
- Detailed job listings with company, location, and description
- Matching algorithm prioritizes jobs that fit your experience

### 3. Career Guidance
- Personalized career path recommendations
- Detailed skill gap analysis
- Custom skill development plans with timeline estimates
- Recommended certifications and courses for career advancement
- Project ideas to build your portfolio

### 4. Interview Preparation
- Customized interview questions based on your resume and target job
- Questions organized by categories (experience, technical skills, soft skills)
- Practice answering common and job-specific questions
- Tips and strategies for successful interviews

### 5. AI Interview Simulation
- Real-time conversation with an AI interviewer
- Practice answering questions in a simulated interview environment
- Receive detailed feedback and performance score after the interview
- Specific suggestions for improvement based on your responses

## Technology Stack

### Frontend
- HTML5, CSS3, JavaScript
- Bootstrap 5 for responsive design
- Font Awesome icons
- Animate.css for animations
- AJAX for asynchronous requests

### Backend
- Python 3.8+
- Flask web framework
- Jinja2 templating engine
- MySQL database for user data storage

### AI & Machine Learning
- Google Generative AI (Gemini) for AI-powered features
- PyPDF2 and PyMuPDF (fitz) for document processing
- Natural Language Processing for resume and text analysis

### Security
- Email verification with OTP
- Password hashing and secure authentication
- Session management

## Setup

### Prerequisites
- Python 3.8 or higher
- MySQL Server
- Google Generative AI API key (for AI-powered features)
- SMTP server access for email sending (for registration)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/career-up.git
   cd career-up
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   python install_dependencies.py
   ```
   
   Or manually install required packages:
   ```
   pip install flask mysql-connector-python PyPDF2 pymupdf google-generativeai==0.3.1 protobuf==3.20.3
   ```

4. Configure Google Generative AI API:
   - Get your API key from Google AI Studio
   - Add it to the `config.py` file:
     ```python
     GEMINI_API_KEY = "your-gemini-api-key"
     ```

5. Set up the MySQL database:
   ```sql
   CREATE DATABASE career_up;
   ```

6. Configure email for OTP verification in `run.py`:
   ```python
   # Set environment variables for email
   os.environ['EMAIL_SENDER'] = "your_email@gmail.com"
   os.environ['EMAIL_PASSWORD'] = "your_app_password"  # App password for Gmail
   ```

## Usage

1. Start the application:
   ```
   python run.py
   ```

2. Visit `http://localhost:5000` in your web browser

3. Register for an account and verify your email

4. Upload your resume to get started with personalized features

5. Navigate through the dashboard to access all tools:
   - Resume Parser: Upload and analyze your resume
   - Job Matcher: Find matching job opportunities
   - Career Guidance: Get personalized career path recommendations
   - Interview Preparation: Practice with tailored questions
   - Interview Chatbot: Simulate a real interview with AI

## Project Structure

```
career-up/
├── app.py                  # Main Flask application
├── core.py                 # Core functionality and database operations
├── run.py                  # Application entry point
├── config.py               # Configuration settings
├── interview_prep2.py      # Interview simulation functionality
├── templates/              # HTML templates
│   ├── base.html           # Base template with layout
│   ├── dashboard.html      # User dashboard
│   ├── resume_parser.html  # Resume upload and analysis
│   └── ...                 # Other template files
├── utils/                  # Utility functions
│   ├── file_helpers.py     # File operation utilities
│   └── ...                 # Other utility modules
├── output/                 # Generated JSON and analysis files
│   ├── job_matches.json    # Job matching results
│   ├── structured_resume.json  # Processed resume data
│   └── interview_prep.json # Interview questions
└── uploads/                # User uploaded files (resumes)
```

## Development

- To add new features, extend the corresponding functionality in:
  - `app.py` for route handlers
  - `core.py` for core functionality 
  - Create new templates in the `templates/` directory

- The application follows a modular structure to separate concerns:
  - Route handling in `app.py`
  - Business logic in `core.py` and specialized modules
  - Data storage in MySQL database
  - File storage in `uploads/` and `output/` directories

## Troubleshooting

### Common Issues
- **Email verification not working**: Check SMTP settings and credentials
- **AI features not working**: Verify your Google Generative AI API key
- **Database connection errors**: Ensure MySQL server is running and credentials are correct

### Debugging
- Check the console output for error messages
- The application uses structured logging to help identify issues
- For AI related issues, check if the API key has proper permissions

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Generative AI (Gemini) for powering the intelligent features
- Bootstrap for the responsive UI components
- The open-source community for libraries and tools 