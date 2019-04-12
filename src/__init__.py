import folium
import pandas as pd
import geopandas as gp
from geopy.distance import geodesic


class Cidades:
    url = dict(
        estados="https://raw.githubusercontent.com/kelvins/Municipios-Brasileiros/master/csv/estados.csv",
        municipios="https://raw.githubusercontent.com/kelvins/Municipios-Brasileiros/master/csv/municipios.csv",
        municipios_topo="https://raw.githubusercontent.com/betafcc/Brasil-Topojsons/master/min/municipios.topo.json",
    )

    def __init__(self):
        self.dataframe = (
            pd.read_csv(self.url["estados"])
            .rename(columns={"nome": "estado"})
            .merge(
                pd.read_csv(self.url["municipios"]).rename(
                    columns={"nome": "municipio"}
                ),
                on="codigo_uf",
            )
            .set_index("codigo_ibge")
        )

        self.geodataframe = gp.read_file(self.url["municipios_topo"])

    def codigo_ibge(self, uf, municipio):
        matches = self.dataframe.loc[lambda df: df.uf == uf].loc[
            lambda df: df.municipio == municipio
        ]

        if len(matches) < 1:
            raise ValueError("No matches")
        elif len(matches) > 1:
            raise ValueError("More than one matched")
        else:
            return matches.iloc[0].name

    def distance(self, uf, municipio):
        cidade = self.dataframe.loc[self.codigo_ibge(uf, municipio)]
        latitude, longitude = cidade.latitude, cidade.longitude

        return self.dataframe.apply(
            lambda r: geodesic(
                (latitude, longitude), (r.latitude, r.longitude)
            ).kilometers,
            axis="columns",
        ).rename("distance")

    def cities_in_radius(self, uf, municipio, radius):
        return self.dataframe.join(
            self.distance(uf, municipio).loc[lambda s: s <= radius], how="right"
        ).sort_values("distance")

    def show(self, uf, municipio, radius):
        cidade = self.dataframe.loc[self.codigo_ibge(uf, municipio)]

        df = self.geodataframe[
            lambda df: df.id.astype(int).isin(
                set(self.cities_in_radius(uf, municipio, radius).index)
            )
        ]
        df.crs = {"init": "epsg:4326"}

        c = df.centroid
        xi, yi, xf, yf = df.geometry.unary_union.bounds

        m = folium.Map()
        folium.Choropleth(
            geo_data=df, location=[c.y.sum() / len(c), c.x.sum()], fill_color="red"
        ).add_to(m)
        folium.Circle(
            location=[cidade.latitude, cidade.longitude],
            radius=radius * 1000,
            color="#3186cc",
            fill=True,
            fill_color="#3186cc",
        ).add_to(m)
        m.fit_bounds([[yi, xi], [yf, xf]])
        return m
