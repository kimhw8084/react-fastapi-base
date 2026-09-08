#!/usr/bin/env python3
"""Loopback-only static server for the shipped, dependency-free Experience Lab.

This never starts the application API, reads AccessKey, or opens company storage.
Not a production internet-facing application server.
"""
from __future__ import annotations
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'experience-lab/public'

class LabHandler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml'}
    def __init__(self,*args,directory=None,**kwargs):
        self.public=Path(directory or PUBLIC).resolve()
        super().__init__(*args,directory=str(self.public),**kwargs)
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'")
        super().end_headers()
    def list_directory(self,path):
        self.send_error(404,'Directory listing is disabled');return None
    def send_head(self):
        host=urlsplit('//'+self.headers.get('Host','')).hostname
        if host not in {'127.0.0.1','localhost','::1'}:
            self.send_error(403,'Only loopback hosts are accepted');return None
        route=unquote(urlsplit(self.path).path)
        parts=Path(route).parts
        if '\x00' in route or '\\' in route or any(p in {'..','.'} or (p.startswith('.') and p!='/') for p in parts):
            self.send_error(403,'Invalid asset path');return None
        target=(self.public/route.lstrip('/')).resolve()
        if not target.is_relative_to(self.public):
            self.send_error(403,'Asset outside public directory');return None
        if any(p.is_symlink() for p in (self.public/route.lstrip('/'),*(self.public/route.lstrip('/')).parents) if p.is_relative_to(self.public)):
            self.send_error(403,'Symbolic link assets are forbidden');return None
        return super().send_head()

def make_server(port:int=4173,public:Path=PUBLIC)->ThreadingHTTPServer:
    if not (public/'index.html').is_file():raise ValueError('Compiled Experience Lab is missing. Run ./dev lab-build.')
    server=ThreadingHTTPServer(('127.0.0.1',port),partial(LabHandler,directory=str(public)))
    server.daemon_threads=True
    return server

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=4173);args=parser.parse_args()
    if not 1<=args.port<=65535:parser.error('Port must be 1–65535.')
    with make_server(args.port) as server:
        print(f'Experience Lab: http://127.0.0.1:{server.server_port}\nSynthetic data only. Ctrl+C stops this server.',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
    return 0
if __name__=='__main__':raise SystemExit(main())
