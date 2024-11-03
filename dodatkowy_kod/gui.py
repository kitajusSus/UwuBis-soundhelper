import tkinter as tk
from tkinter import filedialog, messagebox
from main import Main

class App:
    def __init__(self, root):
        self.main = Main()
        self.root = root
        self.root.title("Audio Progress Tracker")
        
        self.label = tk.Label(root, text="Wybierz folder z plikami audio")
        self.label.pack(pady=10)
        
        self.select_button = tk.Button(root, text="Wybierz folder", command=self.select_folder)
        self.select_button.pack(pady=10)
        
        self.progress_label = tk.Label(root, text="")
        self.progress_label.pack(pady=10)
    
    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.main.katalog_audio = folder_selected
            self.show_progress()
    
    def show_progress(self):
        if self.main.ile_slow_do_rozpoznania is None or self.main.ile_slow_do_rozpoznania == 0:
            messagebox.showerror("Error", "ile_slow_do_rozpoznania is not set or is zero.")
            return
        progress_text = "Progres:\n"
        for file, progress in self.main.bookmarks.items():
            if isinstance(progress, (int, float)) and self.main.ile_slow_do_rozpoznania != 0:
                completion = (progress / self.main.ile_slow_do_rozpoznania) * 100
                progress_text += f"{file}: {completion:.2f}% ukończono\n"
            else:
                progress_text += f"{file}: Progress data unavailable\n"
        self.progress_label.config(text=progress_text)
        self.run_main()
    def run_main(self):
        self.main.run()    

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()