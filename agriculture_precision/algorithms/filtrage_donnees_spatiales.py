# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Precision Agriculture
                                 A QGIS plugin
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-07-21
        copyright            : (C) 2020 by ASPEXIT
        email                : cleroux@aspexit.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Lisa Rollier - ASPEXIT'
__date__ = '2020-07-21'
__copyright__ = '(C) 2020 by ASPEXIT'

__author__ = 'ASPEXIT'
__date__ = '2020-07-21'
__copyright__ = '(C) 2020 by ASPEXIT'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

#import QColor

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsApplication,
                       QgsVectorLayer,
                       QgsDataProvider,
                       QgsVectorDataProvider,
                       QgsField,
                       QgsFeature,
                       QgsGeometry,
                       QgsPointXY,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterNumber)

from qgis import processing 

import numpy as np
import pandas as pd
from scipy.spatial import distance

class FiltreDonneesSpatiales(QgsProcessingAlgorithm):
    """
    
    """

    OUTPUT= 'OUTPUT'
    INPUT = 'INPUT'
    FIELD = 'FIELD'
    INPUT_METHOD = 'INPUT_METHOD'
    INPUT_CONFIANCE = 'INPUT_CONFIANCE'
    BOOLEAN = 'BOOLEAN'
    INPUT_VOISINS = 'INPUT_VOISINS'
    INPUT_DISTANCE = 'INPUT_DISTANCE'
    BOOLEAN_DISTANCE = 'BOOLEAN_DISTANCE'
    INPUT_CV_MAX = 'INPUT_CV_MAX'
    INPUT_SD = 'INPUT_SD'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT,
                self.tr('Layer to filter')
            )
        )
        
        self.addParameter( 
            QgsProcessingParameterField( 
                self.FIELD, 
                self.tr( "Field selection" ), 
                QVariant(),
                self.INPUT,
                type=QgsProcessingParameterField.Numeric
            ) 
        )
        
        self.addParameter(
            QgsProcessingParameterEnum(
                self.INPUT_METHOD,
                self.tr('Filtering method'),
                ['Normal distribution','Coefficient of Variation','IDW']
            )
        )
        
        self.addParameter(
            QgsProcessingParameterEnum(
                self.INPUT_CONFIANCE,
                self.tr('Confidence interval (for normal distribution method)'),
                ['68%','95%', '99,5%']
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_SD, 
                self.tr('Number of standard deviations (IDW)'),
                QgsProcessingParameterNumber.Integer,
                2
            )
        ) 
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_VOISINS, 
                self.tr('Number of neighbours'),
                QgsProcessingParameterNumber.Integer,
                5
            )
        ) 
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_CV_MAX, 
                self.tr('Maximum Coefficient of variation (for coefficient of variation method)'),
                QgsProcessingParameterNumber.Double,
                2
            )
        ) 
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.BOOLEAN_DISTANCE,
                self.tr('Consider a distance-based neighbourhood')
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_DISTANCE, 
                self.tr('Neighbourhood distance'),
                QgsProcessingParameterNumber.Double,
                5e-5
            )
        ) 
       
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.BOOLEAN,
                self.tr('Remove outliers')
            )
        )
       
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Filtered layer')
            )
        )
        
        

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        
        layer=self.parameterAsVectorLayer(parameters,self.INPUT,context) 
        
        #on ajoute un nouveau champ 'Aberrant' dans la couche en sortie 
        new_fields = layer.fields()
        
        if not parameters['BOOLEAN'] :
            new_fields.append(QgsField('Aberrant', QVariant.Double))
        
        (sink, dest_id) = self.parameterAsSink(parameters,self.OUTPUT,context, new_fields, layer.wkbType(), layer.sourceCrs())
        method=self.parameterAsEnum(parameters,self.INPUT_METHOD,context)
        int_confiance=self.parameterAsEnum(parameters,self.INPUT_CONFIANCE,context)
        nb_sd = self.parameterAsInt(parameters,self.INPUT_SD,context)
        field_to_filter = self.parameterAsString(parameters,self.FIELD, context) 
        
        
        if feedback.isCanceled():
            return {}
        

        #on créer une matrice avec les coordonnées
        features = layer.getFeatures()
        coordinates_arr = np.array([[feat.geometry().asPoint()[k] for k in range(2)] for feat in features])
        
        #création de la matrice de distance
        dist_array = distance.cdist(coordinates_arr,coordinates_arr)
        
        #tri de la matrice selon les lignes
        sort_array = np.sort(dist_array,axis=1)
        
        if parameters['BOOLEAN_DISTANCE'] :
            min_dist_array = np.where(sort_array>parameters['INPUT_DISTANCE'], np.nan , sort_array)
              #on supprime le point des données pour IDW
            if method == 2:
                min_dist_array = min_dist_array[:,1:]
        #selection d'uniquement les premières "colonnes" : donc les plus proches voisins
        #creation d'une matrice ou chaque ligne correspond a une liste des distances des plus proches voisin pour un point (indiceligne = indice du point)
        else :
            min_dist_array = np.delete(sort_array,parameters['INPUT_VOISINS'],1)
            for k in range(parameters['INPUT_VOISINS']+1,len(sort_array[0])-1):
                min_dist_array = np.delete(min_dist_array,parameters['INPUT_VOISINS'],1)
            #on supprime le point des données pour IDW
            if method == 2: 
                min_dist_array = np.delete(min_dist_array,0,1)
        

        if feedback.isCanceled():
            return {}
        
        
        #nombre de points dans le shp
        nb_points = len(coordinates_arr)
        
        #creation d'une liste de liste : liste des index des voisins les plus proches pour chaque point
        neighbors = []
        for k in range (nb_points) :
            l = np.nonzero(np.in1d(dist_array[k],min_dist_array[k]))[0].tolist()
            neighbors.append(l)
        
        
        #création du dataframe de données
        features = layer.getFeatures()
        
        #liste contenant les noms des champs
        field_list=[field.name() for field in layer.fields()]
        
        #on créé une matrice ou 1 ligne = 1 feature
        data = np.array([[feat[field_name] for field_name in field_list] for feat in features])
                
        #on créer le dataframe avec les données et les noms des colonnes
        df = pd.DataFrame(data, columns = field_list)
        
        
        if feedback.isCanceled():
            return {}
        

        if method == 0 :
            int_confiance+=1
            mean = []
            sd = []
            for k in range (nb_points) :
                mean.append(df.iloc[neighbors[k]][field_to_filter].mean())
                sd.append(df.iloc[neighbors[k]][field_to_filter].std())
            df['mean'] = mean
            df['sd'] = sd
            
            
            #met 1 quand c'est aberrant, 0 sinon
            df['Aberrant'] = np.where((df[field_to_filter] > df['mean'] - int_confiance*df['sd']) & (df[field_to_filter] < df['mean'] + int_confiance*df['sd']), 0, 1)
            df = df.drop(columns = 'mean')
            df = df.drop(columns = 'sd')
        
        elif method == 1:
           
            mean = []
            sd = []
            nb_neighbors = []
            for k in range (nb_points) :
                mean.append(df.iloc[neighbors[k]][field_to_filter].mean())
                sd.append(df.iloc[neighbors[k]][field_to_filter].std())
                nb_neighbors.append(len(neighbors[k]))
            
            df['mean'] = mean
            df['sd'] = sd
            df['CV_neighbors'] = 100 * (df['sd']/df['mean'])
            df = df.drop(columns = 'sd')
            df = df.drop(columns = 'mean')
            df['nb_neighbors'] = nb_neighbors
            
            nb_high_cv = []
            for k in range (nb_points) :
                nb_high_cv.append(len(df.iloc[neighbors[k]][df['CV_neighbors']>parameters['INPUT_CV_MAX']]))
            df['nb_high_cv'] = nb_high_cv
            
            df['Aberrant'] = np.where((df['nb_neighbors'] -1 <= df['nb_high_cv']), 1,0)
            
            df = df.drop(columns = 'CV_neighbors')
            df = df.drop(columns = 'nb_neighbors')
            df = df.drop(columns = 'nb_high_cv')
          
        else :
            sd = []
            denominateur = []
            numerateur =[]
            df_distances = pd.DataFrame(min_dist_array)
            denom = (1/(df_distances**2)).sum(axis = 1)
            values = []
            for k in range (nb_points) :
                sd.append(df.iloc[neighbors[k]][field_to_filter].std())
                values.append(df.iloc[neighbors[k]][field_to_filter].values.tolist())
            df['sd'] = sd
            df_values = pd.DataFrame(values)
            num = (df_values*(1/(df_distances**2))).sum(axis = 1)
            df['interpolation']=num/denom
            
            df['Aberrant'] = np.where((df[field_to_filter] > df['interpolation'] - nb_sd*df['sd']) & (df[field_to_filter] < df['interpolation'] + nb_sd*df['sd']) , 0,1)
            df = df.drop(columns = 'sd')
            df = df.drop(columns = 'interpolation')
          
        
        if feedback.isCanceled():
            return {}
        
  
        #on va créer un dataframe avec les coordonnées, normalement les features sont parcourrues dans le même ordre
        
        coordinates = pd.DataFrame(coordinates_arr, columns = ['X','Y'])
        df['X']=coordinates['X']
        df['Y']=coordinates['Y']    
        
        if parameters['BOOLEAN'] :
            indexNames = df[df['Aberrant'] == 1 ].index
            df.drop(indexNames , inplace=True)
            df.drop(columns = 'Aberrant')
        
        #on transforme le dataframe en liste pour les attributs
        df_list=df.values.tolist()
         
        if feedback.isCanceled():
            return {}
        
       
                
        featureList=[]
        
        #on va parcourrir chaque ligne, ie chaque feature
        for row in df_list:
            feat = QgsFeature()
            feat.setAttributes(row[0:-2]) #row = une ligne, on exclu les deux dernières colonnes qui sont les coordonnées
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(row[-2],row[-1]))) #on définit la position de chaque point 
            featureList.append(feat) #on ajoute la feature à la liste
                
            if feedback.isCanceled():
                return {}
            


        #on ajoute la liste des features à la couche de sortie
        sink.addFeatures(featureList)
        
        
        return{self.OUTPUT : dest_id} 

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'V - Spatial univariate filtering'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Filtering')

    def shortHelpString(self):
        short_help = self.tr(
            'Detects local/spatial outliers for a given field (column) of a vector'
            ' layer using several filtering methods. Outliers can either be removed'
            ' or identified in a new column in the vector layer. \n \n'
            'Points are compared to their spatial neighbours\n \n'
            '- Normal distribution: Assuming a normal distribution of the data,'
            ' the function identifies data within the ranges (mean +/- 1 standard'
            'deviation; mean +/- 2 standard deviations; mean +/- 3 standard deviations;'
            'and beyond) in the neighbourhood \n'
            '- Coefficient of variation : from Spekken et al. (2013). '
            'A simple method for filtering spatial data. ECPA Congress]'
            'IDW : Point value (Zi) is compared to interpolated value from '
            'neighbours (Zj). If Zi is beyond the range of Zj +/- n standard '
            'deviations of neighbourood values, the point is considered an outlier.'
            '\n\n\n\n'
            'provided by ASPEXIT\n'
            'author : Lisa Rollier'
        ) 
        return short_help


    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'filtering'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return FiltreDonneesSpatiales()
