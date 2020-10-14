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
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterField,
                       QgsProcessingParameterBoolean,
                       
                       QgsProcessingUtils,
                       NULL,
                       QgsMessageLog)

from qgis import processing 

import numpy as np
import pandas as pd

class DonneesPaysage(QgsProcessingAlgorithm):
    """
    
    """

    OUTPUT= 'OUTPUT'
    INPUT= 'INPUT'
    FIELD_ID = 'FIELD_ID'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT,
                self.tr('Zones layer'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter( 
            QgsProcessingParameterField( 
                self.FIELD_ID,
                self.tr( "Zones class" ), 
                QVariant(),
                self.INPUT
            ) 
        )       
        
        
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('File'),
                '.csv',
            )
        )
        
        

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        
       
        csv = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        zone_id = self.parameterAsString(parameters, self.FIELD_ID, context)
      
        if feedback.isCanceled():
            return {}
                
        alg_params = {
            'CALC_METHOD': 0,
            'INPUT': parameters['INPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        alg_result= processing.run('qgis:exportaddgeometrycolumns', alg_params, context=context, feedback=feedback, is_child_algorithm=True)['OUTPUT']
        layer = QgsProcessingUtils.mapLayerFromString(alg_result,context)
        
        if feedback.isCanceled():
            return {}
      
        features = layer.getFeatures()
              
        #if parameters[self.BOOLEAN] :
            #liste contenant les noms des champs (uniquement numériques)
        field_list=[field.name() for field in layer.fields() if field.type() in [2,4,6] or field.name() == zone_id] 
            # 4 integer64, 6 Real
       # else :
        #    field_list =[choosed_field, zone_id]
      
        #on créé une matrice ou 1 ligne = 1 feature
        data = np.array([[feat[field_name] for field_name in field_list] for feat in features])
                
        #on créer le dataframe avec les données et les noms des colonnes
        df = pd.DataFrame(data, columns = field_list)
        
        #Remplacer les valeur NULL (Qvariant) en Nan de panda dataframe
        df = df.where(df!=NULL)
        
        #Mettre toutes les valeurs du dataframe en réel
        df = df.astype(float)# !!! ne va pas marcher si l'identifiant de parcelle n'est pas un chiffre 
        
        if feedback.isCanceled():
            return {}
                
        #moyenne du perimetre de chaque classe
        df_mean_perimeter_zone = df.groupby([zone_id]).mean()['perimeter']
        #total du perimetre sur lchaque classe
        df_total_perimeter_zone = df.groupby([zone_id]).sum()['perimeter']
        #proportion en aire de chaque classe
        df_total_area_zone = df.groupby([zone_id]).sum()['area']
        total_area = df_total_area_zone.sum()
        df_area_ratio = (df_total_area_zone/total_area)*100
       
        #densité de chaque classe
        df_count = df.groupby([zone_id]).count()['perimeter']
        nb_total = df_count.sum()
        df_class_density = df_count/nb_total
               
        #conversion des dataframes en listes
        mean_perimeter_zone = df_mean_perimeter_zone.tolist()
        area_ratio = df_area_ratio.tolist()
        total_perimeter_zone = df_total_perimeter_zone.tolist()
        class_density = df_class_density.tolist()
        
        #crééer une liste avec les indentifiants de chaque zone
        zones = df[zone_id].unique().tolist()
        nb_zones = len(zones)
        
        if feedback.isCanceled():
            return {}
        
        #création du fichier csv qui va contenir les données de RV
        with open(csv, 'w') as output_file:
            # write header
            line = 'zone_id,mean_perimeter,total_perimeter,area_ratio,class_density\n'
            output_file.write(line)
            
            for k in range (len(zones)):
                line = str(zones[k]) + ',' + str(mean_perimeter_zone[k]) + ',' + str(total_perimeter_zone[k]) + ',' + str(area_ratio[k]) + ',' + str(class_density[k]) + '\n'
                output_file.write(line)
          
         
       
        return{self.OUTPUT : csv} 

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'V - Landscape Metrics'

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
        return self.tr('Zoning')

    def shortHelpString(self):
        short_help = self.tr(
            'Allow to compute several zoning descriptors (mean perimeter'
            'of the zones, total perimeters of the zones, density of zones..). \n\n'
            'The variable selected in the function must be the class of each zone'
            '(the data originating the zones must have been classified before).'
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
        return 'zoning'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DonneesPaysage()
