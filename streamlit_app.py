import streamlit as st
import requests
import io

st.title("Summarizer App")

options = st.selectbox("Choose input type", ("PDF","URL"))

if options == "PDF":
    uploaded_file = st.file_uploader("Choose  a PDF file", type="pdf")
    if uploaded_file is not None and st.button("Summarize"):
        with st.spinner("Summarizing..."):
            files = {"file":  uploaded_file}
            response  = requests.post("http://localhost:5000/api/pdf", files=files)
            if response.status_code == 200:
                summary = response.json()['summary']
                st.success("Summary:")
                st.write(summary)
            else:
                st.error("Error: " + response.json()['error'])
    elif options == "URL":
        url = st.text_input("Enter a URL")
        if url and st.button("Summarize"):
            with st.spinner("Summarizing..."):
                data = {"url": url}
                response = requests.post("http://localhost:5000/api/url", json=data)
                if response.status_code == 200:
                    summary = response.json()['summary']
                    st.success("Summary:")
                    st.write(summary)
                else:
                    st.error("Error: " + response.json()['error'])