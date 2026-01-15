import http.server
import socketserver
import json
import sqlite3
import hashlib
import os
from urllib.parse import urlparse, parse_qs

PORT = 8080
DB_FILE = 'webnav_rpg.db'

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        # Disable caching to ensure browser always gets latest files
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
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

    def get_body_json(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        return json.loads(post_data.decode('utf-8'))

    def respond_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    # --- Handlers ---

    def handle_save_game(self):
        try:
            data = self.get_body_json()
            slot_id = data.get('slot_id', 0)
            game_data = data.get('data') # JSON string or object
            
            if isinstance(game_data, dict):
                game_data = json.dumps(game_data)

            conn = sqlite3.connect(DB_FILE)
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
            self.respond_json({'success': False, 'message': str(e)}, 500)

    def handle_load_game(self):
        try:
            data = self.get_body_json()
            slot_id = data.get('slot_id', 0)

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT data_json FROM game_saves WHERE user_id=1 AND slot_id=?', (slot_id,))
            row = c.fetchone()
            conn.close()

            if row:
                self.respond_json({'success': True, 'data': json.loads(row[0])})
            else:
                self.respond_json({'success': False, 'message': 'No save found'})
        except Exception as e:
            self.respond_json({'success': False, 'message': str(e)}, 500)

    def handle_list_saves(self):
        """List all save slots with metadata for save/load UI"""
        try:
            data = self.get_body_json()
            user_id = data.get('user_id', 1)
            
            conn = sqlite3.connect(DB_FILE)
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
                    # Skip corrupted saves
                    continue
            
            self.respond_json({'success': True, 'saves': saves})
        except Exception as e:
            self.respond_json({'success': False, 'message': str(e)}, 500)

    def handle_save_drawing(self):
        try:
            data = self.get_body_json()
            paper_id = data.get('paper_id')
            strokes = data.get('strokes') # JSON array

            if not paper_id:
                raise ValueError("paper_id is required")

            conn = sqlite3.connect(DB_FILE)
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
            print(e)
            self.respond_json({'success': False, 'message': str(e)}, 500)

    def handle_get_drawing(self):
        try:
            data = self.get_body_json()
            paper_id = data.get('paper_id')

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT strokes_json FROM drawings WHERE user_id=1 AND paper_id=?', (paper_id,))
            row = c.fetchone()
            conn.close()

            if row:
                self.respond_json({'success': True, 'strokes': json.loads(row[0])})
            else:
                self.respond_json({'success': True, 'strokes': []}) # Return empty if new
        except Exception as e:
            self.respond_json({'success': False, 'message': str(e)}, 500)

    def handle_get_cached_ai(self):
        try:
            data = self.get_body_json()
            prompt = data.get('prompt', '')
            # Generate hash
            prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT response FROM ai_cache WHERE prompt_hash=?', (prompt_hash,))
            row = c.fetchone()
            conn.close()

            if row:
                self.respond_json({'success': True, 'cached': True, 'response': row[0]})
            else:
                self.respond_json({'success': True, 'cached': False})
        except Exception as e:
            self.respond_json({'success': False, 'message': str(e)}, 500)

    def handle_cache_ai(self):
        try:
            data = self.get_body_json()
            prompt = data.get('prompt', '')
            response = data.get('response', '')
            provider = data.get('provider', 'unknown')
            model = data.get('model', 'unknown')
            
            prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('''
                INSERT OR IGNORE INTO ai_cache (prompt_hash, prompt_text, response, provider, model)
                VALUES (?, ?, ?, ?, ?)
            ''', (prompt_hash, prompt, response, provider, model))
            conn.commit()
            conn.close()
            
            self.respond_json({'success': True})
        except Exception as e:
            self.respond_json({'success': False, 'message': str(e)}, 500)

    def handle_get_story(self):
        """Fetch AI story content from story database"""
        try:
            data = self.get_body_json()
            q_id = data.get('q_id')
            year = data.get('year')
            lang = data.get('lang', 'cn')  # 'cn' or 'en'
            is_correct = data.get('is_correct', True)
            
            story_db = 'story_content.db'
            if not os.path.exists(story_db):
                self.respond_json({'success': False, 'message': 'Story database not found'}, 404)
                return
            
            conn = sqlite3.connect(story_db)
            c = conn.cursor()
            
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
                self.respond_json({'success': False, 'message': 'Story not found'}, 404)
        except Exception as e:
            self.respond_json({'success': False, 'message': str(e)}, 500)

print(f"Serving at http://localhost:{PORT}")
http.server.HTTPServer(('0.0.0.0', PORT), CustomHandler).serve_forever()
