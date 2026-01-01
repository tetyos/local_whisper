"""Script to create a simple icon for the application."""

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("PIL not installed. Run: pip install Pillow")
    print("Then run this script again to generate the icon.")
    exit(1)


def create_icon():
    """Create a simple microphone icon."""
    # Create a 256x256 image with transparency
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background circle
    margin = 20
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill='#00d4aa'
    )
    
    # Microphone body (dark)
    mic_width = 60
    mic_height = 100
    mic_x = (size - mic_width) // 2
    mic_y = size // 2 - mic_height // 2 - 15
    draw.rounded_rectangle(
        [mic_x, mic_y, mic_x + mic_width, mic_y + mic_height],
        radius=30,
        fill='#1a1a2e'
    )
    
    # Microphone stand
    stand_width = 15
    stand_x = (size - stand_width) // 2
    stand_y = mic_y + mic_height
    draw.rectangle(
        [stand_x, stand_y, stand_x + stand_width, stand_y + 30],
        fill='#1a1a2e'
    )
    
    # Base
    base_width = 80
    base_height = 15
    base_x = (size - base_width) // 2
    base_y = stand_y + 30
    draw.rounded_rectangle(
        [base_x, base_y, base_x + base_width, base_y + base_height],
        radius=5,
        fill='#1a1a2e'
    )
    
    # Save as ICO with multiple sizes
    img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    print("Icon created: assets/icon.ico")


if __name__ == "__main__":
    create_icon()

