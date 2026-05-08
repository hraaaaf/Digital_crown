from PIL import Image
import os

# Paths
input_path = r"C:\Users\lenovo\.gemini\antigravity\brain\ce958c43-643b-4129-94b4-3104cc7af605\clinic_icons_1776530552270.png"
output_dir = r"C:\Users\lenovo\Documents\Cabinet\DigitalCrown\backend\static\assets\icons"
os.makedirs(output_dir, exist_ok=True)

img = Image.open(input_path)
width, height = img.size

# Assuming icons are side-by-side or stacked. Let's do a simple split if side-by-side.
# Or just crop two squares.
# Usually generate_image puts them in a grid.
# I'll just save two copies for now or try to be smart.
# A better way is to just use the image and clip it in ReportLab.
# But let's just make two small icons.

# Simple split center
phone = img.crop((0, 0, width//2, height))
whatsapp = img.crop((width//2, 0, width, height))

# Save as small icons
phone.thumbnail((64, 64))
whatsapp.thumbnail((64, 64))

phone.save(os.path.join(output_dir, "phone.png"))
whatsapp.save(os.path.join(output_dir, "whatsapp.png"))

print("Icons created in static/assets/icons/")
