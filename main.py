import ollama
from PIL import Image
import io

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
image_path = "/Users/emtiazahamed/Desktop/check-box-detection/sample_photos/2.png"
image = Image.open(image_path)

# Optionally, show image info
print(f"Image size: {image.size}, mode: {image.mode}")


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

# Convert the image to bytes for sending to the LLM (if supported)
image_bytes_io = io.BytesIO()
if image.format == 'PNG':
    image.save(image_bytes_io, format='PNG')
else:
    image.save(image_bytes_io, format='JPEG')
image_bytes = image_bytes_io.getvalue()

# Send the prompt and image to the LLM (assuming ollama.chat supports images)
response = ollama.chat(
        model=model_name,
        messages=[
                {"role": "user", "content": document_verifier_prompt, "images": [image_bytes]}
        ]
)

print(response['message']['content'])