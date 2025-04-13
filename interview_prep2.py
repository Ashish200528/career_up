import base64
import os
import json
from google import genai
from google.genai import types
import config
from utils.file_helpers import load_json_from_file, save_json_to_file

# Global conversation history
conversation_history = []
resume_data = None
interview_questions = None

def reset_conversation():
    """Reset the conversation history"""
    global conversation_history
    conversation_history = []
    
    # Initialize with default AI message
    ai_greeting = "Hello! I'll be conducting your interview today. Let's start by having you tell me a bit about yourself and your background."
    conversation_history.append({"role": "assistant", "content": ai_greeting})
    
    # Save conversation history
    save_conversation_history()
    return True

def load_data():
    """Load resume and interview question data"""
    global resume_data, interview_questions
    
    if resume_data is None:
        resume_data = load_json_from_file(config.STRUCTURED_RESUME_JSON)
    
    if interview_questions is None:
        interview_questions = load_json_from_file(config.INTERVIEW_PREP_JSON)
    
    return resume_data is not None and interview_questions is not None

def process_message(user_message):
    """Process a user message and return AI response"""
    global conversation_history
    
    # Make sure data is loaded
    if not load_data():
        return "Error: Could not load necessary data. Please try again."
    
    # Load conversation history if empty
    if not conversation_history:
        try:
            conv_data = load_json_from_file(config.CONVERSATION_JSON)
            if conv_data and "conversation_history" in conv_data:
                conversation_history = conv_data["conversation_history"]
        except:
            # If loading fails, reset the conversation
            reset_conversation()
    
    # Add user message to history
    conversation_history.append({"role": "user", "content": user_message})
    
    # Check if we should end the interview
    if user_message.lower() in ["ok lets over", "end interview", "let's end"]:
        return generate_feedback()
    
    # Setup API call
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    # Prepare the conversation context
    conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-5:]])
    
    # Create instruction prompt
    instruction = f'''You are an interview panel member conducting an interview for a job role. 
The candidate details are:
{json.dumps(resume_data, indent=2)}

The interview questions to ask from are:
{json.dumps(interview_questions, indent=2)}

You are having a conversation with the candidate. Your task is to:
1. Ask thoughtful questions based on the candidate's responses
2. Follow up on their answers when appropriate
3. Cover various topics from the interview questions list
4. Be professional and encouraging

Keep your responses concise and natural, as if having a real conversation.
The conversation history so far:
{conversation_context}'''

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=instruction),
            ],
        ),
    ]
    
    tools = [
        types.Tool(google_search=types.GoogleSearch())
    ]
    
    generate_content_config = types.GenerateContentConfig(
        tools=tools,
        response_mime_type="text/plain",
    )

    try:
        # Generate AI response
        response = client.models.generate_content(
            model=config.JOB_MATCHER_MODEL,
            contents=contents,
            config=generate_content_config,
        )
        
        ai_response = response.text.strip()
        
        # Sometimes Gemini adds prefixes like "Interviewer:" - let's remove those
        ai_response = ai_response.replace("Interviewer:", "").replace("AI:", "").replace("Assistant:", "").strip()
        
        # Add AI response to conversation history
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        # Save conversation history
        save_conversation_history()
        
        return ai_response
        
    except Exception as e:
        print(f"[ERROR] Error generating response: {str(e)}")
        return f"I apologize, but I'm having trouble generating a response. Let's try again."

def generate_feedback():
    """Generate feedback for the interview"""
    global conversation_history
    
    # Make sure data is loaded
    if not load_data():
        return "Error: Could not load necessary data. Please generate feedback manually."
    
    # Setup API call
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    # Create instruction prompt for feedback
    instruction = f'''You are an expert interview coach reviewing an interview that just concluded.
The candidate details are:
{json.dumps(resume_data, indent=2)}

The interview questions were based on:
{json.dumps(interview_questions, indent=2)}

The full interview conversation:
{json.dumps(conversation_history, indent=2)}

Please provide comprehensive feedback on the candidate's interview performance. Your feedback should:
1. Highlight strengths in their responses
2. Identify areas for improvement
3. Provide specific examples from their answers
4. Offer actionable advice for future interviews
5. Give an overall score out of 100

Format your feedback in HTML for better readability with appropriate headings, paragraphs, and bullet points.'''

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=instruction),
            ],
        ),
    ]
    
    tools = [
        types.Tool(google_search=types.GoogleSearch())
    ]
    
    generate_content_config = types.GenerateContentConfig(
        tools=tools,
        response_mime_type="text/plain",
    )

    try:
        # Generate feedback
        response = client.models.generate_content(
            model=config.JOB_MATCHER_MODEL,
            contents=contents,
            config=generate_content_config,
        )
        
        feedback = response.text.strip()
        
        # Reset conversation after feedback
        reset_conversation()
        
        return feedback
        
    except Exception as e:
        print(f"[ERROR] Error generating feedback: {str(e)}")
        return "<div class='alert alert-danger'>I apologize, but I'm having trouble generating your feedback. Please try again.</div>"

def save_conversation_history():
    """Save the conversation history to a file"""
    try:
        conversation_data = {
            "conversation_history": conversation_history
        }
        save_json_to_file(conversation_data, config.CONVERSATION_JSON)
    except Exception as e:
        print(f"[ERROR] Error saving conversation history: {str(e)}")

def interview_prep2_main():
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    # Load the resume data
    fetched_resume_structured_data = load_json_from_file(config.STRUCTURED_RESUME_JSON)
    if not fetched_resume_structured_data:
        print(f"[ERROR] Could not load resume data from {config.STRUCTURED_RESUME_JSON}")
        return None
    
    # Load interview questions
    interview_prep_json = load_json_from_file(config.INTERVIEW_PREP_JSON)
    
    instruction = f'''You are an interview panel member who task is to interview the candidate. The details of the candidate are 
    {fetched_resume_structured_data}
    and the questions from which you have to ask questions and do conversation are 
    {interview_prep_json}

    You have to do the conversation with the candidate and then when the user will say "ok lets over" end it and give the score to the user out of 100 based on the interview and then give suggestions to the user.
    Keep your responses concise and natural, as if having a real conversation.'''

    model = config.JOB_MATCHER_MODEL
    conversation_history = []
    
    # Start with default user message
    default_user_message = "Hi, let's begin"
    print(f"You: {default_user_message}")
    conversation_history.append({"role": "user", "content": default_user_message})
    
    while True:
        # Prepare the conversation context
        conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-5:]])
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=json.dumps(fetched_resume_structured_data)),
                    types.Part.from_text(text=conversation_context),
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
                types.Part.from_text(text=instruction),
            ],
        )

        try:
            # Generate AI response
            print("AI: ", end="")
            response_text = ""
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                print(chunk.text, end="")
                response_text += chunk.text
            
            # Add AI response to conversation history
            conversation_history.append({"role": "assistant", "content": response_text})
            
            # Save the conversation
            conversation_data = {
                "conversation_history": conversation_history
            }
            save_json_to_file(conversation_data, config.CONVERSATION_JSON)
            
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Check if user wants to end the interview
            if user_input.lower() in ["ok lets over", "end interview", "quit", "exit"]:
                print("\nAI: Thank you for completing the interview. Let me provide your score and feedback...")
                break
                
            # Add user message to conversation history
            conversation_history.append({"role": "user", "content": user_input})
            
        except Exception as e:
            print(f"\n[ERROR] An error occurred: {str(e)}")
            print("AI: I apologize for the technical difficulty. Could you please repeat your last response?")
            continue

if __name__ == "__main__":
    interview_prep2_main()
