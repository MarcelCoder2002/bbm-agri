import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from database.models import Stock, Product, StockRecord, SalesDepartment
from modules.db import DB
from modules.page import Page as BasePage, st


class Page(BasePage):
	@classmethod
	def get_stock_records_data(cls):
		"""Récupère les enregistrements de stock avec leurs données"""
		query = DB.query(
			StockRecord.id.label('record_id'),
			StockRecord.start_date,
			StockRecord.end_date,
			SalesDepartment.name.label('department_name'),
			Product.name.label('product_name'),
			Product.quantity.label('product_quantity'),
			Product.unit.label('product_unit'),
			Stock.quantity.label('stock_quantity')
		).join(
			SalesDepartment, StockRecord.id_sales_department == SalesDepartment.id
		).join(
			Stock, StockRecord.id == Stock.id_stock_record
		).join(
			Product, Stock.id_product == Product.id
		).order_by(StockRecord.start_date.desc(), Product.name)

		data = query.all()
		df = pd.DataFrame(data)

		if not df.empty:
			# Créer un nom de produit unique
			df['product_full_name'] = df.apply(
				lambda row: f"{row['product_name']} {row['product_quantity']}{row['product_unit']}"
				if pd.notna(row['product_quantity']) and pd.notna(row['product_unit'])
				else row['product_name'],
				axis=1
			)

			# Créer un identifiant de période
			df['period_label'] = df.apply(
				lambda
					row: f"{row['department_name']} ({row['start_date'].strftime('%d/%m/%Y')} - {row['end_date'].strftime('%d/%m/%Y')})",
				axis=1
			)

		return df

	@classmethod
	def create_flow_comparison_chart(cls, selected_records_data, selected_products=None):
		"""Crée un graphique de comparaison des flux entre périodes"""

		if selected_products:
			filtered_data = selected_records_data[selected_records_data['product_full_name'].isin(selected_products)]
		else:
			filtered_data = selected_records_data

		fig = px.line(
			filtered_data,
			x='product_full_name',
			y='stock_quantity',
			color='period_label',
			markers=True,
			title='Comparaison des Niveaux de Stock entre Périodes',
			labels={
				'product_full_name': 'Produit',
				'stock_quantity': 'Quantité en Stock',
				'period_label': 'Période'
			}
		)

		fig.update_layout(
			height=600,
			xaxis={'tickangle': 45},
			legend=dict(
				orientation="h",
				yanchor="bottom",
				y=1.02,
				xanchor="right",
				x=1
			)
		)

		return fig

	@classmethod
	def create_variation_chart(cls, selected_records_data):
		"""Crée un graphique des variations absolues et relatives"""

		# Calculer les variations entre la première et la dernière période
		pivot_data = selected_records_data.pivot_table(
			index='product_full_name',
			columns='period_label',
			values='stock_quantity',
			fill_value=0
		)

		if pivot_data.shape[1] < 2:
			st.warning("Il faut au moins 2 périodes pour calculer les variations.")
			return None

		# Prendre la première et dernière colonne (période)
		first_period = pivot_data.columns[0]
		last_period = pivot_data.columns[-1]

		variations_df = pd.DataFrame({
			'product_full_name': pivot_data.index,
			'stock_initial': pivot_data[first_period],
			'stock_final': pivot_data[last_period]
		})

		# Calculer les variations
		variations_df['variation_absolue'] = variations_df['stock_final'] - variations_df['stock_initial']
		variations_df['variation_relative'] = np.where(
			variations_df['stock_initial'] != 0,
			(variations_df['variation_absolue'] / variations_df['stock_initial']) * 100,
			0
		)

		# Créer le graphique avec deux axes Y
		fig = make_subplots(
			rows=1, cols=2,
			subplot_titles=['Variation Absolue', 'Variation Relative (%)'],
			specs=[[{"secondary_y": False}, {"secondary_y": False}]]
		)

		# Variation absolue
		colors_abs = ['red' if x < 0 else 'green' for x in variations_df['variation_absolue']]
		fig.add_trace(
			go.Bar(
				x=variations_df['product_full_name'],
				y=variations_df['variation_absolue'],
				name='Variation Absolue',
				marker_color=colors_abs,
				showlegend=False
			),
			row=1, col=1
		)

		# Variation relative
		colors_rel = ['red' if x < 0 else 'green' for x in variations_df['variation_relative']]
		fig.add_trace(
			go.Bar(
				x=variations_df['product_full_name'],
				y=variations_df['variation_relative'],
				name='Variation Relative (%)',
				marker_color=colors_rel,
				showlegend=False
			),
			row=1, col=2
		)

		fig.update_layout(
			title=f'Variations du Stock entre {first_period} et {last_period}',
			height=500
		)

		fig.update_xaxes(tickangle=45)

		return fig, variations_df

	@classmethod
	def create_heatmap_chart(cls, selected_records_data):
		"""Crée une heatmap des stocks par produit et période"""

		pivot_data = selected_records_data.pivot_table(
			index='product_full_name',
			columns='period_label',
			values='stock_quantity',
			fill_value=0
		)

		fig = px.imshow(
			pivot_data.values,
			x=pivot_data.columns,
			y=pivot_data.index,
			color_continuous_scale='RdYlGn',
			title='Heatmap des Niveaux de Stock par Période',
			labels={'color': 'Quantité en Stock'}
		)

		fig.update_layout(
			height=max(400, len(pivot_data.index) * 20),
			xaxis={'tickangle': 45}
		)

		return fig

	@classmethod
	def create_trend_analysis_chart(cls, selected_records_data):
		"""Crée un graphique d'analyse des tendances"""

		# Calculer la tendance moyenne par produit
		trend_data = []

		for product in selected_records_data['product_full_name'].unique():
			product_data = selected_records_data[selected_records_data['product_full_name'] == product]
			product_data = product_data.sort_values('start_date')

			if len(product_data) > 1:
				# Calculer la tendance (pente de régression linéaire simple)
				x = np.arange(len(product_data))
				y = product_data['stock_quantity'].values
				trend = np.polyfit(x, y, 1)[0]  # Pente

				trend_data.append({
					'product_full_name': product,
					'trend': trend,
					'avg_stock': product_data['stock_quantity'].mean(),
					'volatility': product_data['stock_quantity'].std()
				})

		trend_df = pd.DataFrame(trend_data)

		if not trend_df.empty:
			fig = px.scatter(
				trend_df,
				x='avg_stock',
				y='trend',
				size='volatility',
				hover_name='product_full_name',
				title='Analyse des Tendances: Stock Moyen vs Tendance',
				labels={
					'avg_stock': 'Stock Moyen',
					'trend': 'Tendance (évolution)',
					'volatility': 'Volatilité'
				}
			)

			# Ajouter des lignes de référence
			fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.7)

			fig.update_layout(height=500)
			return fig, trend_df

		return None, pd.DataFrame()

	@classmethod
	def create_period_summary_table(cls, selected_records_data):
		"""Crée un tableau récapitulatif par période"""

		summary = selected_records_data.groupby('period_label').agg({
			'stock_quantity': ['sum', 'mean', 'std', 'count'],
			'product_full_name': 'nunique'
		}).round(2)

		summary.columns = ['Stock Total', 'Stock Moyen', 'Écart-type', 'Nb Entrées', 'Nb Produits']
		summary = summary.reset_index()

		return summary

	@classmethod
	def render(cls):
		"""Interface principale pour l'analyse des flux de stock"""

		st.title("📈 Analyse des Flux de Stock entre Périodes")
		st.markdown("---")

		try:
			with st.spinner("Chargement des données..."):
				df = cls.get_stock_records_data()

			if df.empty:
				st.warning("Aucun enregistrement de stock disponible.")
				return

			# Sidebar pour sélection des périodes
			st.sidebar.header("🎯 Sélection des Périodes")

			# Obtenir les enregistrements uniques
			unique_records = df[['record_id', 'period_label', 'start_date']].drop_duplicates()
			unique_records = unique_records.sort_values('start_date', ascending=False)

			# Limiter à 5 enregistrements maximum
			max_records = min(5, len(unique_records))

			selected_records = st.sidebar.multiselect(
				f"Sélectionnez jusqu'à {max_records} périodes à comparer:",
				options=unique_records['record_id'].tolist(),
				format_func=lambda x: unique_records[unique_records['record_id'] == x]['period_label'].iloc[0],
				default=unique_records['record_id'].head(min(3, max_records)).tolist(),
				max_selections=max_records
			)

			if len(selected_records) < 2:
				st.warning("Veuillez sélectionner au moins 2 périodes pour effectuer une comparaison.")
				return

			# Filtrer les données selon les enregistrements sélectionnés
			selected_data = df[df['record_id'].isin(selected_records)]

			# Filtre par département
			departments = selected_data['department_name'].unique()
			selected_departments = st.sidebar.multiselect(
				"Départements:",
				departments,
				default=departments
			)

			selected_data = selected_data[selected_data['department_name'].isin(selected_departments)]

			# Filtre par produit
			all_products = selected_data['product_full_name'].unique()
			selected_products = st.sidebar.multiselect(
				"Produits spécifiques (optionnel):",
				all_products,
				default=[],
				help="Laissez vide pour voir tous les produits"
			)

			# Métriques principales
			st.subheader("📊 Aperçu Général")

			col1, col2, col3, col4 = st.columns(4)

			with col1:
				st.metric("Périodes Sélectionnées", len(selected_records))

			with col2:
				st.metric("Produits Uniques", selected_data['product_full_name'].nunique())

			with col3:
				st.metric("Départements", selected_data['department_name'].nunique())

			with col4:
				total_records = len(selected_data)
				st.metric("Total Enregistrements", total_records)

			st.markdown("---")

			# Tableau récapitulatif par période
			st.subheader("📋 Récapitulatif par Période")
			summary_table = cls.create_period_summary_table(selected_data)
			st.dataframe(summary_table, use_container_width=True)

			st.markdown("---")

			# Graphique principal de comparaison
			st.subheader("📈 Comparaison des Niveaux de Stock")

			flow_chart = cls.create_flow_comparison_chart(selected_data,
			                                              selected_products if selected_products else None)
			st.plotly_chart(flow_chart, use_container_width=True)

			# Analyse des variations
			st.subheader("🔄 Analyse des Variations")

			variation_chart, variations_df = cls.create_variation_chart(selected_data)
			if variation_chart is not None:
				st.plotly_chart(variation_chart, use_container_width=True)

				# Top variations
				col1, col2 = st.columns(2)

				with col1:
					st.write("**🔺 Plus Grandes Augmentations**")
					top_increases = variations_df.nlargest(5, 'variation_absolue')[
						['product_full_name', 'variation_absolue', 'variation_relative']]
					st.dataframe(top_increases, use_container_width=True)

				with col2:
					st.write("**🔻 Plus Grandes Diminutions**")
					top_decreases = variations_df.nsmallest(5, 'variation_absolue')[
						['product_full_name', 'variation_absolue', 'variation_relative']]
					st.dataframe(top_decreases, use_container_width=True)

			# Heatmap et analyse des tendances
			col1, col2 = st.columns(2)

			with col1:
				st.subheader("🌡️ Heatmap des Stocks")
				heatmap = cls.create_heatmap_chart(selected_data)
				st.plotly_chart(heatmap, use_container_width=True)

			with col2:
				st.subheader("📊 Analyse des Tendances")
				trend_chart, trend_df = cls.create_trend_analysis_chart(selected_data)
				if trend_chart is not None:
					st.plotly_chart(trend_chart, use_container_width=True)

					if not trend_df.empty:
						with st.expander("Voir les tendances détaillées"):
							st.dataframe(
								trend_df.sort_values('trend', ascending=False),
								use_container_width=True
							)

			# Données détaillées
			with st.expander("📋 Données Détaillées"):
				st.dataframe(
					selected_data.sort_values(['start_date', 'product_full_name']),
					use_container_width=True
				)

				# Export
				csv_data = selected_data.to_csv(index=False)
				st.download_button(
					label="💾 Télécharger les données (CSV)",
					data=csv_data,
					file_name="flux_stock_analysis.csv",
					mime="text/csv"
				)

		except Exception as e:
			st.error(f"Erreur lors du chargement des données: {str(e)}")
			st.info("Vérifiez que votre base de données est accessible et contient des données.")


Page.run()
