import tkinter as tk
from tkinter import font as tkfont
import traceback
from lexer import Lexer, Token, Tokentype
from parser import Parser, AST

# ── Colour Palette ──────────────────────────────────────────────
BG          = "#0D1117"   # near-black canvas
PANEL       = "#161B22"   # slightly lighter panels
BORDER      = "#30363D"   # subtle borders
GUTTER      = "#1C2128"   # line-number gutter
LINE_NUM_FG = "#484F58"   # muted line numbers
CARET       = "#58A6FF"   # blue cursor / accent
TEXT_MAIN   = "#E6EDF3"   # primary text
TEXT_DIM    = "#8B949E"   # secondary / comments
SUCCESS     = "#3FB950"   # green
ERROR       = "#F85149"   # red
WARNING     = "#D29922"   # amber

# Syntax-highlight colours
SH_KEYWORD  = "#FF7B72"   # red-orange  – type keywords + control flow
SH_CONTROL  = "#FFA657"   # amber       – if / else / while / for
SH_NUMBER   = "#79C0FF"   # sky blue    – numeric literals
SH_OP       = "#FF7B72"   # same as keyword for operators
SH_COMMENT  = "#6E7681"   # grey        – (future use)
SH_ID       = "#E6EDF3"   # plain white – identifiers

FONT_EDITOR = None           # resolved after Tk root exists (see App.__init__)
FONT_UI     = ("Segoe UI", 11)
FONT_TITLE  = ("Segoe UI", 14, "bold")
FONT_SMALL  = ("Segoe UI",  9)

KEYWORDS    = {"int", "float", "char", "double"}
CONTROL     = {"if", "else", "while", "for"}
OPERATORS   = set("+-*/=<>{}();")


# ── AST dump ────────────────────────────────────────────────────
def dump_ast(node, indent=0):
    if node is None:
        return ""
    res, prefix = "", "  " * indent
    if isinstance(node, AST):
        res += prefix + f"[{node.__class__.__name__}]\n"
        for key, value in vars(node).items():
            if key == "token":
                continue
            if isinstance(value, list):
                res += prefix + f"  {key}:\n"
                for item in value:
                    res += dump_ast(item, indent + 2) + "\n"
            elif isinstance(value, AST):
                res += prefix + f"  {key}:\n"
                res += dump_ast(value, indent + 2) + "\n"
            else:
                res += prefix + f"  {key}: {value}\n"
    else:
        res += prefix + str(node)
    return res.rstrip()


# ── Custom Widgets ───────────────────────────────────────────────
class LineNumberCanvas(tk.Canvas):
    """Draws line numbers synced to a Text widget."""
    def __init__(self, master, text_widget, **kw):
        kw.setdefault("bg", GUTTER)
        kw.setdefault("highlightthickness", 0)
        kw.setdefault("width", 48)
        super().__init__(master, **kw)
        self._text = text_widget
        self._font = tkfont.Font(font=FONT_EDITOR)
        self._text.bind("<<Change>>",    self._redraw)
        self._text.bind("<Configure>",   self._redraw)
        self._text.bind("<KeyRelease>",  self._redraw)
        self._text.bind("<MouseWheel>",  self._redraw)

    def _redraw(self, _=None):
        self.delete("all")
        i = self._text.index("@0,0")
        while True:
            dline = self._text.dlineinfo(i)
            if dline is None:
                break
            y   = dline[1]
            num = str(i).split(".")[0]
            self.create_text(
                38, y + dline[3] // 2,
                anchor="e", text=num,
                fill=CARET if self._text.compare(i, "==", tk.INSERT) else LINE_NUM_FG,
                font=self._font
            )
            i = self._text.index(f"{i}+1line")
            if self._text.compare(i, ">=", "end"):
                break


class StatusBar(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=PANEL, height=26)
        self.pack_propagate(False)
        self._left  = tk.Label(self, bg=PANEL, fg=TEXT_DIM, font=FONT_SMALL, anchor="w", padx=12)
        self._right = tk.Label(self, bg=PANEL, fg=TEXT_DIM, font=FONT_SMALL, anchor="e", padx=12)
        self._left.pack(side=tk.LEFT)
        self._right.pack(side=tk.RIGHT)

    def set(self, left="", right="", color=TEXT_DIM):
        self._left.config(text=left,  fg=color)
        self._right.config(text=right, fg=TEXT_DIM)


# ── Main Application ─────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # Resolve editor font now that the root window exists
        global FONT_EDITOR
        families = tkfont.families()
        FONT_EDITOR = ("JetBrains Mono", 13) if "JetBrains Mono" in families else \
                      ("Fira Code",       13) if "Fira Code"       in families else \
                      ("Consolas",        13)
        self.title("C-lite Parser")
        self.geometry("1100x760")
        self.minsize(820, 580)
        self.configure(bg=BG)

        self._build_ui()
        self._bind_shortcuts()
        self._insert_sample()
        self._highlight()

    # ── UI Construction ──────────────────────────────────────────
    def _build_ui(self):
        # ── Top bar
        top = tk.Frame(self, bg=PANEL, height=48)
        top.pack(fill=tk.X)
        top.pack_propagate(False)

        tk.Label(top, text="◈ C-lite", bg=PANEL, fg=CARET,
                 font=("Segoe UI", 15, "bold"), padx=18).pack(side=tk.LEFT, pady=8)
        tk.Label(top, text="Recursive Descent Parser & AST Viewer", bg=PANEL,
                 fg=TEXT_DIM, font=FONT_UI).pack(side=tk.LEFT)

        self._run_btn = tk.Button(
            top, text="▶  Run  (Ctrl+↵)", bg=CARET, fg=BG,
            activebackground="#79C0FF", activeforeground=BG,
            font=("Segoe UI", 11, "bold"), relief=tk.FLAT,
            padx=18, pady=6, cursor="hand2",
            command=self.run_check
        )
        self._run_btn.pack(side=tk.RIGHT, padx=18, pady=8)
        
        self._vis_btn = tk.Button(
            top, text="📊 Visualize", bg=SUCCESS, fg=BG,
            activebackground="#56D069", activeforeground=BG,
            font=("Segoe UI", 11, "bold"), relief=tk.FLAT,
            padx=18, pady=6, cursor="hand2",
            command=self.run_visualization
        )
        self._vis_btn.pack(side=tk.RIGHT, pady=8)

        self._clear_btn = tk.Button(
            top, text="✕ Clear", bg=PANEL, fg=TEXT_DIM,
            activebackground=BORDER, activeforeground=TEXT_MAIN,
            font=FONT_UI, relief=tk.FLAT, padx=12, pady=6,
            cursor="hand2", command=self._clear_output
        )
        self._clear_btn.pack(side=tk.RIGHT, pady=8)

        # thin accent line under top bar
        tk.Frame(self, bg=CARET, height=2).pack(fill=tk.X)

        # ── Separator labels row
        label_row = tk.Frame(self, bg=BG)
        label_row.pack(fill=tk.X, padx=0, pady=(12, 4))

        tk.Label(label_row, text="  SOURCE EDITOR", bg=BG, fg=LINE_NUM_FG,
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(18, 0))
        tk.Label(label_row, text="PARSER OUTPUT  ", bg=BG, fg=LINE_NUM_FG,
                 font=("Segoe UI", 9, "bold")).pack(side=tk.RIGHT, padx=(0, 18))

        # ── Paned body
        pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=BG,
                              sashwidth=6, sashrelief=tk.FLAT,
                              handlesize=0, bd=0)
        pane.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        # Left – editor panel
        left_panel = tk.Frame(pane, bg=BORDER, padx=1, pady=1)
        editor_wrap = tk.Frame(left_panel, bg=PANEL)
        editor_wrap.pack(fill=tk.BOTH, expand=True)

        # gutter + editor side by side
        gutter_wrap = tk.Frame(editor_wrap, bg=GUTTER)
        gutter_wrap.pack(fill=tk.BOTH, expand=True)

        self.editor = tk.Text(
            gutter_wrap, bg=PANEL, fg=TEXT_MAIN,
            insertbackground=CARET, font=FONT_EDITOR,
            relief=tk.FLAT, padx=14, pady=12,
            undo=True, maxundo=200,
            selectbackground="#264F78", selectforeground=TEXT_MAIN,
            tabs=("28p",), wrap=tk.NONE,
            highlightthickness=0
        )

        self._line_canvas = LineNumberCanvas(gutter_wrap, self.editor)
        self._line_canvas.pack(side=tk.LEFT, fill=tk.Y)

        ed_scroll_y = tk.Scrollbar(gutter_wrap, orient=tk.VERTICAL,
                                   command=self.editor.yview, bg=PANEL,
                                   troughcolor=PANEL, bd=0, width=10)
        ed_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        ed_scroll_x = tk.Scrollbar(editor_wrap, orient=tk.HORIZONTAL,
                                   command=self.editor.xview, bg=PANEL,
                                   troughcolor=PANEL, bd=0, width=10)
        ed_scroll_x.pack(fill=tk.X)

        self.editor.config(yscrollcommand=ed_scroll_y.set,
                           xscrollcommand=ed_scroll_x.set)
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        pane.add(left_panel, minsize=340, stretch="always")

        # Right – output panel (tabbed: AST / Tokens)
        right_panel = tk.Frame(pane, bg=BORDER, padx=1, pady=1)
        output_wrap  = tk.Frame(right_panel, bg=PANEL)
        output_wrap.pack(fill=tk.BOTH, expand=True)

        # Tab bar
        tab_bar = tk.Frame(output_wrap, bg=GUTTER, height=34)
        tab_bar.pack(fill=tk.X)
        tab_bar.pack_propagate(False)

        self._tab_ast    = tk.Button(tab_bar, text="AST",    relief=tk.FLAT,
                                     font=("Segoe UI", 10, "bold"),
                                     bg=PANEL,  fg=CARET, padx=20, cursor="hand2",
                                     command=lambda: self._switch_tab("ast"))
        self._tab_tokens = tk.Button(tab_bar, text="Tokens", relief=tk.FLAT,
                                     font=("Segoe UI", 10, "bold"),
                                     bg=GUTTER, fg=TEXT_DIM, padx=20, cursor="hand2",
                                     command=lambda: self._switch_tab("tokens"))
        self._tab_ast.pack(side=tk.LEFT)
        self._tab_tokens.pack(side=tk.LEFT)

        # AST output
        ast_scroll_y = tk.Scrollbar(output_wrap, orient=tk.VERTICAL, bg=PANEL,
                                    troughcolor=PANEL, bd=0, width=10)
        ast_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.output = tk.Text(
            output_wrap, bg=PANEL, fg=SUCCESS, font=FONT_EDITOR,
            relief=tk.FLAT, padx=14, pady=12, state=tk.DISABLED,
            selectbackground="#264F78", wrap=tk.NONE,
            highlightthickness=0
        )
        self.output.pack(fill=tk.BOTH, expand=True)
        self.output.config(yscrollcommand=ast_scroll_y.set)
        ast_scroll_y.config(command=self.output.yview)

        # Token output (hidden initially)
        tok_scroll_y = tk.Scrollbar(output_wrap, orient=tk.VERTICAL, bg=PANEL,
                                    troughcolor=PANEL, bd=0, width=10)

        self.token_out = tk.Text(
            output_wrap, bg=PANEL, fg=SH_NUMBER, font=FONT_EDITOR,
            relief=tk.FLAT, padx=14, pady=12, state=tk.DISABLED,
            selectbackground="#264F78", wrap=tk.NONE,
            highlightthickness=0
        )
        self.token_out.config(yscrollcommand=tok_scroll_y.set)
        tok_scroll_y.config(command=self.token_out.yview)
        self._tok_scroll = tok_scroll_y

        self._active_tab = "ast"
        pane.add(right_panel, minsize=320, stretch="always")

        # ── Status bar
        self._status = StatusBar(self)
        self._status.pack(fill=tk.X, side=tk.BOTTOM)
        self._status.set("Ready", "Mini C-lite Compiler")

        # Syntax-highlight tags
        self.editor.tag_config("kw",  foreground=SH_KEYWORD)
        self.editor.tag_config("ctl", foreground=SH_CONTROL)
        self.editor.tag_config("num", foreground=SH_NUMBER)
        self.editor.tag_config("op",  foreground=SH_OP)

        self.editor.bind("<<Modified>>", self._on_modified)
        self.editor.bind("<KeyRelease>", lambda _: self._update_cursor_status())

    # ── Tab switching ────────────────────────────────────────────
    def _switch_tab(self, tab):
        self._active_tab = tab
        if tab == "ast":
            self._tab_ast.config(bg=PANEL, fg=CARET)
            self._tab_tokens.config(bg=GUTTER, fg=TEXT_DIM)
            self._tok_scroll.pack_forget()
            self.token_out.pack_forget()
            self.output.pack(fill=tk.BOTH, expand=True)
        else:
            self._tab_ast.config(bg=GUTTER, fg=TEXT_DIM)
            self._tab_tokens.config(bg=PANEL, fg=CARET)
            self.output.pack_forget()
            self.token_out.pack(fill=tk.BOTH, expand=True)
            self._tok_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # ── Syntax Highlighting ──────────────────────────────────────
    def _highlight(self, _=None):
        for tag in ("kw", "ctl", "num", "op"):
            self.editor.tag_remove(tag, "1.0", tk.END)

        text = self.editor.get("1.0", tk.END)
        pos  = 0

        while pos < len(text):
            ch = text[pos]

            # skip whitespace
            if ch.isspace():
                pos += 1; continue

            # word (keyword / identifier)
            if ch.isalpha() or ch == '_':
                end = pos
                while end < len(text) and (text[end].isalnum() or text[end] == '_'):
                    end += 1
                word = text[pos:end]
                tag  = "kw" if word in KEYWORDS else "ctl" if word in CONTROL else None
                if tag:
                    s = f"1.0 + {pos} chars"
                    e = f"1.0 + {end} chars"
                    self.editor.tag_add(tag, s, e)
                pos = end; continue

            # number
            if ch.isdigit() or (ch == '.' and pos + 1 < len(text) and text[pos+1].isdigit()):
                end = pos
                while end < len(text) and (text[end].isdigit() or text[end] == '.'):
                    end += 1
                s = f"1.0 + {pos} chars"
                e = f"1.0 + {end} chars"
                self.editor.tag_add("num", s, e)
                pos = end; continue

            # operator
            if ch in OPERATORS:
                s = f"1.0 + {pos} chars"
                e = f"1.0 + {pos+1} chars"
                self.editor.tag_add("op", s, e)

            pos += 1

    def _on_modified(self, _=None):
        if self.editor.edit_modified():
            self._highlight()
            self._update_cursor_status()
            self.editor.edit_modified(False)

    def _update_cursor_status(self):
        idx  = self.editor.index(tk.INSERT)
        line, col = idx.split(".")
        self._status.set(f"Ln {line}, Col {int(col)+1}",
                         "Mini C-lite Compiler")

    # ── Helpers ──────────────────────────────────────────────────
    def _bind_shortcuts(self):
        self.bind("<Control-Return>", lambda _: self.run_check())
        self.bind("<Control-l>",      lambda _: self._clear_output())

    def _insert_sample(self):
        sample = (
            "int x = 5;\n"
            "int y = 10;\n"
            "\n"
            "if (x < y) {\n"
            "    x = x + 1;\n"
            "}\n"
            "\n"
            "while (x < y) {\n"
            "    x = x + 2;\n"
            "}\n"
            "\n"
            "for (int i = 0; i < 5; i = i + 1) {\n"
            "    y = y - 1;\n"
            "}"
        )
        self.editor.insert("1.0", sample)

    def _write_output(self, widget, text, color=None):
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        if color:
            widget.config(fg=color)
        widget.insert(tk.END, text)
        widget.config(state=tk.DISABLED)

    def _clear_output(self):
        self._write_output(self.output,    "")
        self._write_output(self.token_out, "")
        self._status.set("Cleared", "Mini C-lite Compiler")

    # ── Token dump ───────────────────────────────────────────────
    def _collect_tokens(self, source):
        lexer  = Lexer(source)
        tokens = []
        try:
            while True:
                tok = lexer.get_next_token()
                tokens.append(tok)
                if tok.type == Tokentype.EOF:
                    break
        except Exception as e:
            tokens.append(f"<Lexer error: {e}>")
        return tokens

    def _format_tokens(self, tokens):
        lines = []
        for i, tok in enumerate(tokens):
            if isinstance(tok, str):
                lines.append(f"  {i:>3}  {tok}")
            else:
                val = f"  ← {tok.value!r}" if tok.value is not None else ""
                lines.append(f"  {i:>3}  {tok.type.name:<12}{val}")
        return "\n".join(lines)

    # ── Core run logic ───────────────────────────────────────────
    def run_check(self, _=None):
        source = self.editor.get("1.0", tk.END).strip()
        if not source:
            self._status.set("⚠  Nothing to parse", "", WARNING)
            return

        # ── Token tab
        tokens     = self._collect_tokens(source)
        tok_text   = f"  {'#':>3}  {'TYPE':<12}  VALUE\n"
        tok_text  += "  " + "─" * 36 + "\n"
        tok_text  += self._format_tokens(tokens)
        self._write_output(self.token_out, tok_text, SH_NUMBER)

        # ── AST tab
        try:
            lexer  = Lexer(source)
            parser = Parser(lexer)
            ast    = parser.parse()

            if parser.errors:
                err_text  = f"✕  {len(parser.errors)} error(s) found\n"
                err_text += "─" * 45 + "\n\n"
                for e in parser.errors:
                    err_text += f"  •  {e}\n"
                self._write_output(self.output, err_text, ERROR)
                self._status.set(f"✕  {len(parser.errors)} parse error(s)",
                                 "", ERROR)
            else:
                out  = "✔  Parse successful — no errors\n"
                out += "─" * 45 + "\n\n"
                out += dump_ast(ast)
                self._write_output(self.output, out, SUCCESS)
                self._status.set("✔  Parse successful", "", SUCCESS)

        except Exception as e:
            tb   = traceback.format_exc()
            text = f"✕  Fatal compiler error\n{'─'*45}\n\n{e}\n\n{tb}"
            self._write_output(self.output, text, ERROR)
            self._status.set("✕  Compiler crashed", "", ERROR)

        # Switch to AST tab after running
        self._switch_tab("ast")

    def run_visualization(self, _=None):
        source = self.editor.get("1.0", tk.END).strip()
        if not source:
            self._status.set("⚠  Nothing to visualize", "", WARNING)
            return

        try:
            import visualization
            lexer = Lexer(source)
            parser = Parser(lexer)
            ast = parser.parse()
            
            if len(parser.errors) > 0:
                self._status.set(f"📊 Visualizing {len(parser.errors)} Error(s)", "", WARNING)
                visualization.visualize_errors(parser.errors)
            else:
                self._status.set("📊 Visualizing AST tree", "", SUCCESS)
                visualization.visualize_ast(ast)
                
        except Exception as e:
            tb = traceback.format_exc()
            text = f"✕  Visualization Error\n{'─'*45}\n\nMake sure you have installed networkx and matplotlib!\npip install networkx matplotlib\n\n{e}\n\n{tb}"
            self._write_output(self.output, text, ERROR)
            self._status.set("✕  Visualization crashed", "", ERROR)
            self._switch_tab("ast")


if __name__ == "__main__":
    app = App()
    app.mainloop()