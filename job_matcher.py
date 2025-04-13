import base64
import os
import json
from google import genai
from google.genai import types
import config
from utils.file_helpers import load_json_from_file, save_json_to_file


def job_matcher_main(job_position=None):
    client = genai.Client(api_key=config.GEMINI_API_KEY)

    fetched_resume_structured_data = load_json_from_file(config.STRUCTURED_RESUME_JSON)
    if not fetched_resume_structured_data:
        print(f"[ERROR] Could not load resume data from {config.STRUCTURED_RESUME_JSON}")
        return None
    
    if job_position is None or job_position.strip() == "":
        job_position = ""
    else:
        print(f"[INFO] Searching for job position: {job_position}")

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
Search across LinkedIn, Google Jobs, and Indeed for job listings posted in the last week or last month.
Ensure the jobs are active. Prioritize relevance to the user's profile.
List 5-10 jobs with:
- Job Title
- Company
- Location
- Posted Date
- Short Description

Return the results in a clean, readable json format properly, and no other things to print just the json file 
"""),
        ],
    )

    job_matches_text = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")
        job_matches_text += chunk.text

    # Parse the JSON response
    try:
        # Clean up any markdown formatting if present
        cleaned_text = job_matches_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text.removeprefix("```json").strip()
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text.removesuffix("```").strip()
        
        # Parse the JSON
        job_matches_json = json.loads(cleaned_text)
        
        # Save as JSON file
        save_json_to_file(job_matches_json, config.JOB_MATCHES_JSON)
        print(f"\n[INFO] Job matches saved to: {config.JOB_MATCHES_JSON}")
        return job_matches_json
    except json.JSONDecodeError as e:
        print(f"\n[ERROR] Error parsing JSON response: {str(e)}")
        print("[DEBUG] Raw response:", job_matches_text)
        return None

if __name__ == "__main__":
    job_matcher_main()
