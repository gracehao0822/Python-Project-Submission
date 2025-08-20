README - Book Recommendation System
1.	Project Description 
The Book Recommendation System is a application that helps users discover books based on their preferences. It fetches data from the Open Library API, processes it, and provides an intuitive graphical interface for browsing and discovering books across various genres.

2.	Functionality
•	Data Fetching: Retrieves book information from the Open Library API
•	Data Caching: Stores book data locally with configurable expiration
•	Advanced Filtering: Filter books by genre, publication year, popularity, ranking, and heat index
•	Random Recommendations: Get personalized random book suggestions
•	Book Details: View comprehensive information about each book
•	External Links: Direct access to Open Library pages for more information

3.	Technical Implementation
Software Requirements
•	Python 3.7+
Libraries Used
•	requests: HTTP requests to the Open Library API
•	pandas: Data manipulation and processing
•	tkinter: Graphical user interface
•	PIL (Pillow): Image processing and display
•	json: Data serialization
•	os: File system operations
•	datetime: Date and time handling
•	random: Random selection functionality
•	urllib: Additional HTTP functionality
•	webbrowser: Opening external links
•	io: Input/output operations

4.	User instruction:
Installation
1.	Ensure Python 3.7+ is installed on your system
2.	Install required packages
3.	Run the application: Books recommendation V3.py
Browse Books Tab
1.	Select a genre from the dropdown (optional)
2.	Set publication year range (optional)
3.	Specify minimum popularity (1-5 scale)
4.	Set maximum ranking (lower numbers are better)
5.	Choose how many results to display
6.	Click "Apply Filters" to see matching books
7.	Double-click any book to view detailed information
Random Recommendation Tab
1.	Select a genre or choose "Any" for all genres
2.	Click "Get Random Recommendation"
3.	View the recommended book with details
4.	Click "More info on Open Library" to view the book on the Open Library website
