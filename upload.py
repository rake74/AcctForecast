#!/usr/bin/env python3

import os
import sys
import json
import argparse
import traceback
from datetime import datetime, timezone
from neocities import Neocities, AuthenticationError, OpFailedError

# The local source file is fixed.
SOURCE_FILE = 'accountforecast.html'
API_KEY_FILE = 'apikey'

def main():
    """
    Main function to parse arguments and upload the file to Neocities.
    """
    parser = argparse.ArgumentParser(
        description=f"Uploads '{SOURCE_FILE}' to a specified Neocities site with a timestamp."
    )
    parser.add_argument('sitename', help="Your Neocities site name (e.g., 'rake74').")
    parser.add_argument('-d', '--destination', default='index.html', help="The filename to use on the server.")
    args = parser.parse_args()

    # 1. Check for the source file
    if not os.path.exists(SOURCE_FILE):
        print(f"Error: Source file '{SOURCE_FILE}' not found.")
        return

    # 2. Load the API Key
    api_key = os.getenv('NEOCITIES_API_KEY')
    key_source = "environment variable"
    if not api_key:
        if os.path.exists(API_KEY_FILE):
            key_source = f"local '{API_KEY_FILE}' file"
            try:
                with open(API_KEY_FILE, 'r') as f:
                    api_key = f.read().strip()
            except Exception as e:
                print(f"Error: Could not read '{API_KEY_FILE}': {e}")
                return
    if not api_key:
        print("Error: API key not found.")
        return

    print(f"Successfully loaded API key from {key_source}.")

    # 3. Read the file content and inject the timestamp
    try:
        print(f"Reading content from '{SOURCE_FILE}'...")
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            file_content = f.read()

        # Get current time in UTC
        now_utc = datetime.now(timezone.utc)
        # Format as ISO 8601 with whole seconds and 'Z' for UTC
        timestamp_str = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

        # Create the HTML snippet
        timestamp_html = f"<pre>Updated: {timestamp_str}</pre>\n</body>"

        # Inject the snippet before the closing body tag
        if '</body>' in file_content:
            print(f"Injecting timestamp: {timestamp_str}")
            file_content = file_content.replace('</body>', timestamp_html)
        else:
            print("Warning: Closing </body> tag not found. Appending timestamp to end of file.")
            file_content += f"\n<pre>Updated: {timestamp_str}</pre>"

        client = Neocities()
        client.login(api=api_key)

        print(f"Uploading content to '{args.sitename}' as '{args.destination}'...")

        client.upload_text({args.destination: file_content})

        print("Upload successful!")
        print(f"View live at: https://{args.sitename}.neocities.org/{args.destination}")

    except OpFailedError as e:
        if "failed to store files" in str(e):
            print("File exists. Attempting to replace it...")
            try:
                # The file content with timestamp is already in memory
                client.delete(args.destination)
                client.upload_text({args.destination: file_content})
                print("Replacement successful!")
                print(f"View live at: https://{args.sitename}.neocities.org/{args.destination}")
            except Exception as replace_e:
                print("\n--- FAILED TO REPLACE FILE ---")
                print(f"Error: {replace_e}")
                traceback.print_exc(file=sys.stdout)
        else:
            print("\n--- OPERATION FAILED ---")
            print(f"Server message: {e}")
            traceback.print_exc(file=sys.stdout)

    except AuthenticationError as e:
        print("\n--- AUTHENTICATION FAILED ---")
        print(f"Server message: {e}")

    except Exception as e:
        print(f"\n--- A CRITICAL ERROR OCCURRED ---")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        traceback.print_exc(file=sys.stdout)

if __name__ == "__main__":
    main()
