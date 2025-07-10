import json
import os
from pathlib import Path

def process_jobs():
    # Configuration - adjust these paths as needed
    input_dir = Path('admin_jobs')
    input_file = input_dir / 'processed.json'
    output_dir = Path('processed_data')
    output_file = output_dir / 'processed_jobs.json'

    # Ensure directories exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load the input JSON data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
    except Exception as e:
        print(f"Error loading input file: {e}")
        return False

    processed_jobs = []
    unprocessed_jobs = []

    for job in jobs:
        try:
            # Get the source folder path (relative to input directory)
            source_folder = job.get('source_folder', '')
            if not source_folder:
                print(f"Skipping job - no source_folder specified")
                unprocessed_jobs.append(job)
                continue

            # Build the full path to the contact file
            contact_file_path = input_dir / source_folder / 'application_method.txt'
            
            # Read contact information
            contact_info = ""
            if contact_file_path.exists():
                with open(contact_file_path, 'r', encoding='utf-8') as f:
                    contact_info = f.read().strip()
                print(f"Loaded contact info from {contact_file_path}: {contact_info}")
            else:
                print(f"Contact file not found at {contact_file_path}")

            # Create the processed job object
            processed_job = {
                'title': job.get('title', ''),
                'category': job.get('category', ''),
                'requirements': job.get('requirements', ''),
                'description': job.get('description', ''),
                'salary': job.get('salary', ''),
                'contact': contact_info
            }

            processed_jobs.append(processed_job)
            print(f"Processed job: {job.get('title')}")

        except Exception as e:
            print(f"Error processing job: {e}")
            unprocessed_jobs.append(job)

    # Save processed jobs
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_jobs, f, ensure_ascii=False, indent=4)
    print(f"\nSaved {len(processed_jobs)} processed jobs to {output_file}")

    # Update input file with unprocessed jobs
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(unprocessed_jobs, f, ensure_ascii=False, indent=4)
    print(f"Updated input file with {len(unprocessed_jobs)} remaining jobs")

    return True

if __name__ == "__main__":
    print("Starting job processing...")
    if process_jobs():
        print("Processing completed successfully!")
    else:
        print("Processing failed with errors")