#!/usr/bin/env python
"""
Generate PNG/SVG images from DOT files for documentation.
This allows diagrams to display properly on Read the Docs.
"""

import graphviz
from pathlib import Path

def render_diagrams():
    """Convert DOT files to PNG images."""
    
    vis_dir = Path("docs/source/_visualizations")
    
    diagrams = {
        "simpm_architecture": "SimPM Architecture",
        "simpm_classes": "SimPM Class Hierarchy",
        "simpm_workflow": "SimPM Workflow",
    }
    
    print("=" * 60)
    print("Rendering Graphviz diagrams to PNG...")
    print("=" * 60)
    
    for dot_file, title in diagrams.items():
        dot_path = vis_dir / f"{dot_file}.dot"
        
        if not dot_path.exists():
            print(f"✗ {title}: {dot_file}.dot not found")
            continue
        
        try:
            # Read the DOT file
            with open(dot_path, 'r') as f:
                dot_content = f.read()
            
            # Create a Graphviz source object
            src = graphviz.Source(dot_content)
            
            # Render to PNG
            output_path = vis_dir / dot_file
            src.render(str(output_path), format='png', cleanup=True, quiet=True)
            
            # Also render to SVG for better quality
            src.render(str(output_path), format='svg', cleanup=True, quiet=True)
            
            print(f"✓ {title}: rendered successfully")
            print(f"  PNG: {dot_file}.png")
            print(f"  SVG: {dot_file}.svg")
            
        except Exception as e:
            print(f"✗ {title}: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Diagram rendering complete!")
    print("=" * 60)

if __name__ == "__main__":
    render_diagrams()
