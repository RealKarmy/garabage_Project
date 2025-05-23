# Data models for future database integration
from datetime import datetime
from enum import Enum

class UserType(Enum):
    ADMIN = "Admin"
    DONOR = "Donor"
    RECIPIENT = "Recipient"
    STAFF = "Staff"

class RequestStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    FULFILLED = "fulfilled"

class TransactionType(Enum):
    DEPOSIT = "deposit"
    PAYMENT = "payment"

# User model structure (for database schema design)
class UserModel:
    def __init__(self):
        self.id = None
        self.username = None
        self.password_hash = None  # Will be hashed in production
        self.user_type = None
        self.created_at = None
        self.paid_requests = 0
        self.rank = "Hope Giver"
        self.is_staff = False
        self.staff_invite_pending = False
        self.staff_invite_message = ""
        self.balance = 0.0  # Only for donors

# Donation request model structure
class DonationRequestModel:
    def __init__(self):
        self.id = None
        self.recipient_id = None
        self.amount = None
        self.remaining_amount = None
        self.priority_level = None
        self.reason = None
        self.case_details = None
        self.status = RequestStatus.PENDING
        self.created_at = None
        self.approved_at = None
        self.declined_at = None

# Transaction model structure
class TransactionModel:
    def __init__(self):
        self.id = None
        self.user_id = None
        self.transaction_type = None
        self.amount = None
        self.description = None
        self.request_id = None  # For payment transactions
        self.created_at = None