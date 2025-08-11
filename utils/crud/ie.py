import io
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Type

import pandas as pd
import streamlit as st
from sqlalchemy import inspect
from streamlit.connections import SQLConnection

from database.base import Base


class DynamicImportExport:
	"""Classe pour gérer l'import/export dynamique des données pour les modèles SQLAlchemy"""

	def __init__(self, connection: SQLConnection, model: Type[Base],
	             process_imported_dataframe: Optional[callable] = None):
		"""
		Initialise le gestionnaire d'import/export
		"""
		self.connection = connection
		self.model = model
		self.logger = logging.getLogger(__name__)
		self.process_imported_dataframe = process_imported_dataframe

	@staticmethod
	def get_model_columns(model_class: Type) -> Dict[str, Dict[str, Any]]:
		"""Récupère les informations sur les colonnes d'un modèle"""
		inspector = inspect(model_class)
		columns_info = {}

		for column in inspector.columns:
			col_info = {
				'name': column.name,
				'type': str(column.type),
				'nullable': column.nullable,
				'primary_key': column.primary_key,
				'foreign_key': bool(column.foreign_keys),
				'default': column.default,
				'autoincrement': column.autoincrement
			}
			columns_info[column.name] = col_info

		return columns_info

	def export_table_data(self, filters: Optional[Dict] = None) -> pd.DataFrame:
		"""Exporte les données d'une table vers un DataFrame"""
		table_name = self.model.__tablename__
		try:
			if not self.model:
				raise ValueError(f"Modèle pour la table '{table_name}' non trouvé")

			# Construire la requête
			with self.connection.session as session:
				query = session.query(self.model)

				# Appliquer les filtres si fournis
				if filters:
					for column, value in filters.items():
						if hasattr(self.model, column) and value is not None:
							query = query.filter(getattr(self.model, column) == value)

				# Exécuter la requête et convertir en DataFrame
				results = query.all()

				if not results:
					return pd.DataFrame()

				# Convertir en dictionnaire puis DataFrame
				data_list = []
				for result in results:
					row_data = {}
					for column in inspect(self.model).columns:
						value = getattr(result, column.name)
						# Gérer les types spéciaux
						if isinstance(value, datetime):
							value = value.isoformat()
						elif value is None:
							value = None
						else:
							value = str(value) if not isinstance(value, (int, float, bool)) else value
						row_data[column.name] = value
					data_list.append(row_data)

				return pd.DataFrame(data_list)

		except Exception as e:
			self.logger.error(f"Erreur lors de l'export de {table_name}: {str(e)}")
			raise

	def validate_import_data(self, df: pd.DataFrame) -> Dict[str, List[str]]:
		"""Valide les données à importer"""
		table_name = self.model.__tablename__
		if not self.model:
			return {"errors": [f"Modèle pour la table '{table_name}' non trouvé"]}

		columns_info = self.get_model_columns(self.model)
		errors = []
		warnings = []

		# Vérifier les colonnes obligatoires
		required_columns = [col for col, info in columns_info.items()
		                    if not info['nullable'] and not info['autoincrement']
		                    and info['default'] is None]

		missing_required = [col for col in required_columns if col not in df.columns]
		if missing_required:
			errors.append(f"Colonnes obligatoires manquantes: {', '.join(missing_required)}")

		# Vérifier les colonnes inconnues
		unknown_columns = [col for col in df.columns if col not in columns_info]
		if unknown_columns:
			warnings.append(f"Colonnes inconnues (ignorées): {', '.join(unknown_columns)}")

		# Vérifier les valeurs nulles dans les colonnes non-nulles
		for col in df.columns:
			if col in columns_info and not columns_info[col]['nullable']:
				null_count = df[col].isnull().sum()
				if null_count > 0:
					errors.append(f"Colonne '{col}' contient {null_count} valeurs nulles (non autorisées)")

		return {"errors": errors, "warnings": warnings}

	def import_table_data(self, df: pd.DataFrame,
	                      mode: str = "insert") -> Dict[str, Any]:
		"""
		Importe les données dans une table

		Args:
			df: DataFrame contenant les données
			mode: "insert", "update", "upsert" ou "replace"
		"""
		table_name = self.model.__tablename__
		with self.connection.session as session:
			try:
				if not self.model:
					raise ValueError(f"Modèle pour la table '{table_name}' non trouvé")

				columns_info = self.get_model_columns(self.model)

				# Filtrer les colonnes connues
				valid_columns = [col for col in df.columns if col.lower() in columns_info]
				df_filtered = df[valid_columns].copy()

				success_count = 0
				error_count = 0
				errors = []

				if mode == "replace":
					# Supprimer toutes les données existantes
					session.query(self.model).delete()
					session.flush()

				# Traiter chaque ligne
				for index, row in df_filtered.iterrows():
					try:
						row_data = {}

						# Préparer les données de la ligne
						for col in valid_columns:
							value = row[col]

							# Gérer les valeurs NaN
							if pd.isna(value):
								if columns_info[col]['nullable']:
									value = None
								else:
									continue  # Ignorer si non-nullable

							# Conversion de type basique
							if 'INTEGER' in str(columns_info[col]['type']).upper():
								value = int(value) if value is not None else None
							elif 'FLOAT' in str(columns_info[col]['type']).upper():
								value = float(value) if value is not None else None
							elif 'BOOLEAN' in str(columns_info[col]['type']).upper():
								value = bool(value) if value is not None else None

							row_data[col] = value

						if mode == "insert" or mode == "replace":
							# Créer une nouvelle instance
							instance = self.model(**row_data)
							session.add(instance)

						elif mode == "update" or mode == "upsert":
							# Trouver la clé primaire
							pk_columns = [col for col, info in columns_info.items() if info['primary_key']]

							if not pk_columns:
								errors.append(f"Ligne {index}: Aucune clé primaire trouvée pour le mode {mode}")
								error_count += 1
								continue

							# Construire le filtre de clé primaire
							pk_filter = {}
							for pk_col in pk_columns:
								if pk_col in row_data:
									pk_filter[pk_col] = row_data[pk_col]

							if len(pk_filter) != len(pk_columns):
								errors.append(f"Ligne {index}: Clé primaire incomplète")
								error_count += 1
								continue

							# Chercher l'enregistrement existant
							query = session.query(self.model)
							for pk_col, pk_value in pk_filter.items():
								query = query.filter(getattr(self.model, pk_col) == pk_value)

							existing = query.first()

							if existing:
								# Mettre à jour l'enregistrement existant
								for col, value in row_data.items():
									if not columns_info[col]['primary_key']:  # Ne pas modifier les clés primaires
										setattr(existing, col, value)
							elif mode == "upsert":
								# Créer un nouvel enregistrement
								instance = self.model(**row_data)
								session.add(instance)
							else:
								errors.append(f"Ligne {index}: Enregistrement non trouvé pour la mise à jour")
								error_count += 1
								continue

						success_count += 1

					except Exception as e:
						error_count += 1
						errors.append(f"Ligne {index}: {str(e)}")
						continue

				# Commit des changements
				session.commit()

				return {
					"success": True,
					"success_count": success_count,
					"error_count": error_count,
					"errors": errors
				}

			except Exception as e:
				session.rollback()
				self.logger.error(f"Erreur lors de l'import dans {table_name}: {str(e)}")
				return {
					"success": False,
					"success_count": 0,
					"error_count": len(df),
					"errors": [str(e)]
				}


def render_export(key_prefix: str, table_name: str, pretty_table_name: str, import_export_manager: DynamicImportExport):
	st.write("**Exporter les données de la table**")

	# Options d'export
	col1, col2 = st.columns(2)

	with col1:
		export_format = st.selectbox(
			"Format d'export",
			["CSV", "Excel"],
			key=f"{key_prefix}_export_format_{table_name}"
		)

	with col2:
		limit_records = st.number_input(
			"Limite d'enregistrements (0 = tous)",
			min_value=0,
			value=0,
			key=f"{key_prefix}_limit_{table_name}"
		)

	# Bouton d'export
	if st.button(f"🔽 Exporter {pretty_table_name}", key=f"{key_prefix}_export_btn_{table_name}"):
		try:
			with st.spinner("Export en cours..."):
				# Récupérer les données
				df = import_export_manager.export_table_data()

				if df.empty:
					st.warning("Aucune donnée à exporter")
				else:
					# Appliquer la limite si spécifiée
					if limit_records > 0:
						df = df.head(limit_records)

					timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

					if export_format == "CSV":
						# Export CSV
						csv_data = df.to_csv(index=False)
						st.download_button(
							label="📄 Télécharger CSV",
							data=csv_data,
							file_name=f"{table_name}_{timestamp}.csv",
							mime="text/csv",
							key=f"{key_prefix}_download_csv_{table_name}"
						)
					else:
						# Export Excel
						excel_buffer = io.BytesIO()
						with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
							df.to_excel(writer, sheet_name=table_name, index=False)

						st.download_button(
							label="📊 Télécharger Excel",
							data=excel_buffer.getvalue(),
							file_name=f"{table_name}_{timestamp}.xlsx",
							mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
							key=f"{key_prefix}_download_excel_{table_name}"
						)

					st.success(f"✅ Export réussi! {len(df)} enregistrements")

					# Aperçu des données
					with st.expander("👁️ Aperçu des données exportées"):
						st.dataframe(df.head(10), use_container_width=True)

		except Exception as e:
			st.error(f"❌ Erreur lors de l'export: {str(e)}")


def render_import(key_prefix: str, table_name: str, pretty_table_name: str, import_export_manager: DynamicImportExport):
	st.write("**Importer des données dans la table**")

	# Upload du fichier
	uploaded_file = st.file_uploader(
		f"Fichier pour {pretty_table_name}",
		type=['xlsx', 'xls', 'csv'],
		key=f"{key_prefix}_upload_{table_name}"
	)

	if uploaded_file is not None:
		try:
			# Lire le fichier
			if uploaded_file.name.endswith('.csv'):
				df = pd.read_csv(uploaded_file)
			else:
				df = pd.read_excel(uploaded_file)

			if import_export_manager.process_imported_dataframe:
				df = import_export_manager.process_imported_dataframe(df)

			st.success(f"✅ Fichier lu: {len(df)} lignes, {len(df.columns)} colonnes")

			# Aperçu des données
			with st.expander("👁️ Aperçu des données à importer"):
				st.dataframe(df.head(10), use_container_width=True)

			# Validation des données
			validation_result = import_export_manager.validate_import_data(df)

			if validation_result.get("warnings"):
				for warning in validation_result["warnings"]:
					st.warning(f"⚠️ {warning}")

			if validation_result.get("errors"):
				for error in validation_result["errors"]:
					st.error(f"❌ {error}")
				can_import = False
			else:
				can_import = True

			if can_import:
				# Options d'import
				col1, col2 = st.columns(2)

				with col1:
					import_mode = st.selectbox(
						"Mode d'import",
						["insert", "update", "upsert", "replace"],
						help="""
	                            - insert: Ajouter de nouveaux enregistrements
	                            - update: Mettre à jour les enregistrements existants
	                            - upsert: Insérer ou mettre à jour selon l'existence
	                            - replace: Remplacer toutes les données de la table
	                            """,
						key=f"{key_prefix}_mode_{table_name}"
					)

				with col2:
					st.number_input(
						"Taille de lot",
						min_value=1,
						max_value=1000,
						value=100,
						key=f"{key_prefix}_batch_{table_name}"
					)

				# Confirmation pour le mode replace
				confirm_replace = True
				if import_mode == "replace":
					confirm_replace = st.checkbox(
						"⚠️ Je confirme vouloir remplacer toutes les données existantes",
						key=f"{key_prefix}_confirm_{table_name}"
					)

				# Bouton d'import
				if st.button(
						f"🔼 Importer dans {pretty_table_name}",
						disabled=not confirm_replace,
						key=f"{key_prefix}_import_btn_{table_name}"
				):
					with st.spinner("Import en cours..."):
						result = import_export_manager.import_table_data(df, import_mode)

						if result["success"]:
							st.success(f"✅ Import réussi! {result['success_count']} enregistrements traités")

							if result["error_count"] > 0:
								st.warning(f"⚠️ {result['error_count']} erreurs rencontrées")

								with st.expander("Voir les erreurs"):
									for error in result["errors"]:
										st.error(error)

							# Rerun pour actualiser les données
							st.rerun()
						else:
							st.error(f"❌ Import échoué: {result['error_count']} erreurs")
							for error in result["errors"]:
								st.error(error)

		except Exception as e:
			st.error(f"❌ Erreur lors de la lecture du fichier: {str(e)}")

def render_import_export_interface(import_export_manager: DynamicImportExport,
                                   key_prefix: str = "", can_import: bool = True, can_export: bool = True):
	"""
	Affiche l'interface Streamlit pour l'import/export d'une table

	Args:
		import_export_manager: Instance de DynamicImportExport
		key_prefix: Préfixe pour les clés Streamlit (éviter les conflits)
	"""
	table_name = import_export_manager.model.__tablename__
	pretty_table_name = import_export_manager.model.__crud_tablename__

	if not can_import and not can_export:
		st.warning("Aucune action disponible pour cette table")
		return
	elif not can_import:
		st.subheader(f"📊 Export - {pretty_table_name}")
		render_export(key_prefix, table_name, pretty_table_name)
	elif not can_export:
		st.subheader(f"📊 Import - {pretty_table_name}")
		render_import(key_prefix, table_name, pretty_table_name, import_export_manager)
	else:
		st.subheader(f"📊 Import/Export - {pretty_table_name}")
		# Onglets pour séparer import et export
		tab_export, tab_import = st.tabs(["📤 Export", "📥 Import"])
		with tab_export:
			render_export(key_prefix, table_name, pretty_table_name, import_export_manager)
		with tab_import:
			render_import(key_prefix, table_name, pretty_table_name, import_export_manager)
