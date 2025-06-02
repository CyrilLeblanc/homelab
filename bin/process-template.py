#!/usr/bin/env python3

# read all files in ./stacks/*/template.json
# add all the objects of theses files to "templates" array
# create a templates.json file in the current directory

import os
import json
import sys

def main():
    # Determine the path to the 'stacks' directory (one level up from this script)
    stacks_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stacks')
    templates = []
    # Iterate over each subdirectory in 'stacks'
    for stack_name in os.listdir(stacks_dir):
        stack_path = os.path.join(stacks_dir, stack_name)
        # Skip if not a directory
        if not os.path.isdir(stack_path):
            continue
        # Look for a template.json file in the subdirectory
        template_file = os.path.join(stack_path, 'template.json')
        if os.path.isfile(template_file):
            with open(template_file, 'r') as f:
                try:
                    # Load the JSON data and add to the templates list
                    data = json.load(f)
                    data['type'] = 3
                    data['repository'] = {
                        'url': 'https://github.com/CyrilLeblanc/homelab',
                        'stackfile': f'stacks/{stack_name}/docker-compose.yaml'
                    }
                    data['platform'] = 'linux'
                    data['logo'] = f'https://github.com/CyrilLeblanc/homelab/blob/main/stacks/{stack_name}/logo.png?raw=true'

                    templates.append(data)
                except Exception as e:
                    # Warn if the file could not be parsed
                    print(f"Warning: Could not parse {template_file}: {e}", file=sys.stderr)

    # Write the collected templates to templates.json in the current directory
    output_path = os.path.join(os.getcwd(), 'templates.json')
    with open(output_path, 'w') as out:
        json.dump({"version": "2", "templates": templates}, out, indent=2)
    print(f"Wrote {len(templates)} templates to {output_path}")

if __name__ == "__main__":
    main()

