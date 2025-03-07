# watch the video for this project here: https://youtu.be/bZ88gnHzwz8
import requests, statistics
from PIL import Image
from io import BytesIO
import re

MAX_COLOR_VALUE = 256
MAX_BIT_VALUE = 8

def make_image(data, resolution):
    image = Image.new("RGB", resolution)
    image.putdata(data)

    return image

def remove_n_least_significant_bits(value, n):
    value = value >> n 
    return value << n

def get_n_least_significant_bits(value, n):
    value = value << MAX_BIT_VALUE - n
    value = value % MAX_COLOR_VALUE
    return value >> MAX_BIT_VALUE - n

def get_n_most_significant_bits(value, n):
    return value >> MAX_BIT_VALUE - n

def shit_n_bits_to_8(value, n):
    return value << MAX_BIT_VALUE - n

def lsbencode(image_to_hide, image_to_hide_in, n_bits):

    width, height = image_to_hide.size

    hide_image = image_to_hide.load()
    hide_in_image = image_to_hide_in.load()

    data = []

    for y in range(height):
        for x in range(width):

            # (107, 3, 10)
            # most sig bits
            r_hide, g_hide, b_hide = hide_image[x,y]

            r_hide = get_n_most_significant_bits(r_hide, n_bits)
            g_hide = get_n_most_significant_bits(g_hide, n_bits)
            b_hide = get_n_most_significant_bits(b_hide, n_bits)

            # remove lest n sig bits
            r_hide_in, g_hide_in, b_hide_in = hide_in_image[x,y]

            r_hide_in = remove_n_least_significant_bits(r_hide_in, n_bits)
            g_hide_in = remove_n_least_significant_bits(g_hide_in, n_bits)
            b_hide_in = remove_n_least_significant_bits(b_hide_in, n_bits)

            data.append((r_hide + r_hide_in, 
                         g_hide + g_hide_in,
                         b_hide + b_hide_in))

    return make_image(data, image_to_hide.size)

def lsbdecode(image_to_decode, n_bits):
    width, height = image_to_decode.size
    encoded_image = image_to_decode.load()

    data = []

    for y in range(height):
        for x in range(width):

            r_encoded, g_encoded, b_encoded = encoded_image[x,y]
            
            r_encoded = get_n_least_significant_bits(r_encoded, n_bits)
            g_encoded = get_n_least_significant_bits(g_encoded, n_bits)
            b_encoded = get_n_least_significant_bits(b_encoded, n_bits)

            r_encoded = shit_n_bits_to_8(r_encoded, n_bits)
            g_encoded = shit_n_bits_to_8(g_encoded, n_bits)
            b_encoded = shit_n_bits_to_8(b_encoded, n_bits)

            data.append((r_encoded, g_encoded, b_encoded))

    return make_image(data, image_to_decode.size)

def resize_and_pad(image_to_hide, target_size):
    """
    Resizes an image while maintaining aspect ratio and adds padding to match the target size.
    """
    # Resize while maintaining aspect ratio
    image_to_hide.thumbnail(target_size, Image.Resampling.LANCZOS)

    # Create a new image with the target size and a white background
    padded_image = Image.new("RGB", target_size, color=(255, 255, 255))

    # Paste the resized image in the center of the new image
    paste_x = (target_size[0] - image_to_hide.size[0]) // 2
    paste_y = (target_size[1] - image_to_hide.size[1]) // 2
    padded_image.paste(image_to_hide, (paste_x, paste_y))

    return padded_image

def text_to_binary(text):
    """Convert text to binary representation."""
    binary = bin(int.from_bytes(text.encode(), 'big'))[2:]
    # Pad the binary string to ensure it's a multiple of 8
    return binary.zfill((len(binary) + 7) // 8 * 8)

def binary_to_text(binary):
    """Convert binary representation back to text."""
    # Convert binary string to bytes
    n = int(binary, 2)
    return n.to_bytes((n.bit_length() + 7) // 8, 'big').decode()

def encode_text_in_image(image_path, text, n_bits=2):
    """
    Encode text into an image using LSB steganography.
    
    :param image_path: Path to the carrier image
    :param text: Text to hide
    :param n_bits: Number of least significant bits to use (default 2)
    :return: Modified image with encoded text
    """
    # Open the image
    image = Image.open(image_path).convert("RGB")
    pixels = image.load()
    width, height = image.size

    # Convert text to binary
    binary_text = text_to_binary(text)
    
    # Add length of text as prefix (to know how much to decode later)
    binary_text = f"{len(binary_text):032b}" + binary_text
    
    # Check if image is large enough to hide the text
    max_text_bits = (width * height * 3 * n_bits)
    if len(binary_text) > max_text_bits:
        raise ValueError(f"Text is too long to hide. Maximum {max_text_bits} bits can be hidden.")

    # Encode binary text into image
    binary_index = 0
    for y in range(height):
        for x in range(width):
            # Get current pixel
            r, g, b = pixels[x, y]
            
            # Modify color channels
            if binary_index < len(binary_text):
                # Red channel
                r_modified = (r & ~((1 << n_bits) - 1)) | int(binary_text[binary_index:binary_index+n_bits], 2)
                binary_index += n_bits
            
            if binary_index < len(binary_text):
                # Green channel
                g_modified = (g & ~((1 << n_bits) - 1)) | int(binary_text[binary_index:binary_index+n_bits], 2)
                binary_index += n_bits
            
            if binary_index < len(binary_text):
                # Blue channel
                b_modified = (b & ~((1 << n_bits) - 1)) | int(binary_text[binary_index:binary_index+n_bits], 2)
                binary_index += n_bits
            
            # Update pixel
            pixels[x, y] = (r_modified, g_modified, b_modified)
            
            # Stop if we've encoded entire text
            if binary_index >= len(binary_text):
                break
        
        if binary_index >= len(binary_text):
            break

    return image

def decode_text_from_image(image_path, n_bits=2):
    """
    Decode hidden text from an image.
    
    :param image_path: Path to the image with hidden text
    :param n_bits: Number of least significant bits used (default 2)
    :return: Decoded text
    """
    # Open the image
    image = Image.open(image_path).convert("RGB")
    pixels = image.load()
    width, height = image.size

    # Decode binary text
    binary_text = ""
    bit_count = 0
    text_length = None

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            # Extract bits from each channel
            r_bits = r & ((1 << n_bits) - 1)
            binary_text += format(r_bits, f'0{n_bits}b')
            bit_count += n_bits
            
            if text_length is None and bit_count >= 32:
                # First 32 bits represent the total text length
                text_length = int(binary_text[:32], 2)
                binary_text = binary_text[32:]
                bit_count -= 32
            
            if text_length is not None and bit_count >= text_length:
                break
            
            g_bits = g & ((1 << n_bits) - 1)
            binary_text += format(g_bits, f'0{n_bits}b')
            bit_count += n_bits
            
            if text_length is not None and bit_count >= text_length:
                break
            
            b_bits = b & ((1 << n_bits) - 1)
            binary_text += format(b_bits, f'0{n_bits}b')
            bit_count += n_bits
            
            if text_length is not None and bit_count >= text_length:
                break
        
        if text_length is not None and bit_count >= text_length:
            break

    # Trim to exact text length and convert back to text
    return binary_to_text(binary_text[:text_length])

# def decode_text_from_url(image_url, n_bits=2):
#     """
#     Decode hidden text from an image accessed via URL.
    
#     :param image_url: URL of the image with hidden text
#     :param n_bits: Number of least significant bits used (default 2)
#     :return: Decoded text
#     :raises: RequestException if URL fetch fails, ValueError if image processing fails
#     """
#     try:
#         # Download the image from URL
#         response = requests.get(image_url, timeout=10)
#         response.raise_for_status()  # Raise exception for bad status codes
        
#         # Create image from downloaded bytes
#         image = Image.open(BytesIO(response.content)).convert("RGB")
#         pixels = image.load()
#         width, height = image.size

#         # Decode binary text
#         binary_text = ""
#         bit_count = 0
#         text_length = None

#         for y in range(height):
#             for x in range(width):
#                 r, g, b = pixels[x, y]
                
#                 # Extract bits from each channel
#                 r_bits = r & ((1 << n_bits) - 1)
#                 binary_text += format(r_bits, f'0{n_bits}b')
#                 bit_count += n_bits
                
#                 if text_length is None and bit_count >= 32:
#                     # First 32 bits represent the total text length
#                     text_length = int(binary_text[:32], 2)
#                     binary_text = binary_text[32:]
#                     bit_count -= 32
                
#                 if text_length is not None and bit_count >= text_length:
#                     break
                
#                 g_bits = g & ((1 << n_bits) - 1)
#                 binary_text += format(g_bits, f'0{n_bits}b')
#                 bit_count += n_bits
                
#                 if text_length is not None and bit_count >= text_length:
#                     break
                
#                 b_bits = b & ((1 << n_bits) - 1)
#                 binary_text += format(b_bits, f'0{n_bits}b')
#                 bit_count += n_bits
                
#                 if text_length is not None and bit_count >= text_length:
#                     break
            
#             if text_length is not None and bit_count >= text_length:
#                 break

#         # Trim to exact text length and convert back to text
#         return binary_to_text(binary_text[:text_length])

#     except requests.RequestException as e:
#         raise ValueError(f"Failed to download image from URL: {str(e)}")
#     except Exception as e:
#         raise ValueError(f"Failed to process image: {str(e)}")
    
def validate_steganography(image, n_bits=2):
    """
    Validate if an image likely contains steganographic content.
    
    :param image: PIL Image object
    :param n_bits: Number of least significant bits used
    :return: tuple (bool, str) - (is_valid, reason)
    """
    pixels = image.load()
    width, height = image.size
    
    # Check 1: Get the first 32 bits to read the claimed length
    binary_text = ""
    for y in range(min(4, height)):  # We only need first few pixels for length
        for x in range(min(4, width)):
            r, g, b = pixels[x, y]
            r_bits = r & ((1 << n_bits) - 1)
            binary_text += format(r_bits, f'0{n_bits}b')
            if len(binary_text) >= 32:
                break
        if len(binary_text) >= 32:
            break
    
    try:
        claimed_length = int(binary_text[:32], 2)
        
        # Check if claimed length is reasonable
        max_possible_length = (width * height * 3 * n_bits) // 8
        if claimed_length <= 0 or claimed_length > max_possible_length:
            return False, "Invalid claimed message length"
            
        # Check if claimed length is suspiciously large
        if claimed_length > max_possible_length // 2:
            return False, "Suspiciously large message length"
    except ValueError:
        return False, "Invalid length encoding"
    
    # Check 2: Statistical analysis of least significant bits
    # Sample a portion of the image to save processing time
    sample_size = min(1000, width * height)
    lsb_values = []
    
    for i in range(sample_size):
        x = i % width
        y = i // width
        r, g, b = pixels[x, y]
        lsb_values.extend([
            r & ((1 << n_bits) - 1),
            g & ((1 << n_bits) - 1),
            b & ((1 << n_bits) - 1)
        ])
    
    # Calculate statistics of LSBs
    std_dev = statistics.stdev(lsb_values)
    mean = statistics.mean(lsb_values)
    
    # In true steganographic images, LSBs should be fairly random
    # If they're too uniform or too patterned, it's probably not steganographic
    if std_dev < 0.5 or (mean < 0.1 or mean > (2**n_bits - 0.1)):
        return False, "LSB pattern suggests no hidden data"
    
    return True, "Image likely contains hidden data"

def decode_text_from_url(image_url, n_bits=2):
    """
    Decode hidden text from an image accessed via URL.
    
    :param image_url: URL of the image with hidden text
    :param n_bits: Number of least significant bits used (default 2)
    :return: Decoded text or error message
    """
    try:
        # Download the image from URL
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Create image from downloaded bytes
        image = Image.open(BytesIO(response.content)).convert("RGB")
        
        # # Validate if image contains steganographic content
        # is_valid, reason = validate_steganography(image, n_bits)
        # if not is_valid:
        #     # return f"No hidden message detected: {reason}"
        #     return False
        
        pixels = image.load()
        width, height = image.size

        # Decode binary text
        binary_text = ""
        bit_count = 0
        text_length = None

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                
                # Extract bits from each channel
                r_bits = r & ((1 << n_bits) - 1)
                binary_text += format(r_bits, f'0{n_bits}b')
                bit_count += n_bits
                
                if text_length is None and bit_count >= 32:
                    text_length = int(binary_text[:32], 2)
                    binary_text = binary_text[32:]
                    bit_count -= 32
                
                if text_length is not None and bit_count >= text_length:
                    break
                
                g_bits = g & ((1 << n_bits) - 1)
                binary_text += format(g_bits, f'0{n_bits}b')
                bit_count += n_bits
                
                if text_length is not None and bit_count >= text_length:
                    break
                
                b_bits = b & ((1 << n_bits) - 1)
                binary_text += format(b_bits, f'0{n_bits}b')
                bit_count += n_bits
                
                if text_length is not None and bit_count >= text_length:
                    break
            
            if text_length is not None and bit_count >= text_length:
                break

        return binary_to_text(binary_text[:text_length])

    except requests.RequestException as e:
        # return f"Failed to download image from URL: {str(e)}"
        return False
    except Exception as e:
        # return f"Failed to process image: {str(e)}"
        return False

def extract_image_url(text):
    # Regex pattern to match .png and .jpg URLs
    pattern = r'https?://[^\s]+(?:\.png|\.jpe?g)'
    
    match = re.search(pattern, text)
    return match.group(0) if match else None

# def extract_image_url(text):
#     """
#     Extract image URLs from text that end in .png, .jpg, or .jpeg
#     Handles multiline strings and case-insensitive extension matching.
    
#     :param text: Text containing potential image URLs (can be multiline)
#     :return: First matched image URL or None if no match found
#     """
#     # Regex pattern to match image URLs with re.DOTALL flag to handle newlines
#     pattern = r'https?://[^\s<>"\']+?(?i)\.(?:png|jpe?g)'
    
#     try:
#         match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
#         if match:
#             url = match.group(0)
#             # Additional validation to ensure URL doesn't have trailing punctuation
#             url = re.sub(r'[.,!?)]$', '', url)
#             return url
#         return None
#     except Exception as e:
#         return None

# def extract_all_image_urls(text):
#     """
#     Extract all image URLs from text that end in .png, .jpg, or .jpeg
#     Handles multiline strings and case-insensitive extension matching.
    
#     :param text: Text containing potential image URLs (can be multiline)
#     :return: List of matched image URLs
#     """
#     pattern = r'https?://[^\s<>"\']+?(?i)\.(?:png|jpe?g)'
    
#     try:
#         # Find all matches
#         matches = re.finditer(pattern, text, re.DOTALL | re.MULTILINE)
#         # Clean up URLs and remove any trailing punctuation
#         urls = [re.sub(r'[.,!?)]$', '', match.group(0)) for match in matches]
#         return urls
#     except Exception as e:
#         return []
    

if __name__ == "__main__":
    # # Image on Image LSB
    # image_to_hide_path = "qrcode1.png"
    # image_to_hide_in_path = "nutmeme.jpg"
    # encoded_image_path = "encodedecash.png"
    # decoded_image_path = "decodedecash.png"
    # n_bits = 2

    # image_to_hide = Image.open(image_to_hide_path).convert("RGB")
    # image_to_hide_in = Image.open(image_to_hide_in_path).convert("RGB")

    # # Resize and pad the QR code to match the size of the carrier image
    # image_to_hide = resize_and_pad(image_to_hide, image_to_hide_in.size)

    # lsbencode(image_to_hide, image_to_hide_in, n_bits).save(encoded_image_path)

    # image_to_decode = Image.open(encoded_image_path)
    # lsbdecode(image_to_decode, n_bits).save(decoded_image_path)

    # Text on Image LSB
    # Encode text
    # carrier_image = r"C:\Users\clayt\Downloads\secretimage.png"
    # secret_text = "This is a super secret message!"
    # encoded_image = encode_text_in_image(carrier_image, secret_text)
    # encoded_image.save("encoded_image.png")

    # Decode text
    # target_image = r"C:\Users\clayt\Downloads\secretimage.png"
    # decoded_text = decode_text_from_image(target_image)
    # target_url = 'https://image.nostr.build/f2cab01dbc3c016dbb10f0d2917e19beb8b580084b931f407265cdd0704245f3.png'
    # target_url = 'https://primal.b-cdn.net/media-cache?s=o&a=0&u=https%3A%2F%2Fm.primal.net%2FOdwF.jpg'
    # target_url = 'https://image.nostr.build/6ba5fd6db986727d61340f4f4714ac644da6a78530686cb96b06abe5e90373ef.png'
    # decoded_text = decode_text_from_url(target_url)
    # print(decoded_text)

    # Extract url
    # import re
    # def extract_image_url(text):
    #     # Regex pattern to match .png and .jpg URLs
    #     pattern = r'https?://[^\s]+(?:\.png|\.jpg)'
        
    #     match = re.search(pattern, text)
    #     return match.group(0) if match else None
    
    event = str({"id":"d0100ddb990b06e1708fde6efa2976c2d3b66ff8e989690a0a588a9607cd1033","sig":"92f65f69639eb118d7d83a7307560171d19de685ca636e94f2e0b806e795666963d881a40205956aeef8805ee5f1a3e7364be9168299a641d153944b4b83c0cc","kind":1,"tags":[["r","wss://nostr.wine/"],["r","wss://relay.gifbuddy.lol/"],["r","wss://relay.damus.io/"],["r","wss://eden.nostr.land/"],["r","wss://news.utxo.one/"],["r","wss://nos.lol/"],["r","wss://relay.primal.net/"]],"pubkey":"be7358c4fe50148cccafc02ea205d80145e253889aa3958daafa8637047c840e","content":"gn\nhttps://image.nostr.build/6ba5fd6db986727d61340f4f4714ac644da6a78530686cb96b06abe5e90373ef.png","created_at":1739523520})
    event = """gn\nhttps://image.nostr.build/6ba5fd6db986727d61340f4f4714ac644da6a78530686cb96b06abe5e90373ef.png"""
    url = extract_image_url(event)
    print(url)