import os

def check_and_fix():
    path = 'README.md'
    with open(path, 'rb') as f:
        data = f.read()
    
    # Print analysis
    print(f"Total bytes: {len(data)}")
    counts = {
        'CR (\\r)': data.count(b'\r'),
        'LF (\\n)': data.count(b'\n'),
        'CRLF (\\r\\n)': data.count(b'\r\n'),
        'NUL (\\x00)': data.count(b'\x00'),
    }
    for k, v in counts.items():
        print(f"{k}: {v}")

    # Fix: remove NULs and convert isolated CR or LF to CRLF or LF
    if b'\x00' in data:
        data = data.replace(b'\x00', b'')
        print("Removed NUL bytes.")
    
    # Normalize line endings to standard LF
    # First, replace CRLF with LF
    data = data.replace(b'\r\n', b'\n')
    # Then replace any remaining isolated CR with LF
    data = data.replace(b'\r', b'\n')
    
    with open(path, 'wb') as f:
        f.write(data)
    print("Fixed line endings and saved to", path)

if __name__ == '__main__':
    check_and_fix()

