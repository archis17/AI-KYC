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
    """Generate a synthetic ID card image"""
    width, height = 600, 400
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Draw border
    draw.rectangle([10, 10, width-10, height-10], outline='black', width=3)
    
    # Title
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    draw.text((width//2, 30), "IDENTITY CARD", fill='black', font=font_large, anchor='mt')
    
    # Information
    y = 100
    draw.text((50, y), f"Name: {name}", fill='black', font=font_medium)
    y += 40
    draw.text((50, y), f"Date of Birth: {dob}", fill='black', font=font_medium)
    y += 40
    draw.text((50, y), f"Address: {address[:50]}", fill='black', font=font_small)
    y += 40
    draw.text((50, y), f"ID Number: {id_number}", fill='black', font=font_medium)
    
    image.save(output_path)
    print(f"Generated ID card: {output_path}")

def generate_passport(name: str, dob: str, address: str, passport_number: str, output_path: Path):
    """Generate a synthetic passport document (PDF)"""
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(100, height - 50, "PASSPORT")
    
    # Information
    y = height - 150
    c.setFont("Helvetica", 14)
    c.drawString(100, y, f"Name: {name}")
    y -= 30
    c.drawString(100, y, f"Date of Birth: {dob}")
    y -= 30
    c.drawString(100, y, f"Address: {address}")
    y -= 30
    c.drawString(100, y, f"Passport Number: {passport_number}")
    y -= 30
    c.drawString(100, y, f"Nationality: {fake.country()}")
    y -= 30
    c.drawString(100, y, f"Place of Birth: {fake.city()}")
    
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

def generate_synthetic_documents(count: int = 5):
    """Generate multiple sets of synthetic KYC documents"""
    print(f"Generating {count} sets of synthetic KYC documents...")
    
    for i in range(1, count + 1):
        # Generate consistent fake data for each person
        name = fake.name()
        dob = fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%Y-%m-%d')
        address = fake.address().replace('\n', ', ')
        id_number = fake.ssn().replace('-', '')
        passport_number = fake.bothify(text='??#######').upper()
        account_number = fake.credit_card_number()
        
        # Create directory for this person
        person_dir = OUTPUT_DIR / f"person_{i}"
        person_dir.mkdir(exist_ok=True)
        
        # Generate documents
        generate_id_card(
            name, dob, address, id_number,
            person_dir / f"id_card_{i}.png"
        )
        
        generate_passport(
            name, dob, address, passport_number,
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
        
        # Create a metadata file
        with open(person_dir / "metadata.txt", "w") as f:
            f.write(f"Name: {name}\n")
            f.write(f"DOB: {dob}\n")
            f.write(f"Address: {address}\n")
            f.write(f"ID Number: {id_number}\n")
            f.write(f"Passport Number: {passport_number}\n")
            f.write(f"Account Number: {account_number}\n")
        
        print(f"Generated document set {i}/{count}")
    
    print(f"\nAll synthetic documents generated in: {OUTPUT_DIR}")

if __name__ == "__main__":
    import sys
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    generate_synthetic_documents(count)

