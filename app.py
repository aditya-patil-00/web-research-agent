import streamlit as st
from tools import search_web, scrape_urls, summarize_content

st.title("Web Research Agent")
query = st.text_input("Enter your research topic:")

if st.button("Research") and query:
    with st.spinner("Searching..."):
        urls = search_web(query)

    with st.spinner("Scraping content..."):
        contents = scrape_urls(urls)

    with st.spinner("Summarizing..."):
        summary = summarize_content(contents)

    st.subheader("📄 Summary")
    st.write(summary)
