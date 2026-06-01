#!/usr/bin/env python3
import os
import random
import subprocess
import xml.etree.ElementTree as ET

# Configuration
CHANCE_TO_RUN = 0.30     # 30% chance to execute
MAX_BROKEN = 3           # Max allowed failing files at one time
REPORT_PATH = "../build/reports/checkstyle/main.xml"

def run_git(args):
    """Executes a single git command."""
    try:
        subprocess.run(["git"] + args, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Git error running {args}: {e.stderr}")

def get_all_java_files():
    """Finds all Java files in the repo, excluding target/build folders."""
    java_files = []
    for root, dirs, files in os.walk("../src/main/java"):
        if any(p in root for p in ["target", "build", ".git"]):
            continue
        for file in files:
            if file.endswith(".java"):
                java_files.append(os.path.abspath(os.path.join(root, file)))
    return java_files

def get_broken_files_from_xml():
    """Parses Checkstyle XML to find files with actual errors."""
    if not os.path.exists(REPORT_PATH):
        print(f"Error: Checkstyle report not found at {REPORT_PATH}")
        return None
        
    broken = set()
    try:
        tree = ET.parse(REPORT_PATH)
        root = tree.getroot()
        for file_node in root.findall("file"):
            if file_node.findall("error"):
                broken.add(os.path.abspath(file_node.get("name")))
    except ET.ParseError:
        print("Error: Could not parse Checkstyle XML.")
        return None
    return list(broken)

def main():
    # 1. Roll the dice (30% chance)
    if random.random() > CHANCE_TO_RUN:
        print("Skipping: Dice roll determined no action this turn.")
        return

    # 2. Gather file states
    all_files = get_all_java_files()
    broken_files = get_broken_files_from_xml()
    
    if broken_files is None or not all_files:
        return

    # Filter out files that are broken to find the clean ones
    clean_files = [f for f in all_files if f not in broken_files]
    
    print(f"Status: {len(broken_files)} failing, {len(clean_files)} passing.")

    # 3. Decision Logic (Strictly picks ONE action for ONE file)
    if len(broken_files) >= MAX_BROKEN:
        action = "FIX"
    elif len(broken_files) == 0:
        action = "BREAK"
    else:
        action = random.choice(["FIX", "BREAK"])

    # 4. Execute the single action
    if action == "FIX" and broken_files:
        # Pick EXACTLY ONE random broken file to fix
        target = random.choice(broken_files)
        
        with open(target, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # Verify line 1 has our simulated trailing space to avoid touching real developer errors
        if lines and lines[0].endswith(" \n"):
            lines[0] = lines[0].rstrip(" \n") + "\n"
            with open(target, "w", encoding="utf-8") as f:
                f.writelines(lines)
                
            run_git(["add", target])
            run_git(["commit", "-m", f"chore: fix checkstyle simulation in {os.path.basename(target)}"])
            print(f"Action: FIXED 1 file -> {os.path.basename(target)}")
        else:
            print(f"Skipping fix: {os.path.basename(target)} has a legitimate developer error.")

    elif action == "BREAK" and clean_files:
        # Pick EXACTLY ONE random clean file to break
        target = random.choice(clean_files)
        
        with open(target, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        if lines:
            lines[0] = lines[0].rstrip("\n") + " \n"
            with open(target, "w", encoding="utf-8") as f:
                f.writelines(lines)
                
            run_git(["add", target])
            run_git(["commit", "-m", f"chore: inject checkstyle simulation into {os.path.basename(target)}"])
            print(f"Action: BROKE 1 file -> {os.path.basename(target)}")
    else:
        print("No action taken.")

if __name__ == "__main__":
    main()
