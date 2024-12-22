from PIL import ImageFont, ImageDraw, Image
from io import BytesIO

def create_overlay_image(base_image: BytesIO, text: str, font_path: str, font_size: int, text_color: str = "white"):
    """
    Adds custom text overlay on an image.

    Args:
    - base_image (BytesIO): The base image in bytes.
    - text (str): The overlay text to add.
    - font_path (str): Path to the font file.
    - font_size (int): Size of the font.
    - text_color (str): Color of the text.

    Returns:
    - BytesIO: Image with the overlay text.
    """
    # Open base image
    base_img = Image.open(base_image).convert("RGBA")

    # Create an overlay layer
    overlay = Image.new("RGBA", base_img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    # Load font
    font = ImageFont.truetype(font_path, font_size)

    # Calculate text size and position
    text_width, text_height = draw.textsize(text, font=font)
    position = ((base_img.size[0] - text_width) // 2, base_img.size[1] - text_height - 20)

    # Add text to overlay
    draw.text(position, text, fill=text_color, font=font)

    # Merge base image with overlay
    combined = Image.alpha_composite(base_img, overlay)

    # Save to BytesIO
    output = BytesIO()
    combined.save(output, format="PNG")
    output.seek(0)
    return output
