import os
import sys
import time

# In DaVinci Resolve's internal Python 3 console, the 'resolve' object is already global.
# We ensure it exists just in case.
try:
    resolve
except NameError:
    try:
        import DaVinciResolveScript as dvr_script
        resolve = dvr_script.scriptapp("Resolve")
    except:
        resolve = bmd.scriptapp("Resolve")

if not resolve:
    print("Error: Could not find resolve object.")
else:
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    
    if not project:
        print("Error: No project open.")
    else:
        timeline = project.GetCurrentTimeline()
        if not timeline:
            print("Error: No timeline open.")
        else:
            print(f"Spike 0: Analyzing Timeline '{timeline.GetName()}'")
            
            playhead_tc = timeline.GetCurrentTimecode()
            print(f"Playhead Timecode: {playhead_tc}")
            
            items = timeline.GetItemListInTrack("video", 1)
            if not items:
                print("Error: No clips on Video Track 1.")
            else:
                target_clip = items[0]
                clip_name = target_clip.GetName()
                start_frame = target_clip.GetStart()
                end_frame = target_clip.GetEnd()
                duration = target_clip.GetDuration()
                
                print(f"Target Clip Found: {clip_name} (Frames {start_frame} to {end_frame}, Duration: {duration})")
                
                # Setup render
                project.SetRenderSettings({"SelectAllFrames": False, "MarkIn": start_frame, "MarkOut": end_frame - 1})
                
                project_root = os.path.dirname(os.path.abspath(__file__))
                export_dir = os.path.join(project_root, "data", "exports")
                os.makedirs(export_dir, exist_ok=True)
                export_path = os.path.join(export_dir, "export_spike.mov")
                
                render_settings = {
                    "TargetDir": export_dir,
                    "CustomName": "export_spike",
                    "FormatWidth": 1920,
                    "FormatHeight": 1080,
                    "ExportVideo": True,
                    "ExportAudio": False
                }
                
                project.SetRenderSettings(render_settings)
                project.DeleteAllRenderJobs()
                project.AddRenderJob()
                
                print(f"Rendering clip segment to {export_path}...")
                project.StartRendering()
                
                while project.IsRenderingInProgress():
                    time.sleep(1)
                    
                print("Render complete!")
                
                media_pool = project.GetMediaPool()
                root_folder = media_pool.GetRootFolder()
                
                if not os.path.exists(export_path):
                    print(f"Error: Rendered file not found at {export_path}")
                else:
                    print(f"Importing {export_path} into Media Pool...")
                    imported_items = media_pool.ImportMedia([export_path])
                    
                    if not imported_items:
                        print("Error: Failed to import media.")
                    else:
                        imported_clip = imported_items[0]
                        
                        # 4. Place imported media as overlay
                        print(f"Placing imported media as overlay on Track 2 at frame {start_frame}...")
                        
                        # Resolve API allows appending via dictionaries
                        clip_info = {
                            "mediaPoolItem": imported_clip,
                            "startFrame": 0,
                            "endFrame": duration - 1,
                            "trackIndex": 2,
                            "recordFrame": start_frame
                        }
                        
                        # Use media_pool.AppendToTimeline which accepts a list of dicts in modern Resolve API
                        result = media_pool.AppendToTimeline([clip_info])
                        
                        if not result:
                            print("Warning: AppendToTimeline with dict failed. Try dragging it manually for now.")
                        else:
                            print("Successfully placed overlay on timeline!")
                            
                        print("Spike 0 tasks completed successfully!")
