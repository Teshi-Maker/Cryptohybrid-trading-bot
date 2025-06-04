from datetime import datetime
import json
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import random

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    notification_email = db.Column(db.String(120), nullable=True)
    email_notifications_enabled = db.Column(db.Boolean, default=True)
    notify_trades = db.Column(db.Boolean, default=True)
    notify_arbitrage = db.Column(db.Boolean, default=True)
    notify_ml = db.Column(db.Boolean, default=True)
    notify_errors = db.Column(db.Boolean, default=True)
    notify_bot_status = db.Column(db.Boolean, default=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime)
    account_locked_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    api_keys = db.relationship('ApiKey', backref='user', lazy=True)
    bot_configs = db.relationship('BotConfig', backref='user', lazy=True)
    trades = db.relationship('Trade', backref='user', lazy=True)
    withdrawals = db.relationship('Withdrawal', backref='user', lazy=True)
    deposits = db.relationship('Deposit', backref='user', lazy=True)
    
    @staticmethod
    def validate_username(username):
        import re
        if not username or len(username) < 5 or len(username) > 64:
            return False, "Username must be between 5 and 64 characters"
        
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]+$', username):
            return False, "Username must start with a letter and can only contain letters, numbers, and underscore"
        
        return True, ""
    
    @staticmethod
    def validate_password(password):
        import re
        if not password or len(password) < 12:
            return False, "Password must be at least 12 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, ""
    
    def set_password(self, password):
        valid, message = self.validate_password(password)
        if not valid:
            raise ValueError(message)
            
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def record_failed_login(self):
        from datetime import timedelta
        
        self.failed_login_attempts += 1
        self.last_failed_login = datetime.utcnow()
        
        if self.failed_login_attempts >= 5:
            self.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
            
        db.session.commit()
        
    def reset_failed_logins(self):
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.account_locked_until = None
        db.session.commit()
        
    def is_account_locked(self):
        if self.account_locked_until:
            return datetime.utcnow() < self.account_locked_until
        return False

class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exchange = db.Column(db.String(50), nullable=False)
    api_key = db.Column(db.String(100), nullable=False)
    api_secret = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class BotConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    strategies = db.Column(db.String(200), nullable=False)
    pairs = db.Column(db.String(500), nullable=False)
    hft_active = db.Column(db.Boolean, default=False)
    arbitrage_active = db.Column(db.Boolean, default=False)
    portfolio_active = db.Column(db.Boolean, default=False)
    sentiment_active = db.Column(db.Boolean, default=False)
    rebalance_frequency = db.Column(db.Integer, default=86400)
    arb_profit_threshold = db.Column(db.Float, default=0.003)
    ml_confidence_threshold = db.Column(db.Float, default=0.7)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def get_strategies(self):
        try:
            return json.loads(self.strategies) if self.strategies else []
        except:
            return []
    
    def set_strategies(self, strategies_list):
        self.strategies = json.dumps(strategies_list)
    
    def get_pairs(self):
        try:
            return json.loads(self.pairs) if self.pairs else []
        except:
            return []
    
    def set_pairs(self, pairs_list):
        self.pairs = json.dumps(pairs_list)

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exchange = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    order_id = db.Column(db.String(50))
    side = db.Column(db.String(10), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    fee = db.Column(db.Float)
    status = db.Column(db.String(20), nullable=False)
    strategy = db.Column(db.String(50), nullable=False)
    profit_loss = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class ArbitrageOpportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)
    exchange_1 = db.Column(db.String(50), nullable=False)
    exchange_2 = db.Column(db.String(50), nullable=False)
    price_1 = db.Column(db.Float, nullable=False)
    price_2 = db.Column(db.Float, nullable=False)
    profit_percent = db.Column(db.Float, nullable=False)
    executed = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class PortfolioSnapshot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    assets = db.Column(db.Text, nullable=False)
    total_value_usd = db.Column(db.Float, nullable=False)
    weights = db.Column(db.Text, nullable=False)
    sharpe_ratio = db.Column(db.Float)
    volatility = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def get_assets(self):
        try:
            return json.loads(self.assets) if self.assets else {}
        except:
            return {}
    
    def set_assets(self, assets_dict):
        self.assets = json.dumps(assets_dict)
    
    def get_weights(self):
        try:
            return json.loads(self.weights) if self.weights else {}
        except:
            return {}
    
    def set_weights(self, weights_dict):
        self.weights = json.dumps(weights_dict)

class NewsItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    sentiment_score = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    related_assets = db.Column(db.String(200))
    
    def get_related_assets(self):
        try:
            return json.loads(self.related_assets) if self.related_assets else []
        except:
            return []
    
    def set_related_assets(self, assets_list):
        self.related_assets = json.dumps(assets_list)

class Deposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exchange = db.Column(db.String(50), nullable=False)
    asset = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    destination_tag = db.Column(db.String(200))
    network = db.Column(db.String(50), default="native")
    status = db.Column(db.String(20), default="pending")
    transaction_id = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    fee = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Withdrawal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exchange = db.Column(db.String(50), nullable=False)
    asset = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    memo = db.Column(db.String(200))
    network = db.Column(db.String(50), default="native")
    status = db.Column(db.String(20), default="pending")
    transaction_id = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    fee = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class BacktestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    strategy = db.Column(db.String(50), nullable=False)
    pairs = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    initial_capital = db.Column(db.Float, nullable=False)
    final_capital = db.Column(db.Float, nullable=False)
    total_return = db.Column(db.Float, nullable=False)
    sharpe_ratio = db.Column(db.Float)
    max_drawdown = db.Column(db.Float)
    win_rate = db.Column(db.Float)
    parameters = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class WithdrawalOTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    withdrawal_id = db.Column(db.Integer, db.ForeignKey('withdrawal.id'), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, default=False)
    attempts = db.Column(db.Integer, default=0)
    
    __table_args__ = (
        db.UniqueConstraint('withdrawal_id', name='unique_withdrawal_otp'),
    )
    
    @staticmethod
    def generate_otp():
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self, code):
        return (not self.is_expired() and 
                not self.verified and 
                self.attempts < 3 and 
                self.otp_code == code)
