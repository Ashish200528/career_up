from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import core
from functools import wraps
import json

app = Flask(__name__)
app.secret_key = 'intelligent_career_advisor_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        success, result = core.login_user(email, password)
        
        if success:
            user = result   
            session['user_id'] = user['id']
            session['email'] = user['email']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(result, 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '')  # Name is optional now
        email = request.form['email']
        password = request.form['password']
        
        # Check if email already exists
        success, message = core.register_user(name, email, password)
        
        if not success:
            if message == "Email already registered":
                flash('Email already registered', 'danger')
                return redirect(url_for('register'))
            else:
                flash(f'Registration error: {message}', 'danger')
                return redirect(url_for('register'))
        
        # Generate OTP
        otp = core.generate_otp()
        
        # Store registration data in session
        session['temp_registration'] = {
            'email': email,
            'otp': otp
        }
        
        # Store OTP in database with expiration
        core.store_otp(email, otp)
        
        # Create professional HTML email
        email_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}
                .header {{
                    background-color: #4a90e2;
                    color: white;
                    padding: 15px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    padding: 20px;
                }}
                .otp-code {{
                    font-size: 24px;
                    font-weight: bold;
                    text-align: center;
                    padding: 15px;
                    margin: 20px 0;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                    letter-spacing: 5px;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #888;
                    border-top: 1px solid #ddd;
                    padding-top: 15px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Intelligent Career Up</h2>
                </div>
                <div class="content">
                    <h3>Welcome to Your Career Journey!</h3>
                    <p>Thank you for registering with Intelligent Career Up. To complete your registration, please use the following One-Time Password (OTP):</p>
                    
                    <div class="otp-code">{otp}</div>
                    
                    <p>This code will expire in 10 minutes for security reasons.</p>
                    
                    <p>If you did not request this registration, please ignore this email.</p>
                    
                    <p>Best regards,<br>
                    The Intelligent Career Up Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>&copy; 2024 Intelligent Career Up. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send OTP email with proper styling
        email_subject = "Verify Your Email - Intelligent Career Up"
        
        if core.send_email(email, email_subject, email_message):
            flash('A verification code has been sent to your email. Please check your inbox and enter the code to complete registration.', 'success')
        else:
            flash('There was an issue sending the verification email. Please try again.', 'danger')
            return redirect(url_for('register'))
        
        return redirect(url_for('verify_otp'))
    
    return render_template('register.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'temp_registration' not in session:
        return redirect(url_for('register'))
    
    if request.method == 'POST':
        otp = request.form['otp']
        email = session['temp_registration']['email']
        
        # Verify OTP from database (primary method)
        if core.verify_otp(email, otp):
            verification_success = True
        # Fallback to session OTP if database verification fails
        elif otp == session['temp_registration']['otp']:
            verification_success = True
        else:
            verification_success = False
        
        if verification_success:
            # Find the user by email
            conn = core.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            # Set session variables
            if user:
                session['user_id'] = user['id']
                session['email'] = user['email']
                
                # Clear temporary registration data
                session.pop('temp_registration', None)
                
                flash('Registration successful! Welcome to Career Up!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Error finding your account. Please login manually.', 'warning')
                session.pop('temp_registration', None)
                return redirect(url_for('login'))
        else:
            flash('Invalid verification code. Please try again.', 'danger')
    
    return render_template('verify_otp.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user data for dashboard
    user_id = session['user_id']
    
    # Get resume score from database if available
    resume_score = 0
    job_matches = 0
    interview_questions_count = 0
    career_progress = 0
    
    try:
        # Get resume score
        conn = core.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT resume_score FROM resume_data WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            resume_score = result['resume_score']
        
        # Count job matches
        import config
        from utils.file_helpers import load_json_from_file
        job_matches_data = load_json_from_file(config.JOB_MATCHES_JSON)
        if job_matches_data and isinstance(job_matches_data, list):
            job_matches = len(job_matches_data)
        
        # Count interview questions
        interview_questions_data = load_json_from_file(config.INTERVIEW_PREP_JSON)
        if interview_questions_data and 'interview_questions' in interview_questions_data:
            question_count = 0
            for category in interview_questions_data['interview_questions']:
                if 'questions' in category:
                    question_count += len(category['questions'])
            interview_questions_count = question_count
        
        # Calculate career progress (simple algorithm)
        if resume_score > 0:
            career_progress = 25  # Started progress
        if job_matches > 0:
            career_progress += 25
        if interview_questions_count > 0:
            career_progress += 25
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Error getting dashboard data: {str(e)}")
    
    return render_template('dashboard.html',
                          resume_score=resume_score,
                          job_matches=job_matches,
                          interview_questions_count=interview_questions_count,
                          career_progress=career_progress)

@app.route('/resume_parser', methods=['GET', 'POST'])
@login_required
def resume_parser_page():
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        resume_file = request.files['resume']
        
        if resume_file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if resume_file:
            try:
                # Import config 
                import config
                
                # Create resume_samples directory if it doesn't exist
                os.makedirs(config.RESUME_SAMPLES_DIR, exist_ok=True)
                
                # Save the file to correct location as Sample_resume.pdf
                sample_path = os.path.join(config.RESUME_SAMPLES_DIR, "Sample_resume.pdf")
                print(f"[INFO] Saving uploaded resume to: {sample_path}")
                
                # First remove any existing file
                if os.path.exists(sample_path):
                    try:
                        os.remove(sample_path)
                        print(f"[INFO] Removed existing sample resume at {sample_path}")
                    except Exception as e:
                        print(f"[WARNING] Failed to remove existing sample resume: {str(e)}")
                
                # Save the new file
                resume_file.save(sample_path)
                
                # Verify file was saved successfully
                if not os.path.exists(sample_path) or os.path.getsize(sample_path) == 0:
                    print("[ERROR] File did not save properly")
                    flash('Error saving the uploaded file. Please try again.', 'danger')
                    return redirect(request.url)
                
                # Store the user_id in session for processing
                session['resume_to_process'] = True
                
                # Set a flag to force processing
                session['force_processing'] = True
                
                # Redirect to process_resume
                return redirect(url_for('process_resume'))
                
            except Exception as e:
                print(f"[ERROR] Save error: {str(e)}")
                flash(f'Error saving resume: {str(e)}', 'danger')
                return redirect(request.url)
    
    return render_template('resume_parser.html')

@app.route('/process_resume')
@login_required
def process_resume():
    user_id = session['user_id']
    print(f"[DEBUG] Starting process_resume for user {user_id}")
    
    try:
        # Only process if needed
        if session.get('resume_to_process', False):
            # Get force_processing flag from session
            force_processing = session.get('force_processing', True)
            print(f"[DEBUG] Using force_processing={force_processing}")
            
            # Import required modules
            import sys
            import config
            import importlib.util
            from utils.file_helpers import load_json_from_file
            
            print(f"[INFO] Starting resume processing for user {user_id}")
            
            try:
                # Load the resume_parser module
                resume_parser_path = os.path.join(config.BASE_DIR, "resume_parser.py")
                print(f"[DEBUG] Loading resume_parser from {resume_parser_path}")
                
                spec = importlib.util.spec_from_file_location(
                    "resume_parser", 
                    resume_parser_path
                )
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'resume_parser_main'):
                    print("[INFO] Found resume_parser_main function, calling it now")
                    # Call the resume_parser_main function with force_processing flag
                    result = module.resume_parser_main(force_processing=force_processing)
                    if result is None:
                        print("[ERROR] resume_parser_main returned None")
                        flash('Error processing resume. Please try again.', 'danger')
                        session.pop('resume_to_process', None)
                        session.pop('force_processing', None)
                        return redirect(url_for('resume_parser_page'))
                    
                    print(f"[DEBUG] Resume processing result: {type(result)}")
                else:
                    print("[ERROR] resume_parser_main function not found in the module")
                    flash('Error: resume_parser_main function not found', 'danger')
                    session.pop('resume_to_process', None)
                    session.pop('force_processing', None)
                    return redirect(url_for('resume_parser_page'))
                    
            except Exception as e:
                print(f"[ERROR] Error importing or calling resume_parser_main: {str(e)}")
                # Fall back to loading the JSON directly
                result = load_json_from_file(config.STRUCTURED_RESUME_JSON)
                if not result:
                    flash(f'Error processing resume: {str(e)}', 'danger')
                    session.pop('resume_to_process', None)
                    session.pop('force_processing', None)
                    return redirect(url_for('resume_parser_page'))
            
            # Store the parsed data in the database
            conn = core.get_db_connection()
            cursor = conn.cursor()
            
            try:
                # Determine what data to store based on the structure
                if isinstance(result, dict):
                    # Handle skills list
                    if isinstance(result.get('skills', []), list):
                        skills_json = json.dumps(result['skills'])
                    else:
                        skills_json = json.dumps([])
                    
                    # Handle experience
                    if isinstance(result.get('experience', []), list):
                        # Convert list of experience objects to a simple string
                        experience_text = ""
                        for exp in result['experience']:
                            if isinstance(exp, dict):
                                exp_parts = []
                                if exp.get('job_role'):
                                    exp_parts.append(f"Role: {exp['job_role']}")
                                if exp.get('company'):
                                    exp_parts.append(f"Company: {exp['company']}")
                                if exp.get('duration'):
                                    exp_parts.append(f"Duration: {exp['duration']}")
                                if exp.get('responsibilities'):
                                    # Join responsibilities with commas instead of newlines
                                    responsibilities = [r.replace('\n', ' ').replace('\r', ' ') for r in exp['responsibilities']]
                                    exp_parts.append("Responsibilities: " + ", ".join(responsibilities))
                                experience_text += " | ".join(exp_parts) + "\n\n"
                        experience = experience_text
                    else:
                        experience = str(result.get('experience', ''))
                    
                    # Handle education
                    if isinstance(result.get('education', []), list):
                        # Convert list of education objects to a simple string
                        education_text = ""
                        for edu in result['education']:
                            if isinstance(edu, dict):
                                edu_parts = []
                                if edu.get('degree'):
                                    edu_parts.append(f"Degree: {edu['degree']}")
                                if edu.get('institution'):
                                    edu_parts.append(f"Institution: {edu['institution']}")
                                if edu.get('years'):
                                    edu_parts.append(f"Years: {edu['years']}")
                                education_text += " | ".join(edu_parts) + "\n\n"
                        education = education_text
                    else:
                        education = str(result.get('education', ''))
                    
                    # Default resume score
                    resume_score = result.get('resume_score', 85)
                else:
                    # Handle unexpected result type
                    skills_json = "[]"
                    experience = "No experience found"
                    education = "No education found"
                    resume_score = 50
                
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
                """, (
                    user_id, 
                    "Parsed from Sample_resume.pdf", 
                    skills_json, 
                    experience,
                    education,
                    resume_score
                ))
                
                conn.commit()
                # Remove all processing flags
                session.pop('resume_to_process', None)
                session.pop('force_processing', None)
                flash('Resume processed successfully!', 'success')
                print("[INFO] Resume data successfully saved to database")
            
            except Exception as e:
                print(f"[ERROR] Database error: {str(e)}")
                flash(f'Error storing resume data: {str(e)}', 'danger')
                session.pop('resume_to_process', None)
                session.pop('force_processing', None)
                return redirect(url_for('resume_parser_page'))
            finally:
                cursor.close()
                conn.close()
        
        # Read the structured resume data from the correct output location
        import config
        from utils.file_helpers import load_json_from_file
        
        # Check if the JSON exists and load it
        print(f"[INFO] Looking for structured resume at: {config.STRUCTURED_RESUME_JSON}")
        try:
            # First try direct file loading
            if os.path.exists(config.STRUCTURED_RESUME_JSON):
                print(f"[DEBUG] Structured resume file exists, loading directly")
                with open(config.STRUCTURED_RESUME_JSON, 'r', encoding='utf-8') as f:
                    structured_data = json.load(f)
                print(f"[DEBUG] Successfully loaded JSON directly")
                return render_template('resume_parser_result.html', result=structured_data)
            else:
                print(f"[DEBUG] Structured resume file does not exist")
                structured_data = None
        except Exception as e:
            print(f"[ERROR] Error loading JSON directly: {str(e)}")
            # Fall back to utility function
            structured_data = load_json_from_file(config.STRUCTURED_RESUME_JSON)
            if structured_data:
                return render_template('resume_parser_result.html', result=structured_data)
        
        # If no structured data found, check alternative locations
        alternative_paths = [
            os.path.join(config.OUTPUT_DIR, "structured_resume.json"),
            os.path.join(config.BASE_DIR, "output", "structured_resume.json")
        ]
        
        for path in alternative_paths:
            print(f"[INFO] Looking for alternative structured resume at: {path}")
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        structured_data = json.load(f)
                    print(f"[INFO] Structured resume data loaded successfully from {path}")
                    return render_template('resume_parser_result.html', result=structured_data)
                except Exception as e:
                    print(f"[ERROR] Error loading from {path}: {str(e)}")
        
        # If still no JSON found, check the database
        print(f"[INFO] No structured resume found, checking database")
        conn = core.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT skills, experience, education, resume_score, last_updated
                FROM resume_data WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            if result:
                # Convert JSON string back to list
                result['skills'] = json.loads(result['skills'])
                result['parsed_date'] = result['last_updated'].strftime("%Y-%m-%d %H:%M:%S")
                return render_template('resume_parser_result.html', result=result)
            else:
                print("[DEBUG] No resume data found in database")
                flash('No resume data found. Please upload a resume.', 'warning')
                return redirect(url_for('resume_parser_page'))
        finally:
            cursor.close()
            conn.close()
        
    except Exception as e:
        print(f"[ERROR] Process error: {str(e)}")
        flash(f'Error in resume processing: {str(e)}', 'danger')
        session.pop('resume_to_process', None)
        session.pop('force_processing', None)
        return redirect(url_for('resume_parser_page'))

@app.route('/job_matcher', methods=['GET', 'POST'])
@login_required
def job_matcher_page():
    user_id = session['user_id']
    
    # Handle job position form submission
    job_position = None
    if request.method == 'POST' and 'job_position' in request.form:
        job_position = request.form['job_position'].strip()
        print(f"[INFO] User {user_id} searching for job position: {job_position}")
        
        # Store the job position in session for potential re-use
        session['job_position'] = job_position
        
        # Set processing flag
        session['jobs_to_process'] = True
        
        return redirect(url_for('process_jobs'))
    
    # Check if we already have job matches
    import config
    from utils.file_helpers import load_json_from_file
    
    # Try to load job matches from JSON file
    job_matches = load_json_from_file(config.JOB_MATCHES_JSON)
    
    if job_matches:
        # Check if job_matches is a dict with a 'jobs' key (the new format)
        if isinstance(job_matches, dict) and 'jobs' in job_matches:
            job_list = job_matches['jobs']
            print(f"[INFO] Found {len(job_list)} existing job matches")
        else:
            # Backward compatibility for old format
            job_list = job_matches
            print(f"[INFO] Found {len(job_list)} existing job matches")
            
        # Transform the job data to match template expectations
        transformed_jobs = []
        for job in job_list:
            # Handle different possible structures
            if isinstance(job, dict):
                transformed_job = {
                    "title": job.get("job_title", job.get("Job Title", "Unknown Title")),
                    "company": job.get("company", job.get("Company", "Unknown Company")),
                    "location": job.get("location", job.get("Location", "Remote/Flexible")),
                    "posted_date": job.get("posted_date", job.get("Posted Date", "Recent")),
                    "description": job.get("description", job.get("short_description", job.get("Short Description", "No description available"))),
                    "url": job.get("url", "#")  # Default URL
                }
            else:
                # In case job is a string or other type
                transformed_job = {
                    "title": "Unknown Title",
                    "company": "Unknown Company",
                    "location": "Unknown Location",
                    "posted_date": "Unknown Date",
                    "description": str(job) if job else "No description available",
                    "url": "#"
                }
            transformed_jobs.append(transformed_job)
        
        return render_template('job_matcher.html', job_matches=transformed_jobs, 
                              previous_position=session.get('job_position', ''))
    
    # If no existing matches, show the search form
    return render_template('job_matcher.html', job_matches=None,
                          previous_position=session.get('job_position', ''))

@app.route('/process_jobs')
@login_required
def process_jobs():
    user_id = session['user_id']
    print(f"[DEBUG] Starting process_jobs for user {user_id}")
    
    try:
        # Only process if needed
        if session.get('jobs_to_process', False):
            job_position = session.get('job_position')
            print(f"[DEBUG] Processing jobs for position: {job_position}")
            
            try:
                # Import modules needed for job matching
                import config
                try:
                    from google import genai
                    genai_available = True
                except ImportError as ie:
                    print(f"[WARNING] Google Generative AI import error: {str(ie)}")
                    genai_available = False
                
                # Call the job matcher function
                success, job_matches = core.find_job_matches(user_id, job_position)
                
                # Clear processing flag
                session.pop('jobs_to_process', None)
                
                if not success:
                    flash(f'Error finding job matches: {job_matches}', 'danger')
                    return redirect(url_for('job_matcher_page'))
                    
                flash('Job matches found successfully!', 'success')
            except Exception as e:
                print(f"[ERROR] Job matcher error: {str(e)}")
                flash(f'Error in job matching: {str(e)}', 'danger')
                session.pop('jobs_to_process', None)
                return redirect(url_for('job_matcher_page'))
        
        return redirect(url_for('job_matcher_page'))
        
    except Exception as e:
        print(f"[ERROR] Process jobs error: {str(e)}")
        flash(f'Error processing job matches: {str(e)}', 'danger')
        session.pop('jobs_to_process', None)
        return redirect(url_for('job_matcher_page'))

@app.route('/career_guidance', methods=['GET', 'POST'])
@login_required
def career_guidance_page():
    user_id = session['user_id']
    
    try:
        # Handle career path form submission
        career_path = None
        if request.method == 'POST' and 'career_path' in request.form:
            career_path = request.form['career_path'].strip()
            print(f"[INFO] User {user_id} exploring career path: {career_path}")
            
            # Store the career path in session for potential re-use
            session['career_path'] = career_path
            
            # Get career guidance based on the specified path
            try:
                success, guidance = core.get_career_guidance(user_id, career_path)
                
                if success and guidance:
                    flash('Career guidance generated successfully!', 'success')
                    return render_template('career_guidance.html', guidance=guidance, previous_path=career_path)
                else:
                    error_message = 'Error generating career guidance'
                    if isinstance(guidance, str):
                        error_message = guidance
                    flash(f'{error_message}. Using default guidance.', 'warning')
                    # Create default guidance
                    guidance = {
                        "skill_gap_analysis": ["Technical skills for the field", "Practical experience", "Industry knowledge"],
                        "skill_development_plan": ["Learn fundamentals", "Build projects", "Network with professionals"],
                        "certifications_courses": ["Online courses", "Industry certifications", "Specialized training"],
                        "project_ideas": ["Portfolio website", "Practice projects", "Open source contributions"],
                        "estimated_timeline": {"total_estimated_time": "6-12 months depending on commitment"},
                        "job_readiness_indicator": "Please try again with specific details about your target career path."
                    }
                    return render_template('career_guidance.html', guidance=guidance, previous_path=career_path)
            except Exception as e:
                print(f"[ERROR] Exception in get_career_guidance: {str(e)}")
                flash(f'Error generating career guidance: {str(e)}. Using default guidance.', 'warning')
                # Create default guidance
                guidance = {
                    "skill_gap_analysis": ["Technical skills for the field", "Practical experience", "Industry knowledge"],
                    "skill_development_plan": ["Learn fundamentals", "Build projects", "Network with professionals"],
                    "certifications_courses": ["Online courses", "Industry certifications", "Specialized training"],
                    "project_ideas": ["Portfolio website", "Practice projects", "Open source contributions"],
                    "estimated_timeline": {"total_estimated_time": "6-12 months depending on commitment"},
                    "job_readiness_indicator": "Please try again with specific details about your target career path."
                }
                return render_template('career_guidance.html', guidance=guidance, previous_path=career_path)
        
        # If GET request or no career path specified, try to load existing guidance
        import config
        from utils.file_helpers import load_json_from_file
        
        # Try to load guidance from JSON file
        guidance_data = None
        try:
            guidance_data = load_json_from_file(config.CAREER_GUIDANCE_JSON)
        except Exception as e:
            print(f"[ERROR] Error loading career guidance JSON: {str(e)}")
        
        previous_path = session.get('career_path', '')
        
        if not guidance_data:
            # Try to get guidance from the database or generate default
            try:
                success, guidance_data = core.get_career_guidance(user_id)
                if not success or not guidance_data:
                    # Create default empty guidance structure for the template
                    guidance_data = {
                        "skill_gap_analysis": [],
                        "skill_development_plan": [],
                        "certifications_courses": [],
                        "project_ideas": [],
                        "estimated_timeline": {},
                        "job_readiness_indicator": "Please enter a career path to get personalized guidance."
                    }
            except Exception as e:
                print(f"[ERROR] Error in fallback guidance generation: {str(e)}")
                # Create default empty guidance structure for the template
                guidance_data = {
                    "skill_gap_analysis": [],
                    "skill_development_plan": [],
                    "certifications_courses": [],
                    "project_ideas": [],
                    "estimated_timeline": {},
                    "job_readiness_indicator": "Please enter a career path to get personalized guidance."
                }
        
        return render_template('career_guidance.html', guidance=guidance_data, previous_path=previous_path)
    except Exception as e:
        print(f"[ERROR] Unhandled exception in career_guidance_page: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Absolute fallback - always show something
        flash('An unexpected error occurred. Please try again.', 'danger')
        guidance_data = {
            "skill_gap_analysis": ["Focus on core skills"],
            "skill_development_plan": ["Start with fundamentals"],
            "certifications_courses": ["Online learning platforms"],
            "project_ideas": ["Build a portfolio"],
            "estimated_timeline": {"total_estimated_time": "Varies based on experience"},
            "job_readiness_indicator": "Please enter a specific career path for detailed guidance."
        }
        return render_template('career_guidance.html', guidance=guidance_data, previous_path=session.get('career_path', ''))

@app.route('/interview_prep', methods=['GET', 'POST'])
@login_required
def interview_prep_page():
    user_id = session['user_id']
    
    try:
        # Handle job role form submission
        if request.method == 'POST' and 'job_role' in request.form:
            job_role = request.form['job_role'].strip()
            
            if job_role:
                # Store in session for later use
                session['interview_job_role'] = job_role
                
                print(f"[INFO] User {user_id} requesting interview questions for job role: {job_role}")
                
                # Import interview_prep module dynamically
                import importlib.util
                import os
                
                # Path to interview_prep.py
                interview_prep_path = os.path.join(os.getcwd(), "interview_prep.py")
                
                if os.path.exists(interview_prep_path):
                    try:
                        # Load module dynamically
                        spec = importlib.util.spec_from_file_location("interview_prep", interview_prep_path)
                        interview_prep = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(interview_prep)
                        
                        # Call interview_prep_main with job_role
                        if hasattr(interview_prep, 'interview_prep_main'):
                            questions_json = interview_prep.interview_prep_main(job_role)
                            
                            if questions_json:
                                flash('Interview questions generated successfully!', 'success')
                                return render_template('interview_prep.html', questions=questions_json, previous_job_role=job_role)
                            else:
                                flash('Error generating interview questions. Please try again.', 'danger')
                        else:
                            flash('Error: interview_prep_main function not found.', 'danger')
                    except Exception as e:
                        flash(f'Error generating interview questions: {str(e)}', 'danger')
                else:
                    flash('Error: interview_prep.py file not found.', 'danger')
                
        # For GET requests or if POST failed, try to load existing questions
        import config
        from utils.file_helpers import load_json_from_file
        
        # Load previous job role from session if available
        previous_job_role = session.get('interview_job_role', '')
        
        # Try to load questions from JSON file
        try:
            questions_data = load_json_from_file(config.INTERVIEW_PREP_JSON)
            return render_template('interview_prep.html', questions=questions_data, previous_job_role=previous_job_role)
        except Exception as e:
            print(f"[ERROR] Error loading interview questions: {str(e)}")
            return render_template('interview_prep.html', questions=None, previous_job_role=previous_job_role)
            
    except Exception as e:
        print(f"[ERROR] Unhandled error in interview_prep_page: {str(e)}")
        flash(f'An unexpected error occurred: {str(e)}', 'danger')
        return render_template('interview_prep.html', questions=None, previous_job_role='')

@app.route('/interview_answer', methods=['POST'])
@login_required
def interview_answer():
    user_id = session['user_id']
    question_id = request.form['question_id']
    answer = request.form['answer']
    
    success, result = core.analyze_interview_answer(user_id, question_id, answer)
    
    return jsonify(success=success, result=result)

@app.route('/interview_chatbot', methods=['GET', 'POST'])
@login_required
def interview_chatbot_page():
    user_id = session['user_id']
    
    # Check if interview questions exist
    import config
    from utils.file_helpers import load_json_from_file
    
    try:
        interview_questions = load_json_from_file(config.INTERVIEW_PREP_JSON)
        if not interview_questions:
            flash('Please generate interview questions first.', 'warning')
            return redirect(url_for('interview_prep_page'))
    except:
        flash('Please generate interview questions first.', 'warning')
        return redirect(url_for('interview_prep_page'))
    
    # If POST request, it's a message from the chatbot
    if request.method == 'POST':
        message = request.form.get('message')
        
        if not message:
            return jsonify(success=False, error="No message provided")
        
        # Import the interview_prep2 module
        try:
            import importlib.util
            import os
            
            # Path to interview_prep2.py
            interview_prep2_path = os.path.join(os.getcwd(), "interview_prep2.py")
            
            if not os.path.exists(interview_prep2_path):
                return jsonify(success=False, error="Chatbot module not found")
                
            # Load the module
            spec = importlib.util.spec_from_file_location("interview_prep2", interview_prep2_path)
            interview_prep2 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(interview_prep2)
            
            # Check if message is end interview trigger
            if message.lower() in ["ok lets over", "let's end", "end interview"]:
                # Call function for ending interview and generating feedback
                try:
                    feedback = interview_prep2.generate_feedback()
                    return jsonify(success=True, response=feedback)
                except Exception as e:
                    print(f"[ERROR] Error generating feedback: {str(e)}")
                    return jsonify(success=False, error=f"Error generating feedback: {str(e)}")
            
            # Process the message
            try:
                response = interview_prep2.process_message(message)
                return jsonify(success=True, response=response)
            except Exception as e:
                print(f"[ERROR] Error processing message: {str(e)}")
                return jsonify(success=False, error=f"Error processing message: {str(e)}")
            
        except Exception as e:
            print(f"[ERROR] Chatbot error: {str(e)}")
            return jsonify(success=False, error=f"Chatbot error: {str(e)}")
    
    # For GET request, render the chatbot page
    job_role = session.get('interview_job_role', 'the position')
    return render_template('interview_chatbot.html', job_role=job_role)

@app.route('/interview_chatbot_message', methods=['POST'])
@login_required
def interview_chatbot_message():
    message = request.form.get('message')
    
    if not message:
        return jsonify(success=False, error="No message provided")
    
    # Import the interview_prep2 module
    try:
        import importlib.util
        import os
        
        # Path to interview_prep2.py
        interview_prep2_path = os.path.join(os.getcwd(), "interview_prep2.py")
        
        if not os.path.exists(interview_prep2_path):
            return jsonify(success=False, error="Chatbot module not found")
            
        # Load the module
        spec = importlib.util.spec_from_file_location("interview_prep2", interview_prep2_path)
        interview_prep2 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(interview_prep2)
        
        # Check if message is end interview trigger
        if message.lower() in ["ok lets over", "let's end", "end interview"]:
            # Call function for ending interview and generating feedback
            try:
                feedback = interview_prep2.generate_feedback()
                return jsonify(success=True, response=feedback)
            except Exception as e:
                print(f"[ERROR] Error generating feedback: {str(e)}")
                return jsonify(success=False, error=f"Error generating feedback: {str(e)}")
        
        # Process the message
        try:
            response = interview_prep2.process_message(message)
            return jsonify(success=True, response=response)
        except Exception as e:
            print(f"[ERROR] Error processing message: {str(e)}")
            return jsonify(success=False, error=f"Error processing message: {str(e)}")
        
    except Exception as e:
        print(f"[ERROR] Chatbot error: {str(e)}")
        return jsonify(success=False, error=f"Chatbot error: {str(e)}")

@app.route('/interview_chatbot_reset', methods=['POST'])
@login_required
def interview_chatbot_reset():
    try:
        import importlib.util
        import os
        
        # Path to interview_prep2.py
        interview_prep2_path = os.path.join(os.getcwd(), "interview_prep2.py")
        
        if not os.path.exists(interview_prep2_path):
            return jsonify(success=False, error="Chatbot module not found")
            
        # Load the module
        spec = importlib.util.spec_from_file_location("interview_prep2", interview_prep2_path)
        interview_prep2 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(interview_prep2)
        
        # Reset the conversation
        if hasattr(interview_prep2, 'reset_conversation'):
            interview_prep2.reset_conversation()
            
        return jsonify(success=True)
    except Exception as e:
        print(f"[ERROR] Error resetting conversation: {str(e)}")
        return jsonify(success=False, error=f"Error resetting conversation: {str(e)}")

@app.route('/mysql_test')
def mysql_test():
    try:
        conn = core.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return f"MySQL connection successful! Result: {result}"
    except Exception as e:
        return f"MySQL connection failed: {str(e)}"

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize database
    core.initialize_database()
    
    app.run(debug=True) 