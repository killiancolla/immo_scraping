import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from function import *
import socket
import plotly.express as px
import re

ip = socket.gethostbyname(socket.gethostname())

st.set_page_config(
    page_title='Mon application immobilière',
    page_icon='🏢',
    layout='centered'
)

scrap = Scrap()
streamlit = Streamlit()
database = DataBase("immoDB")

streamlit.sidebar()

st.title('Mon application immobilière 🏢')
st.write('Cette application vous permet de rechercher des offres de vente de biens dans votre ville. Chaque recherches qui sont faites vont enrichir notre base de données en scrapant le site https://www.bienici.com, nous enregistrons également vos recherches qui sont liées à votre adresse IP afin que vous puissiez retrouver vos recherches.')
st.write("Vous pouvez également visualiser nos graphiques en actionnant le bouton ci-dessous.")

if st.checkbox("Voir les informations"):
    df = pd.DataFrame(database.select_table('offres'), columns=['id_', 'link', 'image', 'name', 'place', 'size', 'price', 'square_price'])
    bins = np.arange(0, df['size'].max() + 10, 10)
    labels = [f'{int(i)}-{int(i + 10)}' for i in bins[:-1]]
    df['size_range'] = pd.cut(df['size'], bins=bins, labels=labels, right=False)
    avg_prices = df.groupby('size_range')['price'].mean().reset_index()
    fig = px.bar(avg_prices, x='size_range', y='price', title='Moyenne des prix par taille', labels={'price': 'Prix moyen (en €)', 'size_range': 'Taille (en m²)'})
    st.plotly_chart(fig)

    def extract_city(place):
        # Liste des villes à extraire
        cities = ["Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Montpellier",
                "Strasbourg", "Bordeaux", "Lille", "Rennes", "Reims", "Saint-Étienne",
                "Le Havre", "Toulon", "Grenoble", "Dijon", "Angers", "Nîmes", "Villeurbanne"]

        for city in cities:
            if re.search(city, place, re.IGNORECASE):
                return city
        return None

    df['city'] = df['place'].apply(extract_city)
    df['square_price'] = round(df['price'] / df['size'], 0)
    avg_square_prices = df.groupby('city')['square_price'].mean().round().reset_index()
    fig = px.bar(avg_square_prices, x='city', y='square_price', title='Prix moyen au m² par ville', labels={'square_price': 'Prix moyen au m² (en €)', 'city': 'Ville'})
    st.plotly_chart(fig)


user_input = st.text_input("Choisissez une ville")
nb_article = st.slider("Nombre d'offres à afficher ?", 1, 300)

if st.button('Lancer la recherche'):
    try: 
        data, search = scrap.scrap_immo(user_input, nb_article)
        # Enregistrement en base des données trouvées ainsi que de l'historique
        scrap.save_data(ip, data, search)
        df = pd.DataFrame.from_dict(data, orient='index')
        towrite = BytesIO()
        df.to_excel(towrite, index=False, engine='openpyxl')
        towrite.seek(0)
        file_name = "article.xlsx"
        st.download_button(label="Télécharger les données en Excel",
                            data=towrite,
                            file_name=file_name,
                            mime="application/vnd.ms-excel")
        for url, details in data.items():
            col1, col2 = st.columns(2)
            with col1: 
                st.image(details['image'])
            with col2:
                st.write(details['name'])
                st.write(details['place'])
                st.write(str(details['size']) + ' m²')
                st.write(str(details['price']) + '€')
                st.write(str(details['square_price']) + '€/m²')
            st.markdown("<hr>", unsafe_allow_html=True)
    except: 
        st.write("Aucune donnée n'ont été trouvées.")


df = database.select_table('offres')
df = pd.DataFrame(df)
def extract_postal_code(place):
    return place[:5]

df['postal_code'] = df['place'].apply(extract_postal_code)
df_sorted = df.sort_values(by='postal_code')
unique_places = df_sorted['place'].unique()

st.write('Recherche dans la base de données')
city = st.selectbox("Choisissez votre ville", unique_places)
df_new = database.select_table('offres', {'place': city})
nb_article = st.slider("Nombre d'offres à afficher ?", 0, len(df_new))

if nb_article > 0:
    for i in range(nb_article):
        try:
            col1, col2 = st.columns(2)
            with col1: 
                st.image(df_new[i].image)
                st.link_button("Accèder à l'offre", df_new[i].name)
            with col2:
                st.write(df_new[i]['name'])
                st.write(df_new[i].place)
                st.write(str(df_new[i].size) + ' m²')
                st.write(str(df_new[i].price) + '€')
                st.write(str(df_new[i].square_price) + '€/m²')
        except:
            break