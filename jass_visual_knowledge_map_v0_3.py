"""
JASS Visual Knowledge Map
v0.2 — Knowledge Workspace

Local-first visual knowledge workspace built with PySide6 + SQLite.

Features
- Persistent SQLite workspace (.jvkm / .db)
- Create, edit and delete knowledge nodes
- Node types: Document, Dataset, Image, Audio, Video, Code,
  Database, Project, Concept, Folder
- Create relationships between nodes
- Relationship types: Contains, Uses, Related to, Depends on,
  References, Derived from, Part of
- Interactive graph canvas
- Search and type filtering
- Folder import with automatic node classification
- Node inspector with notes and metadata
- Save / Save As / Open workspace
- PNG export
"""

from __future__ import annotations

import math
import os
import sqlite3
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QBrush, QPixmap
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QFrame, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsScene, QGraphicsTextItem, QGraphicsView, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPushButton, QSplitter, QTextEdit, QToolBar,
    QVBoxLayout, QWidget, QInputDialog, QToolTip
)

APP_NAME = "JASS Visual Knowledge Map"
APP_VERSION = "0.3 — Visual Previews"

NODE_TYPES = [
    "Document", "Dataset", "Image", "Audio", "Video", "Code",
    "Database", "Project", "Concept", "Folder"
]

RELATION_TYPES = [
    "Contains", "Uses", "Related to", "Depends on",
    "References", "Derived from", "Part of"
]

TYPE_COLORS = {
    "Document": "#7c3aed",
    "Dataset": "#059669",
    "Image": "#16a34a",
    "Audio": "#9333ea",
    "Video": "#dc2626",
    "Code": "#ea580c",
    "Database": "#0284c7",
    "Project": "#2563eb",
    "Concept": "#d97706",
    "Folder": "#64748b",
}

EXTENSION_TYPES = {
    ".pdf": "Document", ".doc": "Document", ".docx": "Document",
    ".txt": "Document", ".md": "Document", ".rtf": "Document",
    ".csv": "Dataset", ".json": "Dataset", ".xml": "Dataset",
    ".parquet": "Dataset", ".tsv": "Dataset",
    ".png": "Image", ".jpg": "Image", ".jpeg": "Image",
    ".webp": "Image", ".gif": "Image",
    ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio",
    ".mp4": "Video", ".mkv": "Video", ".avi": "Video",
    ".py": "Code", ".js": "Code", ".ts": "Code", ".java": "Code",
    ".cpp": "Code", ".c": "Code", ".html": "Code", ".css": "Code",
    ".db": "Database", ".sqlite": "Database", ".sqlite3": "Database",
}


def node_color(node_type: str) -> str:
    return TYPE_COLORS.get(node_type, "#475569")


class WorkspaceDB:
    """Small SQLite persistence layer for .jvkm workspaces."""

    def __init__(self, path: Optional[str] = None):
        self.path = path
        self.conn: Optional[sqlite3.Connection] = None

    def open(self, path: str):
        self.close()
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._schema()

    def _schema(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS workspace (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            node_type TEXT NOT NULL,
            path TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            metadata TEXT DEFAULT '',
            x REAL DEFAULT 0,
            y REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            relation_type TEXT NOT NULL,
            notes TEXT DEFAULT '',
            FOREIGN KEY(source_id) REFERENCES nodes(id) ON DELETE CASCADE,
            FOREIGN KEY(target_id) REFERENCES nodes(id) ON DELETE CASCADE
        );
        """)
        self.conn.commit()

    def ensure_workspace(self, name: str):
        self.conn.execute(
            "INSERT OR IGNORE INTO workspace(id,name) VALUES(1,?)", (name,)
        )
        self.conn.commit()

    def set_workspace_name(self, name: str):
        self.conn.execute(
            "UPDATE workspace SET name=?, updated_at=CURRENT_TIMESTAMP WHERE id=1",
            (name,)
        )
        self.conn.commit()

    def workspace_name(self) -> str:
        row = self.conn.execute("SELECT name FROM workspace WHERE id=1").fetchone()
        return row["name"] if row else "JASS Knowledge Workspace"

    def add_node(self, title, node_type, path="", notes="", metadata="", x=0, y=0):
        cur = self.conn.execute("""
            INSERT INTO nodes(title,node_type,path,notes,metadata,x,y)
            VALUES(?,?,?,?,?,?,?)
        """, (title, node_type, path, notes, metadata, x, y))
        self.conn.commit()
        return cur.lastrowid

    def update_node(self, node_id, title, node_type, path, notes, metadata, x, y):
        self.conn.execute("""
            UPDATE nodes
            SET title=?, node_type=?, path=?, notes=?, metadata=?,
                x=?, y=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (title, node_type, path, notes, metadata, x, y, node_id))
        self.conn.commit()

    def delete_node(self, node_id):
        self.conn.execute("DELETE FROM nodes WHERE id=?", (node_id,))
        self.conn.commit()

    def nodes(self):
        return self.conn.execute(
            "SELECT * FROM nodes ORDER BY title COLLATE NOCASE"
        ).fetchall()

    def add_relationship(self, source_id, target_id, relation_type, notes=""):
        if source_id == target_id:
            return
        exists = self.conn.execute("""
            SELECT id FROM relationships
            WHERE source_id=? AND target_id=? AND relation_type=?
        """, (source_id, target_id, relation_type)).fetchone()
        if not exists:
            self.conn.execute("""
                INSERT INTO relationships(source_id,target_id,relation_type,notes)
                VALUES(?,?,?,?)
            """, (source_id, target_id, relation_type, notes))
            self.conn.commit()

    def delete_relationship(self, relationship_id):
        self.conn.execute(
            "DELETE FROM relationships WHERE id=?", (relationship_id,)
        )
        self.conn.commit()

    def relationships(self):
        return self.conn.execute("""
            SELECT r.*, s.title AS source_title, t.title AS target_title
            FROM relationships r
            JOIN nodes s ON s.id=r.source_id
            JOIN nodes t ON t.id=r.target_id
            ORDER BY r.id
        """).fetchall()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None


class NodeItem(QGraphicsEllipseItem):
    """Graph node with lightweight hover previews for visual files."""

    IMAGE_TYPES = {"Image"}

    def __init__(self, node_id, title, node_type, path="", radius=42):
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        self.node_id = node_id
        self.title = title
        self.node_type = node_type
        self.path = path
        self.setBrush(QBrush(QColor(node_color(node_type))))
        self.setPen(QPen(QColor("#cbd5e1"), 2))
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(2)

        self.label = QGraphicsTextItem(self.short_title(), self)
        self.label.setDefaultTextColor(QColor("#f8fafc"))
        font = QFont("Segoe UI", 9)
        font.setBold(True)
        self.label.setFont(font)
        rect = self.label.boundingRect()
        self.label.setPos(-rect.width() / 2, -rect.height() / 2)

        self.preview = None

    def short_title(self):
        return self.title if len(self.title) <= 18 else self.title[:16] + "…"

    def refresh(self, title, node_type, path=""):
        self.title = title
        self.node_type = node_type
        self.path = path
        self.setBrush(QBrush(QColor(node_color(node_type))))
        self.label.setPlainText(self.short_title())
        rect = self.label.boundingRect()
        self.label.setPos(-rect.width() / 2, -rect.height() / 2)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemSelectedChange:
            selected = bool(value)
            self.setPen(
                QPen(
                    QColor("#ffffff" if selected else "#cbd5e1"),
                    4 if selected else 2
                )
            )
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        if self.node_type == "Image" and self.path:
            self.show_image_preview()
        else:
            QToolTip.showText(
                event.screenPos(),
                f"{self.title}\n{self.node_type}",
                None
            )
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if self.preview:
            self.preview.close()
            self.preview = None
        QToolTip.hideText()
        super().hoverLeaveEvent(event)

    def show_image_preview(self):
        path = Path(self.path)
        if not path.is_file():
            return

        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return

        # A lightweight floating preview window. The original image is untouched.
        from PySide6.QtWidgets import QLabel, QFrame

        preview = QFrame(None, Qt.WindowType.ToolTip)
        preview.setStyleSheet("""
            QFrame {
                background: #0b1220;
                border: 1px solid #38bdf8;
                border-radius: 10px;
            }
            QLabel { color: #e5e7eb; }
        """)
        layout = QVBoxLayout(preview)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setPixmap(
            pixmap.scaled(
                320, 240,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        layout.addWidget(image_label)

        info = QLabel(
            f"<b>{path.name}</b><br>"
            f"{pixmap.width()} × {pixmap.height()} px<br>"
            f"{self.human_size(path.stat().st_size)}"
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info)

        preview.adjustSize()
        preview.move(self.scene().views()[0].mapToGlobal(
            self.scene().views()[0].mapFromScene(self.scenePos())
        ))
        preview.show()
        self.preview = preview

    @staticmethod
    def human_size(size):
        value = float(size)
        for unit in ("B", "KB", "MB", "GB"):
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} TB"


class GraphScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.setBackgroundBrush(QColor("#070b14"))
        self.edge_items = {}

    def clear_graph(self):
        self.clear()
        self.edge_items.clear()


class GraphView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse
        )
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)


class NodeDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Knowledge Node")
        self.resize(520, 430)

        data = data or {}
        layout = QFormLayout(self)

        self.title = QLineEdit(data.get("title", ""))
        self.type = QComboBox()
        self.type.addItems(NODE_TYPES)
        if data.get("node_type") in NODE_TYPES:
            self.type.setCurrentText(data["node_type"])

        self.path = QLineEdit(data.get("path", ""))
        browse = QPushButton("Browse…")
        browse.clicked.connect(self.browse_path)

        path_row = QHBoxLayout()
        path_row.addWidget(self.path)
        path_row.addWidget(browse)

        self.notes = QTextEdit(data.get("notes", ""))
        self.metadata = QTextEdit(data.get("metadata", ""))

        layout.addRow("Title", self.title)
        layout.addRow("Type", self.type)
        layout.addRow("Location", path_row)
        layout.addRow("Notes", self.notes)
        layout.addRow("Metadata", self.metadata)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def browse_path(self):
        path = QFileDialog.getOpenFileName(self, "Choose file")[0]
        if path:
            self.path.setText(path)

    def values(self):
        return {
            "title": self.title.text().strip() or "Untitled",
            "node_type": self.type.currentText(),
            "path": self.path.text().strip(),
            "notes": self.notes.toPlainText().strip(),
            "metadata": self.metadata.toPlainText().strip(),
        }


class RelationshipDialog(QDialog):
    def __init__(self, nodes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Relationship")
        self.resize(460, 230)

        layout = QFormLayout(self)
        self.source = QComboBox()
        self.target = QComboBox()
        self.relation = QComboBox()
        self.relation.addItems(RELATION_TYPES)

        for node in nodes:
            text = f"{node['title']}  [{node['node_type']}]"
            self.source.addItem(text, node["id"])
            self.target.addItem(text, node["id"])

        layout.addRow("From", self.source)
        layout.addRow("Relationship", self.relation)
        layout.addRow("To", self.target)

        self.notes = QLineEdit()
        self.notes.setPlaceholderText("Optional relationship note")
        layout.addRow("Notes", self.notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def validate(self):
        if self.source.currentData() == self.target.currentData():
            QMessageBox.warning(self, APP_NAME, "Choose two different nodes.")
            return
        self.accept()

    def values(self):
        return (
            self.source.currentData(),
            self.target.currentData(),
            self.relation.currentText(),
            self.notes.text().strip()
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — v{APP_VERSION}")
        self.resize(1450, 900)
        self.db = WorkspaceDB()
        self.node_items = {}
        self.edge_items = {}
        self.current_file = None
        self.build_style()
        self.build_ui()
        self.new_workspace()

    def build_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background:#090d16;
                color:#e5e7eb;
                font-family:"Segoe UI";
            }
            QToolBar {
                background:#0d1422;
                border:0;
                padding:7px;
                spacing:6px;
            }
            QPushButton,QLineEdit,QComboBox {
                background:#111a2b;
                color:#e5e7eb;
                border:1px solid #263750;
                border-radius:7px;
                padding:7px 10px;
            }
            QPushButton:hover { border-color:#38bdf8; }
            QLabel#title {
                color:#f8fafc;
                font-size:20px;
                font-weight:700;
            }
            QLabel#section {
                color:#38bdf8;
                font-size:12px;
                font-weight:700;
            }
            QLabel#muted { color:#94a3b8; }
            QFrame#inspector {
                background:#0c1320;
                border-left:1px solid #1e293b;
            }
            QListWidget {
                background:#0b1220;
                border:1px solid #1e293b;
            }
        """)

    def build_ui(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        title = QLabel("  🧠 JASS Visual Knowledge Map")
        title.setObjectName("title")
        toolbar.addWidget(title)
        toolbar.addSeparator()

        for text, slot in [
            ("New", self.new_workspace),
            ("Open", self.open_workspace),
            ("Save", self.save_workspace),
            ("Save As", self.save_as),
        ]:
            button = QPushButton(text)
            button.clicked.connect(slot)
            toolbar.addWidget(button)

        toolbar.addSeparator()

        add = QPushButton("+ Node")
        add.clicked.connect(self.add_node)
        toolbar.addWidget(add)

        rel = QPushButton("↔ Relationship")
        rel.clicked.connect(self.add_relationship)
        toolbar.addWidget(rel)

        import_btn = QPushButton("📁 Import Folder")
        import_btn.clicked.connect(self.import_folder)
        toolbar.addWidget(import_btn)

        export = QPushButton("Export PNG")
        export.clicked.connect(self.export_png)
        toolbar.addWidget(export)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search…")
        self.search.setFixedWidth(200)
        self.search.textChanged.connect(self.filter_graph)
        toolbar.addWidget(self.search)

        self.filter_type = QComboBox()
        self.filter_type.addItem("All types")
        self.filter_type.addItems(NODE_TYPES)
        self.filter_type.currentTextChanged.connect(self.filter_graph)
        toolbar.addWidget(self.filter_type)

        split = QSplitter(Qt.Orientation.Horizontal)

        self.scene = GraphScene()
        self.view = GraphView(self.scene)
        split.addWidget(self.view)

        inspector = QFrame()
        inspector.setObjectName("inspector")
        inspector.setMinimumWidth(340)
        inspector.setMaximumWidth(430)
        il = QVBoxLayout(inspector)
        il.setContentsMargins(22, 22, 22, 22)

        heading = QLabel("Knowledge Inspector")
        heading.setObjectName("title")
        il.addWidget(heading)

        self.node_title = QLabel("No node selected")
        self.node_title.setWordWrap(True)
        self.node_title.setStyleSheet("font-size:18px;font-weight:700;")
        il.addWidget(self.node_title)

        self.node_type = QLabel("—")
        self.node_type.setObjectName("section")
        il.addWidget(self.node_type)

        self.node_path = QLabel("")
        self.node_path.setObjectName("muted")
        self.node_path.setWordWrap(True)
        il.addWidget(self.node_path)

        self.node_notes = QLabel("")
        self.node_notes.setWordWrap(True)
        il.addWidget(self.node_notes)

        edit = QPushButton("Edit Node")
        edit.clicked.connect(self.edit_selected)
        il.addWidget(edit)

        delete = QPushButton("Delete Node")
        delete.clicked.connect(self.delete_selected)
        il.addWidget(delete)

        il.addSpacing(18)
        rel_title = QLabel("Relationships")
        rel_title.setObjectName("section")
        il.addWidget(rel_title)

        self.relationship_list = QListWidget()
        il.addWidget(self.relationship_list)

        remove_rel = QPushButton("Remove Selected Relationship")
        remove_rel.clicked.connect(self.remove_selected_relationship)
        il.addWidget(remove_rel)

        il.addStretch()

        footer = QLabel("JASS Digital Lab  •  Local-first  •  PySide6 + SQLite")
        footer.setObjectName("muted")
        il.addWidget(footer)

        split.addWidget(inspector)
        split.setSizes([1100, 370])

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(split)
        self.setCentralWidget(central)

        self.statusBar().showMessage("Ready")

    def new_workspace(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Create Knowledge Workspace",
            "JASS-Knowledge-Workspace.jvkm",
            "JASS Knowledge Map (*.jvkm);;SQLite Database (*.db)"
        )
        if not path:
            if self.db.conn is None:
                self._create_temp()
            return

        self.db.open(path)
        self.db.ensure_workspace(Path(path).stem)
        self.current_file = path
        self.refresh_graph()
        self.setWindowTitle(f"{APP_NAME} — {Path(path).name}")

    def _create_temp(self):
        self.db.open(":memory:")
        self.db.ensure_workspace("Untitled Knowledge Workspace")
        self.current_file = None
        self.refresh_graph()

    def open_workspace(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Knowledge Workspace", "",
            "JASS Knowledge Map (*.jvkm *.db);;All Files (*)"
        )
        if not path:
            return
        try:
            self.db.open(path)
            self.db.ensure_workspace(Path(path).stem)
            self.current_file = path
            self.refresh_graph()
            self.setWindowTitle(f"{APP_NAME} — {Path(path).name}")
        except Exception as exc:
            QMessageBox.critical(self, APP_NAME, f"Could not open workspace:\n{exc}")

    def save_workspace(self):
        if not self.current_file:
            return self.save_as()
        self.persist_positions()
        self.statusBar().showMessage("Workspace saved")

    def save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Knowledge Workspace As",
            "JASS-Knowledge-Workspace.jvkm",
            "JASS Knowledge Map (*.jvkm);;SQLite Database (*.db)"
        )
        if not path:
            return
        self.persist_positions()

        rows = self.db.nodes()
        rels = self.db.relationships()

        newdb = WorkspaceDB()
        newdb.open(path)
        newdb.ensure_workspace(Path(path).stem)

        idmap = {}
        for row in rows:
            nid = newdb.add_node(
                row["title"], row["node_type"], row["path"],
                row["notes"], row["metadata"], row["x"], row["y"]
            )
            idmap[row["id"]] = nid

        for row in rels:
            newdb.add_relationship(
                idmap[row["source_id"]], idmap[row["target_id"]],
                row["relation_type"], row["notes"]
            )

        self.db.close()
        self.db = newdb
        self.current_file = path
        self.refresh_graph()
        self.setWindowTitle(f"{APP_NAME} — {Path(path).name}")
        self.statusBar().showMessage("Workspace saved as new file")

    def add_node(self):
        dialog = NodeDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        v = dialog.values()
        existing = self.db.nodes()
        angle = len(existing) * 0.75
        radius = 220 + (len(existing) // 10) * 80
        nid = self.db.add_node(
            v["title"], v["node_type"], v["path"],
            v["notes"], v["metadata"],
            math.cos(angle) * radius, math.sin(angle) * radius
        )
        self.refresh_graph(select_id=nid)

    def edit_selected(self):
        nid = self.selected_node_id()
        if not nid:
            QMessageBox.information(self, APP_NAME, "Select a node first.")
            return
        row = next((r for r in self.db.nodes() if r["id"] == nid), None)
        if not row:
            return
        dialog = NodeDialog(self, dict(row))
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        v = dialog.values()
        item = self.node_items[nid]
        pos = item.scenePos()
        self.db.update_node(
            nid, v["title"], v["node_type"], v["path"],
            v["notes"], v["metadata"], pos.x(), pos.y()
        )
        self.refresh_graph(select_id=nid)

    def delete_selected(self):
        nid = self.selected_node_id()
        if not nid:
            return
        answer = QMessageBox.question(
            self, APP_NAME,
            "Delete the selected node and its relationships?"
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.db.delete_node(nid)
            self.refresh_graph()

    def add_relationship(self):
        rows = self.db.nodes()
        if len(rows) < 2:
            QMessageBox.information(
                self, APP_NAME,
                "Create at least two nodes before creating a relationship."
            )
            return
        dialog = RelationshipDialog(rows, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        source, target, relation, notes = dialog.values()
        self.db.add_relationship(source, target, relation, notes)
        self.refresh_graph()

    def import_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Import Folder")
        if not folder:
            return
        root = Path(folder)

        root_id = self.db.add_node(
            root.name, "Folder", str(root),
            "Imported folder", "", 0, 0
        )

        files = [p for p in root.rglob("*") if p.is_file()][:100]
        for index, path in enumerate(files):
            node_type = EXTENSION_TYPES.get(path.suffix.lower(), "Document")
            angle = index * 0.32
            radius = 300 + (index // 30) * 180
            nid = self.db.add_node(
                path.name, node_type, str(path),
                "", f"extension={path.suffix.lower()}",
                math.cos(angle) * radius,
                math.sin(angle) * radius
            )
            self.db.add_relationship(root_id, nid, "Contains")

        self.refresh_graph(select_id=root_id)
        self.statusBar().showMessage(
            f"Imported {len(files)} files from {root}"
        )

    def selected_node_id(self):
        selected = self.scene.selectedItems()
        for item in selected:
            if isinstance(item, NodeItem):
                return item.node_id
        return None

    def refresh_graph(self, select_id=None):
        self.scene.clear_graph()
        self.node_items.clear()
        self.edge_items.clear()

        rows = self.db.nodes()
        for row in rows:
            item = NodeItem(row["id"], row["title"], row["node_type"], row["path"])
            item.setPos(row["x"], row["y"])
            self.scene.addItem(item)
            self.node_items[row["id"]] = item

        for row in self.db.relationships():
            source = self.node_items.get(row["source_id"])
            target = self.node_items.get(row["target_id"])
            if not source or not target:
                continue

            line = QGraphicsLineItem()
            line.setPen(QPen(QColor("#334155"), 1.5))
            line.setZValue(0)
            self.scene.addItem(line)
            self.edge_items[row["id"]] = (line, source, target)

            label = QGraphicsTextItem(row["relation_type"])
            label.setDefaultTextColor(QColor("#64748b"))
            label.setFont(QFont("Segoe UI", 8))
            label.setZValue(1)
            self.scene.addItem(label)
            self.edge_items[row["id"]] += (label,)

        self.update_edges()

        if rows:
            rect = self.scene.itemsBoundingRect().adjusted(-120, -120, 120, 120)
            self.scene.setSceneRect(rect)
            self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

        if select_id and select_id in self.node_items:
            self.node_items[select_id].setSelected(True)
            self.show_node(select_id)

    def update_edges(self):
        for line, source, target, label in self.edge_items.values():
            a, b = source.scenePos(), target.scenePos()
            line.setLine(a.x(), a.y(), b.x(), b.y())
            label.setPos((a.x() + b.x()) / 2, (a.y() + b.y()) / 2)

    def persist_positions(self):
        if not self.db.conn:
            return
        for nid, item in self.node_items.items():
            p = item.scenePos()
            row = next((r for r in self.db.nodes() if r["id"] == nid), None)
            if row:
                self.db.update_node(
                    nid, row["title"], row["node_type"], row["path"],
                    row["notes"], row["metadata"], p.x(), p.y()
                )

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

    def show_node(self, nid):
        rows = self.db.nodes()
        row = next((r for r in rows if r["id"] == nid), None)
        if not row:
            return

        self.node_title.setText(row["title"])
        self.node_type.setText(row["node_type"])
        self.node_path.setText(row["path"] or "No location")
        self.node_notes.setText(row["notes"] or "No notes")

        self.relationship_list.clear()
        for rel in self.db.relationships():
            if rel["source_id"] == nid:
                text = f"→ {rel['relation_type']} → {rel['target_title']}"
            elif rel["target_id"] == nid:
                text = f"← {rel['relation_type']} ← {rel['source_title']}"
            else:
                continue
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, rel["id"])
            self.relationship_list.addItem(item)

    def scene_selection_changed(self):
        nid = self.selected_node_id()
        if nid:
            self.show_node(nid)

    def filter_graph(self):
        query = self.search.text().strip().lower()
        selected_type = self.filter_type.currentText()

        for nid, item in self.node_items.items():
            row = next((r for r in self.db.nodes() if r["id"] == nid), None)
            if not row:
                continue
            visible = (
                (not query or query in row["title"].lower() or
                 query in row["path"].lower())
                and (selected_type == "All types" or
                     row["node_type"] == selected_type)
            )
            item.setVisible(visible)

        for line, source, target, label in self.edge_items.values():
            line.setVisible(source.isVisible() and target.isVisible())
            label.setVisible(source.isVisible() and target.isVisible())

    def remove_selected_relationship(self):
        item = self.relationship_list.currentItem()
        if not item:
            return
        rid = item.data(Qt.ItemDataRole.UserRole)
        self.db.delete_relationship(rid)
        nid = self.selected_node_id()
        self.refresh_graph(select_id=nid)

    def export_png(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Knowledge Map",
            "jass-knowledge-map.png", "PNG Images (*.png)"
        )
        if not filename:
            return

        rect = self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50)
        image = QImage(
            max(1, int(rect.width())),
            max(1, int(rect.height())),
            QImage.Format.Format_ARGB32
        )
        image.fill(QColor("#070b14"))
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene.render(painter, QRectF(image.rect()), rect)
        painter.end()
        image.save(filename)
        self.statusBar().showMessage(f"Exported {filename}")

    def closeEvent(self, event):
        self.persist_positions()
        self.db.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = MainWindow()
    window.scene.selectionChanged.connect(window.scene_selection_changed)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
