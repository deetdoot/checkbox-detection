import ollama
from PIL import Image
import io
import os
from opik import track
from dotenv import load_dotenv
import weaviate
from weaviate.classes.init import Auth
from opik.evaluation.metrics import (Hallucination)
from opik.evaluation import evaluate
from opik import Opik


# Load environment variables from .env file
load_dotenv()
weaviate_url = os.getenv("WEAVIATE_URL")
weaviate_api_key = os.getenv("WEAVIATE_API_KEY")    


weaviate_client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
)

weaviate_client.connect()


print(weaviate_client.is_ready())  # Should print: `True`


# Load environment variables from .env file
load_dotenv()

# Set environment variables for Opik from .env
os.environ["OPIK_API_KEY"] = os.getenv("OPIK_API_KEY")
os.environ["OPIK_WORKSPACE"] = os.getenv("OPIK_WORKSPACE")


# Load the granite3.2-vision:2b model
model_name = "granite3.2-vision:2b"  # Updated to use the correct model name

# Pull the model if not already available
ollama.pull(model_name)

# Run a simple prompt using the model
response = ollama.chat(model=model_name, messages=[
    {"role": "user", "content": "Hello, how are you?"}
])

#print(response['message']['content'])


# Read the image '1.jpg'
image_path = "/Users/emtiazahamed/Desktop/check-box-detection/sample_photos/3.png"

# Create a prompt for the LLM to act as an intelligent document verifier
document_verifier_prompt = """
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


opik_client = Opik()

@track
def analyze_checkbox_document(image_path, model_name, document_verifier_prompt):
    """Analyze checkboxes in document image with Opik tracing"""
    # Load and process the image
    image = Image.open(image_path)
    print(f"Image size: {image.size}, mode: {image.mode}")
    
    # Convert the image to bytes for sending to the LLM
    image_bytes_io = io.BytesIO()
    if image.format == 'PNG':
        image.save(image_bytes_io, format='PNG')
    else:
        image.save(image_bytes_io, format='JPEG')
    image_bytes = image_bytes_io.getvalue()
    
    # Send the prompt and image to the LLM (now with tracing)
    response = ollama.chat(
            model=model_name,
            messages=[
                    {"role": "user", "content": document_verifier_prompt, "images": [image_bytes]}
            ]
    )
    
    return response['message']['content']

# Execute the analysis with tracing
result = analyze_checkbox_document(image_path, model_name, document_verifier_prompt)
print(result)

def evaluation_task(dataset_item):
    # your LLM application is called here

    result_to_eval = {

        "input": image_path,
        "output": result,
        "context": "Nothing"
    }

    return result_to_eval

dataset = opik_client.get_dataset(name="checkbox")

metrics = [Hallucination()]

# eval_results = evaluate(
#   experiment_name="my_evaluation",
#   dataset=dataset,
#   task=evaluation_task,
#   scoring_metrics=metrics
# )


questions = weaviate_client.collections.get("Checkbox_task_collection")

with questions.batch.fixed_size(batch_size=200) as batch:
    batch.add_object(
        {
            "filepath": image_path,
            "output": result,
        }
    )

weaviate_client.close()  # Free up resources
