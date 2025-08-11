from abc import abstractmethod, ABC
from typing import Dict, Any

import pandas as pd
import streamlit as st


class BasePreprocessor(ABC):
	"""Classe de base pour les préprocesseurs de données"""

	@abstractmethod
	def process(self, df: pd.DataFrame, column: str, **kwargs) -> pd.DataFrame:
		"""
		Traite une colonne spécifique du DataFrame

		Args:
			df: DataFrame à traiter
			column: Nom de la colonne à traiter
			**kwargs: Paramètres additionnels

		Returns:
			DataFrame modifié
		"""
		pass

	@abstractmethod
	def get_config_ui(self, column: str, key_prefix: str) -> Dict[str, Any]:
		"""
		Affiche l'interface de configuration Streamlit et retourne les paramètres

		Args:
			column: Nom de la colonne
			key_prefix: Préfixe pour les clés Streamlit

		Returns:
			Dictionnaire des paramètres configurés
		"""
		pass


class TextPreprocessor(BasePreprocessor):
	"""Préprocesseur pour les données textuelles"""

	def process(self, df: pd.DataFrame, column: str, **kwargs) -> pd.DataFrame:
		if column not in df.columns:
			return df

		df = df.copy()

		# Nettoyage des espaces
		if kwargs.get('strip_whitespace', True):
			df[column] = df[column].astype(str).str.strip()

		# Conversion de casse
		case_option = kwargs.get('case_conversion', 'none')
		if case_option == 'upper':
			df[column] = df[column].astype(str).str.upper()
		elif case_option == 'lower':
			df[column] = df[column].astype(str).str.lower()
		elif case_option == 'title':
			df[column] = df[column].astype(str).str.title()

		# Suppression des caractères spéciaux
		if kwargs.get('remove_special_chars', False):
			pattern = kwargs.get('special_chars_pattern', r'[^a-zA-Z0-9\s]')
			df[column] = df[column].astype(str).str.replace(pattern, '', regex=True)

		# Remplacement de valeurs
		if kwargs.get('replace_values', False):
			replacements = kwargs.get('replacements', {})
			for old_val, new_val in replacements.items():
				df[column] = df[column].str.replace(old_val, new_val, regex=False)

		# Gestion des valeurs vides
		empty_strategy = kwargs.get('empty_strategy', 'keep')
		if empty_strategy == 'null':
			df.loc[df[column].str.strip() == '', column] = None
		elif empty_strategy == 'default':
			default_value = kwargs.get('default_value', '')
			df.loc[df[column].str.strip() == '', column] = default_value

		return df

	def get_config_ui(self, column: str, key_prefix: str) -> Dict[str, Any]:
		st.write(f"**Configuration pour la colonne texte: {column}**")

		config = {}

		col1, col2 = st.columns(2)

		with col1:
			config['strip_whitespace'] = st.checkbox(
				"Supprimer les espaces en début/fin",
				value=True,
				key=f"{key_prefix}_text_strip_{column}"
			)

			config['case_conversion'] = st.selectbox(
				"Conversion de casse",
				['none', 'upper', 'lower', 'title'],
				key=f"{key_prefix}_text_case_{column}"
			)

			config['remove_special_chars'] = st.checkbox(
				"Supprimer les caractères spéciaux",
				key=f"{key_prefix}_text_special_{column}"
			)

			if config['remove_special_chars']:
				config['special_chars_pattern'] = st.text_input(
					"Pattern regex des caractères à supprimer",
					value=r'[^a-zA-Z0-9\s]',
					key=f"{key_prefix}_text_pattern_{column}"
				)

		with col2:
			config['empty_strategy'] = st.selectbox(
				"Stratégie pour les valeurs vides",
				['keep', 'null', 'default'],
				key=f"{key_prefix}_text_empty_{column}"
			)

			if config['empty_strategy'] == 'default':
				config['default_value'] = st.text_input(
					"Valeur par défaut",
					key=f"{key_prefix}_text_default_{column}"
				)

			config['replace_values'] = st.checkbox(
				"Remplacer des valeurs spécifiques",
				key=f"{key_prefix}_text_replace_{column}"
			)

			if config['replace_values']:
				replacements_text = st.text_area(
					"Remplacements (ancien=nouveau, un par ligne)",
					placeholder="ancien_texte=nouveau_texte",
					key=f"{key_prefix}_text_replacements_{column}"
				)

				replacements = {}
				for line in replacements_text.split('\n'):
					if '=' in line:
						old, new = line.split('=', 1)
						replacements[old.strip()] = new.strip()
				config['replacements'] = replacements

		return config


class NumericPreprocessor(BasePreprocessor):
	"""Préprocesseur pour les données numériques"""

	def process(self, df: pd.DataFrame, column: str, **kwargs) -> pd.DataFrame:
		if column not in df.columns:
			return df

		df = df.copy()

		# Conversion en numérique
		if kwargs.get('force_numeric', True):
			df[column] = pd.to_numeric(df[column], errors='coerce')

		# Gestion des valeurs aberrantes
		outlier_strategy = kwargs.get('outlier_strategy', 'keep')
		if outlier_strategy != 'keep':
			q1 = df[column].quantile(0.25)
			q3 = df[column].quantile(0.75)
			iqr = q3 - q1
			lower_bound = q1 - 1.5 * iqr
			upper_bound = q3 + 1.5 * iqr

			outlier_mask = (df[column] < lower_bound) | (df[column] > upper_bound)

			if outlier_strategy == 'remove':
				df = df[~outlier_mask]
			elif outlier_strategy == 'cap':
				df.loc[df[column] < lower_bound, column] = lower_bound
				df.loc[df[column] > upper_bound, column] = upper_bound
			elif outlier_strategy == 'null':
				df.loc[outlier_mask, column] = None

		# Arrondir les valeurs
		if kwargs.get('round_values', False):
			decimals = kwargs.get('decimal_places', 2)
			df[column] = df[column].round(decimals)

		# Normalisation/Standardisation
		scaling_method = kwargs.get('scaling_method', 'none')
		if scaling_method == 'min_max':
			min_val = df[column].min()
			max_val = df[column].max()
			if max_val != min_val:
				df[column] = (df[column] - min_val) / (max_val - min_val)
		elif scaling_method == 'z_score':
			mean_val = df[column].mean()
			std_val = df[column].std()
			if std_val != 0:
				df[column] = (df[column] - mean_val) / std_val

		# Gestion des valeurs nulles
		null_strategy = kwargs.get('null_strategy', 'keep')
		if null_strategy == 'mean':
			df[column].fillna(df[column].mean(), inplace=True)
		elif null_strategy == 'median':
			df[column].fillna(df[column].median(), inplace=True)
		elif null_strategy == 'mode':
			mode_val = df[column].mode()
			if len(mode_val) > 0:
				df[column].fillna(mode_val[0], inplace=True)
		elif null_strategy == 'zero':
			df[column].fillna(0, inplace=True)
		elif null_strategy == 'custom':
			custom_value = kwargs.get('custom_fill_value', 0)
			df[column].fillna(custom_value, inplace=True)

		return df

	def get_config_ui(self, column: str, key_prefix: str) -> Dict[str, Any]:
		st.write(f"**Configuration pour la colonne numérique: {column}**")

		config = {}

		col1, col2 = st.columns(2)

		with col1:
			config['force_numeric'] = st.checkbox(
				"Forcer la conversion numérique",
				value=True,
				key=f"{key_prefix}_num_force_{column}"
			)

			config['outlier_strategy'] = st.selectbox(
				"Gestion des valeurs aberrantes",
				['keep', 'remove', 'cap', 'null'],
				help="cap: limite aux bornes IQR, remove: supprime les lignes",
				key=f"{key_prefix}_num_outlier_{column}"
			)

			config['round_values'] = st.checkbox(
				"Arrondir les valeurs",
				key=f"{key_prefix}_num_round_{column}"
			)

			if config['round_values']:
				config['decimal_places'] = st.number_input(
					"Nombre de décimales",
					min_value=0,
					max_value=10,
					value=2,
					key=f"{key_prefix}_num_decimals_{column}"
				)

		with col2:
			config['scaling_method'] = st.selectbox(
				"Méthode de normalisation",
				['none', 'min_max', 'z_score'],
				key=f"{key_prefix}_num_scaling_{column}"
			)

			config['null_strategy'] = st.selectbox(
				"Gestion des valeurs nulles",
				['keep', 'mean', 'median', 'mode', 'zero', 'custom'],
				key=f"{key_prefix}_num_null_{column}"
			)

			if config['null_strategy'] == 'custom':
				config['custom_fill_value'] = st.number_input(
					"Valeur de remplacement",
					key=f"{key_prefix}_num_custom_{column}"
				)

		return config


class DatePreprocessor(BasePreprocessor):
	"""Préprocesseur pour les données de date/heure"""

	def process(self, df: pd.DataFrame, column: str, **kwargs) -> pd.DataFrame:
		if column not in df.columns:
			return df

		df = df.copy()

		# Conversion en datetime
		if kwargs.get('parse_dates', True):
			date_format = kwargs.get('date_format', 'infer')
			if date_format == 'infer':
				df[column] = pd.to_datetime(df[column], errors='coerce')
			else:
				df[column] = pd.to_datetime(df[column], format=date_format, errors='coerce')

		# Extraction de composants
		extract_components = kwargs.get('extract_components', [])
		for component in extract_components:
			if component == 'year':
				df[f"{column}_year"] = df[column].dt.year
			elif component == 'month':
				df[f"{column}_month"] = df[column].dt.month
			elif component == 'day':
				df[f"{column}_day"] = df[column].dt.day
			elif component == 'weekday':
				df[f"{column}_weekday"] = df[column].dt.weekday
			elif component == 'hour':
				df[f"{column}_hour"] = df[column].dt.hour

		# Formatage de sortie
		output_format = kwargs.get('output_format', 'keep_datetime')
		if output_format == 'iso_string':
			df[column] = df[column].dt.strftime('%Y-%m-%d %H:%M:%S')
		elif output_format == 'date_only':
			df[column] = df[column].dt.date
		elif output_format == 'custom_format':
			custom_format = kwargs.get('custom_format', '%Y-%m-%d')
			df[column] = df[column].dt.strftime(custom_format)

		return df

	def get_config_ui(self, column: str, key_prefix: str) -> Dict[str, Any]:
		st.write(f"**Configuration pour la colonne date: {column}**")

		config = {}

		col1, col2 = st.columns(2)

		with col1:
			config['parse_dates'] = st.checkbox(
				"Parser les dates automatiquement",
				value=True,
				key=f"{key_prefix}_date_parse_{column}"
			)

			config['date_format'] = st.selectbox(
				"Format de date d'entrée",
				['infer', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S'],
				key=f"{key_prefix}_date_format_{column}"
			)

			config['extract_components'] = st.multiselect(
				"Extraire des composants",
				['year', 'month', 'day', 'weekday', 'hour'],
				key=f"{key_prefix}_date_extract_{column}"
			)

		with col2:
			config['output_format'] = st.selectbox(
				"Format de sortie",
				['keep_datetime', 'iso_string', 'date_only', 'custom_format'],
				key=f"{key_prefix}_date_output_{column}"
			)

			if config['output_format'] == 'custom_format':
				config['custom_format'] = st.text_input(
					"Format personnalisé",
					value='%Y-%m-%d',
					key=f"{key_prefix}_date_custom_{column}"
				)

		return config