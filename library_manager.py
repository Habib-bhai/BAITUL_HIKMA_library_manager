import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from pymongo import MongoClient
from litellm import completion
import os
from dotenv import load_dotenv
import requests


load_dotenv()

DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING")

# function to search directly from browser using google's programmable custom search engine.
def search_google(query: str) -> str:
    """Fetches top search results from Google Custom Search API."""
    GOOGLE_API_KEY = st.secrets["UNRESTRICTED_KEY"]
    CX_ID = st.secrets["CX_ID"]
    
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={CX_ID}"
    response = requests.get(url).json()
    results = response.get("items", [])
    if not results:
        return "No relevant search results found."

    # Format top results
    
    # Format top results
    search_summary = "\n".join([f"- {item['link']}" for item in results[:3]])
    
    return f"Here are the latest search results:\n{search_summary}"


# searching tool for gemini api, to equip it with searching capabilities (not using right now will use it later on)
# tools = [
#     {
#         "type": "function",
#         "function": {
#             "name": "search_google",
#             "description": "Fetches live search results from Google Search API",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "query": {"type": "string", "description": "Search query string"}
#                 },
#                 "required": ["query"]
#             }
#         }
#     }
# ]

 

gemini_api_key = st.secrets["GEMINI_API_KEY"]

os.environ["GEMINI_API_KEY"] = gemini_api_key


def main():
    st.set_page_config(
    page_title="PIONEERS - Library ",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
    )

    # Custom CSS for styling
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem;
            font-weight: 500;
            margin-bottom: 1rem;
        }
        .card {
            padding: 1.5rem;
            border-radius: 0.7rem;
            background-color: #f8f9fa;
            box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
            margin-bottom: 1rem;
        }
        .success-msg {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #d4edda;
            color: #155724;
            margin-bottom: 1rem;
        }
        .error-msg {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #f8d7da;
            color: #721c24;
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # MongoDB Connection
    @st.cache_resource
    def init_connection():
        return MongoClient("mongodb+srv://habib:yucfudbyuckfu@cluster0.5aovr.mongodb.net/")

    client = init_connection()
    db = client["hikmamanager"]
    library_collection = db["library"]

    # Initialize session state variables if they don't exist
    if 'add_success' not in st.session_state:
        st.session_state.add_success = False

    if 'remove_success' not in st.session_state:
        st.session_state.remove_success = False

    # MongoDB Functions
    def add_book(title, author, publication_year, genre, read_status):
        library_collection.insert_one({
            "title": title,
            "author": author,
            "publication_year": publication_year,
            "genre": genre,
            "read_status": read_status
        })

    def remove_book(title_or_author):
        if title_or_author:
            searchValue = {
                "$or":[
                    {"title": {"$regex": title_or_author, "$options": "i"}},
                    {"author": {"$regex": title_or_author, "$options": "i"}}
                ]
            }
            library_collection.delete_one(searchValue)

    def get_all_books():
        return list(library_collection.find())

    def search_book(title_or_author):
        if title_or_author:
            searchValue = {
                "$or":[
                    {"title": {"$regex": title_or_author, "$options": "i"}},
                    {"author": {"$regex": title_or_author, "$options": "i"}}
                ]
            }
            return list(library_collection.find(searchValue))
        return []

    def display_stats():
        total_number_of_books = library_collection.count_documents({})
        total_books_read = library_collection.count_documents({"read_status": "yes"})

        stats = {
            "total_books": total_number_of_books,
            "books_read": total_books_read
        }

        if total_number_of_books > 0:
            stats["percentage_read"] = (total_books_read / total_number_of_books) * 100
        else:
            stats["percentage_read"] = 0

        return stats

    # Sidebar
    with st.sidebar:
        st.image("https://place-hold.it/300x100?text=PIONEERS&fontsize=23", width=250)
        st.markdown("### Your Personal Library Manager")
        st.markdown("---")

        # Get stats for the sidebar
        stats = display_stats()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Books", stats["total_books"])
        with col2:
            st.metric("Read", f"{stats['percentage_read']:.1f}%")

    # Main content
    st.markdown("<h1 class='main-header'>📚 PIONEERS - Library </h1>", unsafe_allow_html=True)

    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📝 Add Book", "🗑️ Remove Book", "🔍 Search", "📖 All Books", "📊 Statistics", "👨🏻‍💻 Ai Help in Finding Book"])

    # Tab 1: Add a book
    with tab1:
        st.markdown("<h2 class='sub-header'>Add a New Book</h2>", unsafe_allow_html=True)

        with st.container():
            col1, col2 = st.columns(2)

            with col1:
                with st.form("add_book_form"):
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    title = st.text_input("Book Title*")
                    author = st.text_input("Author*")
                    genre = st.selectbox("Genre", ["Fiction", "Non-Fiction", "Science Fiction", "Fantasy", "Mystery", 
                                                  "Thriller", "Romance", "Biography", "History", "Self-Help", "Other"])
                    publication_year = st.number_input("Publication Year", min_value=1000, max_value=datetime.now().year, 
                                          value=datetime.now().year)
                    read_status = st.radio("Read Status", ["yes", "no"])

                    submit_button = st.form_submit_button("Add Book")
                    st.markdown("</div>", unsafe_allow_html=True)

                    if submit_button and title and author:
                        # Add book to MongoDB
                        add_book(title, author, str(publication_year), genre, read_status)
                        st.session_state.add_success = True

            with col2:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("### Tips for Adding Books")
                st.markdown("""
                - Include the full title and author name
                - Check if the book already exists before adding
                - Mark books you've already read
                - Add books as you acquire them to keep your library up-to-date
                """)

                if st.session_state.add_success:
                    st.markdown("<div class='success-msg'>Book added successfully!</div>", unsafe_allow_html=True)
                    # Reset the success message after 1 render
                    st.session_state.add_success = False
                st.markdown("</div>", unsafe_allow_html=True)

    # Tab 2: Remove a book
    with tab2:
        st.markdown("<h2 class='sub-header'>Remove a Book</h2>", unsafe_allow_html=True)

        books = get_all_books()
        if not books:
            st.warning("Your library is empty. Add some books first!")
        else:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            title_or_author = st.text_input("Enter Title or Author to Remove")

            if title_or_author:
                # Find books matching the search term
                search_results = search_book(title_or_author)
                if search_results:
                    st.markdown("### Books matching your search:")
                    for book in search_results:
                        st.write(f"**{book['title']}** by {book['author']}")

                    confirm_remove = st.button("Confirm Removal")
                    if confirm_remove:
                        remove_book(title_or_author)
                        st.session_state.remove_success = True
                else:
                    st.warning("No books found matching that title or author.")
            st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.remove_success:
                st.markdown("<div class='success-msg'>Book removed successfully!</div>", unsafe_allow_html=True)
                # Reset the success message after 1 render
                st.session_state.remove_success = False

    # Tab 3: Search for a book
    with tab3:
        st.markdown("<h2 class='sub-header'>Search Your Library</h2>", unsafe_allow_html=True)

        # state variable to control the dispaly and view state of summary btn
        st.session_state.viewbtn = False
        
        books = get_all_books()
        if not books:
            st.warning("Your library is empty. Add some books first!")
        else:
            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                search_term = st.text_input("Enter Title or Author to Search")
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                if search_term:
                    # Use your existing search function
                    search_results = search_book(search_term)
                    if search_results not in st.session_state:
                        st.session_state.search_results = search_results
                    if search_results:
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown(f"### Found {len(search_results)} results")

                        # Convert to DataFrame for better display
                        df = pd.DataFrame(search_results)
                        
                        # Remove MongoDB _id column for display
                        if '_id' in df.columns:
                            df = df.drop('_id', axis=1)

                        st.dataframe(df, use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.session_state.viewbtn = True
                        
                    else:
                        st.info("No matching books found. Try a different search term.")
        
        
        
        if st.session_state.viewbtn:        
            st.markdown("<div class='card'>", unsafe_allow_html=True)                
            st.subheader("Get a Quick Summary of the Book and purchase link")
            st.button("Get Summary", key="summary_btn")
            if st.session_state.summary_btn:  
                response = completion(
                    model="gemini/gemini-2.0-flash", 
                    messages=[ 
                          {
                              "role": "system",
                              "content": "You are an expert digital library manager AI Agent now and now you are integrated in a library manager's search feature, so, the user will prompt you to give Quick 2 paragraph and well written with heading and bullet points summary of books. So, when you start responding don't say anything like 'I understand! I am now acting as an AI Agent integrated into a library manager's search feature.' just start with the task."
                           },
                          {"role": "user", "content": f" Give a quick summary of book {st.session_state.search_results[0]['title']}, it's author is {st.session_state.search_results[0]['author']}"}
                          ],


                     )      

                st.write(response["choices"][0].message.content)
                
                google_search_result =  search_google(query=f"{st.session_state.search_results[0]['title']} by {st.session_state.search_results[0]['author']} buy links OR purchase OR order site:amazon.com OR site:ebay.com OR site:walmart.com OR site:booksamillion.com OR site:bookdepository.com OR site:target.com")
                
                st.subheader("PURCHASE LINKS")
                st.write(google_search_result)
               

    # Tab 4: Display all books
    with tab4:
        st.markdown("<h2 class='sub-header'>Your Complete Library</h2>", unsafe_allow_html=True)

        books = get_all_books()
        if not books:
            st.warning("Your library is empty. Add some books first!")
        else:
            # Convert to DataFrame for display
            df = pd.DataFrame(books)
            # Remove MongoDB _id column for display
            if '_id' in df.columns:
                df = df.drop('_id', axis=1)

            # Display options
            col1, col2 = st.columns(2)
            with col1:
                filter_genre = st.multiselect("Filter by Genre", options=sorted(df['genre'].unique()) if 'genre' in df.columns else [])
            with col2:
                read_filter = st.multiselect("Read Status", options=["yes", "no"])

            # Apply filters
            filtered_df = df.copy()
            if filter_genre and 'genre' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['genre'].isin(filter_genre)]

            if read_filter and 'read_status' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['read_status'].isin(read_filter)]

            # Display results
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.dataframe(filtered_df, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # Tab 5: Statistics
    with tab5:
        st.markdown("<h2 class='sub-header'>Library Statistics</h2>", unsafe_allow_html=True)

        books = get_all_books()
        if not books:
            st.warning("Your library is empty. Add some books first!")
        else:
            # Convert to DataFrame for analysis
            df = pd.DataFrame(books)

            # Get the stats from your function
            stats = display_stats()

            # Read vs Unread chart
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("### Reading Progress")

                # Create data for pie chart
            read_data = [
                {"status": "Read", "count": stats["books_read"]},
                {"status": "Unread", "count": stats["total_books"] - stats["books_read"]}
            ]
            read_df = pd.DataFrame(read_data)

            fig = px.pie(read_df, values='count', names='status', 
                            color_discrete_sequence=['#4CAF50', '#FFC107'],
                            hole=0.4)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Publication year analysis if publication_year exists
            if 'publication_year' in df.columns:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("### Books by Publication Year")

                # Convert publication_year to numeric
                df['publication_year'] = pd.to_numeric(df['publication_year'], errors='coerce')

                # Group by decade
                df['decade'] = (df['publication_year'] // 10) * 10
                decade_counts = df.groupby('decade').size().reset_index(name='count')
                decade_counts = decade_counts.dropna()
                decade_counts['decade'] = decade_counts['decade'].astype(int).astype(str) + 's'

                fig = px.line(decade_counts, x='decade', y='count', markers=True,
                            line_shape='linear')
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Additional statistics
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("### Key Metrics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Books", stats["total_books"])
            with col2:
                st.metric("Books Read", stats["books_read"])
            with col3:
                st.metric("Read Percentage", f"{stats['percentage_read']:.1f}%")
            st.markdown("</div>", unsafe_allow_html=True)

    # Tab 6: AI Recommendations
   # Tab 6: AI Recommendations
    with tab6:
        st.markdown("<h2 class='sub-header'>🤖 AI Book Recommendations</h2>", unsafe_allow_html=True)

        st.markdown("""
        <div class="ai-card">
            <h3 class="ai-header">Let AI Find Your Next Great Read</h3>
            <p>Tell us about your preferences, and our AI will suggest books tailored just for you.</p>
        </div>
        """, unsafe_allow_html=True)

        # Create two columns for the form layout
        col1, col2 = st.columns([3, 2])

        if 'validation_error' not in st.session_state:
            st.session_state.validation_error = False
            st.session_state.error_message = ""
        
        with col1:
            with st.form("ai_recommendation_form"):
                st.markdown("<div class='preference-section'>", unsafe_allow_html=True)
                st.markdown("### What are you looking for?")
                
                if st.session_state.validation_error:
                    st.error(st.session_state.error_message)

                # Primary preferences
                genre_preference = st.multiselect(
                    "Preferred Genres",
                    options=["Fiction", "Non-Fiction", "Science Fiction", "Fantasy", "Mystery", 
                             "Thriller","Biography", "History", "Philosophy",
                             "Science", "Self-Help", "Poetry", "Classics",
                             "Horror", "Adventure", "Humor", "Drama", "Dystopian"],
                    
                )

                mood = st.select_slider(
                    "What mood are you in?",
                    options=["Lighthearted", "Thoughtful", "Educational", "Thrilling", "Emotional", "Dark", "Inspirational"]
                )

                length_preference = st.radio(
                    "Book Length",
                    options=["Short (under 300 pages)", "Medium (300-500 pages)", "Long (500+ pages)", "Any length"]
                )

                st.markdown("</div>", unsafe_allow_html=True)

                # Advanced preferences
                st.markdown("<div class='preference-section'>", unsafe_allow_html=True)
                st.markdown("### Tell us more (optional)")

                time_period = st.multiselect(
                    "Preferred Time Periods",
                    options=["Contemporary", "20th Century", "19th Century", "Renaissance", 
                             "Medieval", "Ancient", "Future", "Any era"]
                )

                writing_style = st.select_slider(
                    "Writing Style",
                    options=["Simple", "Moderate", "Complex", "Poetic", "Direct", "Descriptive"]
                )

                themes = st.multiselect(
                    "Themes You Enjoy",
                    options=["Family", "Adventure", "Coming of Age", "Redemption", 
                             "Justice", "Power", "Identity", "Survival", "Friendship",
                             "War", "Politics", "Technology", "Nature", "Spirituality"]
                )
                st.markdown("</div>", unsafe_allow_html=True)

                # Personal context
                st.markdown("<div class='preference-section'>", unsafe_allow_html=True)
                st.markdown("### Personal Context")

                recently_read = st.text_area("Books you've recently enjoyed", height=100,
                                             placeholder="Enter titles or authors you've liked recently...")

                avoid = st.text_area("What would you like to avoid?", height=100,
                                     placeholder="Any themes, topics, or styles you don't enjoy...")

                reading_purpose = st.selectbox(
                    "Purpose for Reading",
                    options=["Entertainment", "Learning something new", "Personal growth", 
                             "Escapism", "Academic", "Professional development"]
                )
                st.markdown("</div>", unsafe_allow_html=True)

                # Free text field for specific requests
                specific_request = st.text_area(
                    "Any specific requests for the AI?",
                    height=100,
                    placeholder="E.g., 'Looking for a book similar to Dune but with strong female characters'"
                )

                submitted = st.form_submit_button("Get AI Recommendations")
                
                if submitted:
                # Check if all required fields are filled
                    validation_errors = []

                    if not genre_preference:
                        validation_errors.append("Please select at least one genre")

                    if not time_period:
                        validation_errors.append("Please select at least one time period")

                    if not themes:
                        validation_errors.append("Please select at least one theme")

                    if not recently_read.strip():
                        validation_errors.append("Please enter books you've recently enjoyed")

                    
                    # Update session state based on validation results
                    if validation_errors:
                        st.session_state.validation_error = True
                        st.session_state.error_message = "Please fill in all required fields:\n• " + "\n• ".join(validation_errors)
                        st.rerun()  # Force a rerun to show the error message
                else:
                    st.session_state.validation_error = False
                    st.session_state.error_message = ""

        with col2:
            st.markdown("<div class='ai-card'>", unsafe_allow_html=True)
            st.markdown("### How It Works")
            st.markdown("""
            1. **Fill out your preferences** - The more detail you provide, the better the recommendations
            2. **Submit your request** - Our AI analyzes your preferences
            3. **Review suggestions** - Get personalized book recommendations
            """)
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("### Tips for Great Recommendations")
            st.markdown("""
            - Be specific about books you've enjoyed
            - Include authors whose style you appreciate
            - Mention themes that resonate with you
            - Let us know your reading goals
            """)
            st.markdown("</div>", unsafe_allow_html=True)

            # Display a placeholder for where recommendations will appear
            st.markdown("<div class='ai-card'>", unsafe_allow_html=True)
            
            recommendation_data = {
                        "genres": genre_preference,
                        "mood": mood,
                        "length": length_preference,
                        "time_period": time_period,
                        "writing_style": writing_style,
                        "themes": themes,
                        "recently_read": recently_read,
                        "avoid": avoid,
                        "purpose": reading_purpose,
                        "specific_request": specific_request
                    }

            st.markdown("</div>", unsafe_allow_html=True)

        # Add a new section for AI response that spans the full width below both columns
        st.markdown("<div class='ai-response-section'>", unsafe_allow_html=True)
        st.markdown("## Your Personalized Book Recommendations", unsafe_allow_html=True)

        # Only display content if the form has been submitted
        if 'submitted' in locals() and submitted:
            # Create tabs for different types of recommendations
            rec_tabs = st.tabs(["Top Picks"])

            with rec_tabs[0]:
                st.markdown("<div class='recommendation-card'>", unsafe_allow_html=True)

                # This is where you'll integrate your actual AI response
                if submitted:
                    response_second = completion(
                        model="gemini/gemini-2.0-flash", 
                        messages=[ 
                              {
                                  "role": "system",
                                  "content": "You are a library recommendation engine AI agent now, so, the user will be giving you his perferences i.e. Genres, mood, Time periods, Writing style, Theme, mood, book length, and personal context, based on that you have to suggest him/her books to read and you have to give just specific information like book title, Author Name, ratings, and very short description and read the whole arrays if any information is give in form of array. So, when you start responding don't say anything like 'I understand! I am now acting as an AI Agent integrated into a library manager's search feature.' just start with the task."
                               },
                              {
                                  "role": "user", "content": f"Give me some books on {recommendation_data['genres']} , my mood is {recommendation_data["mood"]} and I want the length of book to be {recommendation_data["length"]}. The recommended books should blong to {recommendation_data["time_period"][0]} time period and their writing style should be {recommendation_data['writing_style']}. The themes of the books should be {recommendation_data['themes']} . I have recently read {recommendation_data['recently_read']} and I want to avoid {recommendation_data['avoid']}. I want to read books for {recommendation_data['purpose']}. {recommendation_data['specific_request']}"
                                  }
                              ],
                         )
                
                    st.write(response_second["choices"][0].message.content)
                
               
                st.markdown("</div>", unsafe_allow_html=True)

           
        else:
            st.info("Submit the form above to see your personalized book recommendations.")

        st.markdown("</div>", unsafe_allow_html=True)
if __name__ == "__main__":
    main()
