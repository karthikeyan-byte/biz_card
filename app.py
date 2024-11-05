import easyocr
from PIL import Image
import numpy as np
import pymongo
import os
import streamlit as st


st.title("OCR App")

uploaded_file = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"])
