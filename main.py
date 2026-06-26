import pandas as pd
import unicodedata
import matplotlib.pyplot as plt
import re

# Fonction pour normaliser les noms de communes
def normaliser_commune(texte):
    """
    Normalise un nom de commune:
    - Supprime les accents
    - Convertit en majuscules
    - Remplace les tirets et apostrophes par des espaces
    - Harmonise les arrondissements (1er -> 01, 2e -> 02, etc.)
    """
    # Supprimer les accents
    texte = ''.join(c for c in unicodedata.normalize('NFD', str(texte))
                    if unicodedata.category(c) != 'Mn')
    # Convertir en majuscules
    texte = texte.upper()
    # Remplacer les tirets et apostrophes par des espaces
    texte = texte.replace('-', ' ').replace("'", ' ')
    
    # Harmoniser les arrondissements (1ER/2E/etc. -> 01/02/etc.)
    def replace_arrondissement(match):
        num = int(match.group(1))
        return f"{num:02d}"
    
    texte = re.sub(r'\b(\d+)(?:ER|E|EST|EME)\b', replace_arrondissement, texte)
    
    # Supprimer "ARRONDISSEMENT"
    texte = texte.replace('ARRONDISSEMENT', '').strip()
    
    # Supprimer les espaces multiples
    texte = ' '.join(texte.split())
    return texte

# Ouvrir les deux fichiers CSV
df1 = pd.read_csv('donnees_communes.csv', sep=';')
df2 = pd.read_csv('20230823-communes-departement-region.csv')

# Normaliser les colonnes communes
df1['Commune_normalise'] = df1['Commune'].apply(normaliser_commune)
df2['nom_commune_normalise'] = df2['nom_commune_postal'].apply(normaliser_commune)

# Faire la jointure des bases de données
df_joined = pd.merge(df1, df2, left_on='Commune_normalise', right_on='nom_commune_normalise', how='inner')

# Filtrer les données valides (avec coordonnées et population)
df_plot = df_joined.dropna(subset=['latitude', 'longitude', 'PTOT']).copy()

print(f"Nombre de points à afficher: {len(df_plot)}")
print(f"Population min: {df_plot['PTOT'].min()}")
print(f"Population max: {df_plot['PTOT'].max()}")

# Vérifier Paris, Marseille, Lyon
print("\n=== Arrondissements détectés ===")
print("Paris:")
print(df_plot[df_plot['Commune_normalise'].str.contains('PARIS', na=False)][['Commune', 'PTOT', 'code_postal']].head(10))
print("\nMarseille:")
print(df_plot[df_plot['Commune_normalise'].str.contains('MARSEILLE', na=False)][['Commune', 'PTOT', 'code_postal']].head(10))
print("\nLyon:")
print(df_plot[df_plot['Commune_normalise'].str.contains('LYON', na=False)][['Commune', 'PTOT', 'code_postal']].head(10))

# Créer le nuage de points
fig, ax = plt.subplots(figsize=(14, 10))

# Créer le scatter plot avec:
# - Position: latitude/longitude
# - Taille: proportionnelle à la population
# - Couleur: gradiente selon la population
scatter = ax.scatter(df_plot['longitude'], 
                     df_plot['latitude'],
                     s=df_plot['PTOT'] / 10,  # Taille proportionnelle à la population
                     c=df_plot['PTOT'],  # Couleur selon la population
                     cmap='twilight',  # Colormap magenta-cyan-magenta
                     alpha=0.6,  # Transparence
                     edgecolors='black',
                     linewidth=0.5)

# Ajouter la barre de couleur
cbar = plt.colorbar(scatter, ax=ax, label='Population')

# Labels et titre
ax.set_xlabel('Longitude', fontsize=12)
ax.set_ylabel('Latitude', fontsize=12)
ax.set_title('Nuage de points - Communes avec populations\n(Taille et couleur proportionnelles à la population)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

# Sauvegarder et afficher
plt.tight_layout()
plt.savefig('nuage_points_communes.png', dpi=300, bbox_inches='tight')
print("\n✅ Graphique sauvegardé en 'nuage_points_communes.png'")
plt.show()
