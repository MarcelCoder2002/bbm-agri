"""Page du dashboard"""
import pandas as pd
import plotly.express as px

from database.models import Stock, Product, StockRecord, SalesDepartment
from modules.db import DB
from modules.page import Page as BasePage, st


class Page(BasePage):
	@classmethod
	def render(cls):
		st.title("📊 Analyse des Niveaux de Stock")
		st.markdown("---")

		# Chargement des données
		try:
			with st.spinner("Chargement des données..."):
				df = cls.get_stock_data()

			if df.empty:
				st.warning("Aucune donnée de stock disponible.")
				return

			# Sidebar pour les filtres
			st.sidebar.header("Filtres")

			# Filtre par département
			departments = df['department_name'].unique()
			selected_departments = st.sidebar.multiselect(
				"Départements",
				departments,
				default=departments
			)

			# Filtre par produit
			product_names = df['product_name'].unique()
			selected_base_products = st.sidebar.multiselect(
				"Produits de base (optionnel)",
				product_names,
				default=[]
			)

			# Filtre par produit complet (nom + quantité + unité)
			full_products = df['product_full_name'].unique()
			selected_full_products = st.sidebar.multiselect(
				"Produits spécifiques (optionnel)",
				full_products,
				default=[],
				help="Sélectionnez des produits spécifiques avec leur taille/unité"
			)

			# Appliquer les filtres
			filtered_df = df[df['department_name'].isin(selected_departments)]
			if selected_base_products:
				filtered_df = filtered_df[filtered_df['product_name'].isin(selected_base_products)]
			if selected_full_products:
				filtered_df = filtered_df[filtered_df['product_full_name'].isin(selected_full_products)]

			# Métriques principales
			col1, col2, col3, col4 = st.columns(4)

			with col1:
				st.metric("Total Produits", len(filtered_df))

			with col2:
				st.metric("Stock Total", f"{filtered_df['stock_quantity'].sum():,.0f}")

			with col3:
				st.metric("Stock Moyen", f"{filtered_df['stock_quantity'].mean():.1f}")

			with col4:
				st.metric("Stock Maximum", f"{filtered_df['stock_quantity'].max():,.0f}")

			st.markdown("---")

			# Graphique principal (similaire à votre image)
			st.subheader("📈 Niveau de Stock par Produit")

			chart_type = st.radio(
				"Type de graphique:",
				["line", "bar"],
				format_func=lambda x: "Ligne" if x == "line" else "Barres",
				horizontal=True
			)

			main_chart = cls.create_stock_level_chart(filtered_df, chart_type)
			st.plotly_chart(main_chart, use_container_width=True)

			# Graphiques supplémentaires
			col1, col2 = st.columns(2)

			with col1:
				st.subheader("🏢 Stock par Département")
				dept_chart = cls.create_department_comparison_chart(filtered_df)
				st.plotly_chart(dept_chart, use_container_width=True)

			with col2:
				st.subheader("📊 Distribution des Stocks")
				dist_chart = cls.create_stock_distribution_chart(filtered_df)
				st.plotly_chart(dist_chart, use_container_width=True)

			# Top produits
			st.subheader("🏆 Top 10 des Produits")
			top_n = st.slider("Nombre de produits à afficher", 5, 20, 10)
			top_chart = cls.create_top_products_chart(filtered_df, top_n)
			st.plotly_chart(top_chart, use_container_width=True)

			# Évolution temporelle
			st.subheader("📅 Évolution dans le Temps")
			time_chart = cls.create_time_series_chart(filtered_df)
			st.plotly_chart(time_chart, use_container_width=True)

			# Graphiques spécifiques aux variantes de produits
			st.subheader("🔄 Analyse des Variantes de Produits")

			col1, col2 = st.columns(2)

			with col1:
				st.write("**Produits Groupés par Variantes**")
				grouped_chart = cls.create_grouped_products_chart(filtered_df)
				st.plotly_chart(grouped_chart, use_container_width=True)

			with col2:
				st.write("**Variantes d'un Produit Spécifique**")
				available_products = filtered_df['product_name'].unique()
				if len(available_products) > 0:
					selected_product_for_variants = st.selectbox(
						"Choisir un produit:",
						available_products,
						key="variant_selector"
					)
					variant_chart = cls.create_product_variants_chart(filtered_df, selected_product_for_variants)
					st.plotly_chart(variant_chart, use_container_width=True)

			# Tableau de données
			with st.expander("📋 Voir les données détaillées"):
				st.dataframe(
					filtered_df.sort_values('stock_quantity', ascending=False),
					use_container_width=True
				)

				# Bouton de téléchargement
				csv = filtered_df.to_csv(index=False)
				st.download_button(
					label="💾 Télécharger les données (CSV)",
					data=csv,
					file_name="stock_data.csv",
					mime="text/csv"
				)

		except Exception as e:
			st.error(f"Erreur lors du chargement des données: {str(e)}")
			st.info("Vérifiez que votre base de données est accessible et contient des données.")

	@classmethod
	def get_stock_data(cls):
		"""Récupère les données de stock depuis la base de données"""

		query = DB.query(
			Product.name.label('product_name'),
			Product.quantity.label('product_quantity'),
			Product.unit.label('product_unit'),
			Stock.quantity.label('stock_quantity'),
			StockRecord.start_date.label('start_date'),
			StockRecord.end_date.label('end_date'),
			SalesDepartment.name.label('department_name')
		).join(
			Stock, Product.id == Stock.id_product
		).join(
			StockRecord, Stock.id_stock_record == StockRecord.id
		).join(
			SalesDepartment, StockRecord.id_sales_department == SalesDepartment.id
		).order_by(Product.name, Product.quantity, StockRecord.start_date)

		data = query.all()
		df = pd.DataFrame(data)

		# Créer un nom de produit unique combinant nom + quantité + unité
		df['product_full_name'] = df.apply(
			lambda row: f"{row['product_name']} {row['product_quantity']}{row['product_unit']}"
			if pd.notna(row['product_quantity']) and pd.notna(row['product_unit'])
			else row['product_name'],
			axis=1
		)

		return df

	@classmethod
	def create_stock_level_chart(cls, df, chart_type="line"):
		"""Crée un graphique des niveaux de stock par produit"""
		fig = None

		if chart_type == "line":
			fig = px.line(
				df,
				x='product_full_name',
				y='stock_quantity',
				title='Niveau de Stock de Tous les Produits',
				labels={
					'product_full_name': 'Produit',
					'stock_quantity': 'Stock'
				}
			)

			# Personnalisation pour ressembler à votre graphique
			fig.update_traces(
				line=dict(color='blue', width=2),
				marker=dict(size=6, color='blue')
			)

		elif chart_type == "bar":
			fig = px.bar(
				df,
				x='product_full_name',
				y='stock_quantity',
				title='Niveau de Stock de Tous les Produits',
				labels={
					'product_full_name': 'Produit',
					'stock_quantity': 'Stock'
				}
			)
			fig.update_traces(marker_color='blue')

		# Mise en forme similaire à votre graphique
		fig.update_layout(
			xaxis_title='Produit',
			yaxis_title='Stock',
			xaxis={'tickangle': 45},
			height=600,
			showlegend=False,
			plot_bgcolor='white',
			paper_bgcolor='white'
		)

		fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
		fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

		return fig

	@classmethod
	def create_department_comparison_chart(cls, df):
		"""Crée un graphique de comparaison par département"""
		dept_summary = df.groupby('department_name')['stock_quantity'].sum().reset_index()

		fig = px.bar(
		    dept_summary,
		    x='department_name',
		    y='stock_quantity',
		    title='Stock Total par Département Commercial',
		    labels={
		        'department_name': 'Département',
		        'stock_quantity': 'Stock Total'
		    }
		)

		fig.update_traces(marker_color='steelblue')
		fig.update_layout(
		    height=400,
		    showlegend=False
		)

		return fig

	@classmethod
	def create_top_products_chart(cls, df, top_n=10):
		"""Crée un graphique des produits avec le plus de stock"""
		top_products = df.nlargest(top_n, 'stock_quantity')

		fig = px.bar(
			top_products,
			x='product_full_name',
			y='stock_quantity',
			title=f'Top {top_n} des Produits avec le Plus de Stock',
			labels={
				'product_full_name': 'Produit',
				'stock_quantity': 'Stock'
			}
		)

		fig.update_traces(marker_color='green')
		fig.update_layout(
			xaxis={'tickangle': 45},
			height=500,
			showlegend=False
		)

		return fig

	@classmethod
	def create_stock_distribution_chart(cls, df):
		"""Crée un histogramme de distribution des stocks"""
		fig = px.histogram(
			df,
			x='stock_quantity',
			nbins=20,
			title='Distribution des Niveaux de Stock',
			labels={
				'stock_quantity': 'Niveau de Stock',
				'count': 'Nombre de Produits'
			}
		)

		fig.update_traces(marker_color='orange')
		fig.update_layout(height=400)

		return fig

	@classmethod
	def create_grouped_products_chart(cls, df):
		"""Crée un graphique groupé par nom de produit de base"""
		grouped_df = df.groupby(['product_name', 'product_full_name'])['stock_quantity'].sum().reset_index()

		fig = px.bar(
			grouped_df,
			x='product_name',
			y='stock_quantity',
			color='product_full_name',
			title='Stock par Produit (Groupé par Tailles/Unités)',
			labels={
				'product_name': 'Produit',
				'stock_quantity': 'Stock',
				'product_full_name': 'Variante'
			}
		)

		fig.update_layout(
			xaxis={'tickangle': 45},
			height=500,
			barmode='group'
		)

		return fig

	@classmethod
	def create_product_variants_chart(cls, df, selected_product=None):
		"""Crée un graphique des variantes d'un produit spécifique"""
		if selected_product:
			product_variants = df[df['product_name'] == selected_product]
		else:
			# Prendre le produit avec le plus de variantes
			variant_counts = df.groupby('product_name').size()
			selected_product = variant_counts.idxmax()
			product_variants = df[df['product_name'] == selected_product]

		fig = px.bar(
			product_variants,
			x='product_full_name',
			y='stock_quantity',
			title=f'Variantes de {selected_product}',
			labels={
				'product_full_name': 'Variante',
				'stock_quantity': 'Stock'
			}
		)

		fig.update_traces(marker_color='teal')
		fig.update_layout(
			xaxis={'tickangle': 45},
			height=400,
			showlegend=False
		)

		return fig

	@classmethod
	def create_time_series_chart(cls, df):
		"""Crée un graphique temporel d'évolution des stocks"""
		# Grouper par date de début et calculer le stock total
		time_series = df.groupby('start_date')['stock_quantity'].sum().reset_index()
		time_series['start_date'] = pd.to_datetime(time_series['start_date'])

		fig = px.line(
		    time_series,
		    x='start_date',
		    y='stock_quantity',
		    title='Évolution des Stocks dans le Temps',
		    labels={
		        'start_date': 'Date',
		        'stock_quantity': 'Stock Total'
		    }
		)

		fig.update_traces(line=dict(color='purple', width=3))
		fig.update_layout(height=400)

		return fig


Page.run()
