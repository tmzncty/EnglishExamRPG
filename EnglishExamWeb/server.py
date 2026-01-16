import http.server
import socketserver
import json
import sqlite3
import hashlib
import os
import datetime
import traceback
from urllib.parse import urlparse, parse_qs

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'webnav_rpg.db')
STORY_DB_FILE = os.path.join(BASE_DIR, 'story_content.db')

# Logging setup
def log_error(msg):
    with open(os.path.join(BASE_DIR, 'server_errors.log'), 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.datetime.now()}] {msg}\n")

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        try:
            # Parse URL
            parsed_path = urlparse(self.path)
            
            # API routing
            if parsed_path.path == '/api/save_game':
                self.handle_save_game()
            elif parsed_path.path == '/api/save_drawing':
                self.handle_save_drawing()
            elif parsed_path.path == '/api/get_cached_ai':
                self.handle_get_cached_ai()
            elif parsed_path.path == '/api/cache_ai':
                self.handle_cache_ai()
            elif parsed_path.path == '/api/load_game':
                self.handle_load_game() 
            elif parsed_path.path == '/api/get_drawing': 
                self.handle_get_drawing()
            elif parsed_path.path == '/api/list_saves':
                self.handle_list_saves()
            elif parsed_path.path == '/api/get_story':
                self.handle_get_story()
            else:
                self.send_error(404, "API Endpoint not found")
        except Exception as e:
            msg = f"Unhandled Error in do_POST: {e}\n{traceback.format_exc()}"
            print(msg)
            log_error(msg)
            self.send_error(500, str(e))

    def get_body_json(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        return json.loads(post_data.decode('utf-8'))

    def respond_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    # Helper to get DB connection with WAL
    def get_db_conn(self, db_path):
        conn = sqlite3.connect(db_path, timeout=10)
        # Enable WAL (Write Ahead Logging) for better concurrency
        try:
            conn.execute('PRAGMA journal_mode=WAL;')
        except:
            pass
        return conn

    # --- Handlers ---

    def handle_save_game(self):
        try:
            data = self.get_body_json()
            slot_id = data.get('slot_id', 0)
            game_data = data.get('data') # JSON string or object
            
            if isinstance(game_data, dict):
                game_data = json.dumps(game_data)

            conn = self.get_db_conn(DB_FILE)
            c = conn.cursor()
            c.execute('''
                INSERT INTO game_saves (user_id, slot_id, data_json, updated_at) 
                VALUES (1, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, slot_id) DO UPDATE SET 
                data_json=excluded.data_json, 
                updated_at=CURRENT_TIMESTAMP
            ''', (slot_id, game_data))
            conn.commit()
            conn.close()
            
            self.respond_json({'success': True, 'message': 'Saved successfully'})
        except Exception as e:
            conn.close()
            log_error(f"Save Game Error: {e}\n{traceback.format_exc()}")
            self.respond_json({'success': False, 'message': str(e)}, 500)

    def handle_load_game(self):
        try:
            data = self.get_body_json()
            slot_id = data.get('slot_id', 0)

            conn = self.get_db_conn(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT data_json FROM game_saves WHERE user_id=1 AND slot_id=?', (slot_id,))
            row = c.fetchone()
            conn.close()

            if row:
                self.respond_json({'success': True, 'data': json.loads(row[0])})
            else:
                self.respond_json({'success': False, 'message': 'No save found'})
        except Exception as e:
            log_error(f"Load Game Error: {e}\n{traceback.format_exc()}")
            print(f"Error in handle_load_game: {e}")
            import traceback
            traceback.print_exc()
            self.respond_json({'success': False, 'message': str(e)}, 500)

    def handle_list_saves(self):
        """List all save slots with metadata for save/load UI"""
        try:
            data = self.get_body_json()
            user_id = data.get('user_id', 1)
            
            conn = self.get_db_conn(DB_FILE)
            c = conn.cursor()
            c.execute('''
                SELECT slot_id, data_json, updated_at 
                FROM game_saves 
                WHERE user_id=? 
                ORDER BY slot_id
            ''', (user_id,))
            rows = c.fetchall()
            conn.close()
            
            saves = []
            for row in rows:
                slot_id, data_json, timestamp = row
                try:
                    game_data = json.loads(data_json)
                    metadata = game_data.get('saveMetadata', {})
                    
                    saves.append({
                        'slotId': slot_id,
                        'timestamp': timestamp,
                        'metadata': metadata
                    })
                except json.JSONDecodeError:
                    continue
            
            self.respond_json({'success': True, 'saves': saves})
        except Exception as e:
            log_error(f"List Saves Error: {e}\n{traceback.format_exc()}")
            self.respond_json({'success': False, 'message': str(e)}, 500)

    def handle_save_drawing(self):
        try:
            data = self.get_body_json()
            paper_id = data.get('paper_id')
            strokes = data.get('strokes') # JSON array

            if not paper_id:
                raise ValueError("paper_id is required")

            conn = self.get_db_conn(DB_FILE)
            c = conn.cursor()
            c.execute('''
                INSERT INTO drawings (user_id, paper_id, strokes_json, updated_at) 
                VALUES (1, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, paper_id) DO UPDATE SET 
                strokes_json=excluded.strokes_json, 
                updated_at=CURRENT_TIMESTAMP
            ''', (paper_id, json.dumps(strokes)))
            conn.commit()
            conn.close()
            
            self.respond_json({'success': True})
        except Exception as e:
            log_error(f"Save Drawing Error: {e}\n{traceback.format_exc()}")
            self.respond_json({'success': False, 'message': str(e)}, 500)

    def handle_get_drawing(self):
        try:
            data = self.get_body_json()
            paper_id = data.get('paper_id')

            conn = self.get_db_conn(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT strokes_json FROM drawings WHERE user_id=1 AND paper_id=?', (paper_id,))
            row = c.fetchone()
            conn.close()

            if row:
                self.respond_json({'success': True, 'strokes': json.loads(row[0])})
            else:
                self.respond_json({'success': True, 'strokes': []}) # Return empty if new
        except Exception as e:
            log_error(f"Get Drawing Error: {e}\n{traceback.format_exc()}")
            self.respond_json({'success': False, 'message': str(e)}, 500)

    def handle_get_cached_ai(self):
        try:
            data = self.get_body_json()
            prompt = data.get('prompt', '')
            # Generate hash
            prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()

            conn = self.get_db_conn(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT response FROM ai_cache WHERE prompt_hash=?', (prompt_hash,))
            row = c.fetchone()
            conn.close()

            if row:
                self.respond_json({'success': True, 'cached': True, 'response': row[0]})
            else:
                self.respond_json({'success': True, 'cached': False})
        except Exception as e:
            log_error(f"Get AI Cache Error: {e}\n{traceback.format_exc()}")
            self.respond_json({'success': False, 'message': str(e)}, 500)

    def handle_cache_ai(self):
        try:
            data = self.get_body_json()
            prompt = data.get('prompt', '')
            response = data.get('response', '')
            provider = data.get('provider', 'unknown')
            model = data.get('model', 'unknown')
            
            prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()

            conn = self.get_db_conn(DB_FILE)
            c = conn.cursor()
            c.execute('''
                INSERT OR IGNORE INTO ai_cache (prompt_hash, prompt_text, response, provider, model)
                VALUES (?, ?, ?, ?, ?)
            ''', (prompt_hash, prompt, response, provider, model))
            conn.commit()
            conn.close()
            
            self.respond_json({'success': True})
        except Exception as e:
            log_error(f"Cache AI Error: {e}\n{traceback.format_exc()}")
            self.respond_json({'success': False, 'message': str(e)}, 500)

    def handle_get_story(self):
        """Fetch AI story content from story database"""
        try:
            data = self.get_body_json()
            q_id = data.get('q_id')
            year = data.get('year')
            lang = data.get('lang', 'cn')  # 'cn', 'en', or 'both'
            is_correct = data.get('is_correct', True)
            
            print(f"[DEBUG] get_story request: q_id={q_id}, year={year}, lang={lang}, is_correct={is_correct}")

            # Ensure compatible types for DB query
            try:
                q_id = int(str(q_id))
                year = int(str(year))
            except (ValueError, TypeError):
                self.respond_json({'success': False, 'message': 'Invalid ID or Year format'}, 400)
                return

            if not os.path.exists(STORY_DB_FILE):
                self.respond_json({'success': False, 'message': f'Story database not found at {STORY_DB_FILE}'}, 404)
                return
            
            conn = self.get_db_conn(STORY_DB_FILE)
            c = conn.cursor()
            
            if lang == 'both':
                # Fetch both languages
                field_cn = 'correct_cn' if is_correct else 'wrong_cn'
                field_en = 'correct_en' if is_correct else 'wrong_en'
                c.execute(f'SELECT {field_cn}, {field_en} FROM stories WHERE q_id=? AND year=?', (q_id, year))
                row = c.fetchone()
                conn.close()
                
                if row and (row[0] or row[1]):
                    self.respond_json({
                        'success': True, 
                        'story': {
                            'cn': row[0] or '',
                            'en': row[1] or '',
                            'bilingual': True
                        }
                    })
                else:
                    log_error(f"Story not found for q_id={q_id}, year={year}, field_cn={field_cn}")
                    self.respond_json({'success': False, 'message': 'Story not found'}, 404)
            else:
                # Legacy single language fetch
                if lang == 'cn':
                    field = 'correct_cn' if is_correct else 'wrong_cn'
                else:
                    field = 'correct_en' if is_correct else 'wrong_en'
                
                c.execute(f'SELECT {field} FROM stories WHERE q_id=? AND year=?', (q_id, year))
                row = c.fetchone()
                conn.close()
                
                if row and row[0]:
                    self.respond_json({'success': True, 'story': row[0]})
                else:
                    log_error(f"Story not found for q_id={q_id}, year={year}, field={field}")
                    self.respond_json({'success': False, 'message': 'Story not found'}, 404)
                    
        except Exception as e:
            log_error(f"Get Story Error: {e}\n{traceback.format_exc()}")
            self.respond_json({'success': False, 'message': str(e)}, 500)

print(f"Serving at http://localhost:{PORT}")
http.server.HTTPServer(('0.0.0.0', PORT), CustomHandler).serve_forever()
