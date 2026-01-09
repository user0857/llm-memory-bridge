
import base64
import requests
import sys

def generate_svg():
    input_file = "architecture.mmd"
    output_file = "architecture.svg"
    bg_color = "#FFFAEE"

    # 1. Read MMD content
    try:
        with open(input_file, "r") as f:
            mmd_content = f.read()
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        sys.exit(1)

    # 2. Encode to Base64
    # mermaid.ink requires standard base64 encoding of the raw string
    mmd_b64 = base64.b64encode(mmd_content.encode("utf-8")).decode("utf-8")
    
    url = f"https://mermaid.ink/svg/{mmd_b64}"
    
    print(f"Fetching SVG from: {url[:50]}...")
    
    # 3. Download SVG
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        svg_content = resp.text
    except Exception as e:
        print(f"Error fetching SVG: {e}")
        sys.exit(1)

    # 4. Inject Background Color
    # We find the first occurrence of ">" after "<svg" and insert a rect
    # Or better, just insert it after the opening tag.
    
    # Simple heuristic: find the end of the opening <svg ...> tag
    insert_idx = svg_content.find(">")
    if insert_idx != -1:
        # Check if style already exists? No, just add a rect at the bottom layer
        # SVG renders in order, so first element is background
        rect = f'\n<rect width="100%" height="100%" fill="{bg_color}"/>'
        
        # We also need to ensure the SVG has a viewbox or width/height for this to work well
        # Usually mermaid.ink returns good SVGs.
        
        final_svg = svg_content[:insert_idx+1] + rect + svg_content[insert_idx+1:]
        
        with open(output_file, "w") as f:
            f.write(final_svg)
        print(f"Success! Saved to {output_file} with background {bg_color}")
    else:
        print("Error: Could not parse SVG structure.")
        # Save anyway just in case
        with open(output_file, "w") as f:
            f.write(svg_content)

if __name__ == "__main__":
    generate_svg()
