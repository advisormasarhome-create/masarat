import database as db
import inspect

print("Function signature:")
print(inspect.signature(db.save_field_visit))
print("File location:")
print(inspect.getfile(db.save_field_visit))
