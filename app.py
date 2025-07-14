# Enhanced Crypto Research Bot with Streaming & Fast Responses
# Requirements: pip install flask openai python-dotenv requests flask-cors gunicorn

import os
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import json
import requests
from datetime import datetime
import logging
import re
import random

# Import configuration constants
from config import (
    COINGECKO_API_BASE, OPENAI_MODEL, MAX_TOKENS, TEMPERATURE, 
    PRESENCE_PENALTY, FREQUENCY_PENALTY, MAX_HISTORY_MESSAGES,
    API_TIMEOUT, MARKET_DATA_TIMEOUT, GREETING_PATTERNS,
    CRYPTO_GREETING_RESPONSES, CRYPTO_KEYWORDS, CRYPTO_SYSTEM_PROMPT,
    MARKET_DATA_PARAMS, CRYPTO_DETAIL_PARAMS, PRICE_DATA_PARAMS,
    ERROR_MESSAGES, SUCCESS_MESSAGES, APP_INFO
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
try:
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    client = None

def is_simple_greeting(message):
    """Check if message is a simple greeting"""
    message_lower = message.lower().strip()
    return any(re.match(pattern, message_lower) for pattern in GREETING_PATTERNS)

def get_crypto_greeting():
    """Get a random crypto-themed greeting response"""
    return random.choice(CRYPTO_GREETING_RESPONSES)

def create_error_response(message, status_code=500):
    """Create standardized error response"""
    logger.error(f"Error: {message}")
    return jsonify({
        "error": message,
        "success": False,
        "timestamp": datetime.now().isoformat()
    }), status_code

def get_crypto_data(crypto_id="bitcoin"):
    """Fetch live crypto data from CoinGecko API"""
    try:
        url = f"{COINGECKO_API_BASE}/simple/price"
        response = requests.get(url, params={**PRICE_DATA_PARAMS, "ids": crypto_id}, timeout=MARKET_DATA_TIMEOUT)
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching crypto data: {str(e)}")
        return None

def get_market_overview():
    """Get overall crypto market data"""
    try:
        url = f"{COINGECKO_API_BASE}/global"
        response = requests.get(url, timeout=MARKET_DATA_TIMEOUT)
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        return None

def enhance_message_with_data(message):
    """Add live market data to crypto-related messages"""
    try:
        enhanced_message = message
        if any(crypto in message.lower() for crypto in CRYPTO_KEYWORDS):
            market_data = get_market_overview()
            if market_data and 'data' in market_data:
                data = market_data['data']
                total_cap = data.get('total_market_cap', {}).get('usd', 0)
                total_vol = data.get('total_volume', {}).get('usd', 0)
                enhanced_message += f"\n\nLive Market Data: Total Market Cap: ${total_cap:,.0f}, 24h Vol: ${total_vol:,.0f}"
        return enhanced_message
    except Exception as e:
        logger.error(f"Error enhancing message: {e}")
        return message

def stream_chat_response(messages):
    """Stream response from OpenAI API"""
    try:
        if not client:
            yield f"data: {json.dumps({'error': ERROR_MESSAGES['client_not_initialized'], 'success': False})}\n\n"
            return

        # Create streaming request
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            presence_penalty=PRESENCE_PENALTY,
            frequency_penalty=FREQUENCY_PENALTY,
            stream=True
        )
        
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                data = json.dumps({
                    "content": content,
                    "success": True
                })
                yield f"data: {data}\n\n"
        
        # Send completion signal
        yield f"data: {json.dumps({'done': True, 'success': True})}\n\n"
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_data = json.dumps({
            "error": f"Streaming error: {str(e)}",
            "success": False
        })
        yield f"data: {error_data}\n\n"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Standard chat endpoint (non-streaming)"""
    try:
        data = request.json
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])
        
        if not user_message:
            return create_error_response(ERROR_MESSAGES['no_message'], 400)
        
        # Check if API key is set
        if not os.getenv('OPENAI_API_KEY'):
            return create_error_response(ERROR_MESSAGES['api_key_missing'], 500)
        
        if not client:
            return create_error_response(ERROR_MESSAGES['client_not_initialized'], 500)
        
        # Quick response for simple greetings
        if is_simple_greeting(user_message):
            return jsonify({
                'response': get_crypto_greeting(),
                'success': True,
                'model': 'instant-response',
                'timestamp': datetime.now().isoformat()
            })
        
        # Enhance message with live data if crypto-specific
        enhanced_message = enhance_message_with_data(user_message)
        
        # Build conversation context
        messages = [{"role": "system", "content": CRYPTO_SYSTEM_PROMPT}]
        
        # Add conversation history (last 10 messages)
        for msg in conversation_history[-MAX_HISTORY_MESSAGES:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current message
        messages.append({"role": "user", "content": enhanced_message})
        
        # Make request to OpenAI API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            presence_penalty=PRESENCE_PENALTY,
            frequency_penalty=FREQUENCY_PENALTY
        )
        
        ai_response = response.choices[0].message.content
        
        return jsonify({
            'response': ai_response,
            'success': True,
            'model': OPENAI_MODEL,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return create_error_response(f'Chat error: {str(e)}', 500)

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Streaming chat endpoint"""
    try:
        data = request.json
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])
        
        if not user_message:
            return create_error_response(ERROR_MESSAGES['no_message'], 400)
        
        # Check if API key is set
        if not os.getenv('OPENAI_API_KEY'):
            return create_error_response(ERROR_MESSAGES['api_key_missing'], 500)
        
        if not client:
            return create_error_response(ERROR_MESSAGES['client_not_initialized'], 500)
        
        # Quick response for simple greetings
        if is_simple_greeting(user_message):
            def quick_greeting():
                response = get_crypto_greeting()
                data = json.dumps({"content": response, "success": True})
                yield f"data: {data}\n\n"
                yield f"data: {json.dumps({'done': True, 'success': True})}\n\n"
            
            return Response(
                quick_greeting(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                }
            )
        
        # Enhance message with live data
        enhanced_message = enhance_message_with_data(user_message)
        
        # Build conversation context
        messages = [{"role": "system", "content": CRYPTO_SYSTEM_PROMPT}]
        
        # Add conversation history (last 10 messages)
        for msg in conversation_history[-MAX_HISTORY_MESSAGES:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current message
        messages.append({"role": "user", "content": enhanced_message})
        
        # Stream response
        return Response(
            stream_chat_response(messages),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
            }
        )
        
    except Exception as e:
        logger.error(f"Stream error: {e}")
        return create_error_response(f'Stream error: {str(e)}', 500)

@app.route('/api/market-data')
def market_data():
    """Endpoint for live market data"""
    try:
        # Get top cryptocurrencies
        url = f"{COINGECKO_API_BASE}/coins/markets"
        response = requests.get(url, params=MARKET_DATA_PARAMS, timeout=MARKET_DATA_TIMEOUT)
        
        if response.status_code != 200:
            return create_error_response(f'{ERROR_MESSAGES["api_error"]}: {response.status_code}', 502)
        
        data = response.json()
        
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Market data request error: {str(e)}")
        return create_error_response(f'{ERROR_MESSAGES["network_error"]}', 502)
    except Exception as e:
        logger.error(f"Market data error: {str(e)}")
        return create_error_response(f'Failed to fetch market data: {str(e)}', 500)

@app.route('/api/crypto/<crypto_id>')
def crypto_detail(crypto_id):
    """Get detailed info for specific cryptocurrency"""
    try:
        # Sanitize crypto_id
        if not crypto_id or not crypto_id.replace('-', '').replace('_', '').isalnum():
            return create_error_response(ERROR_MESSAGES['invalid_crypto_id'], 400)
        
        url = f"{COINGECKO_API_BASE}/coins/{crypto_id}"
        response = requests.get(url, params=CRYPTO_DETAIL_PARAMS, timeout=API_TIMEOUT)
        
        if response.status_code == 404:
            return create_error_response(f'{ERROR_MESSAGES["crypto_not_found"]}: "{crypto_id}"', 404)
        elif response.status_code != 200:
            return create_error_response(f'{ERROR_MESSAGES["api_error"]}: {response.status_code}', 502)
        
        data = response.json()
        
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Crypto detail request error: {str(e)}")
        return create_error_response(f'{ERROR_MESSAGES["network_error"]}', 502)
    except Exception as e:
        logger.error(f"Crypto detail error: {str(e)}")
        return create_error_response(f'Failed to fetch crypto data: {str(e)}', 500)
        
        url = f"{COINGECKO_API_BASE}/coins/{crypto_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "true",
            "developer_data": "true"
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 404:
            return create_error_response(f'Cryptocurrency "{crypto_id}" not found', 404)
        elif response.status_code != 200:
            return create_error_response(f'CoinGecko API error: {response.status_code}', 502)
        
        data = response.json()
        
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Crypto detail request error: {str(e)}")
        return create_error_response(f'Failed to fetch crypto data: Network error', 502)
    except Exception as e:
        logger.error(f"Crypto detail error: {str(e)}")
        return create_error_response(f'Failed to fetch crypto data: {str(e)}', 500)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model': 'gpt-4-turbo-preview',
        'openai_client': 'initialized' if client else 'not initialized',
        'api_key_set': bool(os.getenv('OPENAI_API_KEY')),
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

@app.errorhandler(404)
def not_found(error):
    return create_error_response('Endpoint not found', 404)

@app.errorhandler(405)
def method_not_allowed(error):
    return create_error_response('Method not allowed', 405)

@app.errorhandler(500)
def internal_error(error):
    return create_error_response('Internal server error', 500)

if __name__ == '__main__':
    # Check if API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  WARNING: OPENAI_API_KEY environment variable is not set!")
        print("Please set it before running the app:")
        print("export OPENAI_API_KEY='your_api_key_here'")
        print("or create a .env file with: OPENAI_API_KEY=your_api_key_here")
    
    print("🚀 Starting Enhanced Crypto Research Bot...")
    print("🤖 Powered by OpenAI GPT-4 Turbo")
    print("📈 Live crypto data integration enabled")
    print("⚡ Streaming responses & instant greetings")
    print("🛡️  Enhanced error handling")
    print("🌐 Access the app at: http://localhost:8000")
    
    # Production settings
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(debug=debug, host='0.0.0.0', port=port)