import database as db
import datetime

print("Testing save_field_visit...")
try:
    db.save_field_visit(
        customer_name="تجربة عميل",
        phone="0911234567",
        address="طرابلس",
        furniture_type="مطبخ",
        site_status="تحت التشطيب",
        visit_date="2026-06-30",
        visit_time="10:00",
        visit_value=50.0,
        payment_status="لم يتم بعد",
        measurement_completed="نعم",
        measurement_reason="",
        document_revision_completed="",
        document_revision_reason="",
        media_paths="",
        design_value=150.0,
        map_link="https://maps.google.com",
        site_status_note="يحتاج لتنظيف"
    )
    print("Success! Record saved.")
except Exception as e:
    print(f"Error: {e}")
