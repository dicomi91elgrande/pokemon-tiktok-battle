"""
Servidor puente entre TikFinity/Interactive y el overlay de combate.

  TikFinity (regalo/chat) --POST--> /webhook --SSE--> overlay en OBS

- Sirve el overlay (index.html) en  http://localhost:3000/
- Recibe los eventos de TikFinity por POST en  /webhook
- Los reenvía al overlay en tiempo real por SSE (Server-Sent Events)

No necesita instalar nada: solo la librería estándar de Python.
Arrancar con:   python server.py
"""

import json
import os
import queue
import re
import threading
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

PORT = int(os.environ.get('PORT', 3000))   # el hosting (Render, etc.) asigna el puerto por env
HOOK_TOKEN = os.environ.get('HOOK_TOKEN')  # opcional: si se define, /webhook exige ?token=...
BASE = os.path.dirname(os.path.abspath(__file__))

# Lista de clientes SSE conectados (cada overlay abierto = una cola)
clients = []
clients_lock = threading.Lock()

DEX_NAMES = [
    'Bulbasaur','Ivysaur','Venusaur','Charmander','Charmeleon','Charizard','Squirtle','Wartortle','Blastoise','Caterpie',
    'Metapod','Butterfree','Weedle','Kakuna','Beedrill','Pidgey','Pidgeotto','Pidgeot','Rattata','Raticate',
    'Spearow','Fearow','Ekans','Arbok','Pikachu','Raichu','Sandshrew','Sandslash','Nidoran♀','Nidorina',
    'Nidoqueen','Nidoran♂','Nidorino','Nidoking','Clefairy','Clefable','Vulpix','Ninetales','Jigglypuff','Wigglytuff',
    'Zubat','Golbat','Oddish','Gloom','Vileplume','Paras','Parasect','Venonat','Venomoth','Diglett',
    'Dugtrio','Meowth','Persian','Psyduck','Golduck','Mankey','Primeape','Growlithe','Arcanine','Poliwag',
    'Poliwhirl','Poliwrath','Abra','Kadabra','Alakazam','Machop','Machoke','Machamp','Bellsprout','Weepinbell',
    'Victreebel','Tentacool','Tentacruel','Geodude','Graveler','Golem','Ponyta','Rapidash','Slowpoke','Slowbro',
    'Magnemite','Magneton',"Farfetch'd",'Doduo','Dodrio','Seel','Dewgong','Grimer','Muk','Shellder',
    'Cloyster','Gastly','Haunter','Gengar','Onix','Drowzee','Hypno','Krabby','Kingler','Voltorb',
    'Electrode','Exeggcute','Exeggutor','Cubone','Marowak','Hitmonlee','Hitmonchan','Lickitung','Koffing','Weezing',
    'Rhyhorn','Rhydon','Chansey','Tangela','Kangaskhan','Horsea','Seadra','Goldeen','Seaking','Staryu',
    'Starmie','Mr. Mime','Scyther','Jynx','Electabuzz','Magmar','Pinsir','Tauros','Magikarp','Gyarados',
    'Lapras','Ditto','Eevee','Vaporeon','Jolteon','Flareon','Porygon','Omanyte','Omastar','Kabuto',
    'Kabutops','Aerodactyl','Snorlax','Articuno','Zapdos','Moltres','Dratini','Dragonair','Dragonite','Mewtwo','Mew'
]


def slug(text):
    text = (text or '').strip().lower().replace('♀', 'f').replace('♂', 'm')
    text = unicodedata.normalize('NFD', text)
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    text = re.sub(r"[.'’\-\s]", '', text)
    return re.sub(r'[^a-z0-9]', '', text)


DEX = [{'name': name, 'slug': slug(name)} for name in DEX_NAMES]


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1]


def fuzzy_limit(text):
    return 2 if len(text) >= 8 else 1


def find_mon(text):
    base = slug(text)
    if not base:
        return None
    candidates = [base]
    for word in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ♀♂.'’-]+", text or ''):
        word_slug = slug(word)
        if word_slug and word_slug not in candidates:
            candidates.append(word_slug)
    for query in candidates:
        exact = next((mon for mon in DEX if mon['slug'] == query), None)
        if exact:
            return exact['name']
    for query in candidates:
        if len(query) >= 4:
            partial = next((mon for mon in DEX if mon['slug'].startswith(query) or query in mon['slug'] or mon['slug'] in query), None)
            if partial:
                return partial['name']
    best = None
    for query in candidates:
        for mon in DEX:
            dist = edit_distance(query, mon['slug'])
            if dist <= fuzzy_limit(query) and (best is None or dist < best['dist']):
                best = {'name': mon['name'], 'dist': dist}
    return best['name'] if best else None


def broadcast(obj):
    """Envía un evento (dict) a todos los overlays conectados."""
    data = json.dumps(obj, ensure_ascii=False)
    with clients_lock:
        for q in list(clients):
            q.put(data)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silencioso

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    # ---- CORS preflight ----
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ---- GET: overlay, SSE y estáticos ----
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ('/', '/index.html'):
            self.serve_file('index.html', 'text/html; charset=utf-8')
        elif path == '/events':
            self.handle_sse()
        elif path == '/health':
            self.send_json({'ok': True, 'clients': len(clients)})
        else:
            self.serve_file(path.lstrip('/'), None)

    def serve_file(self, rel, ctype):
        fp = os.path.normpath(os.path.join(BASE, rel))
        if not fp.startswith(BASE) or not os.path.isfile(fp):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404')
            return
        if ctype is None:
            ctype = 'text/html; charset=utf-8' if rel.endswith('.html') \
                else 'application/javascript' if rel.endswith('.js') \
                else 'text/css' if rel.endswith('.css') \
                else 'application/octet-stream'
        with open(fp, 'rb') as f:
            body = f.read()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_sse(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self._cors()
        self.end_headers()
        q = queue.Queue()
        with clients_lock:
            clients.append(q)
        try:
            self.wfile.write(b': conectado\n\n')
            self.wfile.flush()
            while True:
                try:
                    data = q.get(timeout=15)
                    self.wfile.write(('data: ' + data + '\n\n').encode('utf-8'))
                except queue.Empty:
                    self.wfile.write(b': ping\n\n')  # keepalive
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with clients_lock:
                if q in clients:
                    clients.remove(q)

    # ---- POST: eventos de TikFinity ----
    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != '/webhook':
            self.send_response(404)
            self.end_headers()
            return
        # token opcional: solo se exige si HOOK_TOKEN está definido
        if HOOK_TOKEN:
            token = parse_qs(parsed.query).get('token', [''])[0]
            if token != HOOK_TOKEN:
                self.send_response(403)
                self._cors()
                self.end_headers()
                self.wfile.write(b'{"ok":false,"error":"token"}')
                return
        length = int(self.headers.get('Content-Length', '0') or 0)
        raw = self.rfile.read(length) if length else b''
        try:
            obj = json.loads(raw.decode('utf-8')) if raw else {}
        except Exception:
            obj = {'event': 'raw', 'raw': raw.decode('utf-8', 'replace')}
        if obj.get('event') == 'comment':
            matched_mon = find_mon(obj.get('comment') or obj.get('message') or obj.get('text') or obj.get('content') or '')
            if not matched_mon:
                self.send_response(200)
                self._cors()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"ok":true,"filtered":true}')
                return
            obj['comment'] = matched_mon
        broadcast(obj)
        print('webhook:', obj)
        self.send_response(200)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def send_json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    print('=' * 56)
    print(' Pokemon TikTok Battle - servidor puente')
    print(f' Overlay para OBS : http://localhost:{PORT}/')
    print(f' URL del WebHook  : http://localhost:{PORT}/webhook')
    print('=' * 56)
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
