#!/usr/bin/env python
"""
Generate visualization diagrams for SimPM documentation.
Creates UML class diagrams and dependency graphs.
"""

import os
import subprocess
from pathlib import Path

def generate_uml_diagrams():
    """Generate UML class diagrams using pyreverse."""
    print("Generating UML class diagrams...")
    
    docs_dir = Path("docs/source")
    src_dir = Path("src/simpm")
    
    # Create visualizations directory
    vis_dir = docs_dir / "_visualizations"
    vis_dir.mkdir(exist_ok=True)
    
    # Generate class diagrams
    cmd = [
        "pyreverse",
        "-o", "dot",
        "-p", "SimPM",
        str(src_dir)
    ]
    
    result = subprocess.run(cmd, cwd=str(vis_dir), capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ UML diagrams generated successfully")
        # List generated files
        for file in vis_dir.glob("*.dot"):
            print(f"  Generated: {file.name}")
    else:
        print(f"✗ Error generating UML diagrams: {result.stderr}")

def create_graphviz_diagrams():
    """Create custom Graphviz diagrams for documentation."""
    print("Creating Graphviz diagrams...")
    
    docs_dir = Path("docs/source")
    vis_dir = docs_dir / "_visualizations"
    vis_dir.mkdir(exist_ok=True)
    
    # Create architecture diagram
    arch_diagram = """digraph SimPM_Architecture {
    graph [rankdir=LR, bgcolor=white];
    node [shape=box, style="filled,rounded", fillcolor=lightblue];
    
    // Core modules
    Environment [label="Environment\n(Simulation Clock)"];
    Entity [label="Entity\n(Agents/Items)"];
    Resource [label="Resource\n(Capacity Pools)"];
    Distribution [label="Distribution\n(Random Vars)"];
    
    // Process management
    Process [label="Process\n(Generator Functions)"];
    Event [label="Event\n(Event Queue)"];
    
    // Logging & Output
    Recorder [label="Recorder\n(Data Collection)"];
    Dashboard [label="Dashboard\n(Streamlit UI)"];
    Logger [label="Logger\n(Log Config)"];
    
    // Relationships
    Environment -> Entity [label="creates"];
    Environment -> Resource [label="manages"];
    Environment -> Process [label="schedules"];
    Environment -> Event [label="drives"];
    
    Entity -> Process [label="runs"];
    Entity -> Resource [label="uses"];
    Entity -> Recorder [label="records to"];
    
    Resource -> Recorder [label="records to"];
    Distribution -> Entity [label="provides durations"];
    
    Recorder -> Dashboard [label="feeds"];
    Recorder -> Logger [label="configured by"];
    
    // Styling
    Environment [fillcolor=lightcoral];
    Dashboard [fillcolor=lightgreen];
    Recorder [fillcolor=lightyellow];
}"""
    
    arch_file = vis_dir / "simpm_architecture.dot"
    arch_file.write_text(arch_diagram)
    print(f"✓ Architecture diagram created: {arch_file.name}")
    
    # Create class hierarchy diagram
    class_diagram = """digraph SimPM_ClassHierarchy {
    graph [rankdir=TB, bgcolor=white];
    node [shape=box, style="filled", fillcolor=lightblue];
    edge [arrowhead=empty];
    
    // Base classes
    SimObject [label="SimObject\n(Base Class)"];
    
    // Derived classes
    Environment [label="Environment"];
    Entity [label="Entity"];
    Resource [label="Resource"];
    
    // Resource variants
    PriorityResource [label="PriorityResource"];
    PreemptiveResource [label="PreemptiveResource"];
    GeneralResource [label="GeneralResource"];
    
    // Relationships
    SimObject -> Environment;
    SimObject -> Entity;
    SimObject -> Resource;
    
    Resource -> PriorityResource;
    Resource -> PreemptiveResource;
    Resource -> GeneralResource;
    
    // Styling
    SimObject [fillcolor=lightcoral];
    Resource [fillcolor=lightyellow];
    PriorityResource [fillcolor=lightgreen];
    PreemptiveResource [fillcolor=lightgreen];
}"""
    
    class_file = vis_dir / "simpm_classes.dot"
    class_file.write_text(class_diagram)
    print(f"✓ Class hierarchy diagram created: {class_file.name}")
    
    # Create workflow diagram
    workflow_diagram = """digraph SimPM_Workflow {
    graph [rankdir=TB, bgcolor=white];
    node [shape=box, style="filled", fillcolor=lightblue];
    
    Start [shape=ellipse, label="Start"];
    CreateEnv [label="1. Create Environment"];
    CreateResources [label="2. Create Resources"];
    CreateEntities [label="3. Create Entities"];
    DefineProcess [label="4. Define Processes"];
    RunSim [label="5. Run Simulation\n(simpm.run)"];
    ViewResults [label="6. View Results\n(Dashboard/Logs)"];
    End [shape=ellipse, label="End"];
    
    Start -> CreateEnv -> CreateResources -> CreateEntities -> DefineProcess -> RunSim -> ViewResults -> End;
    
    // Styling
    CreateEnv [fillcolor=lightcoral];
    RunSim [fillcolor=lightyellow];
    ViewResults [fillcolor=lightgreen];
}"""
    
    workflow_file = vis_dir / "simpm_workflow.dot"
    workflow_file.write_text(workflow_diagram)
    print(f"✓ Workflow diagram created: {workflow_file.name}")

if __name__ == "__main__":
    print("=" * 60)
    print("Generating SimPM Visualization Diagrams")
    print("=" * 60)
    
    generate_uml_diagrams()
    create_graphviz_diagrams()
    
    print("\n" + "=" * 60)
    print("✓ All diagrams generated successfully!")
    print("=" * 60)
