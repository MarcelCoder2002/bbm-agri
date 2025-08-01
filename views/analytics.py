# views/analytics.py
"""Page d'analytics avancées"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta


def show_analytics(db_manager, user_id):
	"""Affiche la page d'analytics avancées"""
	st.title("📈 Analytics Avancées")

	if not user_id:
		st.error("Erreur: Utilisateur non trouvé")
		return

	df = db_manager.get_user_data(user_id)

	if df.empty:
		st.info("Aucune donnée disponible pour l'analyse.")
		return

	# Analyse temporelle
	show_temporal_analysis(df)

	# Analyse de productivité
	show_productivity_analysis(df)

	# Analyse des tags
	show_tags_analysis(df)

	# Analyse comparative
	show_comparative_analysis(df)


def show_temporal_analysis(df):
	"""Affiche l'analyse temporelle"""
	st.subheader("📅 Analyse Temporelle")

	# Préparation des données temporelles
	df['created_date'] = pd.to_datetime(df['created_at']).dt.date
	df['created_month'] = pd.to_datetime(df['created_at']).dt.to_period('M')
	df['created_week'] = pd.to_datetime(df['created_at']).dt.to_period('W')

	col1, col2 = st.columns(2)

	with col1:
		# Créations par mois
		monthly_data = df.groupby('created_month').size()
		fig_monthly = px.bar(
			x=[str(m) for m in monthly_data.index],
			y=monthly_data.values,
			title="Créations par mois",
			labels={'x': 'Mois', 'y': 'Nombre de créations'}
		)
		fig_monthly.update_layout(xaxis_tickangle=45)
		st.plotly_chart(fig_monthly, use_container_width=True)

	with col2:
		# Créations par jour de la semaine
		df['day_of_week'] = pd.to_datetime(df['created_at']).dt.day_name()
		day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
		day_counts = df['day_of_week'].value_counts().reindex(day_order, fill_value=0)

		fig_days = px.bar(
			x=day_counts.index,
			y=day_counts.values,
			title="Créations par jour de la semaine",
			labels={'x': 'Jour', 'y': 'Nombre de créations'}
		)
		st.plotly_chart(fig_days, use_container_width=True)

	# Timeline des créations
	st.subheader("📊 Timeline des créations")
	daily_counts = df.groupby('created_date').size().reset_index(name='count')

	fig_timeline = px.line(
		daily_counts,
		x='created_date',
		y='count',
		title="Évolution quotidienne des créations",
		markers=True
	)
	fig_timeline.update_layout(xaxis_title="Date", yaxis_title="Nombre de créations")
	print(fig_timeline)
	st.plotly_chart(fig_timeline, use_container_width=True)


def show_productivity_analysis(df):
	"""Affiche l'analyse de productivité"""
	st.subheader("⚡ Analyse de Productivité")

	# Métriques de productivité
	col1, col2, col3, col4 = st.columns(4)

	with col1:
		completion_rate = len(df[df['status'] == 'Completed']) / len(df) * 100
		st.metric("Taux de complétion", f"{completion_rate:.1f}%")

	with col2:
		avg_per_month = len(df) / max(df['created_month'].nunique(), 1)
		st.metric("Moyenne/mois", f"{avg_per_month:.1f}")

	with col3:
		high_priority_ratio = len(df[df['priority'] == 'High']) / len(df) * 100
		st.metric("% Priorité haute", f"{high_priority_ratio:.1f}%")

	with col4:
		active_ratio = len(df[df['status'] == 'Active']) / len(df) * 100
		st.metric("% Actives", f"{active_ratio:.1f}%")

	# Analyse des priorités vs statuts
	st.subheader("🎯 Matrice Priorité vs Statut")

	priority_status = pd.crosstab(df['priority'], df['status'])

	fig_heatmap = px.imshow(
		priority_status.values,
		x=priority_status.columns,
		y=priority_status.index,
		title="Matrice Priorité vs Statut",
		color_continuous_scale="Blues",
		text_auto=True
	)
	st.plotly_chart(fig_heatmap, use_container_width=True)

	# Évolution des statuts dans le temps
	df['status_month'] = pd.to_datetime(df['created_at']).dt.to_period('M')
	status_evolution = df.groupby(['status_month', 'status']).size().unstack(fill_value=0)

	fig_evolution = px.area(
		status_evolution,
		title="Évolution des statuts dans le temps"
	)
	print(fig_evolution)
	st.plotly_chart(fig_evolution, use_container_width=True)


def show_tags_analysis(df):
	"""Affiche l'analyse des tags"""
	st.subheader("🏷️ Analyse des Tags")

	if df['tags'].notna().any():
		# Extraction et comptage des tags
		all_tags = []
		for tags_str in df['tags'].dropna():
			all_tags.extend([tag.strip().lower() for tag in tags_str.split(',') if tag.strip()])

		if all_tags:
			tag_counts = pd.Series(all_tags).value_counts()

			col1, col2 = st.columns(2)

			with col1:
				# Top 15 des tags
				top_tags = tag_counts.head(15)
				fig_tags = px.bar(
					x=top_tags.values,
					y=top_tags.index,
					orientation='h',
					title="Top 15 des Tags les plus utilisés",
					labels={'x': 'Fréquence', 'y': 'Tags'}
				)
				st.plotly_chart(fig_tags, use_container_width=True)

			with col2:
				# Nuage de mots (simulé avec un graphique en bulles)
				tag_df = pd.DataFrame({
					'tag': top_tags.index[:10],
					'count': top_tags.values[:10],
					'size': top_tags.values[:10] * 10
				})

				fig_bubble = px.scatter(
					tag_df,
					x='tag',
					y='count',
					size='size',
					title="Visualisation des tags populaires",
					labels={'count': 'Fréquence'}
				)
				fig_bubble.update_layout(xaxis_tickangle=45)
				st.plotly_chart(fig_bubble, use_container_width=True)

			# Tags par catégorie
			st.subheader("📊 Tags par Catégorie")
			category_tags = {}

			for _, row in df.dropna(subset=['tags']).iterrows():
				category = row['category']
				tags = [tag.strip().lower() for tag in row['tags'].split(',') if tag.strip()]

				if category not in category_tags:
					category_tags[category] = []
				category_tags[category].extend(tags)

			# Graphique des tags par catégorie
			category_tag_data = []
			for category, tags in category_tags.items():
				tag_counts_cat = pd.Series(tags).value_counts().head(5)
				for tag, count in tag_counts_cat.items():
					category_tag_data.append({
						'Catégorie': category,
						'Tag': tag,
						'Count': count
					})

			if category_tag_data:
				category_tag_df = pd.DataFrame(category_tag_data)
				fig_cat_tags = px.bar(
					category_tag_df,
					x='Tag',
					y='Count',
					color='Catégorie',
					title="Top 5 des tags par catégorie",
					barmode='group'
				)
				fig_cat_tags.update_layout(xaxis_tickangle=45)
				st.plotly_chart(fig_cat_tags, use_container_width=True)
		else:
			st.info("Aucun tag trouvé dans les données.")
	else:
		st.info("Aucun tag disponible pour l'analyse.")


def show_comparative_analysis(df):
	"""Affiche l'analyse comparative"""
	st.subheader("🔍 Analyse Comparative")

	# Comparaison par période
	col1, col2 = st.columns(2)

	with col1:
		st.write("**Comparaison par catégories**")

		# Métriques par catégorie
		category_stats = df.groupby('category').agg({
			'id': 'count',
			'status': lambda x: (x == 'Completed').sum(),
			'priority': lambda x: (x == 'High').sum()
		}).rename(columns={
			'id': 'Total',
			'status': 'Complétées',
			'priority': 'Haute priorité'
		})

		# Calcul du taux de complétion par catégorie
		category_stats['Taux complétion %'] = (
				category_stats['Complétées'] / category_stats['Total'] * 100
		).round(1)

		st.dataframe(category_stats, use_container_width=True)

	with col2:
		st.write("**Performance mensuelle**")

		# Performance par mois
		df['month_year'] = pd.to_datetime(df['created_at']).dt.to_period('M')
		monthly_stats = df.groupby('month_year').agg({
			'id': 'count',
			'status': lambda x: (x == 'Completed').sum(),
			'priority': lambda x: (x == 'High').sum()
		}).rename(columns={
			'id': 'Créées',
			'status': 'Complétées',
			'priority': 'Haute priorité'
		})

		monthly_stats.index = monthly_stats.index.astype(str)
		st.dataframe(monthly_stats, use_container_width=True)

	# Graphique radar des catégories
	st.subheader("🎯 Profil Radar des Catégories")

	categories = df['category'].unique()
	if len(categories) > 1:
		radar_data = []

		for category in categories:
			cat_data = df[df['category'] == category]
			total = len(cat_data)
			completed = len(cat_data[cat_data['status'] == 'Completed'])
			high_priority = len(cat_data[cat_data['priority'] == 'High'])
			active = len(cat_data[cat_data['status'] == 'Active'])

			radar_data.append({
				'Catégorie': category,
				'Total': total,
				'Complétées': completed,
				'Haute priorité': high_priority,
				'Actives': active
			})

		radar_df = pd.DataFrame(radar_data)

		# Normalisation pour le radar
		numeric_cols = ['Total', 'Complétées', 'Haute priorité', 'Actives']
		for col in numeric_cols:
			max_val = radar_df[col].max()
			if max_val > 0:
				radar_df[f'{col}_norm'] = radar_df[col] / max_val * 100

		# Création du graphique radar
		fig_radar = go.Figure()

		for _, row in radar_df.iterrows():
			fig_radar.add_trace(go.Scatterpolar(
				r=[row[f'{col}_norm'] for col in numeric_cols],
				theta=numeric_cols,
				fill='toself',
				name=row['Catégorie']
			))

		fig_radar.update_layout(
			polar=dict(
				radialaxis=dict(
					visible=True,
					range=[0, 100]
				)),
			showlegend=True,
			title="Profil comparatif des catégories (normalisé)"
		)

		st.plotly_chart(fig_radar, use_container_width=True)

	# Insights automatiques
	st.subheader("🤖 Insights Automatiques")

	insights = generate_insights(df)
	for insight in insights:
		st.info(f"💡 {insight}")


def generate_insights(df):
	"""Génère des insights automatiques basés sur les données"""
	insights = []

	# Insight sur la productivité
	completion_rate = len(df[df['status'] == 'Completed']) / len(df) * 100
	if completion_rate > 70:
		insights.append(f"Excellente productivité ! Vous avez un taux de complétion de {completion_rate:.1f}%")
	elif completion_rate > 50:
		insights.append(f"Bonne productivité avec {completion_rate:.1f}% de tâches complétées")
	else:
		insights.append(f"Marge d'amélioration : seulement {completion_rate:.1f}% de tâches complétées")

	# Insight sur les catégories
	most_used_category = df['category'].value_counts().index[0]
	category_count = df['category'].value_counts().iloc[0]
	total_entries = len(df)
	category_percentage = category_count / total_entries * 100

	insights.append(
		f"Votre catégorie la plus utilisée est '{most_used_category}' ({category_percentage:.1f}% de vos entrées)")

	# Insight sur les priorités
	high_priority_count = len(df[df['priority'] == 'High'])
	if high_priority_count > total_entries * 0.3:
		insights.append("Attention : vous avez beaucoup de tâches en haute priorité. Pensez à prioriser!")

	# Insight temporel
	df['created_date'] = pd.to_datetime(df['created_at']).dt.date
	recent_entries = len(df[df['created_date'] >= (datetime.now().date() - timedelta(days=7))])

	if recent_entries > 0:
		insights.append(f"Vous avez créé {recent_entries} entrée(s) cette semaine - restez actif!")

	return insights
