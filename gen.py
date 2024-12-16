import requests
from typing import Optional
import urllib.parse
import tempfile
import os

class ImageDownloader:
    def __init__(self):
        self.base_url = "https://image.pollinations.ai/prompt/"

    def download_image_from_url(self, image_url: str, output_filename: str) -> bool:
        """
        Download image from a given URL and save it to a file
        
        Args:
            image_url (str): URL of the image to download
            output_filename (str): Name of the file to save the image
            
        Returns:
            bool: True if download successful, False otherwise
        """
        try:
            response = requests.get(image_url, timeout=30)  # Added timeout
            response.raise_for_status()
            
            with open(output_filename, 'wb') as file:
                file.write(response.content)
            print(f'Download completed: {output_filename}')
            return True
            
        except requests.RequestException as e:
            print(f'Error downloading image: {e}')
            return False
        except IOError as e:
            print(f'Error saving image: {e}')
            return False

    def generate_pollinations_url(self, prompt: str, width: int = 512, height: int = 512, 
                                seed: Optional[int] = None, model: str = 'stable-diffusion') -> str:
        """
        Generate a Pollinations.ai URL with the given parameters
        """
        # URL encode the prompt
        encoded_prompt = urllib.parse.quote(prompt)
        params = {
            'width': width,
            'height': height,
            'model': model
        }
        if seed is not None:
            params['seed'] = seed
            
        url = f"{self.base_url}{prompt}"
        params_str = '&'.join(f"{k}={v}" for k, v in params.items())
        return f"{url}?{params_str}"

    def generate_with_pollinations(self, prompt: str, width: int, height: int,
                                 seed: Optional[int] = None, 
                                 output_filename: str = 'image-output.jpg') -> Optional[str]:
        """
        Generate image using Pollinations API
        
        Returns:
            Optional[str]: URL of the generated image if successful, None otherwise
        """
        try:
            # Generate the URL
            url = self.generate_pollinations_url(prompt, width, height, seed)
            
            # Download the image
            success = self.download_image_from_url(url, output_filename)
            
            if success:
                return url
            return None
            
        except Exception as e:
            print(f'Error generating image: {e}')
            return None

def generate_image(prompt: str, width: int = 1024, height: int = 1024, seed: Optional[int] = None) -> Optional[str]:
    """
    Generate an image using Pollinations API and return the path to the saved image
    
    Args:
        prompt (str): Description of the image to generate
        width (int): Image width (default: 1024)
        height (int): Image height (default: 1024)
        seed (Optional[int]): Random seed for consistent generation (default: None)
        
    Returns:
        Optional[str]: Path to the generated image file, or None if generation failed
    """
    try:
        # Create ImageDownloader instance
        downloader = ImageDownloader()
        
        # Create a temporary file with .png extension
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        # Generate the image using Pollinations
        generated_url = downloader.generate_with_pollinations(
            prompt=prompt,
            width=width,
            height=height,
            seed=seed,
            output_filename=temp_path
        )
        
        if generated_url and os.path.exists(temp_path):
            return temp_path
        return None
        
    except Exception as e:
        print(f"Error in generate_image: {str(e)}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        return None

def main():
    # Example usage
    downloader = ImageDownloader()
    
    # Example parameters
    prompt = 'half shark and half human'
    width = 1384
    height = 1384
    seed = 14111

    # Method 1: Using direct URL download
    url = downloader.generate_pollinations_url(prompt, width, height, seed)
    downloader.download_image_from_url(url, 'direct-download.jpg')

    # Method 2: Using Pollinations API
    generated_url = downloader.generate_with_pollinations(
        prompt=prompt,
        width=width,
        height=height,
        seed=seed,
        output_filename='pollinations-output.jpg'
    )
    
    if generated_url:
        print(f'Generated image URL: {generated_url}')

if __name__ == "__main__":
    main()
