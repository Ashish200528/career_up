import os
import sys
import subprocess
import importlib.util

def check_package(package_name):
    """Check if a package is installed and get its version"""
    try:
        spec = importlib.util.find_spec(package_name)
        return spec is not None
    except (ImportError, AttributeError):
        return False

def main():
    """
    Run the Career Up application with necessary environment variables
    """
    # Set environment variables for email with correct values
    os.environ['EMAIL_SENDER'] = "securebank11@gmail.com"
    os.environ['EMAIL_PASSWORD'] = "ibfttotgvdnnztkr"
    
    print("=== Intelligent Career Up ===")
    
    # Check for critical dependencies
    print("\nChecking dependencies...")
    
    # Check for MySQL connector
    mysql_installed = check_package("mysql.connector")
    if not mysql_installed:
        print("❌ Error: MySQL connector not found! Please install it using:")
        print("   pip install mysql-connector-python")
        sys.exit(1)
    else:
        print("✅ MySQL connector found!")
    
    # Check for Google Generative AI package
    genai_installed = check_package("google.generativeai")
    if not genai_installed:
        print("❌ Warning: Google Generative AI package not found!")
        print("   Some features of the application will not work properly.")
        print("   To fix this, run the dependency installer:")
        print("   python install_dependencies.py")
        
        # Ask if the user wants to continue anyway
        response = input("\nDo you want to continue without the Google Generative AI package? (y/n): ")
        if response.lower() != 'y':
            print("Please install the required dependencies and try again.")
            sys.exit(1)
    else:
        print("✅ Google Generative AI package found!")
    
    # Check for other required packages
    packages_to_check = ["flask", "PyPDF2", "fitz"]
    for package in packages_to_check:
        if check_package(package):
            print(f"✅ {package} found!")
        else:
            print(f"❌ Warning: {package} not found. Some features may not work correctly.")
    
    print("""
    EMAIL CONFIGURATION:
    --------------------
    Email sending has been configured and enabled.
    OTP will be sent to your email during registration.
    """)
    
    print("Starting the application...")
    
    # Check if MySQL database exists
    try:
        from core import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()[0]
        print(f"Connected to MySQL database: {db_name}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        print("Make sure you have created the career_advisor database in MySQL.")
        print("Run the following SQL command: CREATE DATABASE career_advisor;")
        sys.exit(1)
    
    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    
    # Run the Flask application
    print("Starting Flask server...")
    try:
        from app import app
        app.run(debug=True)
    except Exception as e:
        print(f"Error starting the server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 