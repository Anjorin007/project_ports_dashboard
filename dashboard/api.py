"""
Flask API pour West Africa Ports Dashboard
✅ Decimal CORRIGÉ (conversion avant JSON)
✅ Groq réponses complètes fluides
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from groq import Groq
import json
import re
from decimal import Decimal

load_dotenv()

app = Flask(__name__)
CORS(app)

# ============================================================================
# FONCTION DE CONVERSION DECIMAL (AVANT JSON)
# ============================================================================

def convert_decimals(obj):
    """Convertit récursivement tous les Decimal en float"""
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

# ============================================================================
# CONNEXION POOL POSTGRESQL
# ============================================================================

# Connexion DB optionnelle
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1, 10,
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'ports_dashboard'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
        port=os.getenv('DB_PORT', '5432')
    )
except Exception as e:
    print(f"⚠️  DB connection failed: {e}")
    print("Running in dev mode without database")
    db_pool = None

def execute_query(query):
    """Exécute requête SQL et retourne résultats en dict normal"""
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        db_pool.putconn(conn)
        
        # Convertir RealDictRow → dict normal → Decimal → float
        data = [dict(row) for row in results]
        return convert_decimals(data)
    except Exception as e:
        print(f"❌ SQL Error: {e}")
        return []

# ============================================================================
# GROQ CLIENT
# ============================================================================

groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# ============================================================================
# CACHE DONNÉES
# ============================================================================

data_cache = {}
CACHE_VALID = True

def get_cached_data():
    """Récupère ou met à jour le cache"""
    global data_cache
    
    if not data_cache or not CACHE_VALID:
        print("📥 Chargement données...")
        data_cache['summary'] = execute_query("""
            SELECT port_code, year, total_tonnage_mt, total_teus
            FROM public_marts.mart_port_annual_summary
            WHERE year >= 2020
            ORDER BY year DESC, total_tonnage_mt DESC
        """)
        
        data_cache['comparison'] = execute_query("""
            SELECT port_code, year, total_tonnage_mt, tonnage_market_share_pct, 
                   total_teus, teu_market_share_pct, tonnage_rank
            FROM public_marts.mart_port_comparison
            ORDER BY year DESC, total_tonnage_mt DESC
            LIMIT 10
        """)
        
        data_cache['trends'] = execute_query("""
            SELECT port_code, year, total_tonnage_mt, tonnage_yoy_pct
            FROM public_marts.mart_port_trends
            WHERE year >= 2023
            ORDER BY year DESC, tonnage_yoy_pct DESC
        """)
        print("✅ Cache chargé")
    
    return data_cache

# ============================================================================
# ENDPOINTS API
# ============================================================================

@app.route('/', methods=['GET'])
def index():
    """Page d'accueil"""
    return jsonify({
        "message": "🌊 West Africa Ports Dashboard API",
        "status": "running",
        "endpoints": {
            "health": "GET /api/health",
            "summary": "GET /api/ports/summary",
            "comparison": "GET /api/ports/comparison",
            "trends": "GET /api/ports/trends",
            "chat": "POST /api/groq/chat",
            "insights": "GET /api/groq/insights"
        }
    })

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "ok"})