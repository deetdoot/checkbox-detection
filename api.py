from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import ollama
import io
import json
from typing import Dict, Any
import uvicorn
import requests
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(
    title="Checkbox Detection API",
    description="An API service for detecting and analyzing checkboxes in document images",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Model configuration
MODEL_NAME = "granite3.2-vision:2b"

# Document verifier prompt
DOCUMENT_VERIFIER_PROMPT = """
You are an intelligent document verifier. Your job is to analyze images of documents and determine their meaning.

Specifically, you can understand checkboxes in photos. You can identify which options are checked or unchecked.

IMPORTANT: Only analyze checkboxes that are actually visible in the image. Do not include any fields or options that are not present.

Options may be True/False or multiple choice. For grouped options (like Gender, Race, etc.), use nested JSON structure.

For example, if the image contains:
- A simple checkbox for "Option A" that is checked
- A simple checkbox for "Option B" that is unchecked  
- A grouped set like "Gender" with "Male" unchecked and "Female" checked

Your response should look like this:
{
    "Option A": "Checked",
    "Option B": "Unchecked",
    "Gender": {
        "Male": "Unchecked",
        "Female": "Checked"
    }
}

Use "Checked" for selected options and "Unchecked" for unselected options. For grouped options, create nested objects with the group name as the key.

ONLY include checkboxes and options that are actually visible in the image. Do not add any fields that are not present. Don't add any text that doesn't appear in the image.

Analyze the attached image and provide your results. Be as brief and accurate as possible. Do not include any additional text or explanations.
"""

@app.on_event("startup")
async def startup_event():
    """Initialize the model on startup"""
    try:
        # Pull the model if not already available
        ollama.pull(MODEL_NAME)
        print(f"Model {MODEL_NAME} is ready")
    except Exception as e:
        print(f"Warning: Could not pull model {MODEL_NAME}: {e}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={
            "status_code": 200,
            "message": "Checkbox Detection API is running",
            "data": {
                "model": MODEL_NAME
            }
        }
    )

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test if ollama is available
        models = ollama.list()
        model_available = any(model['name'].startswith(MODEL_NAME) for model in models['models'])
        
        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "System health check completed",
                "data": {
                    "status": "healthy",
                    "model": MODEL_NAME,
                    "model_available": model_available,
                    "ollama_running": True
                }
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status_code": 503,
                "message": "System health check failed",
                "data": {
                    "status": "unhealthy",
                    "error": str(e),
                    "ollama_running": False
                }
            }
        )

@app.post("/analyze-checkboxes")
async def analyze_checkboxes(file: UploadFile = File(...)) -> JSONResponse:
    """
    Analyze checkboxes in an uploaded image
    
    Args:
        file: Image file (PNG, JPEG, etc.)
        
    Returns:
        JSONResponse with checkbox analysis results
    """
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        return JSONResponse(
            status_code=400,
            content={
                "status_code": 400,
                "message": "File must be an image",
                "data": None
            }
        )
    
    try:
        # Read and process the image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Get image info
        image_info = {
            "size": image.size,
            "mode": image.mode,
            "format": image.format
        }
        
        # Convert image to bytes for ollama
        image_bytes_io = io.BytesIO()
        if image.format == 'PNG':
            image.save(image_bytes_io, format='PNG')
        else:
            image.save(image_bytes_io, format='JPEG')
        image_bytes = image_bytes_io.getvalue()
        
        # Send to model for analysis
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user", 
                    "content": DOCUMENT_VERIFIER_PROMPT, 
                    "images": [image_bytes]
                }
            ]
        )
        
        # Parse the response
        analysis_result = response['message']['content']
        
        # Try to parse as JSON
        try:
            # Clean up the response if it has markdown code blocks
            if analysis_result.startswith('```json'):
                analysis_result = analysis_result.strip('```json').strip('```').strip()
            elif analysis_result.startswith('```'):
                analysis_result = analysis_result.strip('```').strip()
            
            parsed_result = json.loads(analysis_result)
        except json.JSONDecodeError:
            # If JSON parsing fails, return raw response
            parsed_result = {"raw_response": analysis_result}
        
        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Image analysis completed successfully",
                "data": {
                    "image_info": image_info,
                    "checkbox_analysis": parsed_result,
                    "filename": file.filename
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "message": f"Error processing image: {str(e)}",
                "data": None
            }
        )

@app.post("/analyze-checkboxes-url")
async def analyze_checkboxes_from_url(image_url: str) -> JSONResponse:
    """
    Analyze checkboxes from an image URL
    
    Args:
        image_url: URL of the image to analyze
        
    Returns:
        JSONResponse with checkbox analysis results
    """
    try:
        if not image_url:
            return JSONResponse(
                status_code=400,
                content={
                    "status_code": 400,
                    "message": "Image URL is required",
                    "data": None
                }
            )
        
        # Download image from URL
        try:
            response = requests.get(image_url)
            response.raise_for_status()
        except requests.RequestException as e:
            return JSONResponse(
                status_code=400,
                content={
                    "status_code": 400,
                    "message": f"Failed to download image from URL: {str(e)}",
                    "data": None
                }
            )
        
        # Process the image
        try:
            image = Image.open(io.BytesIO(response.content))
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={
                    "status_code": 400,
                    "message": f"Invalid image format: {str(e)}",
                    "data": None
                }
            )
        
        # Get image info
        image_info = {
            "size": image.size,
            "mode": image.mode,
            "format": image.format,
            "url": image_url
        }
        
        # Convert image to bytes for ollama
        image_bytes_io = io.BytesIO()
        if image.format == 'PNG':
            image.save(image_bytes_io, format='PNG')
        else:
            image.save(image_bytes_io, format='JPEG')
        image_bytes = image_bytes_io.getvalue()
        
        # Send to model for analysis
        ollama_response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user", 
                    "content": DOCUMENT_VERIFIER_PROMPT, 
                    "images": [image_bytes]
                }
            ]
        )
        
        # Parse the response
        analysis_result = ollama_response['message']['content']
        
        # Try to parse as JSON
        try:
            # Clean up the response if it has markdown code blocks
            if analysis_result.startswith('```json'):
                analysis_result = analysis_result.strip('```json').strip('```').strip()
            elif analysis_result.startswith('```'):
                analysis_result = analysis_result.strip('```').strip()
            
            parsed_result = json.loads(analysis_result)
        except json.JSONDecodeError:
            # If JSON parsing fails, return raw response
            parsed_result = {"raw_response": analysis_result}
        
        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Image analysis completed successfully",
                "data": {
                    "image_info": image_info,
                    "checkbox_analysis": parsed_result
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "message": f"Error processing image from URL: {str(e)}",
                "data": None
            }
        )

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
