from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from time import sleep
import streamlit as st
import sqlalchemy as db
from sqlalchemy import and_

class DataBase():
    def __init__(self, name_database='database'):
        self.name = name_database
        self.url = f"sqlite:///{name_database}.db"
        self.engine = db.create_engine(self.url)
        self.connection = self.engine.connect()
        self.metadata = db.MetaData()
        self.table = self.engine.table_names()

    def create_table(self, name_table, **kwargs):
        colums = [db.Column(k, v, primary_key = True) if 'id_' in k else db.Column(k, v) for k,v in kwargs.items()]
        db.Table(name_table, self.metadata, *colums)
        self.metadata.create_all(self.engine)
        print(f"Table : '{name_table}' are created succesfully")

    def read_table(self, name_table, return_keys=False):
        table = db.Table(name_table, self.metadata, autoload=True, autoload_with=self.engine)
        if return_keys:table.columns.keys()
        else : return table

    def add_row(self, name_table, **kwarrgs):
        name_table = self.read_table(name_table)

        stmt = (
            db.insert(name_table).
            values(kwarrgs)
        )
        self.connection.execute(stmt)
        print(f'Row id added')


    def delete_row_by_id(self, table, id_):
        name_table = self.read_table(name_table)

        stmt = (
            db.delete(name_table).
            where(students.c.id_ == id_)
            )
        self.connection.execute(stmt)
        print(f'Row id {id_} deleted')

    def select_table(self, name_table, filter_by=None):
        name_table_ref = self.read_table(name_table)
        query = db.select([name_table_ref])

        if filter_by:
            conditions = [getattr(name_table_ref.c, key).like(f"%{value}%") for key, value in filter_by.items()]
            query = query.where(and_(*conditions))

        return self.connection.execute(query).fetchall()

class Scrap:
    def __init__(self):
        self.url = 'https://www.bienici.com/'
        self.database = DataBase('immoDB')

    def scrap_immo(self, place='France', nb_offers = 10):
        driver = Chrome()
        driver.get(f'{self.url}recherche/achat/{place}?mode=liste')
        sleep(1)
        driver.find_element(By.ID, 'didomi-notice-agree-button').click()
        try: city = driver.find_element(By.CLASS_NAME, 'tag label label-tag'.replace(' ', '.')).text
        except: 
            driver.close()
            return 
        st.experimental_set_query_params()
        data_offers = {}
        while len(data_offers) < nb_offers:
            sleep(2)
            all_offers = driver.find_elements(By.CLASS_NAME, 'detailedSheetLink')
            i = 0
            for offer in all_offers:
                # Image
                try: image = offer.find_element(By.CLASS_NAME, 'img__image img__image--fit-to-parent'.replace(' ', '.')).get_attribute('src')
                except: image = None

                # Nom de l'offre
                try: name = offer.find_element(By.CLASS_NAME, 'ad-overview-details__ad-title').text
                except: name = None

                # Lien de l'offre
                try: link = offer.get_attribute('href')
                except: link = None

                # Lieu
                try: place = offer.find_element(By.CLASS_NAME, 'ad-overview-details__address-title'.replace(' ', '.')).text
                except: place = None

                # Prix
                try: price = int(offer.find_element(By.CLASS_NAME, 'ad-price__the-price'.replace(' ', '.')).text.replace(' ', '').replace('\u20ac', ''))
                except: price = None

                # Taille de l'offre
                try: size = int(name.split(' ')[-2:][0])
                except: size = None

                # Prix au m2
                try: square_price = round(price / size, 2)
                except: square_price = None

                if len(data_offers) < nb_offers:
                    data_offers[link] ={
                        'link': link,
                        'image': image,
                        'name': name,
                        'place': place,
                        'size': size,
                        'price': price,
                        'square_price': square_price
                    }
                else:
                    break
                i=i+1
            driver.find_element(By.CLASS_NAME, 'btn goForward btn-primary pagination__go-forward-button'.replace(' ', '.')).click()
        driver.close()
        return (data_offers, city)

    # Enregistrement en base des offres et de l'historique
    def save_data(self, ip, offers, search):
        for url, details in offers.items():
            # Protection d'insertion de doublons
            if len(self.database.select_table("offres", {"link": url})) == 0:
                self.database.add_row('offres', 
                    link=url, 
                    image=details['image'], 
                    name=details['name'], 
                    place=details['place'], 
                    size=details['size'],
                    price=details['price'],
                    square_price=details['square_price']
                )
        # Protection d'insertion de doublons
        if len(self.database.select_table("historique", {"ip": ip, "search": search})) == 0:
            self.database.add_row('historique', ip=ip, search=search)

    def get_history(self, ip):
        return self.database.select_table("historique", {"ip":ip})

class Streamlit:
    def __init__(self):
        self.name = "Killian Colla"
        self.url = "https://www.bienici.com/"
        pass
    def sidebar(self):
        with st.sidebar:
            st.sidebar.title(self.name)
            st.sidebar.link_button("Lien vers le site", self.url)