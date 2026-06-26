import pandas as pd
import unicodedata
import matplotlib.pyplot as plt
import re
import math

# FONCTION POUR CONVERTIR LES COORDONNEES EN PROJECTION DE MERCATOR
def mercator_projection(latitude, longitude):
    """
    CONVERTIT LES COORDONNEES LATITUDE/LONGITUDE EN PROJECTION MERCATOR
    - ENTREES: latitude et longitude en degrés
    - SORTIES: x (longitude) et y (latitude projetée) en unités Mercator
    """
    # X RESTE LA LONGITUDE (EN RADIANS)
    x = math.radians(longitude)
    
    # Y EST LA LATITUDE TRANSFORMEE SELON LA PROJECTION MERCATOR
    # FORMULE: y = ln(tan(π/4 + latitude/2))
    lat_rad = math.radians(latitude)
    y = math.log(math.tan(math.pi / 4 + lat_rad / 2))
    
    return x, y

# FONCTION POUR NORMALISER LES NOMS DE COMMUNES
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

# OUVRIR LES DEUX FICHIERS CSV
df1 = pd.read_csv('donnees_communes.csv', sep=';')
df2 = pd.read_csv('20230823-communes-departement-region.csv')

# NORMALISER LES COLONNES COMMUNES
df1['Commune_normalise'] = df1['Commune'].apply(normaliser_commune)
df2['nom_commune_normalise'] = df2['nom_commune_postal'].apply(normaliser_commune)

# FAIRE LA JOINTURE DES BASES DE DONNEES
df_joined = pd.merge(df1, df2, left_on='Commune_normalise', right_on='nom_commune_normalise', how='inner')

# FILTRER LES DONNEES VALIDES (AVEC COORDONNEES ET POPULATION)
df_plot = df_joined.dropna(subset=['latitude', 'longitude', 'PTOT']).copy()

# APPLIQUER LA PROJECTION DE MERCATOR AUX COORDONNEES
mercator_coords = df_plot[['latitude', 'longitude']].apply(
    lambda row: mercator_projection(row['latitude'], row['longitude']),
    axis=1,
    result_type='expand'
)
df_plot['x_mercator'] = mercator_coords[0]
df_plot['y_mercator'] = mercator_coords[1]

print(f"Nombre de points à afficher: {len(df_plot)}")
print(f"Population min: {df_plot['PTOT'].min()}")
print(f"Population max: {df_plot['PTOT'].max()}")

# VERIFIER PARIS, MARSEILLE, LYON
print("\n=== ARRONDISSEMENTS DETECTES ===")
print("Paris:")
print(df_plot[df_plot['Commune_normalise'].str.contains('PARIS', na=False)][['Commune', 'PTOT', 'code_postal']].head(10))
print("\nMarseille:")
print(df_plot[df_plot['Commune_normalise'].str.contains('MARSEILLE', na=False)][['Commune', 'PTOT', 'code_postal']].head(10))
print("\nLyon:")
print(df_plot[df_plot['Commune_normalise'].str.contains('LYON', na=False)][['Commune', 'PTOT', 'code_postal']].head(10))

# CREER LE NUAGE DE POINTS AVEC PROJECTION DE MERCATOR
fig, ax = plt.subplots(figsize=(14, 10))

# CREER LE SCATTER PLOT AVEC PROJECTION MERCATOR:
# - POSITION: coordonnees Mercator (x_mercator, y_mercator)
# - TAILLE: proportionnelle à la population
# - COULEUR: gradient selon la population
scatter = ax.scatter(df_plot['x_mercator'], 
                     df_plot['y_mercator'],
                     s=df_plot['PTOT'] / 10,  # TAILLE PROPORTIONNELLE A LA POPULATION
                     c=df_plot['PTOT'],  # COULEUR SELON LA POPULATION
                     cmap='twilight',  # COLORMAP MAGENTA-CYAN-MAGENTA
                     alpha=0.6,  # TRANSPARENCE
                     edgecolors='black',
                     linewidth=0.5)

# AJOUTER LA BARRE DE COULEUR
cbar = plt.colorbar(scatter, ax=ax, label='Population')

# LABELS ET TITRE
ax.set_xlabel('Longitude (Mercator, radians)', fontsize=12)
ax.set_ylabel('Latitude (Mercator, unités log)', fontsize=12)
ax.set_title('Nuage de points - Communes avec populations\n(Projection de Mercator - Taille et couleur proportionnelles à la population)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

# SAUVEGARDER ET AFFICHER
plt.tight_layout()
plt.savefig('nuage_points_communes.png', dpi=300, bbox_inches='tight')
print("\n✅ Graphique sauvegardé en 'nuage_points_communes.png'")
plt.show()
