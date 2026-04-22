import os

def run(**input):
    path = input['path']
    # Resolve relative to the entity directory
    base = os.path.join(os.path.dirname(__file__), '..', '..', '..')
    full_path = os.path.normpath(os.path.join(base, 'entity', path))
    # Safety: ensure we stay inside entity/
    entity_root = os.path.normpath(os.path.join(base, 'entity'))
    if not full_path.startswith(entity_root):
        return "Error: path escapes entity directory"
    if not os.path.exists(full_path):
        return f"Error: file not found: {full_path}"
    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()
