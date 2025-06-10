# Grid topology generator
A tool that can generate dutch MV networks. An example of how the tool can be used can be found in `main.py`.

## Algorithm description
The Dutch DSO's have open datasets available showing the locations of medium and low voltage cables in the ground. Furthermore, the Dutch government has an open dataset available containing data on buildings in the Netherlands. Both these datasets are used as input for this tool.

First, the algorithm assumes that MV networks are in a ring configuration. Second, the algorithm parses both datasets and follows a path of MV cables from an HV/MV substation to MV/LV substations and continues until the path returns to the start HV/MV substation. Based upon the building year of the buildings at the found substation locations an assumption is made about the cable type. Finally, the MV network is outputted in the ESDL format.

A full and detailed description of the algorithm can be found in the following paper:
```
@INPROCEEDINGS{mvtool,
  author={van Schooten, Leo and Verhoeven, Gijs and Kok, Koen and Morren, Johan },
  booktitle={28th International Conference on Electricity Distribution (CIRED 2025) \textit{ACCEPTED}}, 
  title={An open-source tool for generating representative dutch distribution grid models using graph similarity measures and open data}, 
  year={2025}}
```
Whenever a publication followed where this tool was used please cite the above paper.

## Graph matching
The tool also implements a metric to determine how similar two LV grids are. This metric will later be used when the tool also outputs connected LV grids with the addition to MV grids.

## Usefull links
|Link             |description             |
|-----------------|------------------------|
|[ESDL](https://www.esdl.nl/)|Details on the esdl format|
|[Alliander Gis data](https://www.arcgis.com/home/item.html?id=0097c633fb7f421aad7053f55060fa9c)|Details on the GIS data of Alliander|
|[Stedin Gis data](https://www.stedin.net/zakelijk/open-data/liggingsdata-kabels-en-leidingen)|Details on the GIS data of Stedin
|[Enexis Gis data](https://www.enexis.nl/over-ons/open-data)|Details on the GIS data of Enexis
|[Bag data ](https://data.overheid.nl/en/dataset/basisregistratie-adressen-en-gebouwen--bag-)|Details on the BAG dataset from the Dutch Government|