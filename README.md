# 🧠 JASS Visual Knowledge Map

### A local-first visual workspace for exploring files, knowledge, projects and relationships.

**JASS Visual Knowledge Map** is a PySide6 desktop application for turning collections of files and information into an interactive visual knowledge workspace.

Instead of looking at information as a flat list of folders and files, the application represents knowledge as **nodes and relationships** that can be explored visually.

> **See your knowledge as a map — not just a folder.**

---

## ✨ Current Version

**v0.3 — Visual Previews**

The current version builds on the original visual file map and introduces a persistent SQLite knowledge workspace together with interactive visual previews for image nodes.

---

## 🎯 Vision

Modern information collections are often scattered across:

- Documents
- Images
- Datasets
- Code
- Databases
- Projects
- Research material
- Language resources
- AI models and datasets
- Personal notes

JASS Visual Knowledge Map explores a different approach:

```text
Files
  │
  ▼
Knowledge Nodes
  │
  ├── Documents
  ├── Datasets
  ├── Images
  ├── Audio
  ├── Video
  ├── Code
  ├── Databases
  ├── Projects
  ├── Concepts
  └── Folders
       │
       ▼
Relationships
       │
       ▼
Visual Knowledge Map
```

The goal is to make relationships between information easier to see, understand and navigate.

---

# 🚀 Features

## 🧠 Visual Knowledge Graph

Information is represented as movable visual nodes.

Nodes can represent:

- 📄 Documents
- 📊 Datasets
- 🖼️ Images
- 🎵 Audio
- 🎬 Video
- 🐍 Code
- 🗄️ Databases
- 📦 Projects
- 💡 Concepts
- 📁 Folders

Nodes can be moved around the canvas to create a visual arrangement that makes sense to you.

---

## 🔗 Relationships

Knowledge becomes more useful when relationships are explicit.

The application supports relationships such as:

- **Contains**
- **Uses**
- **Related to**
- **Depends on**
- **References**
- **Derived from**
- **Part of**

For example:

```text
Project Athena
      │
      ├── Uses ──────────► SQLite
      │
      ├── References ────► Documents
      │
      └── Related to ────► Hugging Face
```

Relationships are stored in the workspace database and displayed visually on the map.

---

# 🖼️ Visual Image Previews

Version **0.3** introduces visual previews for image nodes.

Hovering over an image node can display:

- Image thumbnail
- Filename
- Image dimensions
- File size

The original image file is never modified.

This visual-preview concept can eventually be extended to other media types.

---

# 💾 Persistent Knowledge Workspaces

Knowledge maps are stored locally using **SQLite**.

Workspace files use the:

```text
.jvkm
```

extension.

A workspace contains:

```text
Workspace
│
├── Nodes
├── Relationships
├── Notes
├── Metadata
└── Node Positions
```

This means your knowledge map can be closed and reopened without losing its structure.

---

# 📁 Folder Import

A folder can be imported into the workspace.

The application scans files and attempts to classify them according to their file type.

For example:

```text
My Research/
│
├── paper.pdf       → Document
├── corpus.csv      → Dataset
├── photograph.jpg  → Image
├── analysis.py     → Code
├── database.db     → Database
└── recording.wav   → Audio
```

The imported information becomes part of the visual workspace.

---

# 🔍 Search & Filtering

The workspace provides tools for finding nodes quickly.

### Search

Search by:

- Node name
- File name
- Location/path

### Filtering

Filter the visual map by node type:

```text
All Types
Documents
Datasets
Images
Audio
Video
Code
Database
Projects
Concepts
Folders
```

---

# 📝 Knowledge Inspector

Selecting a node opens an inspector containing information such as:

```text
Project Athena

Type
Project

Location
C:\Projects\Project-Athena

Notes
Personal knowledge and intelligence system
```

The inspector provides a central place for:

- Node information
- Location
- Notes
- Relationships
- Editing
- Deletion

---

# ✏️ Editable Knowledge Nodes

Nodes can be created and edited directly inside the application.

A node can contain:

- Title
- Type
- Location
- Notes
- Metadata

This means the map doesn't have to represent only files.

You can create conceptual knowledge nodes such as:

```text
Python
    │
    ├── related to → PySide6
    ├── used by → Project Athena
    └── used by → HRTK
```

---

# 🖱️ Interactive Canvas

The graph is designed as an interactive workspace.

Current interactions include:

- Move nodes
- Select nodes
- Zoom
- Search
- Filter
- Create relationships
- Inspect nodes

The visual layout can therefore evolve as your knowledge grows.

---

# 🖼️ Export

The current workspace can be exported as a PNG image.

This makes it possible to create:

- Knowledge-map snapshots
- Project diagrams
- Research diagrams
- Documentation graphics
- Presentation material

---

# 🛠️ Technology

JASS Visual Knowledge Map is deliberately built with lightweight technologies.

| Technology | Purpose |
|---|---|
| **Python** | Application logic |
| **PySide6** | Desktop GUI |
| **Qt Graphics View** | Interactive visual canvas |
| **SQLite** | Local workspace persistence |
| **Pathlib** | File and folder handling |

No cloud service is required.

No external database server is required.

---

# 🔐 Local-First Philosophy

JASS Visual Knowledge Map follows the broader JASS Digital Lab philosophy:

> **Local first. Practical first. Privacy first.**

The application is designed to work with information stored on your own computer.

Your workspace database is local.

Your files remain where they are.

The application does not require uploading your knowledge collection to a remote service.

---

# 🧩 Architecture

The current architecture is intentionally simple:

```text
                 JASS Visual Knowledge Map
                           │
             ┌─────────────┴─────────────┐
             │                           │
          PySide6                     SQLite
             │                           │
       Visual Canvas              Knowledge Data
             │                           │
       ┌─────┴─────┐             ┌───────┴──────┐
       │           │             │              │
     Nodes    Relationships    Nodes       Relationships
       │           │
       └───────────┴───────────────┐
                                   │
                           Visual Workspace
```

The separation between the visual interface and SQLite persistence provides a foundation for future expansion.

---

# 🔮 Roadmap

The current version is intentionally a foundation.

## v0.4 — Richer Visual Previews

Potential additions:

- PDF first pages
- Dataset samples
- CSV/JSON tables
- Audio information
- Video thumbnails
- Code snippets
- Markdown documents

## v0.5 — Advanced Relationships

Potential additions:

- Relationship editing
- Relationship notes
- Multiple relationship categories
- Relationship filtering
- Graph navigation
- Connected-node highlighting

## v0.6 — Knowledge Search

Potential additions:

- Full-text search
- Tagging
- Advanced filters
- Saved searches
- Related-node discovery

## Future — AI-Assisted Knowledge

A future version could optionally integrate local AI systems to help identify relationships between documents and concepts.

Possible integrations include:

```text
JASS Visual Knowledge Map
          │
          ├── Ollama
          ├── LM Studio
          ├── Local embeddings
          └── Project Athena
```

These integrations are future possibilities, not requirements for the current application.

---

# 🧠 Relationship with Project Athena

JASS Visual Knowledge Map is designed to remain useful as a standalone application.

However, its architecture creates an interesting future path toward **Project Athena**.

Potential evolution:

```text
Files
  ↓
Visual Knowledge Map
  ↓
Knowledge Graph
  ↓
Search / Retrieval
  ↓
Project Athena
  ↓
AI-assisted Knowledge Workspace
```

The current application does **not** require Athena.

The goal is to establish a useful visual knowledge layer first.

---

# 📂 Suggested Project Structure

```text
JASS-Visual-Knowledge-Map/
│
├── README.md
├── jass_visual_knowledge_map_v0_3.py
│
├── data/
│   └── workspaces/
│
├── docs/
│
└── screenshots/
```

Workspace files can be kept separately from the application source.

---

# ▶️ Running the Application

## Requirements

Python 3.10+ is recommended.

Install PySide6:

```bash
pip install PySide6
```

Run:

```bash
python jass_visual_knowledge_map_v0_3.py
```

### Windows

```powershell
python .\jass_visual_knowledge_map_v0_3.py
```

### Linux

```bash
python3 jass_visual_knowledge_map_v0_3.py
```

---

# 📌 Current Status

**Status:** 🟢 Operational

**Version:** `0.3`

**Application type:** Desktop

**Framework:** PySide6

**Database:** SQLite

**Architecture:** Local-first

**Platform:** Windows / Linux

---

# 🌱 Development Philosophy

JASS applications are developed incrementally.

```text
Start simple
     ↓
Make it useful
     ↓
Make it visual
     ↓
Make it persistent
     ↓
Add intelligence
```

JASS Visual Knowledge Map follows the same principle.

The objective is not to build a complicated knowledge graph all at once.

The objective is to create a practical visual workspace that can gradually become more capable.

---

# 🧪 JASS Digital Lab

JASS Visual Knowledge Map is part of **JASS Digital Lab**, an independent software laboratory focused on practical desktop applications, AI tools, language technology, data exploration, legacy software modernization and knowledge systems.

---

## 📜 License

Add the project's preferred license here.

---

## 👤 Author

**SinghJasvir · Fanu2**

**JASS Digital Lab**

> **Build useful things. Preserve what matters. Explore what comes next.**
