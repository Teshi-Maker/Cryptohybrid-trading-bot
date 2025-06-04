from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=5, max=64)
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=12, message='Password must be at least 12 characters long')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    admin_email = StringField('Admin Email Verification', validators=[DataRequired(), Email()])
    registration_key = StringField('Registration Key', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(min=5, max=64)])
    admin_recovery_key = StringField('Admin Recovery Key', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=12, message='Password must be at least 12 characters long')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Update Password')

class ApiKeyForm(FlaskForm):
    exchange = SelectField('Exchange', choices=[
        ('binance', 'Binance'),
        ('coinbase', 'Coinbase Pro'),
        ('kraken', 'Kraken'),
        ('huobi', 'Huobi'),
        ('okx', 'OKX'),
        ('kucoin', 'KuCoin')
    ], validators=[DataRequired()])
    api_key = StringField('API Key', validators=[DataRequired()])
    api_secret = PasswordField('API Secret', validators=[DataRequired()])
    submit = SubmitField('Add API Key')

class BotConfigForm(FlaskForm):
    name = StringField('Configuration Name', validators=[DataRequired(), Length(min=1, max=100)])
    strategies = SelectField('Primary Strategy', choices=[
        ('hft', 'High Frequency Trading'),
        ('arbitrage', 'Cross-Exchange Arbitrage'),
        ('ml_prediction', 'ML Price Prediction'),
        ('portfolio_optimization', 'Portfolio Optimization'),
        ('scalping', 'Scalping Strategy'),
        ('hybrid', 'Hybrid Multi-Strategy')
    ], validators=[DataRequired()])
    pairs = StringField('Trading Pairs (comma separated)', validators=[DataRequired()], 
                       render_kw={"placeholder": "BTC/USDT, ETH/USDT, ADA/USDT"})
    hft_active = BooleanField('Enable High Frequency Trading')
    arbitrage_active = BooleanField('Enable Arbitrage Detection')
    portfolio_active = BooleanField('Enable Portfolio Optimization')
    sentiment_active = BooleanField('Enable News Sentiment Analysis')
    rebalance_frequency = IntegerField('Rebalance Frequency (seconds)', 
                                     validators=[NumberRange(min=60, max=86400)], 
                                     default=3600)
    arb_profit_threshold = FloatField('Arbitrage Profit Threshold (%)', 
                                    validators=[NumberRange(min=0.1, max=10.0)], 
                                    default=0.3)
    ml_confidence_threshold = FloatField('ML Confidence Threshold', 
                                       validators=[NumberRange(min=0.1, max=1.0)], 
                                       default=0.7)
    submit = SubmitField('Save Configuration')

class NotificationSettingsForm(FlaskForm):
    notification_email = StringField('Notification Email', validators=[Email()])
    email_notifications_enabled = BooleanField('Enable Email Notifications')
    notify_trades = BooleanField('Trade Notifications')
    notify_arbitrage = BooleanField('Arbitrage Opportunity Notifications')
    notify_ml = BooleanField('ML Prediction Notifications')
    notify_errors = BooleanField('Error Notifications')
    notify_bot_status = BooleanField('Bot Status Notifications')
    submit = SubmitField('Save Settings')

class WithdrawalForm(FlaskForm):
    exchange = SelectField('Exchange', choices=[
        ('binance', 'Binance'),
        ('coinbase', 'Coinbase Pro'),
        ('kraken', 'Kraken'),
        ('huobi', 'Huobi'),
        ('okx', 'OKX'),
        ('kucoin', 'KuCoin')
    ], validators=[DataRequired()])
    asset = StringField('Asset Symbol', validators=[DataRequired()], 
                       render_kw={"placeholder": "BTC, ETH, USDT"})
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.0001)])
    address = StringField('Withdrawal Address', validators=[DataRequired()])
    memo = StringField('Memo/Tag (if required)', render_kw={"placeholder": "Optional"})
    network = StringField('Network', validators=[DataRequired()], 
                         render_kw={"placeholder": "ERC20, TRC20, BSC, etc."})
    submit = SubmitField('Request Withdrawal')

class OTPVerificationForm(FlaskForm):
    otp_code = StringField('6-Digit OTP Code', validators=[
        DataRequired(), 
        Length(min=6, max=6, message='OTP must be exactly 6 digits')
    ])
    submit = SubmitField('Verify and Complete Withdrawal')

class BacktestForm(FlaskForm):
    name = StringField('Backtest Name', validators=[DataRequired(), Length(min=1, max=100)])
    strategy = SelectField('Strategy', choices=[
        ('hft', 'High Frequency Trading'),
        ('arbitrage', 'Cross-Exchange Arbitrage'),
        ('ml_prediction', 'ML Price Prediction'),
        ('portfolio_optimization', 'Portfolio Optimization'),
        ('scalping', 'Scalping Strategy')
    ], validators=[DataRequired()])
    pairs = StringField('Trading Pairs (comma separated)', validators=[DataRequired()],
                       render_kw={"placeholder": "BTC/USDT, ETH/USDT"})
    initial_capital = FloatField('Initial Capital (USD)', validators=[
        DataRequired(), 
        NumberRange(min=100, max=1000000)
    ], default=10000)
    days_back = IntegerField('Days to Backtest', validators=[
        DataRequired(),
        NumberRange(min=1, max=365)
    ], default=30)
    submit = SubmitField('Run Backtest')
