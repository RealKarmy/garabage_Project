from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from datetime import datetime
import uuid
from functools import wraps
import heapq
from collections import defaultdict
import os

app = Flask(__name__, static_folder='frontend', static_url_path='')
app.secret_key = 'egyptian-donation-platform-secret-key-2025'
CORS(app, supports_credentials=True, origins=["http://localhost:5000", "http://127.0.0.1:5000"])

# In-memory storage (will be replaced with database later)
users = {}
donation_requests = {}
approved_requests = {}
pending_requests = []  # Priority queue implementation
transaction_history = defaultdict(list)
request_id_counter = 1

# User types
USER_TYPES = {
    'ADMIN': 'Admin',
    'DONOR': 'Donor', 
    'RECIPIENT': 'Recipient',
    'STAFF': 'Staff'
}

# Rank system
RANKS = {
    0: 'Hope Giver',
    5: 'Lifeline Supporter', 
    10: 'Heart of Gold',
    20: 'Beacon of Light'
}

def require_auth(f):
    """Authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Admin access decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        user = users.get(session['user_id'])
        if not user or user['type'] not in ['Admin', 'Staff']:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def get_user_rank(paid_requests):
    """Calculate user rank based on paid requests"""
    for threshold in sorted(RANKS.keys(), reverse=True):
        if paid_requests >= threshold:
            return RANKS[threshold]
    return RANKS[0]

def validate_amount(amount_str):
    """Validate monetary amount"""
    try:
        amount = float(amount_str)
        if amount <= 0:
            return None, "Amount must be positive"
        return amount, None
    except (ValueError, TypeError):
        return None, "Invalid amount format"

def validate_visa_number(visa):
    """Validate Visa card number"""
    if len(visa) != 16 or not visa.isdigit():
        return False, "Visa number must be exactly 16 digits"
    return True, None

# Serve frontend
@app.route('/')
def serve_frontend():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('frontend', path)
    except:
        return send_from_directory('frontend', 'index.html')

# Authentication Routes
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Find user by username
        user = None
        user_id = None
        for uid, u in users.items():
            if u['username'].lower() == username.lower() and u['password'] == password:
                user = u
                user_id = uid
                break
        
        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Create session
        session.permanent = True
        session['user_id'] = user_id
        session['username'] = user['username']
        session['user_type'] = user['type']
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user_id,
                'username': user['username'],
                'type': user['type'],
                'rank': user.get('rank', 'Hope Giver'),
                'is_staff': user.get('is_staff', False),
                'staff_invite_pending': user.get('staff_invite_pending', False),
                'staff_invite_message': user.get('staff_invite_message', ''),
                'balance': user.get('balance', 0) if user['type'] == 'Donor' else None,
                'paid_requests': user.get('paid_requests', 0)
            }
        })
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'Server error during login'}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        user_type = data.get('type', '').strip()
        
        if not all([username, password, user_type]):
            return jsonify({'error': 'Username, password, and type are required'}), 400
        
        if user_type not in [USER_TYPES['DONOR'], USER_TYPES['RECIPIENT']]:
            return jsonify({'error': 'Invalid user type'}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
            
        if len(password) < 4:
            return jsonify({'error': 'Password must be at least 4 characters'}), 400
        
        # Check if username exists (case insensitive)
        for user in users.values():
            if user['username'].lower() == username.lower():
                return jsonify({'error': 'Username already exists'}), 409
        
        user_id = str(uuid.uuid4())
        users[user_id] = {
            'id': user_id,
            'username': username,
            'password': password,
            'type': user_type,
            'created_at': datetime.now().isoformat(),
            'paid_requests': 0,
            'rank': get_user_rank(0),
            'is_staff': False,
            'staff_invite_pending': False,
            'staff_invite_message': '',
            'balance': 0.0 if user_type == USER_TYPES['DONOR'] else None
        }
        
        return jsonify({
            'success': True,
            'message': 'Registration successful! You can now login.'
        }), 201
        
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({'error': 'Server error during registration'}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logout successful'})

@app.route('/api/auth/profile', methods=['GET'])
@require_auth
def get_profile():
    try:
        user = users.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        profile = {
            'id': user['id'],
            'username': user['username'],
            'type': user['type'],
            'rank': user['rank'],
            'paid_requests': user['paid_requests'],
            'is_staff': user.get('is_staff', False),
            'staff_invite_pending': user.get('staff_invite_pending', False),
            'staff_invite_message': user.get('staff_invite_message', ''),
            'created_at': user['created_at']
        }
        
        if user['type'] == USER_TYPES['DONOR']:
            profile['balance'] = user.get('balance', 0.0)
        
        return jsonify({'success': True, 'user': profile})
        
    except Exception as e:
        print(f"Profile error: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

# Donor Routes
@app.route('/api/donor/balance', methods=['POST'])
@require_auth
def add_balance():
    try:
        user = users.get(session['user_id'])
        if not user or user['type'] not in ['Donor', 'Staff']:
            return jsonify({'error': 'Donor access required'}), 403
        
        data = request.get_json()
        amount, error = validate_amount(data.get('amount'))
        visa_number = data.get('visa_number', '').strip()
        
        if error:
            return jsonify({'error': error}), 400
        
        if not visa_number:
            return jsonify({'error': 'Visa number required'}), 400
        
        valid_visa, visa_error = validate_visa_number(visa_number)
        if not valid_visa:
            return jsonify({'error': visa_error}), 400
        
        user['balance'] = user.get('balance', 0) + amount
        
        # Add transaction history
        transaction_history[user['id']].append({
            'type': 'deposit',
            'amount': amount,
            'description': f'Balance deposit: ${amount:.2f}',
            'timestamp': datetime.now().isoformat(),
            'visa_last_4': visa_number[-4:]
        })
        
        return jsonify({
            'success': True,
            'message': f'${amount:.2f} added successfully!',
            'new_balance': user['balance']
        })
        
    except Exception as e:
        print(f"Add balance error: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/donor/balance', methods=['GET'])
@require_auth
def get_balance():
    try:
        user = users.get(session['user_id'])
        if not user or user['type'] not in ['Donor', 'Staff']:
            return jsonify({'error': 'Donor access required'}), 403
        
        return jsonify({
            'success': True,
            'balance': user.get('balance', 0)
        })
        
    except Exception as e:
        print(f"Get balance error: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/donor/transactions', methods=['GET'])
@require_auth
def get_transaction_history():
    try:
        user = users.get(session['user_id'])
        if not user or user['type'] not in ['Donor', 'Staff']:
            return jsonify({'error': 'Donor access required'}), 403
        
        transactions = transaction_history.get(user['id'], [])
        return jsonify({
            'success': True,
            'transactions': list(reversed(transactions))
        })
        
    except Exception as e:
        print(f"Get transactions error: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/donor/donate', methods=['POST'])
@require_auth
def make_donation():
    try:
        user = users.get(session['user_id'])
        if not user or user['type'] not in ['Donor', 'Staff']:
            return jsonify({'error': 'Donor access required'}), 403
        
        data = request.get_json()
        request_id = data.get('request_id')
        is_full_payment = data.get('is_full_payment', False)
        
        if request_id not in approved_requests:
            return jsonify({'error': 'Request not found or not approved'}), 404
        
        donation_request = approved_requests[request_id]
        
        if is_full_payment:
            amount = donation_request['remaining_amount']
        else:
            amount, error = validate_amount(data.get('amount'))
            if error:
                return jsonify({'error': error}), 400
        
        if amount > user.get('balance', 0):
            return jsonify({'error': f'Insufficient balance. You have ${user.get("balance", 0):.2f}'}), 400
        
        if amount > donation_request['remaining_amount']:
            return jsonify({'error': 'Amount exceeds remaining request amount'}), 400
        
        # Process payment
        user['balance'] -= amount
        user['paid_requests'] += 1
        user['rank'] = get_user_rank(user['paid_requests'])
        
        donation_request['remaining_amount'] -= amount
        
        # Add transaction
        transaction_history[user['id']].append({
            'type': 'payment',
            'amount': amount,
            'description': f'Donation: ${amount:.2f} to {donation_request["reason"]}',
            'timestamp': datetime.now().isoformat(),
            'request_id': request_id,
            'recipient': donation_request['recipient_username']
        })
        
        # If fully paid, remove from approved requests
        fulfilled = donation_request['remaining_amount'] <= 0
        if fulfilled:
            del approved_requests[request_id]
        
        return jsonify({
            'success': True,
            'message': f'Donation of ${amount:.2f} successful!',
            'amount_donated': amount,
            'new_balance': user['balance'],
            'request_fulfilled': fulfilled,
            'remaining_amount': donation_request['remaining_amount'] if not fulfilled else 0,
            'new_rank': user['rank']
        })
        
    except Exception as e:
        print(f"Donation error: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

# Continue with other routes... (keeping them similar but adding proper error handling)
# ... (rest of the routes with similar improvements)

# Public Routes
@app.route('/api/requests/approved', methods=['GET'])
def get_public_approved_requests():
    try:
        requests_list = []
        for req in approved_requests.values():
            requests_list.append({
                'id': req['id'],
                'recipient_username': req['recipient_username'],
                'amount': req['amount'],
                'remaining_amount': req['remaining_amount'],
                'priority_level': req['priority_level'],
                'reason': req['reason'],
                'case_details': req['case_details'],
                'created_at': req['created_at'],
                'progress_percentage': ((req['amount'] - req['remaining_amount']) / req['amount']) * 100
            })
        
        # Sort by priority and creation date
        requests_list.sort(key=lambda x: (x['priority_level'], x['created_at']))
        
        return jsonify({
            'success': True,
            'requests': requests_list
        })
        
    except Exception as e:
        print(f"Get approved requests error: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/stats', methods=['GET'])
def get_platform_stats():
    try:
        total_donated = 0
        total_requests_amount = 0
        
        # Calculate total donated
        for transactions in transaction_history.values():
            for transaction in transactions:
                if transaction['type'] == 'payment':
                    total_donated += transaction['amount']
        
        # Calculate total requests amount
        for req in list(donation_requests.values()) + list(approved_requests.values()):
            total_requests_amount += req['amount']
        
        stats = {
            'total_users': len(users),
            'total_donors': len([u for u in users.values() if u['type'] in ['Donor', 'Staff']]),
            'total_recipients': len([u for u in users.values() if u['type'] == 'Recipient']),
            'pending_requests': len([req for req in donation_requests.values() if not req.get('approved', False)]),
            'approved_requests': len(approved_requests),
            'total_requests': len(donation_requests),
            'total_donated': total_donated,
            'total_requests_amount': total_requests_amount,
            'platform_efficiency': (total_donated / total_requests_amount * 100) if total_requests_amount > 0 else 0
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"Get stats error: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

# Initialize the application with better test data
def init_admin():
    admin_id = str(uuid.uuid4())
    users[admin_id] = {
        'id': admin_id,
        'username': 'admin',
        'password': '1234',
        'type': USER_TYPES['ADMIN'],
        'created_at': datetime.now().isoformat(),
        'paid_requests': 0,
        'rank': 'Administrator',
        'is_staff': True,
        'staff_invite_pending': False,
        'staff_invite_message': ''
    }

def create_realistic_test_data():
    """Create realistic test data with Egyptian context"""
    
    # Create realistic donors with Egyptian names
    realistic_donors = [
        {'username': 'ahmed_hassan', 'password': 'pass123', 'paid_requests': 32, 'balance': 75000, 'name': 'Ahmed Hassan'},
        {'username': 'fatma_ali', 'password': 'pass123', 'paid_requests': 28, 'balance': 65000, 'name': 'Fatma Ali'},
        {'username': 'mohamed_ibrahim', 'password': 'pass123', 'paid_requests': 22, 'balance': 45000, 'name': 'Mohamed Ibrahim'},
        {'username': 'sara_mahmoud', 'password': 'pass123', 'paid_requests': 18, 'balance': 35000, 'name': 'Sara Mahmoud'},
        {'username': 'omar_khaled', 'password': 'pass123', 'paid_requests': 15, 'balance': 28000, 'name': 'Omar Khaled'},
        {'username': 'nour_abdel', 'password': 'pass123', 'paid_requests': 12, 'balance': 22000, 'name': 'Nour Abdel Rahman'},
        {'username': 'youssef_said', 'password': 'pass123', 'paid_requests': 8, 'balance': 15000, 'name': 'Youssef Said'},
        {'username': 'mariam_fouad', 'password': 'pass123', 'paid_requests': 6, 'balance': 12000, 'name': 'Mariam Fouad'},
        {'username': 'kareem_nasser', 'password': 'pass123', 'paid_requests': 3, 'balance': 8000, 'name': 'Kareem Nasser'},
        {'username': 'dina_mostafa', 'password': 'pass123', 'paid_requests': 1, 'balance': 5000, 'name': 'Dina Mostafa'}
    ]
    
    for donor_data in realistic_donors:
        user_id = str(uuid.uuid4())
        users[user_id] = {
            'id': user_id,
            'username': donor_data['username'],
            'password': donor_data['password'],
            'type': USER_TYPES['DONOR'],
            'created_at': datetime.now().isoformat(),
            'paid_requests': donor_data['paid_requests'],
            'rank': get_user_rank(donor_data['paid_requests']),
            'is_staff': donor_data['paid_requests'] >= 25,  # Top donors become staff
            'staff_invite_pending': False,
            'staff_invite_message': '',
            'balance': donor_data['balance'],
            'full_name': donor_data['name']
        }
        
        # Add some transaction history for each donor
        for i in range(min(5, donor_data['paid_requests'])):
            transaction_history[user_id].append({
                'type': 'deposit',
                'amount': donor_data['balance'] / 5,
                'description': f'Balance deposit: ${donor_data["balance"] / 5:.2f}',
                'timestamp': datetime.now().isoformat(),
                'visa_last_4': '1234'
            })
    
    # Create realistic recipients with real Egyptian social causes
    realistic_recipients = [
        {'username': 'heart_surgery_child', 'password': 'help123', 'name': 'عملية قلب مفتوح لطفل'},
        {'username': 'cancer_treatment', 'password': 'help123', 'name': 'علاج مريض سرطان'},
        {'username': 'kidney_dialysis', 'password': 'help123', 'name': 'غسيل كلى لمريض مزمن'},
        {'username': 'orphan_education', 'password': 'help123', 'name': 'تعليم الأيتام'},
        {'username': 'elderly_care', 'password': 'help123', 'name': 'رعاية المسنين'},
        {'username': 'flood_victims', 'password': 'help123', 'name': 'ضحايا السيول'},
        {'username': 'clean_water', 'password': 'help123', 'name': 'مياه نظيفة للقرى'},
        {'username': 'food_bank', 'password': 'help123', 'name': 'بنك الطعام'}
    ]
    
    recipient_ids = []
    for recipient_data in realistic_recipients:
        user_id = str(uuid.uuid4())
        recipient_ids.append((user_id, recipient_data['username']))
        users[user_id] = {
            'id': user_id,
            'username': recipient_data['username'],
            'password': recipient_data['password'],
            'type': USER_TYPES['RECIPIENT'],
            'created_at': datetime.now().isoformat(),
            'paid_requests': 0,
            'rank': get_user_rank(0),
            'is_staff': False,
            'staff_invite_pending': False,
            'staff_invite_message': '',
            'full_name': recipient_data['name']
        }
    
    # Create realistic donation requests
    global request_id_counter
    realistic_requests = [
        {
            'recipient': 'heart_surgery_child',
            'amount': 150000,
            'priority': 1,
            'reason': 'عملية قلب مفتوح عاجلة لطفل 5 سنوات',
            'details': 'طفل يحتاج عملية قلب مفتوح عاجلة في مستشفى خاص. الحالة حرجة ولا يمكن التأخير.',
            'approved': True,
            'funded': 45000
        },
        {
            'recipient': 'cancer_treatment',
            'amount': 200000,
            'priority': 1,
            'reason': 'علاج السرطان والكيماوي',
            'details': 'مريض سرطان في مرحلة متقدمة يحتاج جلسات كيماوي ومتابعة طبية مكثفة.',
            'approved': True,
            'funded': 75000
        },
        {
            'recipient': 'kidney_dialysis',
            'amount': 80000,
            'priority': 2,
            'reason': 'غسيل كلى لمدة سنة كاملة',
            'details': 'مريض فشل كلوي مزمن يحتاج غسيل كلى 3 مرات أسبوعياً لمدة سنة كاملة.',
            'approved': True,
            'funded': 25000
        },
        {
            'recipient': 'orphan_education',
            'amount': 120000,
            'priority': 2,
            'reason': 'مصاريف تعليم 50 يتيم',
            'details': 'دفع مصاريف التعليم الأساسي والثانوي لـ 50 طفل يتيم في دار الأيتام.',
            'approved': True,
            'funded': 40000
        },
        {
            'recipient': 'elderly_care',
            'amount': 60000,
            'priority': 3,
            'reason': 'رعاية 20 مسن بدار المسنين',
            'details': 'توفير الرعاية الصحية والغذاء والأدوية لـ 20 مسن في دار المسنين لمدة 6 أشهر.',
            'approved': True,
            'funded': 15000
        },
        {
            'recipient': 'flood_victims',
            'amount': 300000,
            'priority': 1,
            'reason': 'مساعدة ضحايا السيول في الصعيد',
            'details': 'إعادة بناء منازل وتوفير احتياجات أساسية لـ 100 أسرة تضررت من السيول.',
            'approved': False,
            'funded': 0
        },
        {
            'recipient': 'clean_water',
            'amount': 250000,
            'priority': 2,
            'reason': 'حفر بئر مياه نظيفة',
            'details': 'حفر بئر مياه جوفية وتركيب محطة تنقية لخدمة 3 قرى في صحراء مصر.',
            'approved': False,
            'funded': 0
        },
        {
            'recipient': 'food_bank',
            'amount': 100000,
            'priority': 3,
            'reason': 'وجبات غذائية للأسر المحتاجة',
            'details': 'توفير 1000 وجبة غذائية شهرياً للأسر الأكثر احتياجاً في المناطق الشعبية.',
            'approved': False,
            'funded': 0
        }
    ]
    
    for req_data in realistic_requests:
        recipient_id = None
        for uid, username in recipient_ids:
            if username == req_data['recipient']:
                recipient_id = uid
                break
        
        if recipient_id:
            request_id = str(request_id_counter)
            request_id_counter += 1
            
            remaining_amount = req_data['amount'] - req_data['funded']
            
            new_request = {
                'id': request_id,
                'recipient_username': req_data['recipient'],
                'recipient_id': recipient_id,
                'amount': req_data['amount'],
                'remaining_amount': remaining_amount,
                'priority_level': req_data['priority'],
                'reason': req_data['reason'],
                'case_details': req_data['details'],
                'approved': req_data['approved'],
                'created_at': datetime.now().isoformat(),
                'status': 'approved' if req_data['approved'] else 'pending',
                'funded_amount': req_data['funded']
            }
            
            donation_requests[request_id] = new_request
            
            if req_data['approved']:
                approved_requests[request_id] = new_request
            else:
                heapq.heappush(pending_requests, (req_data['priority'], datetime.now().timestamp(), request_id))

if __name__ == '__main__':
    init_admin()
    create_realistic_test_data()
    
    print("=" * 60)
    print("🇪🇬 EGYPTIAN NATIONAL DONATION PLATFORM")
    print("=" * 60)
    print("🚀 Server starting...")
    print("📍 URL: http://localhost:5000")
    print("📊 Platform loaded with realistic data:")
    print(f"   👥 Users: {len(users)}")
    print(f"   🎯 Active Requests: {len(approved_requests)}")
    print(f"   ⏳ Pending Requests: {len([r for r in donation_requests.values() if not r.get('approved')])}")
    print()
    print("🔑 Demo Accounts:")
    print("   🔐 Admin: admin / 1234")
    print("   💰 Donor: ahmed_hassan / pass123")
    print("   🙏 Recipient: heart_surgery_child / help123")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)