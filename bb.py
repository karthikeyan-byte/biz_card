import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
import sqlite3
from PIL import Image
import cv2
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import re


# SETTING-UP BACKGROUND IMAGE
def setting_bg():
    st.markdown(
        f""" <style>.stApp {{
                        background: url("5.png");
                        background-size: cover}}
                     </style>""", unsafe_allow_html=True)

setting_bg()

# Create the 'uploaded_cards' directory if it doesn't exist
if not os.path.exists('uploaded_cards'):
    os.makedirs('uploaded_cards')

# CREATING OPTION MENU
selected = option_menu(None, ["Home", "Upload & Extract", "Modify"],
                       icons=["house", "cloud-upload", "pencil-square"],
                       default_index=0,
                       orientation="horizontal",
                       styles={"nav-link": {"font-size": "35px", "text-align": "centre", "margin": "0px",
                                             "--hover-color": "#6495ED"},
                               "icon": {"font-size": "35px"},
                               "container": {"max-width": "6000px"},
                               "nav-link-selected": {"background-color": "#6495ED"}})

# INITIALIZING THE EasyOCR READER
reader = easyocr.Reader(['en'])

# CONNECTING WITH SQLite DATABASE
conn = sqlite3.connect('bizcardx_db.sqlite')  # SQLite connection
cursor = conn.cursor()  # Create a cursor object

# TABLE CREATION
cursor.execute('''CREATE TABLE IF NOT EXISTS card_data
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT,
                    card_holder TEXT,
                    designation TEXT,
                    mobile_number TEXT,
                    email TEXT,
                    website TEXT,
                    area TEXT,
                    city TEXT,
                    state TEXT,
                    pin_code TEXT,
                    image BLOB
                    )''')

# HOME MENU
if selected == "Home":
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("## :green[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas")
        st.markdown(
            "## :green[**Overview :**] In this Streamlit web app, you can upload an image of a business card and extract relevant information from it using easyOCR. You can view, modify, or delete the extracted data in this app. This app would also allow users to save the extracted information into a database along with the uploaded business card image. The database would be able to store multiple entries, each with its own business card image and extracted information.")
    with col2:
        st.image("4.png")

# UPLOAD AND EXTRACT MENU
if selected == "Upload & Extract":
    st.markdown("### Upload a Business Card")
    uploaded_card = st.file_uploader("Upload here", label_visibility="collapsed", type=["png", "jpeg", "jpg"])

    if uploaded_card is not None:

        def save_card(uploaded_card):
            file_path = os.path.join("uploaded_cards", uploaded_card.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_card.read())

        save_card(uploaded_card)

        def image_preview(image, res):
            fig, ax = plt.subplots()  # Create a figure and axes
            ax.imshow(image)

            for (bbox, text, prob) in res:
                # Unpack the bounding box coordinates
                (tl, tr, br, bl) = bbox
                tl = (int(tl[0]), int(tl[1]))
                tr = (int(tr[0]), int(tr[1]))
                br = (int(br[0]), int(br[1]))
                bl = (int(bl[0]), int(bl[1]))

                # Create a rectangle using patches.Rectangle
                rect = patches.Rectangle(tl, br[0] - tl[0], br[1] - tl[1],
                                         linewidth=2, edgecolor='green', facecolor='none')
                ax.add_patch(rect)

                # Annotate the rectangle with the extracted text
                ax.text(tl[0], tl[1] - 10, text, fontsize=8, color='red', bbox=dict(facecolor='white', alpha=0.5))

            ax.axis('off')  # Hide axes
            return fig  # Return the figure with annotations

        # DISPLAYING THE UPLOADED CARD
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown("#     ")
            st.markdown("#     ")
            st.markdown("### You have uploaded the card")
            st.image(uploaded_card)
        
        # DISPLAYING THE CARD WITH HIGHLIGHTS
        with col2:
            st.markdown("#     ")
            st.markdown("#     ")
            with st.spinner("Please wait processing image..."):

                saved_img = os.getcwd() + "/" + "uploaded_cards" + "/" + uploaded_card.name
                image = cv2.imread(saved_img)
                res = reader.readtext(saved_img)
                st.markdown("### Image Processed and Data Extracted")
                fig = image_preview(image, res)  # Get the figure
                st.pyplot(fig)

        # easy OCR
        saved_img = os.getcwd() + "/" + "uploaded_cards" + "/" + uploaded_card.name
        result = reader.readtext(saved_img, detail=0, paragraph=False)

        # CONVERTING IMAGE TO BINARY TO UPLOAD TO SQL DATABASE
        def img_to_binary(file):
            # Convert image data to binary format
            with open(file, 'rb') as file:
                binaryData = file.read()
            return binaryData

        data = {"company_name": [],
                "card_holder": [],
                "designation": [],
                "mobile_number": [],
                "email": [],
                "website": [],
                "area": [],
                "city": [],
                "state": [],
                "pin_code": [],
                "image": img_to_binary(saved_img)
                }

        def get_data(res):
            for ind, i in enumerate(res):

                # To get WEBSITE_URL
                if "www " in i.lower() or "www." in i.lower():
                    data["website"].append(i)
                elif "WWW" in i:
                    data["website"] = res[4] + "." + res[5]

                # To get EMAIL ID
                elif "@" in i:
                    data["email"].append(i)

                # To get MOBILE NUMBER
                elif "-" in i:
                    data["mobile_number"].append(i)
                    if len(data["mobile_number"]) == 2:
                        data["mobile_number"] = " & ".join(data["mobile_number"])

                # To get COMPANY NAME
                elif ind == len(res) - 1:
                    data["company_name"].append(i)

                # To get CARD HOLDER NAME
                elif ind == 0:
                    data["card_holder"].append(i)

                # To get DESIGNATION
                elif ind == 1:
                    data["designation"].append(i)

                # To get AREA
                if re.findall('^[0-9].+, [a-zA-Z]+', i):
                    data["area"].append(i.split(',')[0])
                elif re.findall('[0-9] [a-zA-Z]+', i):
                    data["area"].append(i)

                # To get CITY NAME
                match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                match2 = re.findall('.+St,, ([a-zAZ]+).+', i)
                match3 = re.findall('^[E].*', i)
                if match1:
                    data["city"].append(match1[0])
                elif match2:
                    data["city"].append(match2[0])
                elif match3:
                    data["city"].append(match3[0])

                # To get STATE
                state_match = re.findall('[a-zA-Z]{9} +[0-9]', i)
                if state_match:
                    data["state"].append(i[:9])
                elif re.findall('^[0-9].+, ([a-zA-Z]+);', i):
                    data["state"].append(i.split()[-1])
                if len(data["state"]) == 2:
                    data["state"].pop(0)

                # To get PINCODE
                if len(i) >= 6 and i.isdigit():
                    data["pin_code"].append(i)
                elif re.findall('[a-zA-Z]{9} +[0-9]', i):
                    data["pin_code"].append(i[10:])

        get_data(result)

        # FUNCTION TO CREATE DATAFRAME
        def create_df(data):
            df = pd.DataFrame(data)
            return df

        df = create_df(data)
        st.success("### Data Extracted!")
        st.write(df)

        if st.button("Upload to Database"):
            for i, row in df.iterrows():
                # here ? is a placeholder for parameterized queries
                sql = """INSERT INTO card_data(company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,image)
                         VALUES(?,?,?,?,?,?,?,?,?,?)"""
                cursor.execute(sql, tuple(row))
                conn.commit()

# MODIFY MENU
if selected == "Modify":
    col1, col2, col3 = st.columns([3, 3, 2])
    col2.markdown("## Alter or Delete the data here")
    column1, column2 = st.columns(2, gap="large")
    
    try:
        # MODIFYING THE CARD DETAILS
        with column1:
            cursor.execute("SELECT card_holder FROM card_data")
            result = cursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to update", list(business_cards.keys()))
            st.markdown("#### Update or modify any data below")

            # Fetch existing details for selected card holder
            cursor.execute(
                "SELECT company_name, card_holder, designation, mobile_number, email, website, area, city, state, pin_code FROM card_data WHERE card_holder=?",
                (selected_card,))
            result = cursor.fetchone()

            # Display the existing data in input fields
            company_name = st.text_input("Company Name", result[0])
            card_holder = st.text_input("Card Holder", result[1])
            designation = st.text_input("Designation", result[2])
            mobile_number = st.text_input("Mobile Number", result[3])
            email = st.text_input("Email", result[4])
            website = st.text_input("Website", result[5])
            area = st.text_input("Area", result[6])
            city = st.text_input("City", result[7])
            state = st.text_input("State", result[8])
            pin_code = st.text_input("Pin Code", result[9])

            # Commit changes to the database
            if st.button("Commit changes to DB"):
                cursor.execute(
                    "UPDATE card_data SET company_name=?, card_holder=?, designation=?, mobile_number=?, email=?, website=?, area=?, city=?, state=?, pin_code=? WHERE card_holder=?",
                    (company_name, card_holder, designation, mobile_number, email, website, area, city, state, pin_code, selected_card))
                conn.commit()
                st.success("Information updated in the database successfully.")

        # DELETING A CARD
        with column2:
            cursor.execute("SELECT card_holder FROM card_data")
            result = cursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card_to_delete = st.selectbox("Select a card holder name to Delete", list(business_cards.keys()))
            st.write(f"### You have selected :green[**{selected_card_to_delete}'s**] card to delete")
            st.write("#### Proceed to delete this card?")

            # Deleting the selected card
            if st.button("Yes, Delete Business Card"):
                cursor.execute("DELETE FROM card_data WHERE card_holder=?", (selected_card_to_delete,))
                conn.commit()
                st.success("Business card information deleted from the database.")
    except Exception as e:
        st.warning(f"There is no data available in the database. Error: {e}")

    # Viewing the updated data after modification
    if st.button("View updated data"):
        cursor.execute(
            "SELECT company_name, card_holder, designation, mobile_number, email, website, area, city, state, pin_code FROM card_data")
        updated_df = pd.DataFrame(cursor.fetchall(),
                                  columns=["Company Name", "Card Holder", "Designation", "Mobile Number", "Email",
                                           "Website", "Area", "City", "State", "Pin Code"])
        st.write(updated_df)

