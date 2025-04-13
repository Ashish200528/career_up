import mysql.connector as sql
import os
import json
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid
from datetime import datetime
import socket
from werkzeug.security import generate_password_hash, check_password_hash
import importlib.util
import config
from utils.file_helpers import load_json_from_file

# Database configuration
db_config = {
    'host': "localhost",
    'user': "root",
    'passwd': "Student1020@",
    'database': "career_advisor"
}

# Email configuration - using environment variables for security
EMAIL_SENDER = os.environ.get('EMAIL_SENDER', "securebank11@gmail.com")
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', "ibfttotgvdnnztkr")

# Database connection
def get_db_connection():
    try:
        # Add connection parameters to help prevent issues
        conn = sql.connect(
            **db_config,
            autocommit=False,  # Explicitly set autocommit off for transaction control
            buffered=True,     # Use buffered cursor to consume results
            consume_results=True  # Automatically consume unread results
        )
        return conn
    except Exception as e:
        print(f"[ERROR] Database connection error: {str(e)}")
        raise

# Initialize database
def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table - removed name column
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create resume_data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resume_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            resume_text TEXT,
            skills TEXT,
            experience TEXT,
            education TEXT,
            resume_score INT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create job_matches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_matches (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            job_title VARCHAR(255),
            company VARCHAR(255),
            match_score INT,
            job_description TEXT,
            url VARCHAR(255),
            location VARCHAR(255),
            posted_date VARCHAR(100),
            match_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Create career_guidance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS career_guidance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            guidance_text TEXT,
            career_path VARCHAR(100),
            guidance_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create interview_prep table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_prep (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            question TEXT,
            answer TEXT,
            feedback TEXT,
            score INT,
            prep_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create otp_store table to track OTPs (new)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS otp_store (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(100) NOT NULL,
            otp VARCHAR(6) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_used BOOLEAN DEFAULT FALSE
        )
    """)
    
    # Create email_logs table to track email sending (new)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            recipient VARCHAR(100) NOT NULL,
            subject VARCHAR(255) NOT NULL,
            status VARCHAR(20) NOT NULL,
            error_message TEXT,
            ip_address VARCHAR(45),
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

# User Authentication Functions
def register_user(name, email, password):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return False, "Email already registered"
        
        # Store password as is (no hashing)
        cursor.execute("""
            INSERT INTO users (email, password)
            VALUES (%s, %s)
        """, (email, password))
        
        conn.commit()
        return True, "Registration successful"
    except Exception as e:
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def login_user(email, password):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user and user['password'] == password:  # Direct password comparison
            return True, user
        else:
            return False, "Invalid email or password"
    except Exception as e:
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def send_email(receiver_email, subject, message):
    """
    Send an email using the configured email sender.
    Records the email attempt in the database for tracking.
    """
    if not EMAIL_PASSWORD:
        print("Error: Email password not set, email sending is required")
        return False
    
    # Log email attempt
    conn = get_db_connection()
    cursor = conn.cursor()
    current_ip = get_ip_address()
    
    try:
        # Create the email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['To'] = receiver_email
        msg['From'] = f"Intelligent Career Up <{EMAIL_SENDER}>"
        msg.attach(MIMEText(message, 'html'))
        
        # Connect to Gmail SMTP server
        print(f"Connecting to SMTP server...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        # Login with credentials
        print(f"Logging in with email: {EMAIL_SENDER}")
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        
        # Send the email
        print(f"Sending email to: {receiver_email}")
        server.send_message(msg)
        server.quit()
        
        # Record successful email
        print(f"Email sent successfully to {receiver_email}")
        cursor.execute("""
            INSERT INTO email_logs (recipient, subject, status, ip_address)
            VALUES (%s, %s, %s, %s)
        """, (receiver_email, subject, "SUCCESS", current_ip))
        conn.commit()
        
        return True
    except Exception as e:
        error_message = str(e)
        print(f"Failed to send email: {error_message}")
        
        # Try to record failed email
        try:
            cursor.execute("""
                INSERT INTO email_logs (recipient, subject, status, error_message, ip_address)
                VALUES (%s, %s, %s, %s, %s)
            """, (receiver_email, subject, "FAILED", error_message, current_ip))
            conn.commit()
        except Exception as log_error:
            print(f"Failed to log email error: {str(log_error)}")
            
        return False
    finally:
        cursor.close()
        conn.close()

def get_ip_address():
    """Get the current machine's IP address"""
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except:
        return "127.0.0.1"  # Default if unable to determine

def generate_otp():
    """
    Generate a secure 6-digit OTP and store it in the database
    with expiration time and tracking.
    """
    otp = str(random.randint(100000, 999999))
    return otp

def store_otp(email, otp):
    """Store OTP in database with expiration time"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Set expiration time to 10 minutes from now
        cursor.execute("""
            INSERT INTO otp_store (email, otp, expires_at)
            VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL 10 MINUTE))
        """, (email, otp))
        conn.commit()
        return True
    except Exception as e:
        print(f"Failed to store OTP: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def verify_otp(email, otp):
    """Verify if the OTP is valid and not expired"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT * FROM otp_store 
            WHERE email = %s AND otp = %s AND is_used = FALSE
            AND expires_at > NOW()
            ORDER BY created_at DESC LIMIT 1
        """, (email, otp))
        
        result = cursor.fetchone()
        
        if result:
            # Mark OTP as used
            cursor.execute("""
                UPDATE otp_store SET is_used = TRUE
                WHERE id = %s
            """, (result['id'],))
            conn.commit()
            return True
        else:
            return False
    except Exception as e:
        print(f"OTP verification error: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

# Resume Parser Functions
def parse_resume(user_id, resume_text):
    # This would call the resume_parser module
    # For now we'll use a mock implementation
    skills = ["Python", "JavaScript", "Data Analysis", "Communication"]
    experience = "5 years of software development experience"
    education = "Bachelor's in Computer Science"
    resume_score = random.randint(70, 95)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO resume_data (user_id, resume_text, skills, experience, education, resume_score)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            resume_text = VALUES(resume_text),
            skills = VALUES(skills),
            experience = VALUES(experience),
            education = VALUES(education),
            resume_score = VALUES(resume_score),
            last_updated = CURRENT_TIMESTAMP
        """, (user_id, resume_text, json.dumps(skills), experience, education, resume_score))
        
        conn.commit()
        return True, {
            "skills": skills,
            "experience": experience,
            "education": education,
            "resume_score": resume_score
        }
    except Exception as e:
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

# Job Matcher Functions
def find_job_matches(user_id, job_position=None):
    try:
        # Import required modules
        import importlib
        import config
        from utils.file_helpers import load_json_from_file
        
        print(f"[INFO] Starting job matching for user {user_id}")
        
        # First check if there's resume data
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get user's skills from resume_data
            cursor.execute("SELECT skills FROM resume_data WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            
            # Important: Fetch all remaining results to avoid "Unread result found" error
            while cursor.nextset():
                pass
            
            if not result:
                print("[ERROR] No resume data found")
                return False, "No resume data found. Please parse a resume first."
        finally:
            # Ensure cursor and connection are properly closed
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
        # Check if job_matcher.py exists before trying to load it
        job_matcher_path = os.path.join(config.BASE_DIR, "job_matcher.py")
        if not os.path.exists(job_matcher_path):
            print(f"[ERROR] job_matcher.py not found at {job_matcher_path}")
            return False, "Job matcher module not found. Please contact support."
        
        # Load the job_matcher module
        try:
            print(f"[DEBUG] Loading job_matcher from {job_matcher_path}")
            
            # Check for dependency packages
            try:
                # Try importing Google Generative AI packages to check availability
                from google import genai
                from google.genai import types
                genai_available = True
                print("[INFO] Google Generative AI package is available")
            except ImportError as ie:
                genai_available = False
                print(f"[WARNING] Google Generative AI package not available: {str(ie)}. Using fallback mode.")
            
            # Load the module
            spec = importlib.util.spec_from_file_location(
                "job_matcher", 
                job_matcher_path
            )
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'job_matcher_main'):
                print("[INFO] Found job_matcher_main function, calling it now")
                # Call the job_matcher_main function with job_position
                job_matches = module.job_matcher_main(job_position)
                if job_matches is None:
                    print("[ERROR] job_matcher_main returned None")
                    return False, "Error finding job matches. Please try again."
                
                print(f"[DEBUG] Job matches result: {type(job_matches)}")
                
                # Save job matches to database
                db_error = None
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # Clear previous job matches for this user
                    cursor.execute("DELETE FROM job_matches WHERE user_id = %s", (user_id,))
                    
                    # Get table information to check schema
                    cursor.execute("DESCRIBE job_matches")
                    columns = [col[0] for col in cursor.fetchall()]
                    print(f"[DEBUG] job_matches table columns: {columns}")
                    
                    # Ensure all remaining results are consumed
                    while cursor.nextset():
                        pass
                    
                    # Store new job matches
                    for job in job_matches:
                        # Prepare insert fields dynamically based on available columns
                        fields = ["user_id", "job_title", "company", "match_score", "job_description", "url"]
                        values = [
                            user_id, 
                            job.get("Job Title", "Unknown Title"), 
                            job.get("Company", "Unknown Company"), 
                            job.get("match_score", 85),  # Default match score
                            job.get("Short Description", "No description available"), 
                            job.get("url", "#")
                        ]
                        
                        # Add location field if it exists in the schema
                        if "location" in columns:
                            fields.append("location")
                            values.append(job.get("Location", "Remote/Flexible"))
                        
                        # Add posted_date field if it exists in the schema
                        if "posted_date" in columns:
                            fields.append("posted_date")
                            values.append(job.get("Posted Date", "Recent"))
                        
                        # Create dynamic placeholders for SQL query
                        placeholders = ", ".join(["%s"] * len(fields))
                        fields_str = ", ".join(fields)
                        
                        # Execute dynamic SQL query
                        query = f"INSERT INTO job_matches ({fields_str}) VALUES ({placeholders})"
                        cursor.execute(query, values)
                    
                    conn.commit()
                    
                    # Important: Fetch all remaining results to avoid "Unread result found" error
                    while cursor.nextset():
                        pass
                        
                    print("[INFO] Job matches saved to database")
                except Exception as e:
                    db_error = str(e)
                    print(f"[ERROR] Error saving job matches to database: {db_error}")
                finally:
                    # Ensure cursor and connection are properly closed
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()
                
                # Return job matches even if db saving failed
                return True, job_matches
            else:
                print("[ERROR] job_matcher_main function not found in the module")
                return False, "Job matching function not available"
                
        except Exception as e:
            print(f"[ERROR] Error with job matcher: {str(e)}")
            
            # Fall back to loading the JSON directly
            try:
                job_matches = load_json_from_file(config.JOB_MATCHES_JSON)
                if job_matches:
                    print("[INFO] Successfully loaded job matches from JSON file")
                    return True, job_matches
                else:
                    print("[WARNING] Could not load job matches from JSON file, using placeholder data")
                    # Create minimal fallback data
                    fallback_jobs = [
                        {
                            "Job Title": job_position if job_position else "Software Developer",
                            "Company": "Tech Company",
                            "Location": "Remote",
                            "Posted Date": "Recent",
                            "Short Description": "Software development position",
                            "match_score": 85,
                            "url": "#"
                        }
                    ]
                    return True, fallback_jobs
            except Exception as json_error:
                print(f"[ERROR] Error loading job matches JSON: {str(json_error)}")
            
            return False, f"Error finding job matches: {str(e)}"
    except Exception as e:
        print(f"[ERROR] General error in find_job_matches: {str(e)}")
        return False, str(e)

# Career Guidance Functions
def get_career_guidance(user_id, career_path=None):
    try:
        # Import required modules
        import importlib
        import config
        from utils.file_helpers import load_json_from_file
        
        print(f"[INFO] Starting career guidance for user {user_id}")
        
        # First check if there's resume data
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get user's skills from resume_data
            cursor.execute("SELECT skills, experience, education FROM resume_data WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            
            # Important: Fetch all remaining results to avoid "Unread result found" error
            while cursor.nextset():
                pass
            
            if not result:
                print("[ERROR] No resume data found")
                return False, "No resume data found. Please parse a resume first."
        finally:
            # Ensure cursor and connection are properly closed
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
        # Check if career_guidance.py exists before trying to load it
        career_guidance_path = os.path.join(config.BASE_DIR, "career_guidance.py")
        if not os.path.exists(career_guidance_path):
            print(f"[ERROR] career_guidance.py not found at {career_guidance_path}")
            return False, "Career guidance module not found. Please contact support."
        
        # Load the career_guidance module
        try:
            print(f"[DEBUG] Loading career_guidance from {career_guidance_path}")
            
            # Load the module
            spec = importlib.util.spec_from_file_location(
                "career_guidance", 
                career_guidance_path
            )
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'career_guidance_main'):
                print("[INFO] Found career_guidance_main function, calling it now")
                # Call the career_guidance_main function with career_path
                guidance_data = module.career_guidance_main(career_path)
                if guidance_data is None:
                    print("[ERROR] career_guidance_main returned None")
                    return False, "Error generating career guidance. Please try again."
                
                print(f"[DEBUG] Career guidance result: {type(guidance_data)}")
                
                # Save guidance to database
                db_error = None
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # Store new guidance data
                    guidance_text = json.dumps(guidance_data)
                    career_path_str = career_path if career_path else "Default Path"
                    
                    cursor.execute("""
                        INSERT INTO career_guidance (user_id, guidance_text, career_path)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        guidance_text = VALUES(guidance_text),
                        career_path = VALUES(career_path)
                    """, (user_id, guidance_text, career_path_str))
                    
                    conn.commit()
                    print("[INFO] Career guidance saved to database")
                except Exception as e:
                    db_error = str(e)
                    print(f"[ERROR] Error saving career guidance to database: {db_error}")
                finally:
                    # Ensure cursor and connection are properly closed
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()
                
                # Return guidance data even if db saving failed
                return True, guidance_data
            else:
                print("[ERROR] career_guidance_main function not found in the module")
                return False, "Career guidance function not available"
                
        except Exception as e:
            print(f"[ERROR] Error with career guidance: {str(e)}")
            
            # Fall back to loading the JSON directly
            try:
                guidance_data = load_json_from_file(config.CAREER_GUIDANCE_JSON)
                if guidance_data:
                    print("[INFO] Successfully loaded career guidance from JSON file")
                    return True, guidance_data
                else:
                    print("[WARNING] Could not load career guidance from JSON file, using placeholder data")
                    # Create minimal fallback data
                    fallback_guidance = {
                        "skillGapAnalysis": ["Professional experience in target field", "Advanced certifications"],
                        "skillDevelopmentPlan": ["Strengthen technical skills", "Build portfolio projects", "Network with professionals"],
                        "certifications": ["Relevant industry certification", "Online courses on platforms like Coursera or Udemy"],
                        "projectIdeas": ["Build a small project relevant to target field", "Contribute to open source"],
                        "estimatedTimeline": "6-12 months",
                        "jobReadinessIndicator": "Partially ready - need to build more relevant experience"
                    }
                    return True, fallback_guidance
            except Exception as json_error:
                print(f"[ERROR] Error loading career guidance JSON: {str(json_error)}")
            
            return False, f"Error generating career guidance: {str(e)}"
    except Exception as e:
        print(f"[ERROR] General error in get_career_guidance: {str(e)}")
        return False, str(e)

# Interview Preparation Functions
def get_interview_questions(user_id, job_role=None):
    try:
        # Import required modules
        import importlib
        import config
        from utils.file_helpers import load_json_from_file
        
        print(f"[INFO] Getting interview questions for user {user_id}")
        if job_role:
            print(f"[INFO] Job role specified: {job_role}")
        
        # Check if interview questions already exist and no job role is specified
        if not job_role:
            questions = load_json_from_file(config.INTERVIEW_PREP_JSON)
            if questions:
                print("[INFO] Using existing interview questions")
                return True, questions
        
        # Check if interview_prep.py exists
        interview_prep_path = os.path.join(config.BASE_DIR, "interview_prep.py")
        if not os.path.exists(interview_prep_path):
            print(f"[ERROR] interview_prep.py not found at {interview_prep_path}")
            return False, "Interview prep module not found. Please contact support."
        
        # Load the interview_prep module
        try:
            print(f"[DEBUG] Loading interview_prep from {interview_prep_path}")
            
            # Load the module
            spec = importlib.util.spec_from_file_location(
                "interview_prep", 
                interview_prep_path
            )
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'interview_prep_main'):
                print("[INFO] Found interview_prep_main function, calling it now")
                # Call the interview_prep_main function with job_role parameter
                interview_questions = module.interview_prep_main(job_role)
                if interview_questions is None:
                    print("[ERROR] interview_prep_main returned None")
                    return False, "Error generating interview questions. Please try again."
                
                print(f"[DEBUG] Interview questions returned: {type(interview_questions)}")
                
                # Return the questions
                return True, interview_questions
            else:
                print("[ERROR] interview_prep_main function not found in the module")
                return False, "Interview prep function not available"
                
        except Exception as e:
            print(f"[ERROR] Error with interview prep: {str(e)}")
            
            # Fall back to loading the JSON directly
            try:
                questions = load_json_from_file(config.INTERVIEW_PREP_JSON)
                if questions:
                    print("[INFO] Successfully loaded interview questions from JSON file")
                    return True, questions
                else:
                    print("[WARNING] Could not load interview questions from JSON file")
                    return False, "Error generating interview questions"
            except Exception as json_error:
                print(f"[ERROR] Error loading interview questions JSON: {str(json_error)}")
            
            return False, f"Error generating interview questions: {str(e)}"
    except Exception as e:
        print(f"[ERROR] General error in get_interview_questions: {str(e)}")
        return False, str(e)

def analyze_interview_answer(user_id, question_id, answer, question=None):
    try:
        import config
        from google import genai
        
        print(f"[INFO] Analyzing interview answer for user {user_id}, question ID {question_id}")
        
        # Initialize Gemini API
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            model = genai.GenerativeModel(config.JOB_MATCHER_MODEL)
        except Exception as api_error:
            print(f"[ERROR] Gemini API initialization error: {str(api_error)}")
            return False, "Error initializing AI feedback system. Please try again later."
        
        # Prepare prompt for the analysis
        prompt = f"""
        You are an experienced hiring manager and interview coach. Analyze the following interview answer and provide helpful feedback.
        
        Question: {question if question else 'Interview question ' + question_id}
        
        Candidate's Answer: 
        {answer}
        
        Please provide feedback on:
        1. Content: How well did the answer address the question?
        2. Structure: Was the answer well-organized and easy to follow?
        3. Examples: Did the candidate use specific examples from their experience?
        4. Communication: Was the language clear, professional, and concise?
        5. Improvement suggestions: How could this answer be strengthened?
        
        Format your response in HTML with sections for strengths and areas for improvement.
        Be specific, constructive, and encouraging.
        """
        
        try:
            response = model.generate_content(prompt)
            feedback = response.text
            
            # Wrap in a styled HTML div for better display
            styled_feedback = f"""
            <div class="feedback-section">
                {feedback}
            </div>
            """
            
            return True, styled_feedback
            
        except Exception as model_error:
            print(f"[ERROR] Gemini model error: {str(model_error)}")
            return False, "Error generating feedback. Please try again later."
            
    except Exception as e:
        print(f"[ERROR] General error in analyze_interview_answer: {str(e)}")
        return False, str(e)

# Interview Chatbot Functions
def chat_with_interview_bot(user_id, message):
    # This would call the interview_prep2 module
    # For now we'll use a mock implementation
    
    # Mock responses based on common interview messages
    if "hello" in message.lower() or "hi" in message.lower():
        return "Hello! I'm your interview practice assistant. What position are you preparing for today?"
    
    elif "experience" in message.lower() or "background" in message.lower():
        return "That's a common interview question. When describing your experience, focus on highlighting relevant achievements and skills that match the job description. Can you practice by telling me about your experience?"
    
    elif "strength" in message.lower():
        return "When discussing strengths, be specific and provide examples. Avoid generic answers. What would you say is your greatest professional strength?"
    
    elif "weakness" in message.lower():
        return "For weaknesses, it's good to mention something you're actively working to improve. Show self-awareness while keeping it professional. Would you like to practice answering this question?"
    
    elif "thank" in message.lower():
        return "You're welcome! Remember to prepare specific examples from your experience that demonstrate your skills. Is there another question you'd like to practice?"
    
    else:
        return "That's an interesting point. In an interview, try to connect your answers back to the value you can bring to the company. Would you like feedback on your response or try another question?"

# Create necessary database tables on import
if __name__ != "__main__":
    initialize_database() 