# views/data_management.py
"""Page de gestion des données"""

import streamlit as st
import pandas as pd
from config.settings import DEFAULT_CATEGORIES, PRIORITY_OPTIONS, STATUS_OPTIONS


def show_data_management(db_manager, user_id):
	"""Affiche la page de gestion des données"""
	st.title("🗂️ Gestion des Données")

	if not user_id:
		st.error("Erreur: Utilisateur non trouvé")
		return

	df = db_manager.get_user_data(user_id)

	# Onglets pour les différentes actions
	tab1, tab2, tab3 = st.tabs(["📋 Voir les données", "➕ Ajouter", "✏️ Modifier"])

	with tab1:
		show_data_view(df, db_manager, user_id)

	with tab2:
		show_add_data_form(db_manager, user_id)

	with tab3:
		show_edit_data_form(df, db_manager, user_id)


def show_data_view(df, db_manager, user_id):
	"""Affiche la vue des données avec filtres"""
	if df.empty:
		st.info("Aucune donnée disponible.")
		return

	# Filtres
	col1, col2, col3 = st.columns(3)

	with col1:
		categories = ["Toutes"] + sorted(df['category'].unique().tolist())
		selected_category = st.selectbox("Catégorie:", categories)

	with col2:
		statuses = ["Tous"] + sorted(df['status'].unique().tolist())
		selected_status = st.selectbox("Statut:", statuses)

	with col3:
		priorities = ["Toutes"] + sorted(df['priority'].unique().tolist())
		selected_priority = st.selectbox("Priorité:", priorities)

	search_term = st.text_input("🔍 Rechercher:", placeholder="Titre, contenu ou tags...")

	# Application des filtres
	filtered_df = apply_filters(df, selected_category, selected_status, selected_priority, search_term)

	st.write(f"**{len(filtered_df)}** entrée(s) trouvée(s)")

	# Affichage des données
	display_data_entries(filtered_df, db_manager, user_id)


def apply_filters(df, category, status, priority, search_term):
	"""Applique les filtres sur le DataFrame"""
	filtered_df = df.copy()

	if category != "Toutes":
		filtered_df = filtered_df[filtered_df['category'] == category]

	if status != "Tous":
		filtered_df = filtered_df[filtered_df['status'] == status]

	if priority != "Toutes":
		filtered_df = filtered_df[filtered_df['priority'] == priority]

	if search_term:
		mask = (
				filtered_df['title'].str.contains(search_term, case=False, na=False) |
				filtered_df['content'].str.contains(search_term, case=False, na=False) |
				filtered_df['tags'].str.contains(search_term, case=False, na=False)
		)
		filtered_df = filtered_df[mask]

	return filtered_df


def display_data_entries(df, db_manager, user_id):
	"""Affiche les entrées de données"""
	for _, row in df.iterrows():
		with st.container():
			col1, col2 = st.columns([4, 1])

			with col1:
				priority_emoji = {"High": "🔥", "Medium": "⚡", "Low": "📝"}.get(row['priority'], "📝")
				status_emoji = {"Active": "✅", "Completed": "✔️", "Paused": "⏸️", "Cancelled": "❌"}.get(row['status'],
				                                                                                        "📝")

				st.markdown(f"### {priority_emoji} {row['title']}")
				st.markdown(
					f"**Catégorie:** {row['category']} | **Statut:** {status_emoji} {row['status']} | **Priorité:** {row['priority']}")

				if row['content']:
					st.markdown(f"**Contenu:** {row['content']}")

				if row['tags']:
					tags = [f"`{tag.strip()}`" for tag in row['tags'].split(',')]
					st.markdown(f"**Tags:** {' '.join(tags)}")

				st.markdown(f"**Créé:** {pd.to_datetime(row['created_at']).strftime('%d/%m/%Y %H:%M')}")
				if row['updated_at'] != row['created_at']:
					st.markdown(f"**Modifié:** {pd.to_datetime(row['updated_at']).strftime('%d/%m/%Y %H:%M')}")

			with col2:
				if st.button(f"🗑️", key=f"delete_{row['id']}", help="Supprimer"):
					success, message = db_manager.delete_user_data(row['id'], user_id)
					if success:
						st.success(message)
						st.rerun()
					else:
						st.error(message)

			st.divider()


def show_add_data_form(db_manager, user_id):
	"""Affiche le formulaire d'ajout de données"""
	with st.form("add_data_form", clear_on_submit=True):
		st.subheader("➕ Ajouter une nouvelle entrée")

		col1, col2 = st.columns(2)

		with col1:
			title = st.text_input("Titre*", placeholder="Titre de votre entrée")
			category = st.selectbox("Catégorie*", DEFAULT_CATEGORIES)
			priority = st.selectbox("Priorité", PRIORITY_OPTIONS, index=1)

		with col2:
			status = st.selectbox("Statut", STATUS_OPTIONS)
			tags = st.text_input("Tags", placeholder="tag1, tag2, tag3...")

		content = st.text_area("Contenu", height=150, placeholder="Décrivez votre entrée...")

		submitted = st.form_submit_button("💾 Enregistrer", use_container_width=True)

		if submitted:
			if title and category:
				success, message = db_manager.add_user_data(
					user_id, title, content, category, priority, status, tags
				)
				if success:
					st.success(message)
					st.balloons()
				else:
					st.error(message)
			else:
				st.error("Le titre et la catégorie sont obligatoires")


def show_edit_data_form(df, db_manager, user_id):
	"""Affiche le formulaire de modification"""
	if df.empty:
		st.info("Aucune donnée à modifier.")
		return

	# Sélection de l'entrée à modifier
	options = [f"{row['title']} (ID: {row['id']})" for _, row in df.iterrows()]
	selected = st.selectbox("Sélectionner une entrée à modifier:", options)

	if selected:
		entry_id = int(selected.split("ID: ")[1].split(")")[0])
		entry = df[df['id'] == entry_id].iloc[0]

		with st.form("edit_data_form"):
			st.subheader(f"✏️ Modifier: {entry['title']}")

			col1, col2 = st.columns(2)

			with col1:
				title = st.text_input("Titre*", value=entry['title'])
				category = st.selectbox("Catégorie*",
				                        DEFAULT_CATEGORIES,
				                        index=DEFAULT_CATEGORIES.index(entry['category']) if entry[
					                                                                             'category'] in DEFAULT_CATEGORIES else 0)
				priority = st.selectbox("Priorité", PRIORITY_OPTIONS,
				                        index=PRIORITY_OPTIONS.index(entry['priority']) if entry[
					                                                                           'priority'] in PRIORITY_OPTIONS else 1)

			with col2:
				status = st.selectbox("Statut", STATUS_OPTIONS,
				                      index=STATUS_OPTIONS.index(entry['status']) if entry[
					                                                                     'status'] in STATUS_OPTIONS else 0)
				tags = st.text_input("Tags", value=entry['tags'] if entry['tags'] else "")

			content = st.text_area("Contenu", value=entry['content'] if entry['content'] else "", height=150)

			submitted = st.form_submit_button("💾 Mettre à jour", use_container_width=True)

			if submitted:
				if title and category:
					success, message = db_manager.update_user_data(
						entry_id, user_id, title, content, category, priority, status, tags
					)
					if success:
						st.success(message)
						st.rerun()
					else:
						st.error(message)
				else:
					st.error("Le titre et la catégorie sont obligatoires")
