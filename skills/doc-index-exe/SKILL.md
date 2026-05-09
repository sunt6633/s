# doc-index-exe

---
name: doc-index-exe
description: 相对路径文档索引工具（单文件 EXE 版）。使用 PyInstaller 打包成单个 EXE 文件，放到其他电脑上直接运行即可扫描所在目录并打开搜索界面。无需安装 Python，完全便携式。
---

# 相对路径文档索引工具（单文件 EXE 版）

使用 PyInstaller 打包成单个 EXE 文件，放到其他电脑上直接运行即可。

## 功能特点

- 单文件 EXE，无需安装 Python
- 自动扫描 EXE 所在目录
- 生成临时 HTML 并在浏览器中打开
- 完全便携式，可放到其他电脑使用
- 支持搜索、筛选、分页、列表/网格视图

## 制作方法

### 1. 创建 Python 脚本

将以下代码保存为 `doc_index_single.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单文件文档索引工具 - 便携式版本
运行后自动扫描同目录，生成索引并在浏览器中打开
"""

import os
import json
import time
import hashlib
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path

EXT_MAP = {
    ".docx": "Word", ".doc": "Word",
    ".xlsx": "Excel", ".xls": "Excel", ".csv": "Excel",
    ".pptx": "PPT", ".ppt": "PPT",
    ".pdf": "PDF",
    ".wps": "WPS", ".wpt": "WPS",
    ".txt": "文本", ".md": "文本",
    ".png": "图片", ".jpg": "图片", ".jpeg": "图片", ".gif": "图片", ".bmp": "图片", ".webp": "图片",
    ".mp4": "视频", ".avi": "视频", ".mkv": "视频", ".mov": "视频",
    ".mp3": "音频", ".wav": "音频",
    ".zip": "压缩包", ".rar": "压缩包", ".7z": "压缩包",
    ".exe": "程序",
    ".psd": "设计", ".ai": "设计",
    ".dwg": "CAD",
}

SKIP_DIRS = {
    "__pycache__", ".git", "node_modules", ".workbuddy",
    "360js Files", "KingsoftData", "Tencent Files",
    "WPS Cloud Files", "WeChat Files"
}

def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f}KB"
    else:
        return f"{size_bytes/1024/1024:.1f}MB"

def scan_files(root_dir):
    files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        rel_dir = os.path.relpath(dirpath, root_dir)
        parts = rel_dir.replace("\\", "/").split("/")
        skip = any(p in SKIP_DIRS for p in parts)
        if skip:
            dirnames.clear()
            continue
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in EXT_MAP:
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                stat = os.stat(fpath)
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                size = format_size(stat.st_size)
                size_bytes = stat.st_size
            except Exception:
                continue

            rel_path = os.path.relpath(fpath, root_dir).replace("\\", "/")
            fid = hashlib.md5(rel_path.encode("utf-8")).hexdigest()[:8]
            parent = os.path.relpath(dirpath, root_dir).replace("\\", "/")
            if parent == ".":
                parent = "根目录"

            files.append({
                "id": fid,
                "name": fname,
                "path": fpath.replace("\\", "/"),
                "rel": rel_path,
                "dir": parent,
                "ext": ext,
                "type": EXT_MAP.get(ext, "其他"),
                "size": size,
                "size_bytes": size_bytes,
                "mtime": mtime,
            })

    files.sort(key=lambda x: x["mtime"], reverse=True)
    return files

def build_html(files, scan_time, root_dir):
    data_js = json.dumps({
        "scan_time": scan_time,
        "total": len(files),
        "root_dir": root_dir,
        "files": files
    }, ensure_ascii=False, separators=(',', ':'))

    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>文档索引 · 便携式</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #22263a;
    --border: #2e3250;
    --accent: #4f7fff;
    --accent2: #7c5cfc;
    --text: #e8ecf4;
    --text2: #8b90a8;
    --text3: #5c6180;
    --radius: 10px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: var(--bg); color: var(--text);
    min-height: 100vh; display: flex; flex-direction: column;
  }
  header {
    background: linear-gradient(135deg, #1a1d27 0%, #14172a 100%);
    border-bottom: 1px solid var(--border);
    padding: 16px 28px; display: flex; align-items: center; gap: 20px;
    position: sticky; top: 0; z-index: 100;
  }
  .logo { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
  .logo-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 9px; display: flex; align-items: center; justify-content: center; font-size: 18px;
  }
  .logo-text { font-size: 16px; font-weight: 700; }
  .logo-sub  { font-size: 11px; color: var(--text3); margin-top: 1px; }
  .search-wrap { flex: 1; position: relative; max-width: 660px; }
  .search-wrap svg { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); opacity:.4; pointer-events:none; }
  #searchInput {
    width: 100%; background: var(--surface2); border: 1.5px solid var(--border);
    border-radius: 50px; padding: 10px 42px 10px 42px;
    color: var(--text); font-size: 14px; outline: none; transition: border-color .2s, box-shadow .2s;
  }
  #searchInput::placeholder { color: var(--text3); }
  #searchInput:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(79,127,255,.15); }
  .search-clear {
    position: absolute; right: 14px; top: 50%; transform: translateY(-50%);
    background: none; border: none; color: var(--text3); cursor: pointer; font-size: 15px; display: none;
  }
  .search-clear.visible { display: block; }
  .header-right { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
  .btn {
    display: flex; align-items: center; gap: 6px;
    background: var(--surface2); border: 1px solid var(--border);
    color: var(--text2); border-radius: 8px; padding: 7px 13px;
    font-size: 13px; cursor: pointer; transition: all .2s; white-space: nowrap;
  }
  .btn:hover { background: var(--surface); border-color: var(--accent); color: var(--accent); }
  #scanTime { font-size: 12px; color: var(--text3); white-space: nowrap; }
  main { display: flex; flex: 1; overflow: hidden; }
  aside {
    width: 215px; flex-shrink: 0; background: var(--surface);
    border-right: 1px solid var(--border); padding: 14px 0;
    overflow-y: auto; height: calc(100vh - 69px); position: sticky; top: 69px;
  }
  .side-section { padding: 0 10px; margin-bottom: 6px; }
  .side-label { font-size: 10px; color: var(--text3); text-transform: uppercase; letter-spacing: 1px; padding: 4px 8px 7px; }
  .side-item {
    display: flex; align-items: center; justify-content: space-between;
    padding: 6px 10px; border-radius: 7px; cursor: pointer;
    font-size: 13px; color: var(--text2); transition: all .15s; margin-bottom: 2px;
  }
  .side-item:hover { background: var(--surface2); color: var(--text); }
  .side-item.active { background: rgba(79,127,255,.18); color: var(--accent); font-weight: 600; }
  .side-item .badge {
    background: var(--surface2); color: var(--text3);
    font-size: 11px; border-radius: 20px; padding: 1px 7px; min-width: 24px; text-align: center;
  }
  .side-item.active .badge { background: rgba(79,127,255,.3); color: var(--accent); }
  .side-divider { height: 1px; background: var(--border); margin: 6px 10px; }
  .content { flex: 1; overflow-y: auto; height: calc(100vh - 69px); padding: 18px 22px; }
  .stats-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
  .stat-chip {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 20px; padding: 4px 12px; font-size: 12px; color: var(--text2);
    display: flex; align-items: center; gap: 5px;
  }
  .stat-chip strong { color: var(--text); font-size: 13px; }
  .toolbar { display: flex; align-items: center; gap: 7px; margin-bottom: 12px; }
  .sort-btn {
    background: none; border: 1px solid var(--border); color: var(--text3);
    border-radius: 6px; padding: 4px 10px; font-size: 12px; cursor: pointer; transition: all .15s;
  }
  .sort-btn:hover { color: var(--text); border-color: var(--text3); }
  .sort-btn.active { border-color: var(--accent); color: var(--accent); background: rgba(79,127,255,.08); }
  .view-toggle { margin-left: auto; display: flex; gap: 4px; }
  .view-btn {
    background: none; border: 1px solid var(--border); color: var(--text3);
    border-radius: 6px; padding: 5px 8px; cursor: pointer; transition: all .15s; display: flex; align-items: center;
  }
  .view-btn.active { border-color: var(--accent); color: var(--accent); }
  #fileList { display: flex; flex-direction: column; gap: 4px; }
  #fileList.grid-view { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 10px; }
  .file-item {
    display: flex; align-items: center; gap: 12px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 9px 13px;
    cursor: pointer; transition: all .15s; text-decoration: none; color: inherit;
    position: relative; overflow: hidden;
  }
  .file-item::before {
    content: ''; position: absolute; left: 0; top: 0; bottom: 0;
    width: 3px; background: transparent; transition: background .15s;
  }
  .file-item:hover { background: var(--surface2); border-color: var(--accent); transform: translateX(2px); }
  .file-item:hover::before { background: var(--accent); }
  .grid-view .file-item { flex-direction: column; align-items: flex-start; padding: 13px; }
  .grid-view .file-item:hover { transform: translateY(-2px); }
  .grid-view .file-item::before { width: 100%; height: 3px; top: 0; bottom: auto; }
  .file-icon {
    width: 36px; height: 36px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center; font-size: 19px; flex-shrink: 0;
  }
  .grid-view .file-icon { width: 42px; height: 42px; font-size: 22px; margin-bottom: 6px; }
  .file-info { flex: 1; min-width: 0; }
  .file-name {
    font-size: 13.5px; font-weight: 500; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis; margin-bottom: 3px;
  }
  .grid-view .file-name { white-space: normal; word-break: break-all; font-size: 12.5px; line-height: 1.4; max-height: 2.8em; overflow: hidden; }
  .file-meta { font-size: 11px; color: var(--text3); display: flex; gap: 10px; flex-wrap: wrap; }
  .file-type-tag {
    flex-shrink: 0; font-size: 10px; font-weight: 700; letter-spacing: .5px;
    padding: 2px 7px; border-radius: 4px;
  }
  .type-word   { background: rgba(0,122,255,.15); color: #4d9eff; }
  .type-excel  { background: rgba(40,200,120,.15); color: #40cc80; }
  .type-ppt    { background: rgba(255,120,50,.15);  color: #ff8844; }
  .type-pdf    { background: rgba(255,60,60,.15);   color: #ff5f57; }
  .type-wps    { background: rgba(79,127,255,.15);  color: #6a8fff; }
  .type-image  { background: rgba(255,190,0,.15);   color: #ffbd2e; }
  .type-video  { background: rgba(130,60,220,.15);  color: #a070f0; }
  .type-audio  { background: rgba(0,200,200,.15);   color: #30d0d0; }
  .type-text   { background: rgba(180,180,180,.15); color: #a0a8b8; }
  .type-zip    { background: rgba(255,140,0,.15);   color: #ff9900; }
  .type-other  { background: rgba(100,100,140,.15); color: #8888aa; }
  .icon-word   { background: rgba(0,122,255,.1); }
  .icon-excel  { background: rgba(40,200,120,.1); }
  .icon-ppt    { background: rgba(255,120,50,.1);  }
  .icon-pdf    { background: rgba(255,60,60,.1);   }
  .icon-wps    { background: rgba(79,127,255,.1);  }
  .icon-image  { background: rgba(255,190,0,.1);   }
  .icon-video  { background: rgba(130,60,220,.1);  }
  .icon-audio  { background: rgba(0,200,200,.1);   }
  .icon-text   { background: rgba(180,180,180,.1); }
  .icon-zip    { background: rgba(255,140,0,.1);   }
  .icon-other  { background: rgba(100,100,140,.1); }
  mark { background: rgba(79,127,255,.3); color: var(--accent); border-radius: 2px; padding: 0 1px; }
  .empty { text-align: center; padding: 80px 20px; color: var(--text3); display: none; }
  .empty h3 { font-size: 16px; color: var(--text2); margin-bottom: 6px; }
  .pagination { display: flex; align-items: center; justify-content: center; gap: 6px; margin-top: 20px; padding-bottom: 24px; }
  .page-btn {
    background: var(--surface); border: 1px solid var(--border);
    color: var(--text2); border-radius: 6px; padding: 5px 11px;
    font-size: 13px; cursor: pointer; transition: all .15s;
  }
  .page-btn:hover { border-color: var(--accent); color: var(--accent); }
  .page-btn.active { background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 600; }
  .page-btn:disabled { opacity: .3; pointer-events: none; }
  .toast {
    position: fixed; bottom: 20px; right: 20px;
    background: var(--surface2); border: 1px solid var(--border);
    color: var(--text); padding: 10px 16px; border-radius: 9px;
    font-size: 13px; box-shadow: 0 8px 24px rgba(0,0,0,.4);
    transform: translateY(60px); opacity: 0; transition: all .3s; z-index: 999;
  }
  .toast.show { transform: translateY(0); opacity: 1; }
  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--text3); }
</style>
</head>
<body>
<header>
  <div class="logo">
    <div class="logo-icon">📂</div>
    <div>
      <div class="logo-text">文档索引</div>
      <div class="logo-sub">便携式版本</div>
    </div>
  </div>
  <div class="search-wrap">
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>
    <input type="text" id="searchInput" placeholder="搜索文件名、目录…" autocomplete="off" spellcheck="false">
    <button class="search-clear" id="searchClear" title="清空">✕</button>
  </div>
  <div class="header-right">
    <span id="scanTime"></span>
    <button class="btn" onclick="location.reload()">
      🔄 刷新
    </button>
  </div>
</header>
<main>
  <aside id="sidebar"></aside>
  <div class="content">
    <div class="stats-bar" id="statsBar"></div>
    <div class="toolbar">
      <span style="font-size:12px;color:var(--text3);margin-right:2px">排序:</span>
      <button class="sort-btn active" onclick="setSort('mtime',this)">最近修改</button>
      <button class="sort-btn" onclick="setSort('name',this)">文件名</button>
      <button class="sort-btn" onclick="setSort('size',this)">大小</button>
      <div class="view-toggle">
        <button class="view-btn active" id="listViewBtn" onclick="setView('list')" title="列表">☰</button>
        <button class="view-btn" id="gridViewBtn" onclick="setView('grid')" title="网格">▦</button>
      </div>
    </div>
    <div id="fileList"></div>
    <div class="empty" id="emptyState">
      <div style="font-size:48px;margin-bottom:12px;opacity:.3">🔍</div>
      <h3>未找到匹配文件</h3>
      <p style="margin-top:6px">换个关键词试试？</p>
    </div>
    <div class="pagination" id="pagination"></div>
  </div>
</main>
<div class="toast" id="toast"></div>
<script>
const INDEX_DATA = ''' + data_js + ''';

const PAGE_SIZE = 60;
const TYPE_ICON = {
  "Word":"📄","Excel":"📊","PPT":"📑","PDF":"📕","WPS":"📝",
  "图片":"🖼️","视频":"🎬","音频":"🎵","文本":"📃","压缩包":"📦",
  "程序":"⚙️","设计":"🎨","CAD":"📐","其他":"📎"
};
const TYPE_CLASS = {
  "Word":"word","Excel":"excel","PPT":"ppt","PDF":"pdf","WPS":"wps",
  "图片":"image","视频":"video","音频":"audio","文本":"text",
  "压缩包":"zip","程序":"other","设计":"other","CAD":"other","其他":"other"
};

let allFiles = INDEX_DATA.files || [];
let filteredFiles = [];
let currentPage = 1;
let currentSort = "mtime";
let currentFilter = "all";
let currentView = "list";
let searchQuery = "";

function init() {
  document.getElementById("scanTime").textContent = "索引: " + INDEX_DATA.scan_time + " | " + INDEX_DATA.root_dir;
  buildSidebar();
  renderStats();
  applyFilter();
  showToast("✅ 已加载 " + allFiles.length + " 个文件");
}

function buildSidebar() {
  const typeCounts = {}, dirCounts = {};
  for (const f of allFiles) {
    typeCounts[f.type] = (typeCounts[f.type]||0) + 1;
    const top = f.dir.split("/")[0];
    dirCounts[top] = (dirCounts[top]||0) + 1;
  }
  const typeOrder = ["Word","Excel","PPT","PDF","WPS","图片","视频","音频","文本","压缩包","程序","设计","CAD","其他"];
  let html = `<div class="side-section"><div class="side-label">文件类型</div>
    <div class="side-item ${currentFilter==='all'?'active':''}" onclick="setFilter('all')">
      <span>🗂️ 全部文件</span><span class="badge">${allFiles.length}</span>
    </div>`;
  for (const t of typeOrder) {
    if (!typeCounts[t]) continue;
    html += `<div class="side-item ${currentFilter===t?'active':''}" onclick="setFilter('${t}')">
      <span>${TYPE_ICON[t]||'📎'} ${t}</span><span class="badge">${typeCounts[t]}</span>
    </div>`;
  }
  const topDirs = Object.entries(dirCounts).filter(([d])=>d!=="根目录").sort((a,b)=>b[1]-a[1]).slice(0,18);
  if (topDirs.length) {
    html += `</div><div class="side-divider"></div><div class="side-section"><div class="side-label">文件夹</div>`;
    if (dirCounts["根目录"]) {
      html += `<div class="side-item ${currentFilter==='根目录'?'active':''}" onclick="setFilter('根目录')">
        <span>📁 根目录</span><span class="badge">${dirCounts["根目录"]}</span>
      </div>`;
    }
    for (const [dir, cnt] of topDirs) {
      const id = "dir:"+dir;
      const label = dir.length>13 ? dir.slice(0,13)+"…" : dir;
      html += `<div class="side-item ${currentFilter===id?'active':''}" onclick="setFilter('${id.replace(/'/g,"\\'")}')">
        <span title="${dir}">📁 ${label}</span><span class="badge">${cnt}</span>
      </div>`;
    }
  }
  html += `</div>`;
  document.getElementById("sidebar").innerHTML = html;
}

function setFilter(f) { currentFilter=f; currentPage=1; buildSidebar(); applyFilter(); }
function setSort(s,btn) {
  currentSort=s; currentPage=1;
  document.querySelectorAll(".sort-btn").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active");
  applyFilter();
}
function setView(v) {
  currentView=v;
  document.getElementById("fileList").className = v==="grid"?"grid-view":"";
  document.getElementById("listViewBtn").classList.toggle("active",v==="list");
  document.getElementById("gridViewBtn").classList.toggle("active",v==="grid");
  renderPage();
}

function applyFilter() {
  const q = searchQuery.toLowerCase().trim();
  filteredFiles = allFiles.filter(f => {
    if (currentFilter !== "all") {
      if (currentFilter.startsWith("dir:")) {
        if (f.dir.split("/")[0] !== currentFilter.slice(4)) return false;
      } else if (currentFilter === "根目录") {
        if (f.dir !== "根目录") return false;
      } else {
        if (f.type !== currentFilter) return false;
      }
    }
    if (q) return f.name.toLowerCase().includes(q) || f.dir.toLowerCase().includes(q);
    return true;
  });
  if (currentSort==="name") filteredFiles.sort((a,b)=>a.name.localeCompare(b.name,"zh"));
  else if (currentSort==="size") filteredFiles.sort((a,b)=>b.size_bytes-a.size_bytes);
  else filteredFiles.sort((a,b)=>b.mtime.localeCompare(a.mtime));
  renderStats(); renderPage();
}

function renderStats() {
  const tc={};
  for (const f of filteredFiles) tc[f.type]=(tc[f.type]||0)+1;
  const top = Object.entries(tc).sort((a,b)=>b[1]-a[1]).slice(0,4);
  let html = `<div class="stat-chip"><strong>${filteredFiles.length}</strong> 个文件</div>`;
  for (const [t,c] of top)
    html += `<div class="stat-chip">${TYPE_ICON[t]||''} ${t} <strong>${c}</strong></div>`;
  document.getElementById("statsBar").innerHTML = html;
}

function renderPage() {
  const list = document.getElementById("fileList");
  const empty = document.getElementById("emptyState");
  if (!filteredFiles.length) { list.innerHTML=""; empty.style.display="block"; document.getElementById("pagination").innerHTML=""; return; }
  empty.style.display="none";
  const total=filteredFiles.length, totalPages=Math.ceil(total/PAGE_SIZE);
  if (currentPage>totalPages) currentPage=totalPages;
  const start=(currentPage-1)*PAGE_SIZE;
  const q=searchQuery.toLowerCase().trim();
  list.innerHTML = filteredFiles.slice(start,start+PAGE_SIZE).map(f=>renderFile(f,q)).join("");
  renderPagination(totalPages);
}

function hi(text,q) {
  if (!q) return escHtml(text);
  const i=text.toLowerCase().indexOf(q);
  if (i<0) return escHtml(text);
  return escHtml(text.slice(0,i))+"<mark>"+escHtml(text.slice(i,i+q.length))+"</mark>"+escHtml(text.slice(i+q.length));
}
function escHtml(s){ return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }

function renderFile(f,q) {
  const tc=TYPE_CLASS[f.type]||"other";
  const icon=TYPE_ICON[f.type]||"📎";
  const fpath = f.path.replace(/\\/g,"/");
  return `<div class="file-item" onclick="openFile('${fpath.replace(/'/g,"\\'")}')">
    <div class="file-icon icon-${tc}">${icon}</div>
    <div class="file-info">
      <div class="file-name">${hi(f.name,q)}</div>
      <div class="file-meta">
        <span>📁 ${hi(f.dir,q)}</span>
        <span>🕐 ${f.mtime}</span>
        <span>💾 ${f.size}</span>
      </div>
    </div>
    <span class="file-type-tag type-${tc}">${f.type}</span>
  </div>`;
}

function openFile(path) {
  const uri = "file:///" + path.replace(/ /g,"%20");
  window.open(uri, "_blank");
}

function renderPagination(totalPages) {
  if (totalPages<=1) { document.getElementById("pagination").innerHTML=""; return; }
  let btns = `<button class="page-btn" onclick="goPage(${currentPage-1})" ${currentPage===1?"disabled":""}>‹ 上页</button>`;
  let s=Math.max(1,currentPage-2), e=Math.min(totalPages,s+4);
  if (e-s<4) s=Math.max(1,e-4);
  if (s>1) btns+=`<button class="page-btn" onclick="goPage(1)">1</button>`;
  if (s>2) btns+=`<span style="color:var(--text3);padding:0 4px">…</span>`;
  for (let i=s;i<=e;i++) btns+=`<button class="page-btn ${i===currentPage?'active':''}" onclick="goPage(${i})">${i}</button>`;
  if (e<totalPages-1) btns+=`<span style="color:var(--text3);padding:0 4px">…</span>`;
  if (e<totalPages) btns+=`<button class="page-btn" onclick="goPage(${totalPages})">${totalPages}</button>`;
  btns+=`<button class="page-btn" onclick="goPage(${currentPage+1})" ${currentPage===totalPages?"disabled":""}>下页 ›</button>`;
  document.getElementById("pagination").innerHTML = btns;
}
function goPage(p) {
  currentPage=p; renderPage();
  document.querySelector(".content").scrollTo({top:0,behavior:"smooth"});
}

const si=document.getElementById("searchInput"), sc=document.getElementById("searchClear");
let st;
si.addEventListener("input",()=>{
  searchQuery=si.value;
  sc.classList.toggle("visible",searchQuery.length>0);
  clearTimeout(st); st=setTimeout(()=>{currentPage=1;applyFilter();},180);
});
si.addEventListener("keydown",e=>{if(e.key==="Escape")clearSearch();});
sc.addEventListener("click",clearSearch);
function clearSearch(){si.value="";searchQuery="";sc.classList.remove("visible");currentPage=1;applyFilter();si.focus();}
document.addEventListener("keydown",e=>{if((e.ctrlKey||e.metaKey)&&e.key==="f"){e.preventDefault();si.focus();si.select();}});

function showToast(msg,dur=3000){
  const t=document.getElementById("toast");
  t.textContent=msg; t.classList.add("show");
  setTimeout(()=>t.classList.remove("show"),dur);
}

init();
</script>
</body>
</html>'''
    return html

def main():
    print("=" * 60)
    print("📂 文档索引工具 - 便携式版本")
    print("=" * 60)
    print()
    
    # 获取 EXE 所在目录
    if getattr(sys, 'frozen', False):
        # 打包成 EXE 后
        root_dir = os.path.dirname(sys.executable)
    else:
        # 作为脚本运行时
        root_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"📍 扫描目录: {root_dir}")
    print()
    
    # 扫描文件
    print("🔍 正在扫描文件...")
    t0 = time.time()
    files = scan_files(root_dir)
    t1 = time.time()
    
    print(f"✅ 扫描完成！共索引 {len(files)} 个文件")
    print(f"⏱️  耗时 {t1-t0:.1f} 秒")
    print()
    
    # 生成 HTML
    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = build_html(files, scan_time, root_dir)
    
    # 保存到临时文件
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.html', delete=False) as f:
        f.write(html)
        temp_path = f.name
    
    print(f"📄 已生成索引文件")
    print()
    
    # 打开浏览器
    print("🌐 正在打开浏览器...")
    webbrowser.open(f"file:///{temp_path}")
    print()
    print("✅ 完成！")
    print()
    print("提示：关闭此窗口前请先关闭浏览器中的索引页面")
    print("临时文件位置:")
    print(temp_path)
    print()
    print("程序将在 5 秒后自动退出...")
    time.sleep(5)

if __name__ == "__main__":
    import sys
    main()
```

### 2. 安装 PyInstaller

```bash
pip install pyinstaller
```

### 3. 打包成单文件 EXE

```bash
pyinstaller --onefile --noconsole --name 文档索引工具 doc_index_single.py
```

打包完成后，EXE 文件在 `dist/文档索引工具.exe`。

### 4. 使用

1. 将 `文档索引工具.exe` 复制到任意文件夹
2. 双击运行
3. 自动扫描同目录下的所有文件
4. 自动在浏览器中打开搜索界面

## 注意事项

- EXE 文件大小约 6-7MB（包含 Python 解释器和依赖）
- 首次运行会扫描所有文件，耗时较长
- 临时 HTML 文件会在系统临时目录中生成
- 关闭程序后临时文件会自动清理

## 移植方法

直接将 `文档索引工具.exe` 复制到目标电脑的任意位置，双击运行即可。
