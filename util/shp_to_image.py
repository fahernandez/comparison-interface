"""
Script to generate images used on the comparative judgment procedure.
These images are generated using as based a .shp file. This script
extract each of the regions from the shape file and create an image stored
on static/image/. The script will require the presence of files:
-regions.shp
-regions.cpg
-regions.prj
-regions.shx
-regions.dbf
-regions.xml
Use: >python shp_to_image.py {location_to_the_shape_folder}
"""
import os
import shutil
import argparse
import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt
from tqdm.contrib.concurrent import process_map

def load_shapefile(args):
    """Load the shapefile used to extract the images used on the comparative judgement procedure.

    Args:
        args (dict): options used to parse the shp file

    Returns:
        pandas: pandas dataframe containing the shp file structure
    """
    print('Loading Shapefile')
    try:
        df = gpd.read_file(args.shapefile)
        df = df.to_crs(epsg=3857)
    except Exception as e:
        print(e)
        exit()
        
    # Identify geometry column which must exists and be unique
    col_geom = df.select_dtypes(include=['geometry']).columns
    assert len(col_geom) == 1
    col_geom = col_geom[0]

    # Choose ID column
    print(
        '\nYou need to choose a column as unique identifier of your items, potential candidates are:'
    )
    col_idx = None
    while col_idx is None:
        col_idx = choose_column(df)

    print('\n\n\nSummary of selected columns:')
    print('\t[ID] {}'.format(col_idx))
    print('\t[Geometry] {}'.format(col_geom))

    # df.set_index(col_idx, inplace=True)
    df.rename(columns={col_idx: 'chosen_id'}, inplace=True)
    df.reset_index(inplace=True)
    df.index = df.index + 1

    return df[['chosen_id', col_geom]]

def choose_column(df):
    """Select candidates columns from the shp files to use as items descriptors.

    Args:
        df (dataframe): DataFrame containing the shape object

    Returns:
        list: Column manually selected by the website configurator. None on error.
    """
    id_candidates = df.select_dtypes(exclude=['geometry']).columns
    id_candidates = [x for x in id_candidates if df[x].is_unique]
    longest = max([len(x) for x in id_candidates])

    print('--\tColumn Name\tExample')
    for i, col in enumerate(id_candidates):
        print('{})\t{:<{longest}}\t{}'.format(i,
                                              col,
                                              df.iloc[0][col],
                                              longest=longest))

    choice = input('Please choose the ID column to use [0-{}]: '.format(
        len(id_candidates) - 1))

    try:
        choice = id_candidates[int(choice)]
        return choice
    except:
        print('Invalid choice')

    return None

def generate_item_images(df_row):
    """Generate the images used on the comparative judgement from the shapefile.

    Args:
        df_row (PandasRow): each of the items to be compared.
    """
    row = df_row.iloc[0]
    (minx, miny, maxx, maxy) = row.geometry.bounds

    cx = row.geometry.centroid.x
    cy = row.geometry.centroid.y

    dx = (maxx - minx)
    dy = (maxy - miny)

    if dx > dy:
        padding = dx // 2 + dx // 8
    else:
        padding = dy // 2 + dy // 8

    fig, ax = plt.subplots()

    ax.set_xlim((cx - padding, cx + padding))
    ax.set_ylim((cy - padding, cy + padding))

    df_row.plot(ax=ax, facecolor="none", edgecolor="red", lw=1)
    ctx.add_basemap(ax,
                    crs=df_row.geometry.crs.to_string(),
                    source=ctx.providers.Esri.NatGeoWorldMap,
                    attribution='')
    plt.axis('off')

    plt.savefig(f'{abs_image_path}/item_{df_row.index.to_list()[0]}.png',
                dpi=200,
                bbox_inches='tight',
                pad_inches=0)

    plt.close(fig)

def get_image_path():
    """Return the absolute path of the image folder

    Returns:
        string: Absolute image folder path
    """
    return os.path.abspath(os.path.dirname(__file__)) + "/../static/image"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=
        'Create images from a Shapefile containing the items of interest'
    )
    # Positional arguments
    parser.add_argument('shapefile',
                        metavar='shapefile',
                        type=str,
                        help='a Shapefile containing items to be surveyed')

    args = parser.parse_args()
    print('\n\n\n')
    abs_image_path = get_image_path()

    # Create output directory
    if os.path.exists(abs_image_path):
        # TODO Add warning / confirmation about emptying folder
        shutil.rmtree(abs_image_path)

    os.mkdir(abs_image_path)

    # Load Shapefile
    df = load_shapefile(args)

    # Generate images for individual items
    print('\nGenerating images for individual items')
    items = [df.loc[[i]] for i in df.index]
    process_map(generate_item_images, items)

    # TODO Check all images were properly generated, maybe a simple file count?

