import tkinter as tk
from tkinter import messagebox
import sys
import threading
import time

# Konstanten für Schachspalten (a-h entsprechen 0-7, kleingeschrieben wie in der Schachnotation)
a = 0
b = 1
c = 2
d = 3
e = 4
f = 5
g = 6
h = 7

class ChessBoard:
    def __init__(self, root):
        self.root = root
        self.root.title("Schach")
        # Startgröße und minimale Fenstergröße setzen
        self.root.geometry("800x800")
        self.root.minsize(400, 400)
        # 8x8 Brett als Liste von Listen, None bedeutet leeres Feld
        self.board = [[None for _ in range(8)] for _ in range(8)]
        # Buttons für die GUI
        self.buttons = [[None for _ in range(8)] for _ in range(8)]
        # Ausgewählte Figur (Koordinaten oder None)
        self.selected_piece = None
        # Aktueller Spieler (white oder black)
        self.current_player = "white"
        # En-Passant-Zielfeld, falls verfügbar
        self.en_passant_target = None
        # Verfolgt, ob Rochade für weiß und schwarz möglich ist
        self.castling_available = {
            "white": {"king_side": True, "queen_side": True},
            "black": {"king_side": True, "queen_side": True}
        }
        self.setup_board()
        self.setup_sound()
        self.create_gui()

    def setup_board(self):
        # Unicode-Symbole für Schachfiguren (z.B. weißer König = ♔)
        self.pieces_unicode = {
            ("king", "white"): "♔", ("queen", "white"): "♕", ("rook", "white"): "♖",
            ("bishop", "white"): "♗", ("knight", "white"): "♘", ("pawn", "white"): "♙",
            ("king", "black"): "♚", ("queen", "black"): "♛", ("rook", "black"): "♜",
            ("bishop", "black"): "♝", ("knight", "black"): "♞", ("pawn", "black"): "♟"
        }
        # Startaufstellung der Figuren
        # Weiße Figuren auf Zeilen 0 (Hauptfiguren) und 1 (Bauern)
        self.put_piece("rook", "white", a, 1)
        self.put_piece("knight", "white", b, 1)
        self.put_piece("bishop", "white", c, 1)
        self.put_piece("queen", "white", d, 1)
        self.put_piece("king", "white", e, 1)
        self.put_piece("bishop", "white", f, 1)
        self.put_piece("knight", "white", g, 1)
        self.put_piece("rook", "white", h, 1)
        for col in [a, b, c, d, e, f, g, h]:
            self.put_piece("pawn", "white", col, 2)
        # Schwarze Figuren auf Zeilen 7 (Hauptfiguren) und 6 (Bauern)
        self.put_piece("rook", "black", a, 8)
        self.put_piece("knight", "black", b, 8)
        self.put_piece("bishop", "black", c, 8)
        self.put_piece("queen", "black", d, 8)
        self.put_piece("king", "black", e, 8)
        self.put_piece("bishop", "black", f, 8)
        self.put_piece("knight", "black", g, 8)
        self.put_piece("rook", "black", h, 8)
        for col in [a, b, c, d, e, f, g, h]:
            self.put_piece("pawn", "black", col, 7)

    def setup_sound(self):
        """Erstelle einen einfachen Sound für ungültige Züge"""
        self.sound_available = True
        try:
            # Versuche winsound zu importieren (Windows)
            import winsound
            self.play_sound = lambda: winsound.Beep(200, 200)  # 800Hz für 200ms
        except ImportError:
            try:
                # Für Unix/Linux/Mac - verwende os.system mit beep
                import os
                # Test ob beep verfügbar ist
                if os.system("which beep > /dev/null 2>&1") == 0:
                    self.play_sound = lambda: os.system("beep -f 800 -l 200 > /dev/null 2>&1")
                else:
                    # Fallback: Terminal bell
                    self.play_sound = lambda: os.system("printf '\a'")
            except:
                # Wenn nichts funktioniert, verwende einen synthetischen Sound
                self.play_sound = self.generate_beep_sound
    
    def put_piece(self, piece, color, col, row):
        # Spalte ist bereits ein Index (0-7) durch Konstanten wie a, b, ..., h
        col_index = col
        # Zeilen sind 1-8, aber intern 0-7 (row - 1)
        row_index = row - 1
        # Prüfe, ob das Feld auf dem Brett liegt
        if 0 <= col_index < 8 and 0 <= row_index < 8:
            self.board[col_index][row_index] = (piece, color)
            # Aktualisiere den Button-Text mit dem Unicode-Symbol
            if self.buttons[col_index][row_index]:
                piece_symbol = self.pieces_unicode.get((piece, color), "")
                self.buttons[col_index][row_index].config(text=piece_symbol)

    def create_gui(self):
        # Erstelle das GUI-Fenster mit einem 8x8-Gitter
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Konfiguriere die Gewichtungen für Zeilen und Spalten
        for i in range(8):
            self.frame.grid_rowconfigure(i, weight=1)
            self.frame.grid_columnconfigure(i, weight=1)
        
        for row in range(8, 0, -1):  # Zeilen von 8 nach 1 (umgekehrte Reihenfolge für GUI)
            for col in range(8):  # Spalten 0-7 (entsprechen a-h)
                # Wechselnde Farben für Schachbrettmuster - a1 ist dunkel
                # GUI-Zeile 8-row entspricht Brett-Zeile row-1
                board_row = row - 1
                background_color = "gray" if (col + board_row) % 2 == 0 else "white"
                button = tk.Button(self.frame, text="", font=("Arial", 32), 
                                   bg=background_color,
                                   command=lambda c=col, r=row: self.click(c, r))
                # Button im GUI platzieren (Zeilen umgedreht für Anzeige)
                # sticky="nsew" sorgt dafür, dass der Button das ganze Feld ausfüllt
                button.grid(row=8-row, column=col, sticky="nsew")
                self.buttons[col][row-1] = button
        
        # Event-Binding für Fenstergrößenänderungen
        self.root.bind('<Configure>', self.on_window_resize)
        self.update_board()

    def on_window_resize(self, event):
        # Wird aufgerufen, wenn sich die Fenstergröße ändert
        if event.widget == self.root:
            # Berechne neue Schriftgröße basierend auf der Fenstergröße
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            # Verwende die kleinere Dimension für die Schriftgröße
            min_dimension = min(width, height)
            # Schriftgröße proportional zur Fenstergröße (mit Mindest- und Höchstwerten)
            font_size = max(16, min(48, min_dimension // 15))
            
            # Aktualisiere alle Buttons mit der neuen Schriftgröße
            for row in range(8):
                for col in range(8):
                    self.buttons[col][row].config(font=("Arial", font_size))

    def update_board(self):
        # Aktualisiere alle Buttons mit den aktuellen Figuren und Farben
        for col in range(8):
            for row in range(8):
                piece = self.board[col][row]
                if piece:
                    piece_symbol = self.pieces_unicode.get(piece, "")
                else:
                    piece_symbol = ""
                # Setze die Hintergrundfarbe basierend auf der Position (a1 ist dunkel)
                background_color = "gray" if (col + row) % 2 == 0 else "white"
                self.buttons[col][row].config(text=piece_symbol, bg=background_color)

    def click(self, col, row):
        # Behandelt Mausklicks auf dem Brett
        row_index = row - 1  # GUI-Zeilen sind 1-8, intern 0-7
        if self.selected_piece is None:
            # Keine Figur ausgewählt: Prüfe, ob eine Figur angeklickt wurde
            piece = self.board[col][row_index]
            if piece and piece[1] == self.current_player:
                self.selected_piece = (col, row_index)
                self.buttons[col][row_index].config(bg="yellow")
        else:
            # Figur ausgewählt: Versuche, einen Zug zu machen
            from_col, from_row = self.selected_piece
            if self.is_valid_move(from_col, from_row, col, row_index):
                self.move_piece(from_col, from_row, col, row_index)
                self.current_player = "black" if self.current_player == "white" else "white"
                self.selected_piece = None
                self.update_board()  # Aktualisiert alle Button-Farben
            else:
                # Sound für ungültigen Zug abspielen
                self.play_sound()
                # Farbe des ursprünglichen Feldes zurücksetzen
                original_color = "gray" if (from_col + from_row) % 2 == 0 else "white"
                self.buttons[from_col][from_row].config(bg=original_color)
                self.selected_piece = None

    def move_piece(self, from_col, from_row, to_col, to_row):
        # Bewege eine Figur von einem Feld zum anderen
        piece, color = self.board[from_col][from_row]
        self.board[to_col][to_row] = self.board[from_col][from_row]
        self.board[from_col][from_row] = None
        # En-Passant-Logik
        if piece == "pawn" and abs(to_col - from_col) == 1:
            if color == "white" and to_row == 5 and self.en_passant_target == (to_col, to_row):
                self.board[to_col][to_row-1] = None  # Entferne gegnerischen Bauern
            elif color == "black" and to_row == 2 and self.en_passant_target == (to_col, to_row):
                self.board[to_col][to_row+1] = None  # Entferne gegnerischen Bauern
        self.en_passant_target = None
        # Setze En-Passant-Zielfeld, wenn Bauer zwei Felder vorrückt
        if piece == "pawn" and abs(to_row - from_row) == 2:
            self.en_passant_target = (to_col, (from_row + to_row) // 2)
        # Rochade-Logik
        if piece == "king" and abs(to_col - from_col) == 2:
            if to_col == 6:  # Kurze Rochade
                self.board[5][to_row] = self.board[7][to_row]  # Turm bewegen
                self.board[7][to_row] = None
            elif to_col == 2:  # Lange Rochade
                self.board[3][to_row] = self.board[0][to_row]  # Turm bewegen
                self.board[0][to_row] = None
        # Aktualisiere Rochade-Rechte
        if piece == "king":
            self.castling_available[color]["king_side"] = False
            self.castling_available[color]["queen_side"] = False
        if piece == "rook":
            if from_col == 0:
                self.castling_available[color]["queen_side"] = False
            elif from_col == 7:
                self.castling_available[color]["king_side"] = False

    def is_valid_move(self, from_col, from_row, to_col, to_row):
        # Prüfe, ob ein Zug gültig ist
        piece, color = self.board[from_col][from_row]
        if not (0 <= to_col < 8 and 0 <= to_row < 8):
            return False
        target = self.board[to_col][to_row]
        if target and target[1] == color:
            return False
        # Bauer
        if piece == "pawn":
            direction = 1 if color == "white" else -1
            start_row = 1 if color == "white" else 6
            if to_col == from_col and to_row == from_row + direction and not target:
                return True
            if to_col == from_col and to_row == from_row + 2 * direction and from_row == start_row and not target and not self.board[to_col][from_row + direction]:
                return True
            if abs(to_col - from_col) == 1 and to_row == from_row + direction:
                if target or (to_col, to_row) == self.en_passant_target:
                    return True
        # Springer
        elif piece == "knight":
            col_diff = abs(to_col - from_col)
            row_diff = abs(to_row - from_row)
            if (col_diff == 1 and row_diff == 2) or (col_diff == 2 and row_diff == 1):
                return True
        # Läufer
        elif piece == "bishop":
            if abs(to_col - from_col) == abs(to_row - from_row):
                return self.is_path_clear(from_col, from_row, to_col, to_row)
        # Turm
        elif piece == "rook":
            if to_col == from_col or to_row == from_row:
                return self.is_path_clear(from_col, from_row, to_col, to_row)
        # Dame
        elif piece == "queen":
            if to_col == from_col or to_row == from_row or abs(to_col - from_col) == abs(to_row - from_row):
                return self.is_path_clear(from_col, from_row, to_col, to_row)
        # König
        elif piece == "king":
            if max(abs(to_col - from_col), abs(to_row - from_row)) <= 1:
                return True
            # Rochade
            if color == self.current_player and abs(to_col - from_col) == 2 and to_row == from_row:
                # Prüfe, ob der König aktuell im Schach steht
                if self.is_attacked(from_col, from_row, "black" if color == "white" else "white"):
                    return False
                if to_col == 6 and self.castling_available[color]["king_side"]:
                    # Kurze Rochade: Felder f und g dürfen nicht angegriffen sein, Pfad muss frei sein
                    return (self.is_path_clear(from_col, from_row, 7, to_row) and
                            not self.is_attacked(5, to_row, "black" if color == "white" else "white") and
                            not self.is_attacked(6, to_row, "black" if color == "white" else "white"))
                if to_col == 2 and self.castling_available[color]["queen_side"]:
                    # Lange Rochade: Felder d und c dürfen nicht angegriffen sein, Pfad muss frei sein
                    # Zusätzlich muss b frei sein (b1/b8 für weiß/schwarz)
                    return (self.is_path_clear(from_col, from_row, 0, to_row) and
                            not self.board[1][to_row] and  # b1/b8 frei
                            not self.is_attacked(3, to_row, "black" if color == "white" else "white") and
                            not self.is_attacked(2, to_row, "black" if color == "white" else "white"))
        return False

    def is_path_clear(self, from_col, from_row, to_col, to_row):
        # Prüfe, ob der Pfad zwischen zwei Feldern frei ist
        col_step = 0 if to_col == from_col else (1 if to_col > from_col else -1)
        row_step = 0 if to_row == from_row else (1 if to_row > from_row else -1)
        steps = max(abs(to_col - from_col), abs(to_row - from_row))
        for i in range(1, steps):
            current_col = from_col + i * col_step
            current_row = from_row + i * row_step
            if self.board[current_col][current_row]:
                return False
        return True

    def is_attacked(self, col, row, by_color=None):
        # Prüfe, ob ein Feld von einer gegnerischen Figur angegriffen wird
        if by_color is None:
            by_color = "black" if self.current_player == "white" else "white"
        for check_col in range(8):
            for check_row in range(8):
                piece = self.board[check_col][check_row]
                if piece and piece[1] == by_color:
                    if self.is_valid_move(check_col, check_row, col, row):
                        return True
        return False

if __name__ == "__main__":
    root = tk.Tk()
    app = ChessBoard(root)
    root.mainloop()