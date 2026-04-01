#!/usr/bin/env python3
"""Extract text from .docx files using only stdlib (zipfile + xml)."""
import os, zipfile, xml.etree.ElementTree as ET

NSMAP = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def docx_to_text(path):
    """Extract all paragraph text from a .docx file."""
    texts = []
    with zipfile.ZipFile(path) as z:
        # Read main document
        with z.open('word/document.xml') as f:
            tree = ET.parse(f)
        root = tree.getroot()
        for para in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            line_parts = []
            for run in para.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                if run.text:
                    line_parts.append(run.text)
            texts.append(''.join(line_parts))
    return '\n'.join(texts)

frd_dir = "/home/sujeetnew/Downloads/AXONHIS/FRD/OneDrive_2026-03-23/NEW FRD HIS"
output_dir = "/home/sujeetnew/Downloads/AXONHIS/FRD/extracted"
os.makedirs(output_dir, exist_ok=True)

for fname in sorted(os.listdir(frd_dir)):
    if not fname.endswith(".docx"):
        continue
    fpath = os.path.join(frd_dir, fname)
    out_name = fname.replace(".docx", ".txt").replace(" ", "_")
    out_path = os.path.join(output_dir, out_name)
    
    print(f"Processing: {fname}")
    try:
        text = docx_to_text(fpath)
        with open(out_path, "w") as f:
            f.write(text)
        print(f"  -> Saved ({len(text)} chars)")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nDone!")
