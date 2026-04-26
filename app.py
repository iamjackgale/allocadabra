#!/usr/bin/env python

import os

# Set environment variables for Streamlit
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_SERVER_PORT'] = os.environ.get('PORT', '8501')
os.environ['STREAMLIT_SERVER_RUN_ON_SAVE'] = 'false'

from streamlit.web.server import Server

app = Server("frontend/app.py", is_hello=False).app