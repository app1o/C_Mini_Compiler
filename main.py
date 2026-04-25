import tkinter as tk
from tkinter import font
import traceback
from lexer import Lexer, Token
from parser import Parser, AST

def dump_ast(node, indent=0):
    if node is None:
        return ""
    res = ""
    prefix = "  " * indent
    if isinstance(node, AST):
        res += prefix + f"[{node.__class__.__name__}]\n"
        for key, value in vars(node).items():
            if isinstance(value, list):
                res += prefix + f"  {key}:\n"
                for item in value:
                    res += dump_ast(item, indent + 2) + "\n"
            elif isinstance(value, AST):
                res += prefix + f"  {key}:\n"
                res += dump_ast(value, indent + 2) + "\n"
            else:
                if key == "token": continue  # Hide token wrappers to keep AST tree clean
                res += prefix + f"  {key}: {value}\n"
    else:
        res += prefix + str(node)
    return res.rstrip()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mini C-lite Compiler - syntax & parser tool")
        self.geometry("900x700")
        self.configure(bg="#2E3440") # Nordic dark theme
        
        # Fonts
        self.editor_font = font.Font(family="Consolas", size=13)
        self.output_font = font.Font(family="Consolas", size=11)

        # Title Label
        title_label = tk.Label(self, text="Syntax Checker & Recursive Descent Parser Viewer", bg="#2E3440", fg="#D8DEE9", font=("Segoe UI", 16, "bold"))
        title_label.pack(pady=(15, 5))

        # Main frame
        main_frame = tk.Frame(self, bg="#2E3440")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Editor
        editor_label = tk.Label(main_frame, text="Source Code Editor", bg="#2E3440", fg="#88C0D0", font=("Segoe UI", 12))
        editor_label.pack(anchor="w")
        
        # Add a text area frame so scrollbar looks inside
        txt_frame1 = tk.Frame(main_frame, bg="#3B4252")
        txt_frame1.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        self.editor = tk.Text(txt_frame1, height=14, bg="#3B4252", fg="#ECEFF4", insertbackground="#ECEFF4", font=self.editor_font, relief=tk.FLAT, padx=10, pady=10)
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Basic editor scrollbar
        scroll1 = tk.Scrollbar(txt_frame1, command=self.editor.yview)
        scroll1.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor.config(yscrollcommand=scroll1.set)
        
        # Default text sample
        sample_code = "int count = 0;\nwhile (count < 10) {\n    count = count + 1;\n}"
        self.editor.insert("1.0", sample_code)

        # Button Frame
        btn_frame = tk.Frame(main_frame, bg="#2E3440")
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.check_btn = tk.Button(btn_frame, text="Run Lexer & Parser", bg="#81A1C1", fg="#2E3440", activebackground="#5E81AC", activeforeground="#FFF", font=("Segoe UI", 11, "bold"), relief=tk.FLAT, padx=20, pady=8, command=self.run_check)
        self.check_btn.pack(side=tk.LEFT, expand=True, anchor="e", padx=10)

        self.vis_btn = tk.Button(btn_frame, text="Visualize AST & Errors", bg="#A3BE8C", fg="#2E3440", activebackground="#8FBCBB", activeforeground="#2E3440", font=("Segoe UI", 11, "bold"), relief=tk.FLAT, padx=20, pady=8, command=self.run_visualization)
        self.vis_btn.pack(side=tk.RIGHT, expand=True, anchor="w", padx=10)

        # Output Text
        output_label = tk.Label(main_frame, text="Parser Output / Abstract Syntax Tree (AST)", bg="#2E3440", fg="#A3BE8C", font=("Segoe UI", 12))
        output_label.pack(anchor="w")

        txt_frame2 = tk.Frame(main_frame, bg="#4C566A")
        txt_frame2.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.output = tk.Text(txt_frame2, height=14, bg="#2E3440", fg="#A3BE8C", font=self.output_font, relief=tk.FLAT, padx=10, pady=10, highlightthickness=1, highlightbackground="#4C566A")
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Basic output scrollbar
        scroll2 = tk.Scrollbar(txt_frame2, command=self.output.yview)
        scroll2.pack(side=tk.RIGHT, fill=tk.Y)
        self.output.config(yscrollcommand=scroll2.set)

    def run_check(self):
        source = self.editor.get("1.0", tk.END).strip()
        self.output.delete("1.0", tk.END)
        
        if not source:
            self.output.insert(tk.END, "Please write some code before checking.")
            return

        try:
            lexer = Lexer(source)
            parser = Parser(lexer)
            ast = parser.parse()
            
            if len(parser.errors) > 0:
                self.output.configure(fg="#BF616A") # Reddish error color
                error_message = f"❌ Parsing Finished with {len(parser.errors)} Error(s):\n\n"
                for err in parser.errors:
                    error_message += f"- {err}\n"
                self.output.insert(tk.END, error_message)
            else:
                output_text = "✅ Parsing Successful! No Syntax Errors Detected.\n\n"
                output_text += "Abstract Syntax Tree (AST) Visualization:\n"
                output_text += "="*45 + "\n\n"
                output_text += dump_ast(ast)
                
                self.output.configure(fg="#A3BE8C") # Greenish success color
                self.output.insert(tk.END, output_text)
            
        except Exception as e:
            self.output.configure(fg="#BF616A") # Reddish error color
            
            error_message = f"❌ Fatal Error (Compiler crashed):\n\n{str(e)}\n\n"
            error_message += "-"*45 + "\nDebug Trace:\n"
            error_message += traceback.format_exc()
            
            self.output.insert(tk.END, error_message)

    def run_visualization(self):
        source = self.editor.get("1.0", tk.END).strip()
        if not source:
            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END, "Please write some code before visualizing.")
            return

        try:
            import visualization
            lexer = Lexer(source)
            parser = Parser(lexer)
            ast = parser.parse()
            
            if len(parser.errors) > 0:
                visualization.visualize_errors(parser.errors)
            else:
                visualization.visualize_ast(ast)
                
        except Exception as e:
            self.output.delete("1.0", tk.END)
            self.output.configure(fg="#BF616A")
            self.output.insert(tk.END, f"Visualization Error:\n{str(e)}\n\n(Make sure 'matplotlib' and 'networkx' are installed via pip!)")

if __name__ == "__main__":
    app = App()
    app.mainloop()
