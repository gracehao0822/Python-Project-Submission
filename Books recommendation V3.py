import requests
import pandas as pd
import random
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
import io
import urllib.request
import webbrowser

class BookRecommendationSystem:
    """
    A book recommendation system that fetches data from Open Library API,
    processes it, and provides filtering and random recommendation features.
    """
    
    def __init__(self, data_file: str = 'books_data.json', cache_expiry_days: int = 7):
        self.data_file = data_file
        self.cache_expiry_days = cache_expiry_days
        self.books_df = None
        self._initialize_data()

    def _initialize_data(self) -> None:
        if self._is_cache_valid():
            try:
                self._load_data()
                print("Loaded book data from cache.")
                return
            except Exception as e:
                print(f"Error loading cached data: {e}. Fetching fresh data...")
        
        self._fetch_and_process_data()
        self._save_data()
        
    def _is_cache_valid(self) -> bool:
        if not os.path.exists(self.data_file):
            return False
            
        file_time = datetime.fromtimestamp(os.path.getmtime(self.data_file))
        return (datetime.now() - file_time).days < self.cache_expiry_days

    def _fetch_and_process_data(self) -> None:
        print("Fetching book data from Open Library API...")
        
        genres = [
            'fiction', 'mystery', 'science fiction', 'fantasy', 
            'romance', 'horror', 'history', 'biography'
        ]
        
        all_books = []
        
        for genre in genres:
            try:
                url = f"https://openlibrary.org/subjects/{genre}.json?limit=100"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                works = data.get('works', [])
                
                for work in works:
                    popularity = round(random.uniform(1, 5), 1) if random.random() > 0.3 else None
                    ranking = random.randint(1, 100) if random.random() > 0.2 else None
                    
                    book_info = {
                        'title': work.get('title', 'Unknown Title'),
                        'author': ', '.join(author.get('name', 'Unknown Author') 
                                  for author in work.get('authors', [{}])),
                        'genre': genre,
                        'year': work.get('first_publish_year', None),
                        'popularity': popularity or work.get('rating', {}).get('average', None),
                        'ranking': ranking or work.get('rank', None),
                        'cover_id': work.get('cover_id', None),
                        'key': work.get('key', None),
                        'heat_index': random.randint(0, 100)
                    }
                    all_books.append(book_info)
                    
            except requests.RequestException as e:
                print(f"Error fetching data for genre {genre}: {e}")
            except Exception as e:
                print(f"Unexpected error processing genre {genre}: {e}")
        
        self.books_df = pd.DataFrame(all_books)
        self._clean_data()
        print(f"Successfully fetched and processed {len(self.books_df)} books.")

    def _clean_data(self) -> None:
        if self.books_df is None:
            return
            
        # fullfill missing values
        self.books_df['author'].fillna('Unknown Author', inplace=True)
        self.books_df['title'].fillna('Unknown Title', inplace=True)
        self.books_df['year'] = pd.to_numeric(self.books_df['year'], errors='coerce')
        
        # random generate value for popularity and ranking data
        self.books_df['popularity'] = self.books_df['popularity'].apply(
            lambda x: round(random.uniform(1, 5), 1) if pd.isna(x) else x)
        self.books_df['ranking'] = self.books_df['ranking'].apply(
            lambda x: random.randint(1, 100) if pd.isna(x) else x)
        
        # generate head_index
        if 'heat_index' not in self.books_df.columns:
            self.books_df['heat_index'] = random.randint(0, 100)
        
        # calculate composite_score with different weight of popularity, ranking and head_index
        try:
            self.books_df['composite_score'] = (
                self.books_df['popularity'].fillna(3) * 0.6 + 
                (100 - self.books_df['ranking'].fillna(50)) * 0.3 +
                self.books_df['heat_index'].fillna(50) * 0.1
            )
        except Exception as e:
            print(f"Error calculating composite score: {e}")
            # if fail to calculate,give a defualt value
            self.books_df['composite_score'] = 50.0
        
        # drop duplicates for title and author
        self.books_df = self.books_df.drop_duplicates(
            subset=['title', 'author'], 
            keep='first').reset_index(drop=True)

    def _save_data(self) -> None:
        if self.books_df is not None:
            try:
                self.books_df.to_json(self.data_file, orient='records', indent=2)
                print(f"Book data saved to {self.data_file}")
            except Exception as e:
                print(f"Error saving data: {e}")

    def _load_data(self) -> None:
        try:
            self.books_df = pd.read_json(self.data_file, orient='records')
            print(f"Loaded {len(self.books_df)} books from {self.data_file}")
        except Exception as e:
            print(f"Error loading data: {e}")
            raise

    def get_available_genres(self) -> List[str]:
        if self.books_df is None:
            return []
        return sorted(self.books_df['genre'].unique().tolist())

    def filter_books(
        self,
        genre: Optional[str] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        min_popularity: Optional[float] = None,
        max_ranking: Optional[int] = None,
        min_heat: Optional[int] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        if self.books_df is None:
            return pd.DataFrame()
            
        try:
            # confirm composite_score column exist
            if 'composite_score' not in self.books_df.columns:
                self._clean_data()  # clean composit_score data
                
            filtered = self.books_df.copy()
            
            if genre:
                filtered = filtered[filtered['genre'] == genre.lower()]
            if min_year is not None:
                filtered = filtered[filtered['year'] >= min_year]
            if max_year is not None:
                filtered = filtered[filtered['year'] <= max_year]
            if min_popularity is not None:
                filtered = filtered[filtered['popularity'] >= min_popularity]
            if max_ranking is not None:
                filtered = filtered[filtered['ranking'] <= max_ranking]
            if min_heat is not None:
                filtered = filtered[filtered['heat_index'] >= min_heat]
                
            # double confirm composite_score column exist
            if 'composite_score' in filtered.columns:
                filtered = filtered.sort_values('composite_score', ascending=False)
            else:
                # if composite_score column not exist，order value sby popularity
                filtered = filtered.sort_values('popularity', ascending=False)
            
            if limit is not None:
                filtered = filtered.head(limit)
                
            return filtered.reset_index(drop=True)
            
        except Exception as e:
            print(f"Error filtering books: {e}")
            return pd.DataFrame()

    def get_random_book(self, genre: Optional[str] = None) -> Optional[Dict[str, Union[str, int]]]:
        if self.books_df is None or len(self.books_df) == 0:
            return None
            
        filtered = self.books_df.copy()
        
        if genre:
            filtered = filtered[filtered['genre'] == genre.lower()]
            
        if len(filtered) == 0:
            return None
            
        random_book = filtered.sample(1).iloc[0].to_dict()
        
        return {
            'title': random_book.get('title', 'Unknown Title'),
            'author': random_book.get('author', 'Unknown Author'),
            'genre': random_book.get('genre', 'Unknown Genre'),
            'year': random_book.get('year', 'Unknown Year'),
            'popularity': random_book.get('popularity', 'Not rated'),
            'ranking': random_book.get('ranking', 'Not ranked'),
            'heat_index': random_book.get('heat_index', 'Unknown'),
            'cover_url': f"https://covers.openlibrary.org/b/id/{random_book.get('cover_id', '')}-M.jpg" 
                         if random_book.get('cover_id') else None,
            'open_library_url': f"https://openlibrary.org{random_book.get('key', '')}" 
                                if random_book.get('key') else None
        }

class BookRecommendationGUI:
    """
    Graphical User Interface for the Book Recommendation System.
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Book Recommendation System")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Initialize the recommendation system
        self.book_system = BookRecommendationSystem()
        
        # Create main container
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for multiple tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_browse_tab()
        self.create_recommendation_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(
            self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X)
        
        # Center the window
        self.center_window()
        
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_browse_tab(self):
        """Create the tab for browsing books with filters."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Browse Books")
        
        # Filter frame
        filter_frame = ttk.LabelFrame(tab, text="Filters", padding="10")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Genre filter
        ttk.Label(filter_frame, text="Genre:").grid(row=0, column=0, sticky=tk.W)
        self.genre_var = tk.StringVar()
        self.genre_combobox = ttk.Combobox(
            filter_frame, textvariable=self.genre_var,
            values=self.book_system.get_available_genres(), state="readonly")
        self.genre_combobox.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        self.genre_combobox.bind("<<ComboboxSelected>>", self._update_genre)
        
        # Year range filter
        ttk.Label(filter_frame, text="Publication Year:").grid(row=1, column=0, sticky=tk.W)
        year_frame = ttk.Frame(filter_frame)
        year_frame.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(year_frame, text="From:").pack(side=tk.LEFT)
        self.min_year_var = tk.StringVar()
        self.min_year_entry = ttk.Entry(year_frame, textvariable=self.min_year_var, width=6)
        self.min_year_entry.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(year_frame, text="To:").pack(side=tk.LEFT)
        self.max_year_var = tk.StringVar()
        self.max_year_entry = ttk.Entry(year_frame, textvariable=self.max_year_var, width=6)
        self.max_year_entry.pack(side=tk.LEFT, padx=2)
        
        # Popularity filter
        ttk.Label(filter_frame, text="Min Popularity (1-5):").grid(row=2, column=0, sticky=tk.W)
        self.min_popularity_var = tk.StringVar()
        self.min_popularity_entry = ttk.Entry(
            filter_frame, textvariable=self.min_popularity_var, width=6)
        self.min_popularity_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Ranking filter
        ttk.Label(filter_frame, text="Max Ranking (lower is better):").grid(row=3, column=0, sticky=tk.W)
        self.max_ranking_var = tk.StringVar()
        self.max_ranking_entry = ttk.Entry(
            filter_frame, textvariable=self.max_ranking_var, width=6)
        self.max_ranking_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Limit results
        ttk.Label(filter_frame, text="Max Results:").grid(row=4, column=0, sticky=tk.W)
        self.limit_var = tk.StringVar(value="50")
        self.limit_entry = ttk.Entry(filter_frame, textvariable=self.limit_var, width=6)
        self.limit_entry.grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Apply filters button
        apply_button = ttk.Button(
            filter_frame, text="Apply Filters", command=self.apply_filters)
        apply_button.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Results frame
        results_frame = ttk.LabelFrame(tab, text="Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview for displaying books
        self.tree = ttk.Treeview(results_frame, columns=(
            "Title", "Author", "Genre", "Year", "Popularity", "Ranking"), show="headings")
        
        # Configure columns
        columns = {
            "Title": 200,
            "Author": 150,
            "Genre": 100,
            "Year": 50,
            "Popularity": 80,
            "Ranking": 80
        }
        
        for col, width in columns.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=tk.W if col in ["Title", "Author"] else tk.CENTER)
        
        # Add scrollbars
        yscroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        xscroll = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=yscroll.set, xscroll=xscroll.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        yscroll.grid(row=0, column=1, sticky=tk.NS)
        xscroll.grid(row=1, column=0, sticky=tk.EW)
        
        # Configure grid weights
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Double-click event for book details
        self.tree.bind("<Double-1>", self.show_book_details)
        
    def create_recommendation_tab(self):
        """Create the tab for getting random book recommendations."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Random Recommendation")
        
        # Recommendation frame
        rec_frame = ttk.LabelFrame(tab, text="Get Recommendation", padding="10")
        rec_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Genre selection
        ttk.Label(rec_frame, text="Select Genre:").grid(row=0, column=0, sticky=tk.W)
        self.rec_genre_var = tk.StringVar()
        self.rec_genre_combobox = ttk.Combobox(
            rec_frame, textvariable=self.rec_genre_var,
            values=["Any"] + self.book_system.get_available_genres(), state="readonly")
        self.rec_genre_combobox.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.rec_genre_combobox.current(0)
        
        # Get recommendation button
        get_rec_button = ttk.Button(
            rec_frame, text="Get Random Recommendation", command=self.get_recommendation)
        get_rec_button.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Recommendation display frame
        display_frame = ttk.Frame(rec_frame)
        display_frame.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW, pady=10)
        
        # Book cover image
        self.cover_image = None
        self.cover_label = ttk.Label(display_frame)
        self.cover_label.pack(side=tk.LEFT, padx=10)
        
        # Book details
        details_frame = ttk.Frame(display_frame)
        details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.book_title_var = tk.StringVar(value="")
        ttk.Label(details_frame, textvariable=self.book_title_var, 
                 font=('TkDefaultFont', 12, 'bold')).pack(anchor=tk.W)
        
        self.book_author_var = tk.StringVar(value="")
        ttk.Label(details_frame, textvariable=self.book_author_var).pack(anchor=tk.W)
        
        self.book_genre_var = tk.StringVar(value="")
        ttk.Label(details_frame, textvariable=self.book_genre_var).pack(anchor=tk.W)
        
        self.book_year_var = tk.StringVar(value="")
        ttk.Label(details_frame, textvariable=self.book_year_var).pack(anchor=tk.W)
        
        self.book_popularity_var = tk.StringVar(value="")
        ttk.Label(details_frame, textvariable=self.book_popularity_var).pack(anchor=tk.W)
        
        self.book_ranking_var = tk.StringVar(value="")
        ttk.Label(details_frame, textvariable=self.book_ranking_var).pack(anchor=tk.W)
        
        # Open Library link
        self.open_library_link = ttk.Label(details_frame, text="", cursor="hand2")
        self.open_library_link.pack(anchor=tk.W, pady=5)
        self.open_library_link.bind("<Button-1>", self.open_web_link)
        
        # Configure grid weights
        rec_frame.grid_rowconfigure(2, weight=1)
        rec_frame.grid_columnconfigure(1, weight=1)
        
    def _update_genre(self, event=None):
        selected_genre = self.genre_var.get()
        if selected_genre:
            self.rec_genre_combobox.set(selected_genre)
    
    def apply_filters(self):
        try:
            # Get filter values
            genre = self.genre_var.get() if self.genre_var.get() else None
            min_year = int(self.min_year_var.get()) if self.min_year_var.get() else None
            max_year = int(self.max_year_var.get()) if self.max_year_var.get() else None
            min_popularity = float(self.min_popularity_var.get()) if self.min_popularity_var.get() else None
            max_ranking = int(self.max_ranking_var.get()) if self.max_ranking_var.get() else None
            limit = int(self.limit_var.get()) if self.limit_var.get() else None
            
            # Apply filters
            filtered_books = self.book_system.filter_books(
                genre=genre,
                min_year=min_year,
                max_year=max_year,
                min_popularity=min_popularity,
                max_ranking=max_ranking,
                limit=limit
            )
            
            # Clear previous results
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Add new results
            for _, row in filtered_books.iterrows():
                self.tree.insert("", tk.END, values=(
                    row['title'],
                    row['author'],
                    row['genre'],
                    int(row['year']) if pd.notnull(row['year']) else "Unknown",
                    f"{row['popularity']:.1f}" if pd.notnull(row['popularity']) else "Not rated",
                    f"#{row['ranking']}" if pd.notnull(row['ranking']) else "Not ranked"
                ))
            
            self.status_var.set(f"Found {len(filtered_books)} books matching your criteria.")
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"Please enter valid numbers for filters.\nError: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while filtering books.\nError: {e}")
    
    def show_book_details(self, event):
        item = self.tree.selection()[0]
        values = self.tree.item(item, 'values')
        
        detail_window = tk.Toplevel(self.root)
        detail_window.title("Book Details")
        detail_window.geometry("500x400")
        
        title_label = ttk.Label(detail_window, text=values[0], font=('TkDefaultFont', 14, 'bold'))
        title_label.pack(pady=10)
        
        details = [
            f"Author: {values[1]}",
            f"Genre: {values[2]}",
            f"Year: {values[3]}",
            f"Popularity: {values[4]}",
            f"Ranking: {values[5]}"
        ]
        
        for detail in details:
            ttk.Label(detail_window, text=detail).pack(anchor=tk.W, padx=20, pady=2)
        
        ttk.Button(detail_window, text="Close", command=detail_window.destroy).pack(pady=10)
        self.center_child_window(detail_window)
    
    def center_child_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')
    
    def get_recommendation(self):
        try:
            genre = self.rec_genre_var.get() if self.rec_genre_var.get() != "Any" else None
            book = self.book_system.get_random_book(genre=genre)
            
            if book is None:
                messagebox.showinfo("No Books Found", "No books found matching your criteria.")
                return
            
            self.book_title_var.set(f"Title: {book['title']}")
            self.book_author_var.set(f"Author: {book['author']}")
            self.book_genre_var.set(f"Genre: {book['genre'].title()}")
            self.book_year_var.set(f"Year: {book['year']}")
            self.book_popularity_var.set(f"Popularity: {book['popularity']}")
            self.book_ranking_var.set(f"Ranking: {book['ranking']}")
            
            self.update_cover_image(book['cover_url'])
            
            if book['open_library_url']:
                self.open_library_link.config(text="More info on Open Library")
                self.open_library_link.url = book['open_library_url']
            else:
                self.open_library_link.config(text="")
                self.open_library_link.url = None
            
            self.status_var.set("Here's your random book recommendation!")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while getting recommendation.\nError: {e}")
    
    def update_cover_image(self, image_url):
        if not image_url:
            default_image = Image.new('RGB', (200, 300), color='lightgray')
            self.cover_image = ImageTk.PhotoImage(default_image)
            self.cover_label.config(image=self.cover_image)
            self.cover_label.image = self.cover_image
            return
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(image_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as url:
                image_data = url.read()
            
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail((200, 300), Image.Resampling.LANCZOS)
            
            self.cover_image = ImageTk.PhotoImage(image)
            self.cover_label.config(image=self.cover_image)
            self.cover_label.image = self.cover_image
            
        except Exception as e:
            print(f"Error loading cover image: {e}")
            default_image = Image.new('RGB', (200, 300), color='lightgray')
            self.cover_image = ImageTk.PhotoImage(default_image)
            self.cover_label.config(image=self.cover_image)
            self.cover_label.image = self.cover_image
    
    def open_web_link(self, event):
        if hasattr(self.open_library_link, 'url') and self.open_library_link.url:
            webbrowser.open(self.open_library_link.url)

def main():
    root = tk.Tk()
    app = BookRecommendationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()