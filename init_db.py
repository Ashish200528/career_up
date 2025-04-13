import mysql.connector as sql
import time

# Database configuration
db_config_no_db = {
    'host': "localhost",
    'user': "root",
    'passwd': "Student1020@"
}

db_config = {
    'host': "localhost",
    'user': "root",
    'passwd': "Student1020@",
    'database': "career_advisor"
}

def init_database():
    print("=== Initializing Database ===")
    
    # Connect without specifying database
    try:
        print("Connecting to MySQL server...")
        conn = sql.connect(**db_config_no_db)
        cursor = conn.cursor()
        
        # Drop the database if it exists
        print("Dropping database if it exists...")
        cursor.execute("DROP DATABASE IF EXISTS career_advisor")
        
        # Create the database
        print("Creating database career_advisor...")
        cursor.execute("CREATE DATABASE career_advisor")
        
        cursor.close()
        conn.close()
        
        print("Database created successfully!")
    except Exception as e:
        print(f"Error connecting to MySQL: {str(e)}")
        return False
    
    # Wait a moment for the database to be ready
    time.sleep(1)
    
    # Now connect with the database and create tables
    try:
        print("Connecting to career_advisor database...")
        conn = sql.connect(**db_config)
        cursor = conn.cursor()
        
        # Create users table
        print("Creating users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create resume_data table
        print("Creating resume_data table...")
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
        print("Creating job_matches table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_matches (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                job_title VARCHAR(100),
                company VARCHAR(100),
                match_score INT,
                job_description TEXT,
                url VARCHAR(255),
                match_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create career_guidance table
        print("Creating career_guidance table...")
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
        print("Creating interview_prep table...")
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
        
        # Create otp_store table
        print("Creating otp_store table...")
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
        
        # Create email_logs table
        print("Creating email_logs table...")
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
        
        # Create a test user
        print("Creating test user...")
        cursor.execute("""
            INSERT INTO users (email, password)
            VALUES ('test@example.com', 'password123')
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Database initialization completed successfully!")
        return True
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    init_database()
    print("\nNow you can run the application using: python run.py") 