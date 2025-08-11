import re
from typing import Tuple, Optional

import pandas as pd
from sqlalchemy import select, literal, cast

from modules.db import *
from modules.page import Page as BasePage, st
from utils.crud.sql_iu import SqlUi


class Page(BasePage):
	@classmethod
	def render(cls):
		if st.checkbox("Emballage", help="Afficher une seule colonne emballage au lieu de (Quantité/Unité)"):
			fields = (
				Product.id,
				Product.name.label("Nom"),
				(cast(Product.quantity, String) + literal(" ") + Product.unit).label(
					"Emballage"),
				Product.price.label("Prix")
			)
		else:
			fields = (
				Product.id,
				Product.name.label("Nom"),
				Product.quantity.label("Quantité"),
				Product.unit.label("Unité"),
				Product.price.label("Prix")
			)
		SqlUi(
			DB.connection,
			select(
				*fields
			),
			Product,
			read_use_container_width=True,
			enable_import_export=True,
			process_imported_dataframe=cls.process_dataframe
		)

	@classmethod
	def parse_emballage(cls, emballage: str) -> Tuple[Optional[float], Optional[str]]:
		# Nettoyer l'emballage (supprimer espaces en trop)
		emballage = emballage.strip()

		# Pattern pour capturer nombre + unité
		pattern = r'^(\d+(?:\.\d+)?)\s*([A-Za-z]+)$'
		match = re.match(pattern, emballage)

		if match:
			quantity = float(match.group(1))
			unit = match.group(2).upper()
			return quantity, unit.lower()
		else:
			# Si le pattern ne match pas, essayer de gérer les cas spéciaux
			print(f"Attention: Format d'emballage non reconnu: '{emballage}'")
			return None, emballage

	@classmethod
	def process_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
		# Vérifier les colonnes attendues
		expected_columns = ['NOM COMMERCIAL', 'EMBALLAGES', 'PU TTC']
		if not all(col in df.columns for col in expected_columns):
			print(f"Colonnes manquantes. Colonnes trouvées: {list(df.columns)}")
			return pd.DataFrame()

		# Créer le nouveau DataFrame
		processed_data = []

		for index, row in df.iterrows():
			name = row['NOM COMMERCIAL'].strip()
			emballage = str(row['EMBALLAGES']).strip()
			price = float(row['PU TTC'])

			# Parser l'emballage
			quantity, unit = cls.parse_emballage(emballage)

			processed_data.append({
				'name': name,
				'quantity': quantity,
				'unit': unit,
				'price': price
			})

		return pd.DataFrame(processed_data)


Page.run()
