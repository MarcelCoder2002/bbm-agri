import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("📊 Analyse d'un fichier CSV produit depuis un PDF")

# Étape 1 : Upload CSV
uploaded_file = st.file_uploader("📤 Déposez votre fichier CSV", type="csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.success("✅ Fichier chargé avec succès !")
        st.write("Aperçu des données :", df)

        # Étape 2 : Nettoyage automatique si nécessaire
        df.columns = [col.strip().lower() for col in df.columns]
        if "stock" in df.columns:
            df["stock"] = (
                df["stock"]
                .astype(str)
                .str.replace(",", ".")
                .str.replace(" ", "")
                .astype(float)
            )
        else:
            st.warning("Colonne 'stock' non trouvée dans le fichier.")
            st.stop()

        # Étape 3 : Graphique interactif
        st.subheader("📈 Top 10 produits selon le stock")
        top = df.sort_values("stock", ascending=False).head(10)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.barh(top["nom commercial"], top["stock"], color="skyblue")
        ax.set_xlabel("Stock")
        ax.set_title("Top 10 des produits par stock")
        ax.invert_yaxis()
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Erreur de traitement du fichier : {e}")
