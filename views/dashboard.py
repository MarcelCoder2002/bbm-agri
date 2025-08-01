# views/dashboard.py
"""Page du dashboard"""

import pandas as pd
import plotly.express as px
import streamlit as st


def show_dashboard(db_manager, user_id):
	"""Affiche le dashboard principal"""
	st.title("📊 Dashboard Analytics")

	if not user_id:
		st.error("Erreur: Utilisateur non trouvé")
		return

	df = db_manager.get_user_data(user_id)

	if df.empty:
		st.info("🎯 Aucune donnée disponible. Commencez par ajouter des entrées!")
		show_quick_add_form(db_manager, user_id)
		return

	# Métriques principales
	show_main_metrics(df)

	# Graphiques
	show_charts(df)

	# Données récentes
	show_recent_data(df)


def show_main_metrics(df):
	"""Affiche les métriques principales"""
	col1, col2, col3, col4 = st.columns(4)

	with col1:
		st.metric("📝 Total d'entrées", len(df))

	with col2:
		categories_count = df['category'].nunique()
		st.metric("📂 Catégories", categories_count)

	with col3:
		active_entries = len(df[df['status'] == 'Active'])
		st.metric("✅ Actives", active_entries)

	with col4:
		high_priority = len(df[df['priority'] == 'High'])
		st.metric("🔥 Priorité haute", high_priority)


def show_charts(df):
	"""Affiche les graphiques"""
	col1, col2 = st.columns(2)

	with col1:
		st.subheader("📈 Répartition par catégorie")
		category_counts = df['category'].value_counts()
		fig_pie = px.pie(
			values=category_counts.values,
			names=category_counts.index,
			title="Distribution des catégories"
		)
		st.plotly_chart(fig_pie, use_container_width=True)

	with col2:
		st.subheader("📊 Statut des entrées")
		status_counts = df['status'].value_counts()
		fig_bar = px.bar(
			x=status_counts.index,
			y=status_counts.values,
			title="Répartition par statut",
			color=status_counts.values,
			color_continuous_scale="viridis"
		)
		st.plotly_chart(fig_bar, use_container_width=True)


def show_recent_data(df):
	"""Affiche les données récentes"""
	st.subheader("📅 Activité récente")
	recent_data = df.sort_values('created_at', ascending=False).head(5)

	for _, row in recent_data.iterrows():
		with st.expander(f"📝 {row['title']} - {row['category']}"):
			st.write(f"**Contenu:** {row['content']}")
			st.write(f"**Statut:** {row['status']} | **Priorité:** {row['priority']}")
			st.write(f"**Date:** {pd.to_datetime(row['created_at']).strftime('%d/%m/%Y %H:%M')}")


def show_quick_add_form(db_manager, user_id):
	"""Formulaire rapide d'ajout"""
	st.subheader("➕ Ajout rapide")

	with st.form("quick_add_form"):
		col1, col2 = st.columns(2)

		with col1:
			title = st.text_input("Titre*")
			category = st.selectbox("Catégorie*", ["Personnel", "Travail", "Projet", "Idée"])

		with col2:
			priority = st.selectbox("Priorité", ["High", "Medium", "Low"], index=1)
			status = st.selectbox("Statut", ["Active", "Completed"], index=0)

		content = st.text_area("Contenu", height=100)

		if st.form_submit_button("💾 Ajouter", use_container_width=True):
			if title and category:
				success, message = db_manager.add_user_data(
					user_id, title, content, category, priority, status, ""
				)
				if success:
					st.success(message)
					st.rerun()
				else:
					st.error(message)
			else:
				st.error("Titre et catégorie obligatoires")
