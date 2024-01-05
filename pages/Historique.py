import streamlit as st 
import pandas as pd
from function import *
import socket

ip = socket.gethostbyname(socket.gethostname())

scrap = Scrap()
streamlit = Streamlit()

streamlit.sidebar()

key_article = st.selectbox('Choisissez une collect : ', [h['search'] for h in scrap.get_history(ip)])
database = DataBase('immoDB')
data = database.select_table("offres", {"place": key_article})
nb_article = st.slider("Nombre d'offres à afficher ?", 1, len(data))
for i in range(nb_article):
    try:
        col1, col2 = st.columns(2)
        with col1: 
            st.image(data[i].image)
            st.link_button("Accèder à l'offre", data[i].name)
        with col2:
            st.write(data[i]['name'])
            st.write(data[i].place)
            st.write(str(data[i].size) + ' m²')
            st.write(str(data[i].price) + '€')
            st.write(str(data[i].square_price) + '€/m²')
    except:
        break
    st.markdown("<hr>", unsafe_allow_html=True)