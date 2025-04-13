import base64
import os
import json
import traceback
from google import genai
from google.genai import types
import config
from utils.file_helpers import load_json_from_file, save_json_to_file
import re


def sanitize_json_response(json_text):
    """
    Sanitize the JSON response to fix common issues that cause parsing errors
    """
    try:
        # Fix duration_months with math expressions like "duration_months": 2-3
        # Convert them to strings like "duration_months": "2-3"
        pattern = r'"duration_months":\s*(\d+\s*-\s*\d+)'
        replacement = r'"duration_months": "\1"'
        json_text = re.sub(pattern, replacement, json_text)
        
        # Fix unquoted string values
        pattern = r':\s*([A-Za-z][A-Za-z0-9_\s-]+)(\s*[,}])'
        replacement = r': "\1"\2'
        json_text = re.sub(pattern, replacement, json_text)
        
        # Fix any other potential issues
        # Handle potential unquoted keys in JSON
        pattern = r'([{,])\s*(\w+):'
        replacement = r'\1"\2":'
        json_text = re.sub(pattern, replacement, json_text)
        
        # Fix trailing commas in arrays and objects
        json_text = re.sub(r',\s*}', '}', json_text)
        json_text = re.sub(r',\s*]', ']', json_text)
        
        return json_text
    except Exception as e:
        print(f"[ERROR] Error in sanitize_json_response: {str(e)}")
        return json_text  # Return original if sanitizing fails


def create_fallback_guidance(career_path, raw_response=None):
    """
    Create a fallback guidance object with basic structure when JSON parsing fails
    """
    # Default values
    skill_gap = ["Technical skills specific to the field", 
                "Practical experience", 
                "Industry certifications"]
    
    skill_plan = ["Learn fundamentals and core concepts", 
                 "Practice with real-world projects", 
                 "Build portfolio and connect with professionals"]
    
    certifications = ["Online courses on platforms like Coursera or Udemy", 
                     "Industry-recognized certifications", 
                     "Specialized training programs"]
    
    projects = ["Create a personal portfolio", 
               "Contribute to open source projects", 
               "Build applications that solve real problems"]
    
    # Extract information from raw response if available
    if raw_response:
        try:
            # Extract skill gaps
            if "skill_gap_analysis" in raw_response:
                match = re.search(r'"skill_gap_analysis"[^[]*\[(.*?)\]', raw_response, re.DOTALL)
                if match:
                    items = re.findall(r'"(.*?)"', match.group(1))
                    if items and len(items) > 0:
                        skill_gap = items[:5]  # Take up to 5 items
            
            # Extract skill development plan
            if "skill_development_plan" in raw_response:
                match = re.search(r'"skill_development_plan"[^[]*\[(.*?)\]', raw_response, re.DOTALL)
                if match:
                    items = re.findall(r'"(.*?)"', match.group(1))
                    if items and len(items) > 0:
                        skill_plan = items[:5]
            
            # Extract certifications
            if "certifications" in raw_response or "certifications_courses" in raw_response:
                pattern = r'"certifications(?:_courses)?"[^[]*\[(.*?)\]'
                match = re.search(pattern, raw_response, re.DOTALL)
                if match:
                    items = re.findall(r'"(.*?)"', match.group(1))
                    if items and len(items) > 0:
                        certifications = items[:5]
            
            # Extract project ideas
            if "project_ideas" in raw_response:
                match = re.search(r'"project_ideas"[^[]*\[(.*?)\]', raw_response, re.DOTALL)
                if match:
                    items = re.findall(r'"(.*?)"', match.group(1))
                    if items and len(items) > 0:
                        projects = items[:5]
        except Exception as e:
            print(f"[ERROR] Error extracting information from raw response: {str(e)}")
    
    timeline = {
        "learning_fundamentals": "2-3 months",
        "building_projects": "2-4 months",
        "job_preparation": "1-2 months",
        "total_estimated_time": "6-12 months depending on prior experience and time commitment"
    }
    
    readiness = "This is a fallback guidance. Please try again with a more specific career path to get personalized recommendations."
    
    return {
        "skill_gap_analysis": skill_gap,
        "skill_development_plan": skill_plan,
        "certifications_courses": certifications,
        "project_ideas": projects,
        "estimated_timeline": timeline,
        "job_readiness_indicator": readiness
    }


def career_guidance_main(career_path=None):
    """
    Generate career guidance based on resume data and specified career path
    """
    # Global try/except to ensure we always return something displayable
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)

        # Load the structured resume data
        try:
            fetched_resume_structured_data = load_json_from_file(config.STRUCTURED_RESUME_JSON)
            if not fetched_resume_structured_data:
                print(f"[ERROR] Could not load resume data from {config.STRUCTURED_RESUME_JSON}")
                return create_fallback_guidance(career_path)
        except Exception as e:
            print(f"[ERROR] Error loading structured resume: {str(e)}")
            return create_fallback_guidance(career_path)
        
        # Check if career path is provided
        if career_path is None or career_path.strip() == "":
            print(f"[INFO] No career path specified, returning None")
            return create_fallback_guidance("General Career Development")
        else:
            print(f"[INFO] Analyzing career path: {career_path}")

        # Add the career path to the resume data
        fetched_resume_structured_data['new career path'] = career_path
        
        # Set up the API request
        try:
            model = config.JOB_MATCHER_MODEL
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=json.dumps(fetched_resume_structured_data)),
                    ],
                ),
            ]
            tools = [
                types.Tool(google_search=types.GoogleSearch())
            ]
            generate_content_config = types.GenerateContentConfig(
                tools=tools,
                response_mime_type="text/plain",
                system_instruction=[
                    types.Part.from_text(text="""TASK:
The user will provide their current resume data in JSON format (including current skills, education, and experience) and a specific career path they want to explore.

You must analyze the resume data and compare it with the requirements of the target career path.

Return a career roadmap that includes:

Skill Gap Analysis – What's missing compared to the target role.

Skill Development Plan – Specific technologies, tools, or concepts to learn.

Certifications/Courses – Recommended online platforms and certifications.

Project Ideas – To build relevant experience.

Estimated Timeline – How long each step might take (in months).

Job Readiness Indicator – A brief summary of how close the user is to being job-ready.

Output Format:
Return the full roadmap in a clean and structured JSON format only, with no extra text or explanation.
Make sure the JSON is properly formatted with quoted keys and string values.
For numeric ranges like 2-3 months, please quote them as strings like "2-3 months".
"""),
                ],
            )
        except Exception as e:
            print(f"[ERROR] Error setting up API request: {str(e)}")
            return create_fallback_guidance(career_path)

        # Get the response from the API
        job_matches_text = ""
        try:
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                job_matches_text += chunk.text
                
            if not job_matches_text:
                print("[ERROR] Empty response from API")
                return create_fallback_guidance(career_path)
                
        except Exception as e:
            print(f"[ERROR] Error getting response from API: {str(e)}")
            return create_fallback_guidance(career_path)

        # Parse the JSON response
        try:
            # Clean up any markdown formatting if present
            cleaned_text = job_matches_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text.removeprefix("```json").strip()
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text.removesuffix("```").strip()
            
            # Sanitize JSON to fix common issues
            print(f"[DEBUG] Raw text before sanitizing: {cleaned_text[:100]}...")
            sanitized_text = sanitize_json_response(cleaned_text)
            
            # Try to parse the JSON
            try:
                job_matches_json = json.loads(sanitized_text)
                print(f"[INFO] Successfully parsed JSON")
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON decode error after sanitizing: {str(e)}")
                print(f"[DEBUG] Position: {e.pos}, Line: {e.lineno}, Column: {e.colno}")
                print(f"[DEBUG] Problematic text around position: {sanitized_text[max(0, e.pos-20):min(len(sanitized_text), e.pos+20)]}")
                
                # Try to extract the content if it's nested under career_roadmap
                if "career_roadmap" in sanitized_text:
                    try:
                        roadmap_content = re.search(r'"career_roadmap"\s*:\s*({.*})', sanitized_text, re.DOTALL)
                        if roadmap_content:
                            simplified_json = "{" + roadmap_content.group(1) + "}"
                            job_matches_json = json.loads(simplified_json)
                            print(f"[INFO] Successfully extracted and parsed career_roadmap content")
                        else:
                            print(f"[ERROR] Couldn't extract career_roadmap content")
                            # Use the fallback
                            job_matches_json = create_fallback_guidance(career_path, cleaned_text)
                    except Exception as inner_e:
                        print(f"[ERROR] Failed to fix JSON structure: {str(inner_e)}")
                        # Use the fallback with text extraction
                        job_matches_json = create_fallback_guidance(career_path, cleaned_text)
                else:
                    # Use the fallback with text extraction
                    job_matches_json = create_fallback_guidance(career_path, cleaned_text)
            
            # Save the guidance data to file
            try:
                save_json_to_file(job_matches_json, config.CAREER_GUIDANCE_JSON)
                print(f"[INFO] Career guidance saved to: {config.CAREER_GUIDANCE_JSON}")
            except Exception as e:
                print(f"[ERROR] Failed to save guidance to file: {str(e)}")
            
            return job_matches_json
            
        except Exception as e:
            print(f"[ERROR] Error processing API response: {str(e)}")
            print(traceback.format_exc())
            return create_fallback_guidance(career_path, job_matches_text)
            
    except Exception as e:
        # Last resort fallback
        print(f"[ERROR] Critical error in career_guidance_main: {str(e)}")
        print(traceback.format_exc())
        return create_fallback_guidance("General Career")


if __name__ == "__main__":
    career_guidance_main()
