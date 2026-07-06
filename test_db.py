"""Quick test to verify database and modules work correctly."""
import database as db

db.init_db()

print("=== Testing FieldVisits ===")
visits = db.get_all_field_visits()
print(f"Found {len(visits)} visits")
if visits:
    print(f"Columns per visit row: {len(visits[0])}")
    print(f"First visit: {visits[0]}")

print("\n=== Testing Contracts ===")
contracts = db.get_all_contracts()
print(f"Found {len(contracts)} contracts")
if contracts:
    print(f"Columns per contract row: {len(contracts[0])}")
    print(f"First contract: {contracts[0]}")

print("\n=== Testing mod_contracts import ===")
from modules import mod_contracts
print("mod_contracts imported successfully")
print(f"render_page function exists: {hasattr(mod_contracts, 'render_page')}")

print("\n=== Testing mod_production import ===")
from modules import mod_production
print("mod_production imported successfully")
print(f"render_page function exists: {hasattr(mod_production, 'render_page')}")

print("\n=== Testing mod_design import ===")
from modules import mod_design
print("mod_design imported successfully")

print("\n=== Testing mod_visits import ===")
from modules import mod_visits
print("mod_visits imported successfully")

print("\n=== Testing mod_journey import ===")
from modules import mod_journey
print("mod_journey imported successfully")

print("\n=== Testing mod_statistics import ===")
from modules import mod_statistics
print("mod_statistics imported successfully")

print("\n=== All tests passed! ===")
