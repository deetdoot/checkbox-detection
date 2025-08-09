import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:", json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_file_upload(image_path):
    """Test checkbox analysis with file upload"""
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path, f, 'image/png')}
            response = requests.post(f"{BASE_URL}/analyze-checkboxes", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("File Upload Analysis:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error testing file upload: {e}")
        return False

def test_url_analysis(image_url):
    """Test checkbox analysis with image URL"""
    try:
        data = {"image_url": image_url}
        response = requests.post(f"{BASE_URL}/analyze-checkboxes-url", params=data)
        
        if response.status_code == 200:
            result = response.json()
            print("URL Analysis:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error testing URL analysis: {e}")
        return False

if __name__ == "__main__":
    print("Testing Checkbox Detection API...")
    
    # Test health check
    if test_health_check():
        print("Health check passed")
    else:
        print("Health check failed")
    
    # Test with local file
    image_path = "/Users/emtiazahamed/Desktop/check-box-detection/sample_photos/2.png"
    if test_file_upload(image_path):
        print("File upload test passed")
    else:
        print("File upload test failed")
    
    # You can add URL test here if you have a public image URL
    # test_url_analysis("https://example.com/checkbox-form.png")
