#!/usr/bin/env python3
"""Loopback-only static review server with media byte-range support."""
import argparse
import functools
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class MediaHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Accept-Ranges','bytes')
        super().end_headers()

    def send_head(self):
        self.remaining=None
        path=Path(self.translate_path(self.path))
        request=self.headers.get('Range')
        if not request or not path.is_file():
            return super().send_head()
        match=re.fullmatch(r'bytes=(\d*)-(\d*)',request.strip())
        if not match or not any(match.groups()):
            self.send_error(400,'Unsupported byte range');return None
        size=path.stat().st_size
        left,right=match.groups()
        if left:
            start=int(left);end=min(int(right) if right else size-1,size-1)
        else:
            start=max(0,size-int(right));end=size-1
        if start<0 or start>=size or end<start:
            self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.end_headers();return None
        f=path.open('rb');f.seek(start);self.remaining=end-start+1
        self.send_response(206)
        self.send_header('Content-Type',self.guess_type(str(path)))
        self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length',str(self.remaining))
        self.send_header('Last-Modified',self.date_time_string(path.stat().st_mtime))
        self.end_headers();return f

    def copyfile(self,source,outputfile):
        try:
            if self.remaining is None:return super().copyfile(source,outputfile)
            while self.remaining:
                chunk=source.read(min(self.remaining,256*1024))
                if not chunk:break
                outputfile.write(chunk);self.remaining-=len(chunk)
        except (BrokenPipeError,ConnectionResetError):
            pass  # normal when a player seeks or stops buffering

    def log_message(self,format,*args):
        pass


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--port',type=int,default=8779);args=ap.parse_args()
    directory=args.root.resolve()
    if not directory.is_dir():raise SystemExit('Review directory does not exist')
    server=ThreadingHTTPServer(('127.0.0.1',args.port),functools.partial(MediaHandler,directory=str(directory)))
    print(f'Review server: http://127.0.0.1:{args.port}/edit-v1/index.html',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
