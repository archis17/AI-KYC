#!/usr/bin/env python3
"""
Synthetic KYC Document Generator
Generates fake KYC documents for testing and demonstration purposes.
"""

from faker import Faker
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from PIL import Image, ImageDraw, ImageFont
import os
import random
from pathlib import Path

fake = Faker()
Faker.seed(0)  # For reproducible results

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "synthetic"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_id_card(name: str, dob: str, address: str, id_number: str, output_path: Path):
    """Generate a synthetic ID card image with OCR-friendly text"""
    width, height = 800, 500  # Larger size for better OCR
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Draw border
    draw.rectangle([10, 10, width-10, height-10], outline='black', width=3)
    
    # Title - use larger, clearer fonts
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        # Fallback to default fonts
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Title
    draw.text((width//2, 40), "IDENTITY CARD", fill='black', font=font_large, anchor='mt')
    
    # Information - use clear labels and values
    y = 120
    draw.text((60, y), "Name:", fill='black', font=font_medium)
    draw.text((200, y), name, fill='black', font=font_medium)
    y += 50
    
    draw.text((60, y), "Date of Birth:", fill='black', font=font_medium)
    draw.text((200, y), dob, fill='black', font=font_medium)
    y += 50
    
    draw.text((60, y), "Address:", fill='black', font=font_medium)
    # Split long addresses across multiple lines
    address_lines = [address[i:i+60] for i in range(0, len(address), 60)]
    for line in address_lines[:2]:  # Max 2 lines
        draw.text((200, y), line, fill='black', font=font_small)
        y += 35
    
    y += 20
    draw.text((60, y), "ID Number:", fill='black', font=font_medium)
    draw.text((200, y), id_number, fill='black', font=font_medium)
    
    image.save(output_path, dpi=(300, 300))  # Higher DPI for better OCR
    print(f"Generated ID card: {output_path}")

def generate_passport(name: str, dob: str, address: str, passport_number: str, output_path: Path):
    """Generate a synthetic passport document (PDF) with clear formatting"""
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 22)
    c.drawString(100, height - 50, "PASSPORT")
    
    # Information - use clear labels
    y = height - 150
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "Name:")
    c.setFont("Helvetica", 14)
    c.drawString(200, y, name)
    y -= 35
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "Date of Birth:")
    c.setFont("Helvetica", 14)
    c.drawString(200, y, dob)
    y -= 35
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "Address:")
    c.setFont("Helvetica", 12)
    # Handle long addresses
    address_parts = address.split(', ')
    for part in address_parts[:3]:  # Max 3 parts
        c.drawString(200, y, part)
        y -= 25
    
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "Passport Number:")
    c.setFont("Helvetica", 14)
    c.drawString(200, y, passport_number)
    y -= 35
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "Nationality:")
    c.setFont("Helvetica", 14)
    c.drawString(200, y, fake.country())
    y -= 35
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "Place of Birth:")
    c.setFont("Helvetica", 14)
    c.drawString(200, y, fake.city())
    
    c.save()
    print(f"Generated passport: {output_path}")

def generate_proof_of_address(name: str, address: str, output_path: Path):
    """Generate a synthetic proof of address document (PDF)"""
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 50, "PROOF OF ADDRESS")
    
    # Information
    y = height - 120
    c.setFont("Helvetica", 12)
    c.drawString(100, y, "This document certifies that:")
    y -= 30
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, y, name)
    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(100, y, "resides at:")
    y -= 30
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, y, address)
    y -= 50
    c.setFont("Helvetica", 10)
    c.drawString(100, y, f"Issued on: {fake.date_between(start_date='-1y', end_date='today').strftime('%Y-%m-%d')}")
    c.drawString(100, y - 20, f"Issued by: {fake.company()} Utility Services")
    
    c.save()
    print(f"Generated proof of address: {output_path}")

def generate_bank_statement(name: str, account_number: str, output_path: Path):
    """Generate a synthetic bank statement (PDF)"""
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 50, f"{fake.company()} BANK")
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 70, "BANK STATEMENT")
    
    # Account Information
    y = height - 120
    c.setFont("Helvetica", 12)
    c.drawString(100, y, f"Account Holder: {name}")
    y -= 20
    c.drawString(100, y, f"Account Number: {account_number}")
    y -= 20
    c.drawString(100, y, f"Statement Period: {fake.date_between(start_date='-3m', end_date='today').strftime('%B %Y')}")
    
    # Transactions
    y -= 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "Recent Transactions")
    y -= 25
    
    c.setFont("Helvetica", 10)
    balance = 5000.00
    for i in range(5):
        amount = round(random.uniform(-500, 1000), 2)
        balance += amount
        date = fake.date_between(start_date='-30d', end_date='today').strftime('%Y-%m-%d')
        desc = fake.text(max_nb_chars=30)
        c.drawString(100, y, f"{date} | {desc[:25]:<25} | ${amount:>10.2f} | Balance: ${balance:.2f}")
        y -= 20
    
    c.save()
    print(f"Generated bank statement: {output_path}")

def generate_synthetic_documents(count: int = 5, correct: bool = True):
    """
    Generate multiple sets of synthetic KYC documents
    
    Args:
        count: Number of person document sets to generate
        correct: If True, generates consistent data across all documents (for passing validation)
                 If False, generates inconsistent data (for testing failure cases)
    """
    print(f"Generating {count} sets of synthetic KYC documents (correct={correct})...")
    
    for i in range(1, count + 1):
        # Generate consistent fake data for each person
        # Use fixed seed per person to ensure consistency
        person_seed = i if correct else i + 1000
        Faker.seed(person_seed)
        
        name = fake.name()
        dob = fake.date_of_birth(minimum_age=18, maximum_age=80)
        # Use consistent date format: YYYY-MM-DD
        dob_str = dob.strftime('%Y-%m-%d')
        dob_alt = dob_str  # Default to same DOB
        
        # Generate address and normalize it
        full_address = fake.address()
        # Normalize address: remove newlines, standardize format
        address = full_address.replace('\n', ', ').strip()
        
        id_number = fake.ssn().replace('-', '')
        passport_number = fake.bothify(text='??#######').upper()
        account_number = fake.credit_card_number()
        
        # For incorrect data, introduce mismatches
        if not correct:
            if i % 2 == 0:
                # Name mismatch on even numbers
                name = fake.name()  # Different name
            if i % 3 == 0:
                # DOB mismatch on multiples of 3
                dob_alt = fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%Y-%m-%d')
            if i % 3 == 0:
                # Address variation on multiples of 3
                address = address.replace('Street', 'St')  # Minor variation
        
        # Create directory for this person
        person_dir = OUTPUT_DIR / f"person_{i}"
        person_dir.mkdir(exist_ok=True)
        
        # Generate documents with consistent data
        generate_id_card(
            name, dob_str, address, id_number,
            person_dir / f"id_card_{i}.png"
        )
        
        # Use dob_alt for passport if generating incorrect data
        passport_dob = dob_alt if not correct and i % 3 == 0 else dob_str
        generate_passport(
            name, passport_dob, address, passport_number,
            person_dir / f"passport_{i}.pdf"
        )
        
        generate_proof_of_address(
            name, address,
            person_dir / f"proof_of_address_{i}.pdf"
        )
        
        generate_bank_statement(
            name, account_number,
            person_dir / f"bank_statement_{i}.pdf"
        )
        
        # Create a metadata file with all the data
        with open(person_dir / "metadata.txt", "w") as f:
            f.write(f"Name: {name}\n")
            f.write(f"DOB: {dob_str}\n")
            f.write(f"Address: {address}\n")
            f.write(f"ID Number: {id_number}\n")
            f.write(f"Passport Number: {passport_number}\n")
            f.write(f"Account Number: {account_number}\n")
            f.write(f"Correct Data: {correct}\n")
            if not correct:
                f.write(f"Note: This set contains intentional mismatches for testing\n")
        
        print(f"Generated document set {i}/{count}")
    
    print(f"\nAll synthetic documents generated in: {OUTPUT_DIR}")

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic KYC documents')
    parser.add_argument('count', type=int, nargs='?', default=5, help='Number of document sets to generate')
    parser.add_argument('--correct', action='store_true', default=True, help='Generate correct/consistent data (default)')
    parser.add_argument('--incorrect', action='store_false', dest='correct', help='Generate incorrect data with mismatches for testing')
    
    args = parser.parse_args()
    generate_synthetic_documents(args.count, correct=args.correct)

