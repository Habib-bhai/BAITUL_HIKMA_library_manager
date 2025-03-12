import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from pymongo import MongoClient
from litellm import completion


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
        return MongoClient("mongodb+srv://Habib:yuckfu123@baitulhikma.5aovr.mongodb.net/")

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
        st.image("https://place-hold.it/300x100?text=BookShelf&fontsize=23", width=250)
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Add Book", "🗑️ Remove Book", "🔍 Search", "📖 All Books", "📊 Statistics"])

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
                    else:
                        st.info("No matching books found. Try a different search term.")
                        
        st.write("hello world")         
               

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


if __name__ == "__main__":
    main()
