from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db
from forms import (LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm, 
                   ApiKeyForm, BotConfigForm, NotificationSettingsForm, WithdrawalForm, 
                   OTPVerificationForm, BacktestForm)
from models import User, ApiKey, BotConfig, Trade, ArbitrageOpportunity, PortfolioSnapshot, NewsItem
from datetime import datetime, timedelta
import json
import logging

@app.route('/')
@app.route('/index')
def index():
    """Landing page with login/register options"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html', title='Crypto Trading Bot')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login with account lockout protection"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None:
            flash('Invalid username or password', 'error')
            return render_template('login.html', title='Sign In', form=form)
        
        # Check if account is locked
        if user.is_account_locked():
            flash('Account is temporarily locked due to multiple failed login attempts. Please try again later.', 'error')
            return render_template('login.html', title='Sign In', form=form)
        
        if not user.check_password(form.password.data):
            user.record_failed_login()
            flash('Invalid username or password', 'error')
            return render_template('login.html', title='Sign In', form=form)
        
        # Successful login
        user.reset_failed_logins()
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('dashboard')
        return redirect(next_page)
    
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with admin verification"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Verify admin credentials (simple check for demo)
        if (form.admin_email.data != 'admin@cryptobot.com' or 
            form.registration_key.data != 'CRYPTO2024SECURE'):
            flash('Invalid admin verification credentials', 'error')
            return render_template('register.html', title='Register', form=form)
        
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Password recovery for admin account"""
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        # Admin recovery key check
        if form.admin_recovery_key.data != 'RECOVERY2024ADMIN':
            flash('Invalid admin recovery key', 'error')
            return render_template('forgot_password.html', title='Forgot Password', form=form)
        
        user = User.query.filter_by(username=form.username.data, email=form.email.data).first()
        if user:
            # In production, send email with reset link
            flash('Password reset instructions have been sent to your email (Demo: Use emergency reset)', 'info')
        else:
            flash('No account found with those credentials', 'error')
    
    return render_template('forgot_password.html', title='Forgot Password', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    """Main trading dashboard"""
    # Get user's bot configurations
    bot_configs = BotConfig.query.filter_by(user_id=current_user.id).all()
    
    # Get recent trades
    recent_trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.timestamp.desc()).limit(10).all()
    
    # Get active arbitrage opportunities
    arbitrage_opps = ArbitrageOpportunity.query.filter_by(
        user_id=current_user.id, executed=False
    ).order_by(ArbitrageOpportunity.timestamp.desc()).limit(5).all()
    
    # Portfolio summary (mock data for demo)
    portfolio_summary = {
        'total_value': 25847.32,
        'daily_change': 3.24,
        'daily_change_percent': 0.128,
        'positions': [
            {'symbol': 'BTC/USDT', 'value': 15000.00, 'change': 2.1},
            {'symbol': 'ETH/USDT', 'value': 8000.00, 'change': -1.5},
            {'symbol': 'ADA/USDT', 'value': 2847.32, 'change': 4.8}
        ]
    }
    
    return render_template('dashboard.html', 
                         title='Trading Dashboard',
                         bot_configs=bot_configs,
                         recent_trades=recent_trades,
                         arbitrage_opps=arbitrage_opps,
                         portfolio=portfolio_summary)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings and API key management"""
    api_form = ApiKeyForm()
    config_form = BotConfigForm()
    notification_form = NotificationSettingsForm()
    
    # Pre-populate notification form
    notification_form.notification_email.data = current_user.notification_email
    notification_form.email_notifications_enabled.data = current_user.email_notifications_enabled
    notification_form.notify_trades.data = current_user.notify_trades
    notification_form.notify_arbitrage.data = current_user.notify_arbitrage
    notification_form.notify_ml.data = current_user.notify_ml
    notification_form.notify_errors.data = current_user.notify_errors
    notification_form.notify_bot_status.data = current_user.notify_bot_status
    
    # Get user's API keys and bot configurations
    api_keys = ApiKey.query.filter_by(user_id=current_user.id).all()
    bot_configs = BotConfig.query.filter_by(user_id=current_user.id).all()
    
    return render_template('settings.html',
                         title='Settings',
                         api_form=api_form,
                         config_form=config_form,
                         notification_form=notification_form,
                         api_keys=api_keys,
                         bot_configs=bot_configs)

@app.route('/arbitrage')
@login_required
def arbitrage():
    """Arbitrage opportunities dashboard"""
    opportunities = ArbitrageOpportunity.query.filter_by(
        user_id=current_user.id
    ).order_by(ArbitrageOpportunity.timestamp.desc()).limit(20).all()
    
    return render_template('arbitrage.html', 
                         title='Arbitrage Opportunities',
                         opportunities=opportunities)

@app.route('/portfolio')
@login_required
def portfolio():
    """Portfolio management and optimization"""
    # Get portfolio snapshots
    snapshots = PortfolioSnapshot.query.filter_by(
        user_id=current_user.id
    ).order_by(PortfolioSnapshot.timestamp.desc()).limit(30).all()
    
    return render_template('portfolio.html',
                         title='Portfolio Management',
                         snapshots=snapshots)

@app.route('/news_sentiment')
@login_required
def news_sentiment():
    """News sentiment analysis dashboard"""
    news_items = NewsItem.query.order_by(NewsItem.timestamp.desc()).limit(50).all()
    
    return render_template('news_sentiment.html',
                         title='News & Sentiment Analysis',
                         news_items=news_items)

@app.route('/backtesting', methods=['GET', 'POST'])
@login_required
def backtesting():
    """Strategy backtesting interface"""
    form = BacktestForm()
    
    if form.validate_on_submit():
        # In production, this would trigger actual backtesting
        flash('Backtest started! Results will be available shortly.', 'info')
        return redirect(url_for('backtesting'))
    
    return render_template('backtesting.html',
                         title='Strategy Backtesting',
                         form=form)

# API Routes for AJAX calls
@app.route('/api/add_api_key', methods=['POST'])
@login_required
def api_add_api_key():
    """Add new API key via AJAX"""
    try:
        data = request.get_json()
        api_key = ApiKey(
            exchange=data['exchange'],
            api_key=data['api_key'],
            api_secret=data['api_secret'],
            user_id=current_user.id
        )
        db.session.add(api_key)
        db.session.commit()
        return jsonify({'success': True, 'message': 'API key added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/delete_api_key/<int:key_id>', methods=['DELETE'])
@login_required
def api_delete_api_key(key_id):
    """Delete API key via AJAX"""
    try:
        api_key = ApiKey.query.filter_by(id=key_id, user_id=current_user.id).first()
        if api_key:
            db.session.delete(api_key)
            db.session.commit()
            return jsonify({'success': True, 'message': 'API key deleted successfully'})
        return jsonify({'success': False, 'message': 'API key not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/add_bot_config', methods=['POST'])
@login_required
def api_add_bot_config():
    """Add new bot configuration via AJAX"""
    try:
        data = request.get_json()
        config = BotConfig(
            name=data['name'],
            strategies=data['strategies'],
            pairs=data['pairs'],
            hft_active=data.get('hft_active', False),
            arbitrage_active=data.get('arbitrage_active', False),
            portfolio_active=data.get('portfolio_active', False),
            sentiment_active=data.get('sentiment_active', False),
            rebalance_frequency=data.get('rebalance_frequency', 3600),
            arb_profit_threshold=data.get('arb_profit_threshold', 0.003),
            ml_confidence_threshold=data.get('ml_confidence_threshold', 0.7),
            user_id=current_user.id
        )
        db.session.add(config)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Bot configuration saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/start_bot', methods=['POST'])
@login_required
def api_start_bot():
    """Start trading bot via AJAX"""
    try:
        data = request.get_json()
        config_id = data.get('config_id')
        
        # In production, this would start the actual trading bot
        config = BotConfig.query.filter_by(id=config_id, user_id=current_user.id).first()
        if config:
            config.is_active = True
            db.session.commit()
            return jsonify({'success': True, 'message': f'Bot "{config.name}" started successfully'})
        
        return jsonify({'success': False, 'message': 'Configuration not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/stop_bot', methods=['POST'])
@login_required
def api_stop_bot():
    """Stop trading bot via AJAX"""
    try:
        data = request.get_json()
        config_id = data.get('config_id')
        
        config = BotConfig.query.filter_by(id=config_id, user_id=current_user.id).first()
        if config:
            config.is_active = False
            db.session.commit()
            return jsonify({'success': True, 'message': f'Bot "{config.name}" stopped successfully'})
        
        return jsonify({'success': False, 'message': 'Configuration not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/bot_status')
@login_required
def api_bot_status():
    """Get bot status via AJAX"""
    try:
        configs = BotConfig.query.filter_by(user_id=current_user.id).all()
        status_data = []
        
        for config in configs:
            status_data.append({
                'id': config.id,
                'name': config.name,
                'is_active': config.is_active,
                'strategies': config.get_strategies(),
                'pairs': config.get_pairs()
            })
        
        return jsonify({'success': True, 'data': status_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/emergency_reset')
def emergency_reset():
    """Emergency system reset - clears all data"""
    try:
        # Clear all tables
        db.session.query(Trade).delete()
        db.session.query(ArbitrageOpportunity).delete()
        db.session.query(PortfolioSnapshot).delete()
        db.session.query(BotConfig).delete()
        db.session.query(ApiKey).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        flash('Database cleared successfully! You can now register fresh.', 'success')
        return redirect(url_for('register'))
    except Exception as e:
        flash(f'Error during reset: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/quick_reset')
def quick_reset():
    """Quick reset for development - creates default admin account"""
    try:
        # Clear existing data
        db.session.query(User).delete()
        db.session.commit()
        
        # Create default admin user
        admin = User(username='admin', email='admin@cryptobot.com')
        admin.set_password('CryptoBot2024!')
        db.session.add(admin)
        db.session.commit()
        
        flash('Quick reset complete! Login with: admin / CryptoBot2024!', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        flash(f'Error during quick reset: {str(e)}', 'error')
        return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    return render_template('500.html'), 500
