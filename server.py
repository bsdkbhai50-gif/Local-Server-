import http.server
import socketserver
import os
import urllib
import json
import datetime

HOST = ""   # all interfaces
PORT = 8080
UPLOAD_DIR = "/" # Set your 📁 file path

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def get_icon(self, filename):
        """Return emoji based on file type"""
        if os.path.isdir(os.path.join(UPLOAD_DIR, filename)):
            return "📂"
        ext = filename.lower()
        if ext.endswith((".mp4", ".mkv", ".avi", ".mov")):
            return "🎬"
        elif ext.endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")):
            return "🖼️"
        elif ext.endswith(".py"):
            return "🐍"
        elif ext.endswith(".pdf"):
            return "📕"
        elif ext.endswith((".mp3", ".wav", ".ogg")):
            return "🎵"
        else:
            return "📄"

    def format_size(self, size):
        """Convert bytes into KB, MB, GB"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    def format_date(self, path):
        """Return last modified date"""
        timestamp = os.path.getmtime(path)
        return datetime.datetime.fromtimestamp(timestamp).strftime("%d-%m-%Y %H:%M")

    def list_files(self):
        files = os.listdir(UPLOAD_DIR)
        file_items = ""
        for f in files:
            safe_name = urllib.parse.quote(f)
            icon = self.get_icon(f)
            full_path = os.path.join(UPLOAD_DIR, f)

            if os.path.isdir(full_path):
                size_str = ""
            else:
                size_str = f" ({self.format_size(os.path.getsize(full_path))})"

            date_str = self.format_date(full_path)

            file_items += f"""
            <div class="file-card" data-name="{f.lower()}" data-size="{os.path.getsize(full_path) if os.path.isfile(full_path) else 0}" data-date="{os.path.getmtime(full_path)}">
                <a href='/files/{safe_name}' download>{icon} {f}{size_str} – <small>{date_str}</small></a>
                <button class="delete-btn" onclick="deleteFile('{safe_name}')">🗑 Delete</button>
            </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>File Server</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: var(--bg);
                    color: var(--text);
                    text-align: center;
                    padding: 20px;
                    transition: background 0.3s, color 0.3s;
                }}
                h2 {{ color: var(--text); }}
                .file-card {{
                    background: var(--card);
                    margin: 10px auto;
                    padding: 15px;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    width: 90%;
                    max-width: 600px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    transition: 0.2s;
                }}
                .file-card:hover {{
                    transform: scale(1.02);
                    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
                }}
                a {{
                    text-decoration: none;
                    color: #007bff;
                    font-weight: bold;
                }}
                a:hover {{ color: #0056b3; }}
                .delete-btn {{
                    background: #ff4d4d;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 8px;
                    color: white;
                    font-weight: bold;
                    cursor: pointer;
                }}
                .delete-btn:hover {{ background: #cc0000; }}
                .upload-link {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 12px 20px;
                    background: #28a745;
                    color: white;
                    border-radius: 10px;
                    text-decoration: none;
                    font-weight: bold;
                }}
                .upload-link:hover {{ background: #218838; }}
                .theme-toggle {{
                    margin: 20px;
                    padding: 10px 18px;
                    background: #333;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    cursor: pointer;
                }}
                .search-bar, .sort-select {{
                    margin: 10px;
                    padding: 10px;
                    border-radius: 8px;
                    border: 1px solid #ccc;
                    width: 200px;
                }}
            </style>
        </head>
        <body>
            <h2>📂 Available Files</h2>
            <input type="text" class="search-bar" placeholder="🔍 Search files..." onkeyup="searchFiles()">
            <select class="sort-select" onchange="sortFiles(this.value)">
                <option value="name">Sort by Name</option>
                <option value="size">Sort by Size</option>
                <option value="date">Sort by Date</option>
            </select>
            <div id="file-list">
                {file_items if file_items else "<p>No files uploaded yet.</p>"}
            </div>
            <br>
            <a class="upload-link" href="/upload">⬆️ Upload Files</a>
            <br>
            <button class="theme-toggle" onclick="toggleTheme()">🌙 Dark Mode</button>

            <script>
              const root = document.documentElement;
              function setTheme(dark) {{
                if (dark) {{
                  root.style.setProperty('--bg', '#121212');
                  root.style.setProperty('--text', '#f1f1f1');
                  root.style.setProperty('--card', '#1e1e1e');
                  document.querySelector('.theme-toggle').innerText = "☀️ Light Mode";
                }} else {{
                  root.style.setProperty('--bg', '#f4f6f9');
                  root.style.setProperty('--text', '#222');
                  root.style.setProperty('--card', '#fff');
                  document.querySelector('.theme-toggle').innerText = "🌙 Dark Mode";
                }}
                localStorage.setItem("darkmode", dark);
              }}
              function toggleTheme() {{
                const isDark = localStorage.getItem("darkmode") === "true";
                setTheme(!isDark);
              }}
              window.onload = () => {{
                const isDark = localStorage.getItem("darkmode") === "true";
                setTheme(isDark);
              }};

              async function deleteFile(filename) {{
                if (!confirm("Are you sure you want to delete " + filename + "?")) return;
                let res = await fetch("/delete", {{
                  method: "POST",
                  headers: {{ "Content-Type": "application/json" }},
                  body: JSON.stringify({{ "filename": filename }})
                }});
                let data = await res.json();
                alert(data.message);
                location.reload();
              }}

              function searchFiles() {{
                let input = document.querySelector(".search-bar").value.toLowerCase();
                document.querySelectorAll(".file-card").forEach(card => {{
                  card.style.display = card.dataset.name.includes(input) ? "flex" : "none";
                }});
              }}

              function sortFiles(type) {{
                let list = document.getElementById("file-list");
                let cards = Array.from(list.children);
                cards.sort((a,b) => {{
                  if (type=="name") return a.dataset.name.localeCompare(b.dataset.name);
                  if (type=="size") return b.dataset.size - a.dataset.size;
                  if (type=="date") return b.dataset.date - a.dataset.date;
                }});
                list.innerHTML="";
                cards.forEach(c=>list.appendChild(c));
              }}
            </script>
        </body>
        </html>
        """
        return html.encode("utf-8")

    def do_GET(self):
        if self.path == "/" or self.path == "/files":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self.list_files())
        elif self.path.startswith("/files/"):
            file_path = os.path.join(UPLOAD_DIR, urllib.parse.unquote(self.path[7:]))
            if os.path.exists(file_path):
                self.send_response(200)
                self.send_header("Content-Disposition", "attachment")
                self.send_header("Content-Length", str(os.path.getsize(file_path)))
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "File Not Found")
        elif self.path == "/upload":
            html = """
            <html>
            <head>
            <meta charset="UTF-8">
            <title>Upload Files</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: var(--bg);
                    color: var(--text);
                    text-align: center;
                    padding: 40px;
                    transition: background 0.3s, color 0.3s;
                }
                h2 { color: var(--text); }
                input[type=file], button {
                    margin: 10px;
                    padding: 12px;
                    border-radius: 10px;
                    border: 1px solid #ccc;
                }
                button {
                    background: #28a745;
                    color: white;
                    font-weight: bold;
                    border: none;
                    cursor: pointer;
                }
                button:hover { background: #218838; }
                .drop-zone {
                    margin: 20px auto;
                    padding: 40px;
                    border: 2px dashed #aaa;
                    border-radius: 15px;
                    background: #fafafa;
                    color: #666;
                    cursor: pointer;
                }
                .drop-zone.dragover {
                    background: #dff0d8;
                    border-color: #28a745;
                }
                .progress-container {
                    width: 80%;
                    margin: 10px auto;
                }
                .progress {
                    width: 100%;
                    background: #ddd;
                    border-radius: 10px;
                    height: 25px;
                    overflow: hidden;
                    margin-bottom: 5px;
                }
                .progress-bar {
                    height: 100%;
                    width: 0;
                    background: #28a745;
                    text-align: center;
                    color: white;
                    line-height: 25px;
                }
                .theme-toggle {
                    margin: 20px;
                    padding: 10px 18px;
                    background: #333;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    cursor: pointer;
                }
            </style>
            </head>
            <body>
                <h2>⬆️ Upload Files</h2>
                <input type="file" id="fileInput" multiple><br>
                <div class="drop-zone" id="dropZone">Drag & Drop Files Here</div>
                <button onclick="uploadFiles()">Upload</button>
                <div id="progressArea"></div>
                <br>
                <a href="/"><button>⬅ Back</button></a>
                <br>
                <button class="theme-toggle" onclick="toggleTheme()">🌙 Dark Mode</button>
                <script>
                  const root = document.documentElement;
                  function setTheme(dark) {
                    if (dark) {
                      root.style.setProperty('--bg', '#121212');
                      root.style.setProperty('--text', '#f1f1f1');
                      document.querySelector('.theme-toggle').innerText = "☀️ Light Mode";
                    } else {
                      root.style.setProperty('--bg', '#f4f6f9');
                      root.style.setProperty('--text', '#222');
                      document.querySelector('.theme-toggle').innerText = "🌙 Dark Mode";
                    }
                    localStorage.setItem("darkmode", dark);
                  }
                  function toggleTheme() {
                    const isDark = localStorage.getItem("darkmode") === "true";
                    setTheme(!isDark);
                  }
                  window.onload = () => {
                    const isDark = localStorage.getItem("darkmode") === "true";
                    setTheme(isDark);
                  };

                  function uploadFiles(files=null) {
                    files = files || document.getElementById("fileInput").files;
                    if (!files.length) { alert("Select files first!"); return; }
                    let progressArea = document.getElementById("progressArea");
                    progressArea.innerHTML = "";
                    [...files].forEach(file => {
                        let container = document.createElement("div");
                        container.className="progress-container";
                        container.innerHTML = `<b>${file.name}</b>
                          <div class="progress"><div class="progress-bar" id="bar-${file.name.replace(/[^a-z0-9]/gi,'')}">0%</div></div>`;
                        progressArea.appendChild(container);

                        const xhr = new XMLHttpRequest();
                        xhr.upload.addEventListener("progress", e => {
                          if (e.lengthComputable) {
                            let percent = (e.loaded / e.total) * 100;
                            let bar = document.getElementById("bar-"+file.name.replace(/[^a-z0-9]/gi,''));
                            bar.style.width = percent + "%";
                            bar.innerText = Math.round(percent) + "%";
                          }
                        });
                        xhr.onload = () => { if (xhr.status==200) console.log(file.name+" uploaded"); };
                        xhr.open("POST","/upload");
                        const formData = new FormData();
                        formData.append("file",file);
                        xhr.send(formData);
                    });
                  }

                  let dropZone = document.getElementById("dropZone");
                  dropZone.addEventListener("dragover", e => {
                    e.preventDefault(); dropZone.classList.add("dragover");
                  });
                  dropZone.addEventListener("dragleave", e => {
                    dropZone.classList.remove("dragover");
                  });
                  dropZone.addEventListener("drop", e => {
                    e.preventDefault(); dropZone.classList.remove("dragover");
                    uploadFiles(e.dataTransfer.files);
                  });
                </script>
            </body>
            </html>
            """
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_error(404, "Page Not Found")

    def do_POST(self):
        if self.path == "/upload":
            ctype = self.headers['Content-Type']
            if not ctype.startswith('multipart/form-data'):
                self.send_error(400, "Bad Request")
                return
            boundary = ctype.split("=")[1].encode()
            remainbytes = int(self.headers['Content-Length'])
            line = self.rfile.readline(); remainbytes -= len(line)
            if not boundary in line:
                self.send_error(400, "Content does not start with boundary"); return
            line = self.rfile.readline(); remainbytes -= len(line)
            filename = line.decode().split("filename=")[1].strip().strip('"')
            filepath = os.path.join(UPLOAD_DIR, filename)
            line = self.rfile.readline(); remainbytes -= len(line)
            line = self.rfile.readline(); remainbytes -= len(line)
            with open(filepath, "wb") as f:
                preline = self.rfile.readline(); remainbytes -= len(preline)
                while remainbytes > 0:
                    line = self.rfile.readline(); remainbytes -= len(line)
                    if boundary in line:
                        preline = preline.rstrip(b"\r\n")
                        f.write(preline); break
                    else:
                        f.write(preline); preline = line
            self.send_response(200); self.end_headers()

        elif self.path == "/delete":
            length = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(length))
            filename = urllib.parse.unquote(data.get("filename", ""))
            filepath = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                message = f"{filename} deleted successfully"
            else:
                message = f"{filename} not found"
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"message": message}).encode())

with socketserver.TCPServer((HOST, PORT), MyHTTPRequestHandler) as httpd:
    print(f"Serving at http://127.0.0.1:{PORT}")
    httpd.serve_forever()
