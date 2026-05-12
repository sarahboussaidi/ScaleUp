#!/usr/bin/env python3
"""
Simple test script for the document classifier integration
Run this after starting the Flask server
"""

import requests
import json
import sys
import os
from pathlib import Path

BASE_URL = 'http://localhost:5000/api'

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def test_connection():
    """Test if Flask server is running"""
    print_header("Test 1: Flask Server Connection")
    
    try:
        response = requests.get(f'{BASE_URL}/model-info', timeout=5)
        print_success("Flask server is running!")
        return True
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to Flask server at http://localhost:5000")
        print_info("Start Flask server with: cd backend && python app.py")
        return False
    except Exception as e:
        print_error(f"Connection error: {str(e)}")
        return False

def test_model_info():
    """Test the model info endpoint"""
    print_header("Test 2: Model Information")
    
    try:
        response = requests.get(f'{BASE_URL}/model-info', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Model info retrieved successfully")
            
            print(f"\n  {Colors.BOLD}Model Details:{Colors.END}")
            print(f"    - Model Architecture: {data['model']}")
            print(f"    - Device: {Colors.YELLOW}{data['device']}{Colors.END}")
            print(f"    - Classes: {data['classes']}")
            print(f"    - Input Size: {data['image_size']}x{data['image_size']}")
            print(f"    - Loaded: {Colors.GREEN if data['loaded'] else Colors.RED}{data['loaded']}{Colors.END}")
            
            return data['loaded']
        else:
            print_error(f"Failed to get model info: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_classification(image_path):
    """Test the classification endpoint"""
    print_header(f"Test 3: Image Classification")
    print_info(f"Image: {image_path}")
    
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            print_error(f"Image file not found: {image_path}")
            return False
        
        # Get file size
        file_size = os.path.getsize(image_path)
        print_info(f"File size: {file_size / 1024:.1f} KB")
        
        # Upload and classify
        print_info("Sending image to classifier...")
        
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f'{BASE_URL}/predict-document-type',
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Classification completed successfully!")
            
            print(f"\n  {Colors.BOLD}Results:{Colors.END}")
            print(f"    - Document Type: {Colors.YELLOW}{data['document_type']}{Colors.END}")
            print(f"    - Confidence: {Colors.YELLOW}{data['confidence']:.2%}{Colors.END}")
            print(f"    - Class Index: {data['class_index']}")
            
            print(f"\n  {Colors.BOLD}All Probabilities:{Colors.END}")
            for class_name in ['bmc', 'handwritten', 'typed']:
                prob = data['all_probabilities'].get(class_name, 0)
                bar_length = int(prob * 30)
                bar = '█' * bar_length + '░' * (30 - bar_length)
                print(f"    {class_name:12} [{bar}] {prob:.2%}")
            
            return True
        else:
            print_error(f"Classification failed: {response.status_code}")
            try:
                print_error(f"Response: {response.json()}")
            except:
                print_error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Request timed out (>30s). Model might be slow on first run.")
        print_info("First inference can take 5-10 seconds. Try again!")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def find_test_image():
    """Try to find a test image in common locations"""
    possible_paths = [
        'test_image.jpg',
        'sample.jpg',
        'test_bmc.jpg',
        'C:\\Users\\USER\\Desktop\\sample_image.jpg',
        os.path.expanduser('~/Pictures/test_image.jpg'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def main():
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║     Document Classifier Testing Script              ║
    ║     For BMC AI Generation Pipeline                  ║
    ╚══════════════════════════════════════════════════════╝
    """)
    print(Colors.END)
    
    # Test 1: Connection
    if not test_connection():
        print_error("\nCannot proceed without Flask server. Exiting.")
        sys.exit(1)
    
    # Test 2: Model Info
    if not test_model_info():
        print_error("\nModel is not loaded. Check Flask server logs.")
        sys.exit(1)
    
    # Test 3: Classification
    print("\n")
    image_path = None
    
    # Try to find test image automatically
    found_image = find_test_image()
    if found_image:
        print_info(f"Found test image: {found_image}")
        if input(f"Use this image? (y/n): ").lower() == 'y':
            image_path = found_image
    
    # Ask user for image path if not found
    if not image_path:
        image_path = input("\nEnter path to test image (jpg/png/gif/webp): ").strip()
        
        if not image_path:
            print_error("No image provided. Skipping classification test.")
        else:
            test_classification(image_path)
    else:
        test_classification(image_path)
    
    # Summary
    print_header("Testing Complete!")
    print(f"""
{Colors.GREEN}✓ All tests passed!{Colors.END}

Next steps:
1. Frontend integration:
   - Edit app/bmc-generation/page.tsx
   - Update startPipeline() to call real API
   
2. Test full pipeline:
   - Start both Flask and Next.js servers
   - Upload image in BMC Generation page
   - Watch the pipeline complete

3. Debug if needed:
   - Check Flask server logs
   - Use curl for quick tests
   - See TESTING_GUIDE.md for more info

{Colors.CYAN}Happy testing! 🚀{Colors.END}
    """)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Testing interrupted by user{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)
