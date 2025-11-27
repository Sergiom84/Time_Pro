#!/usr/bin/env python3
"""
Script to update client logos in the database from Supabase Storage URLs.

This script updates the logo_url field for each client with their corresponding
logo files stored in Supabase Storage (public Logos bucket).

Usage:
    python3 update_logos.py [client_id] [logo_url]

    Examples:
    # Update Time Pro logo
    python3 update_logos.py 1 "https://gqesfclbingbihakiojm.supabase.co/storage/v1/object/public/Logos/Time_Pro.JPG"

    # Update PruebaCo logo
    python3 update_logos.py 2 "https://gqesfclbingbihakiojm.supabase.co/storage/v1/object/public/Logos/PruebaCo.JPG"

    # Update all at once
    python3 update_logos.py --all
"""

import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

def update_single_logo(client_id: int, logo_url: str):
    """Update a single client's logo URL"""
    try:
        # Import after path is set
        from main import app
        from models.models import Client
        from models.database import db

        with app.app_context():
            client = Client.query.get(client_id)

            if not client:
                print(f"❌ Client with ID {client_id} not found")
                return False

            print(f"Updating {client.name} (ID: {client_id})")
            print(f"  Old URL: {client.logo_url}")
            print(f"  New URL: {logo_url}")

            client.logo_url = logo_url
            db.session.commit()

            print(f"✅ Successfully updated {client.name} logo")
            return True

    except Exception as e:
        print(f"❌ Error updating logo: {e}")
        return False

def update_all_logos():
    """Update all client logos interactively"""
    try:
        from main import app
        from models.models import Client
        from models.database import db

        with app.app_context():
            # Define default logo URLs
            logos = {
                1: {
                    "name": "Time Pro",
                    "prompt": "Enter Time Pro logo URL (or press Enter to skip): ",
                    "url": None
                },
                2: {
                    "name": "PruebaCo",
                    "prompt": "Enter PruebaCo logo URL (or press Enter to skip): ",
                    "url": None
                },
                4: {
                    "name": "Cliente de ejemplo 4",
                    "prompt": "Enter example client 4 logo URL (or press Enter to skip): ",
                    "url": ""
                }
            }

            print("\n=== UPDATE CLIENT LOGOS ===\n")

            # Get URLs from user
            for client_id, info in logos.items():
                print(f"\n{info['name']} (ID: {client_id})")

                # For example client 4, show the existing URL (if any)
                if client_id == 4:
                    print(f"  Current URL: {info['url']}")
                    change = input("  Do you want to change it? (y/n): ").strip().lower()
                    if change == 'y':
                        info['url'] = input(info['prompt']).strip()
                else:
                    url_input = input(info['prompt']).strip()
                    if url_input:
                        info['url'] = url_input

            # Apply updates
            print("\n=== APPLYING UPDATES ===\n")
            success_count = 0

            for client_id, info in logos.items():
                if info['url']:
                    client = Client.query.get(client_id)
                    if client:
                        print(f"Updating {info['name']}...")
                        client.logo_url = info['url']
                        success_count += 1
                    else:
                        print(f"❌ Client {client_id} not found")

            if success_count > 0:
                db.session.commit()
                print(f"\n✅ Updated {success_count} client(s) successfully!")
            else:
                print("\n⚠️  No logos were updated")

            # Show current state
            print("\n=== CURRENT LOGOS ===\n")
            clients = Client.query.filter(Client.id.in_([1, 2, 4])).order_by(Client.id).all()
            for client in clients:
                print(f"{client.id}. {client.name:20} | URL: {client.logo_url or '(not set)'}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    if len(sys.argv) == 1:
        # No arguments - interactive mode
        update_all_logos()
    elif len(sys.argv) == 2 and sys.argv[1] == "--all":
        # Show all logos
        update_all_logos()
    elif len(sys.argv) == 3:
        # Direct update: python3 update_logos.py <client_id> <url>
        try:
            client_id = int(sys.argv[1])
            logo_url = sys.argv[2]

            success = update_single_logo(client_id, logo_url)
            sys.exit(0 if success else 1)
        except ValueError:
            print("❌ Invalid client_id. Must be an integer.")
            sys.exit(1)
    else:
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
