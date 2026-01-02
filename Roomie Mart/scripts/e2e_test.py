import requests
import time
import base64
import os

BASE = 'http://127.0.0.1:5000'

session = requests.Session()

timestamp = int(time.time())
email = f'e2e_{timestamp}@example.com'
password = 'TestPass123'

print('Using test email:', email)

# 1) Register
reg_data = {
    'name': 'E2E Test',
    'email': email,
    'password': password,
    'confirm_password': password,
    'phone': '9999999999',
    'hostel': 'E2EHostel',
    'block': 'E',
    'room': '101'
}
print('\nRegistering...')
resp = session.post(BASE + '/register', data=reg_data)
print('Register status:', resp.status_code)

# 2) Login
print('\nLogging in...')
login_data = {
    'email': email,
    'password': password
}
resp = session.post(BASE + '/login', data=login_data)
print('Login status:', resp.status_code)
print('Login response text (truncated):')
print(resp.text[:1000])

# 3) Check whoami
print('\nWhoami:')
resp = session.get(BASE + '/_whoami')
print(resp.status_code, resp.text)

# 4) prepare tiny png image
img_dir = os.path.join(os.path.dirname(__file__), 'tmp')
os.makedirs(img_dir, exist_ok=True)
img_path = os.path.join(img_dir, 'e2e_image.png')
png_b64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII='
with open(img_path, 'wb') as f:
    f.write(base64.b64decode(png_b64))

# 5) Add item with image
print('\nAdding item...')
with open(img_path, 'rb') as imgf:
    files = {'image': ('e2e_image.png', imgf, 'image/png')}
    data = {
        'title': f'E2E Item {timestamp}',
        'category': 'Other',
        'price': '10',
        'condition': 'Good',
        'description': 'Created by e2e test',
        'hostel': 'E2EHostel',
        'block': 'E'
    }
    resp = session.post(BASE + '/add_item', data=data, files=files)
    print('Add item status:', resp.status_code)

# 6) Fetch my items
print('\nFetching /_my_items...')
resp = session.get(BASE + '/_my_items')
print('Status:', resp.status_code)
try:
    print(resp.json())
except Exception:
    print(resp.text)

print('\nE2E done')
