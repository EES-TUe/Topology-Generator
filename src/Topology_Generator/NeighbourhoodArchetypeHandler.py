import pandas as pd
import geopandas as gpd
from shapely import Point
from pyproj import Transformer

class NeighbourhoodArchetypeHandler:

    def __init__(self, archetype_df : pd.DataFrame):
        self.archetype_df : pd.DataFrame = archetype_df
        self.neigbourhood_gdf : gpd.GeoDataFrame = self.init_neighbourhood_data()
        self.clustered_neighbourhoods = pd.merge(self.neigbourhood_gdf, self.archetype_df, 
                        left_on = "statcode", 
                        right_on = "BU_code")

    def init_neighbourhood_data(self):
        geodata_url = "http://www.friesewoudloper.nl/assets/misc/2019-12-07/buurten.geojson" 
        return gpd.read_file(geodata_url)
    
    def convert_gis_coordinates_to_archetype_coordinates(self, point : Point) -> Point:
        transformer = Transformer.from_crs("EPSG:28992", "EPSG:4326")
        return Point(transformer.transform(point.x, point.y))
    
    def archetype_at_point(self, point : Point):
        converted_coordinates = self.convert_gis_coordinates_to_archetype_coordinates(point)
        output = self.neigbourhood_gdf.sindex.query(Point(converted_coordinates.y, converted_coordinates.x), predicate="within")
        archetype = 0
        if len(output) > 0:
            neighbourhood = self.neigbourhood_gdf.take([output[0]])
            stat_code = neighbourhood["statcode"].values[0]
            archetype = self.archetype_df[self.archetype_df["BU_code"] == stat_code]["archetype"].iloc[0]
        return archetype


