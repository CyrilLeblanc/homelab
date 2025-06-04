#!/usr/bin/env python3

# read all files in ./stacks/*/template.json
# add all the objects of theses files to "templates" array
# create a templates.json file in the current directory

import os
import json
import sys

def get_stacks_dir():
    """Return the absolute path to the 'stacks' directory."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stacks')

def load_template(stack_path, stack_name, stack_id):
    """Load and process a template.json from a stack directory, adding extra fields."""
    template_file = os.path.join(stack_path, 'template.json')
    if not os.path.isfile(template_file):
        return None
    try:
        with open(template_file, 'r') as f:
            data = json.load(f)
            data['id'] = int(stack_id)
            data['name'] = stack_name
            data['type'] = 3
            data['platform'] = 'linux'
            data['repository'] = {
                'url': 'https://github.com/CyrilLeblanc/homelab',
                'stackfile': f'stacks/{stack_name}/docker-compose.yaml'
            }
            # check if logo.png is readable
            logo_path = os.path.join(stack_path, 'logo.png')
            if os.path.isfile(logo_path):
                data['logo'] = f'https://raw.githubusercontent.com/CyrilLeblanc/homelab/refs/heads/main/stacks/{stack_name}/logo.png'
            # check for a note.html
            note_path = os.path.join(stack_path, 'note.html')
            if os.path.isfile(note_path):
                with open(note_path, 'r') as note_file:
                    data['note'] = note_file.read()
            return data
    except Exception as e:
        print(f"Warning: Could not parse {template_file}: {e}", file=sys.stderr)
        return None

def collect_templates(stacks_dir):
    """Iterate over stack directories and collect all templates."""
    templates = []
    id = 1
    for stack_dir in os.listdir(stacks_dir):
        stack_path = os.path.join(stacks_dir, stack_dir)
        if not os.path.isdir(stack_path):
            continue
        template = load_template(stack_path, stack_dir, id)
        if template:
            templates.append(template)
            id += 1
    templates.sort(key=lambda x: x['id'])
    return templates

def write_templates_json(templates, output_path):
    """Write the templates list to a templates.json file."""
    with open(output_path, 'w') as out:
        json.dump({"version": "3", "templates": templates}, out, indent=2)
    print(f"Wrote {len(templates)} templates to {output_path}")

def main():
    stacks_dir = get_stacks_dir()
    templates = collect_templates(stacks_dir)
    output_path = os.path.join(os.getcwd(), 'templates.json')
    write_templates_json(templates, output_path)

if __name__ == "__main__":
    main()

