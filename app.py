# Crypto Research Bot with OpenAI API
# Requirements: pip install flask openai python-dotenv requests flask-cors gunicorn

import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import json
import requests
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Crypto-focused system prompt with latest knowledge
CRYPTO_SYSTEM_PROMPT = """You are CryptoBot, an advanced cryptocurrency research assistant powered by GPT-4 Turbo. You specialize in:

CRYPTOCURRENCY KNOWLEDGE:
- All cryptocurrencies (Bitcoin, Ethereum, altcoins, meme coins)
- Market analysis and price predictions
- Technical analysis and trading strategies
- Fundamental analysis and tokenomics
- Regulatory news and compliance

DEFI & BLOCKCHAIN:
- DeFi protocols and yield farming
- Smart contracts and dApps
- Layer 1 and Layer 2 solutions
- Cross-chain bridges and interoperability
- Staking and governance tokens

TRADING & INVESTMENT:
- Risk management strategies
- Portfolio diversification
- Market cycles and sentiment analysis
- On-chain analytics and metrics
- Derivatives and futures trading

NFT & WEB3:
- NFT marketplaces and collections
- Utility and gaming tokens
- Metaverse and virtual worlds
- Web3 infrastructure and tools

MARKET DATA:
- Real-time price analysis
- Volume and liquidity analysis
- Market cap and dominance trends
- Fear & Greed Index interpretation
- Macro economic impacts

Provide accurate, up-to-date, and actionable insights. Always include risk warnings for investment advice. Use current data when possible and be specific about timeframes and market conditions. Keep responses informative yet accessible to both beginners and advanced users."""

# CoinGecko API for live data (free tier)
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

def get_crypto_data(crypto_id="bitcoin"):
    """Fetch live crypto data from CoinGecko API"""
    try:
        url = f"{COINGECKO_API_BASE}/simple/price"
        params = {
            "ids": crypto_id,
            "vs_currencies": "usd",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true"
        }
        response = requests.get(url, params=params, timeout=5)
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching crypto data: {str(e)}")
        return None

def get_market_overview():
    """Get overall crypto market data"""
    try:
        url = f"{COINGECKO_API_BASE}/global"
        response = requests.get(url, timeout=5)
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])
        
        if not user_message:
            return jsonify({'error': 'No message provided', 'success': False}), 400
        
        # Check if API key is set
        if not os.getenv('OPENAI_API_KEY'):
            return jsonify({'error': 'API key not configured. Please set OPENAI_API_KEY environment variable.', 'success': False}), 500
        
        # Enhance message with live data if crypto-specific
        enhanced_message = user_message
        if any(crypto in user_message.lower() for crypto in ['bitcoin', 'btc', 'ethereum', 'eth', 'price', 'market']):
            market_data = get_market_overview()
            if market_data:
                enhanced_message += f"\n\nLive Market Data: Total Market Cap: ${market_data.get('data', {}).get('total_market_cap', {}).get('usd', 0):,.0f}, 24h Vol: ${market_data.get('data', {}).get('total_volume', {}).get('usd', 0):,.0f}"
        
        # Build conversation context
        messages = [{"role": "system", "content": CRYPTO_SYSTEM_PROMPT}]
        
        # Add conversation history (last 10 messages)
        for msg in conversation_history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current message
        messages.append({"role": "user", "content": enhanced_message})
        
        # Make request to OpenAI API with latest model
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",  # Latest GPT-4 Turbo model
            messages=messages,
            max_tokens=1500,
            temperature=0.7,
            presence_penalty=0.1,
            frequency_penalty=0.1
        )
        
        ai_response = response.choices[0].message.content
        
        return jsonify({
            'response': ai_response,
            'success': True,
            'model': 'gpt-4-turbo-preview',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}', 'success': False}), 500

@app.route('/api/market-data')
def market_data():
    """Endpoint for live market data"""
    try:
        # Get top cryptocurrencies
        url = f"{COINGECKO_API_BASE}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 10,
            "page": 1,
            "sparkline": "false"
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Market data error: {str(e)}")
        return jsonify({'error': f'Failed to fetch market data: {str(e)}', 'success': False}), 500

@app.route('/api/crypto/<crypto_id>')
def crypto_detail(crypto_id):
    """Get detailed info for specific cryptocurrency"""
    try:
        url = f"{COINGECKO_API_BASE}/coins/{crypto_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "true",
            "developer_data": "true"
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Crypto detail error: {str(e)}")
        return jsonify({'error': f'Failed to fetch crypto data: {str(e)}', 'success': False}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model': 'gpt-4-turbo-preview',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found', 'success': False}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'success': False}), 500

if __name__ == '__main__':
    # Check if API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  WARNING: OPENAI_API_KEY environment variable is not set!")
        print("Please set it before running the app:")
        print("export OPENAI_API_KEY='your_api_key_here'")
        print("or create a .env file with: OPENAI_API_KEY=your_api_key_here")
    
    print("🚀 Starting Crypto Research Bot...")
    print("🤖 Powered by OpenAI GPT-4 Turbo")
    print("📈 Live crypto data integration enabled")
    print("🌐 Access the app at: http://localhost:8000")
    
    # Production settings
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(debug=debug, host='0.0.0.0', port=port)