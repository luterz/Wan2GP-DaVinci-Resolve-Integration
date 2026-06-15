import os
import json
import time
import shutil
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

def get_resolve():
    try:
        import DaVinciResolveScript as dvr_script
        res = dvr_script.scriptapp("Resolve")
        if res: return res
    except:
        pass
        
    try:
        res = bmd.scriptapp("Resolve") # type: ignore
        if res: return res
    except:
        pass
    return None

class ResolveBridgeHandler(BaseHTTPRequestHandler):
    
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
        
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/media':
            qs = urllib.parse.parse_qs(parsed.query)
            filepath = qs.get("path", [""])[0]
            if not filepath or not os.path.exists(filepath):
                self.send_response(404)
                self.end_headers()
                return
            
            try:
                file_size = os.path.getsize(filepath)
                range_header = self.headers.get('Range', None)
                
                with open(filepath, 'rb') as f:
                    if range_header:
                        # Parse simple Range header (e.g. bytes=0- or bytes=-100)
                        range_str = range_header.replace('bytes=', '').strip().split('-')
                        if range_str[0] == '':
                            suffix_length = int(range_str[1])
                            start = max(0, file_size - suffix_length)
                            end = file_size - 1
                        else:
                            start = int(range_str[0])
                            end = int(range_str[1]) if len(range_str) > 1 and range_str[1] else file_size - 1
                        
                        length = end - start + 1
                        self.send_response(206)
                        self._set_cors_headers()
                        self.send_header('Content-Type', 'video/quicktime' if filepath.endswith('.mov') else 'video/mp4')
                        self.send_header('Accept-Ranges', 'bytes')
                        self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                        self.send_header('Content-Length', str(length))
                        self.end_headers()
                        
                        f.seek(start)
                        self.wfile.write(f.read(length))
                    else:
                        self.send_response(200)
                        self._set_cors_headers()
                        self.send_header('Content-Type', 'video/quicktime' if filepath.endswith('.mov') else 'video/mp4')
                        self.send_header('Accept-Ranges', 'bytes')
                        self.send_header('Content-Length', str(file_size))
                        self.end_headers()
                        shutil.copyfileobj(f, self.wfile)
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_response(404)
            self.end_headers()
        
    def do_POST(self):
        if self.path == '/export':
            self.handle_export()
        elif self.path == '/import':
            self.handle_import()
        else:
            self.send_response(404)
            self.end_headers()
            
    def handle_export(self):
        resolve = get_resolve()
        if not resolve:
            self.send_error(500, "Resolve object not found. Is DaVinci Resolve running?")
            return
            
        project = resolve.GetProjectManager().GetCurrentProject()
        if not project:
            self.send_error(500, "No active project found in DaVinci Resolve")
            return
            
        timeline = project.GetCurrentTimeline()
        if not timeline:
            self.send_error(500, "No active timeline found in DaVinci Resolve")
            return
        
        target_clip = timeline.GetCurrentVideoItem()
        if not target_clip:
            self.send_error(400, "No video clip found under the playhead. Please position the playhead over the clip you want to process.")
            return
        start_frame = target_clip.GetStart()
        end_frame = target_clip.GetEnd()
        duration = target_clip.GetDuration()
        
        project.SetRenderSettings({"SelectAllFrames": False, "MarkIn": start_frame, "MarkOut": end_frame - 1})
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        export_dir = os.path.join(project_root, "data", "exports")
        os.makedirs(export_dir, exist_ok=True)
        export_name = f"export_bridge_{int(time.time())}"
        export_path = os.path.join(export_dir, f"{export_name}.mp4")
        
        project.SetRenderSettings({
            "TargetDir": export_dir,
            "CustomName": export_name,
            "ExportVideo": True,
            "ExportAudio": False,
            "FormatWidth": 1920,
            "FormatHeight": 1080,
            "Format": "mp4",
            "Codec": "H264"
        })
        
        project.DeleteAllRenderJobs()
        project.AddRenderJob()
        project.StartRendering()
        
        while project.IsRenderingInProgress():
            time.sleep(1)
            
        self.send_response(200)
        self._set_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        width = int(timeline.GetSetting("timelineResolutionWidth") or 1920)
        height = int(timeline.GetSetting("timelineResolutionHeight") or 1080)
        
        response = {
            "media_path": export_path,
            "fps": timeline.GetSetting("timelineFrameRate"),
            "resolution": [width, height],
            "duration_frames": duration,
            "start_frame": start_frame
        }
        self.wfile.write(json.dumps(response).encode())

    def handle_import(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        manifest = json.loads(post_data.decode('utf-8'))
        
        resolve = get_resolve()
        if not resolve:
            self.send_error(500, "Resolve object not found. Is DaVinci Resolve running?")
            return
            
        project = resolve.GetProjectManager().GetCurrentProject()
        if not project:
            self.send_error(500, "No active project found in DaVinci Resolve")
            return
            
        media_pool = project.GetMediaPool()
        
        export_path = manifest.get("output_media_path")
        if not os.path.exists(export_path):
            self.send_error(404, f"File not found: {export_path}")
            return
            
        imported_items = media_pool.ImportMedia([export_path])
        if not imported_items:
            self.send_error(500, "Failed to import media into Resolve")
            return
            
        # Place as overlay
        clip_info = {
            "mediaPoolItem": imported_items[0],
            "startFrame": 0,
            "endFrame": manifest["resolve_metadata"]["duration_frames"] - 1,
            "trackIndex": manifest["resolve_metadata"]["target_track_index"],
            "recordFrame": manifest["resolve_metadata"]["target_start_frame"]
        }
        
        media_pool.AppendToTimeline([clip_info])
        
        self.send_response(200)
        self._set_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "success"}).encode())

def run_server(port=8001):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, ResolveBridgeHandler)
    print(f"Resolve Bridge running on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
