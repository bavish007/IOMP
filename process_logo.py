from PIL import Image

def process_glow(in_path, out_path):
    img = Image.open(in_path).convert('RGBA')
    width, height = img.size
    
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            
            brightness = max(r, g, b)
            
            alpha = min(255, int(brightness * 1.7))
            
            if brightness < 5:
                alpha = 0 
            
            pixels[x, y] = (r, g, b, alpha)

    img.save(out_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print("Successfully generated fully transparent glowing ICO.")

process_glow(r'D:\IOMP-main\logo.png', r'D:\IOMP-main\IOMP-main\jarvis.ico')
