## -*- coding: utf-8 -*-

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


from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsApplication,
                       QgsVectorLayer,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterVectorDestination)



from qgis import processing 


class RecroisementZones(QgsProcessingAlgorithm):
    """
    
    """ 

    OUTPUT= 'OUTPUT'
    INPUT_1 = 'INPUT_1'
    INPUT_2 = 'INPUT_2'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_1,
                self.tr('First zoning'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_2,
                self.tr('Second zoning'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                self.tr('Merged zoning')
            )
        )
        
        

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
                        
        if feedback.isCanceled():
            return {}
                
        # Réparer les géométries
        alg_params = {
            'INPUT': parameters['INPUT_1'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        layer_1 = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                
        if feedback.isCanceled():
            return {}
                
        # Réparer les géométries
        alg_params = {
            'INPUT': parameters['INPUT_2'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        layer_2 = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                
        if feedback.isCanceled():
            return {}
                
        # Union
        alg_params = {
            'INPUT': layer_1['OUTPUT'],
            'OVERLAY': layer_2['OUTPUT'],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        layer_union = processing.run('native:union', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        
                        
        if feedback.isCanceled():
            return {}
            
          # De morceaux multiples à morceaux uniques
        alg_params = {
            'INPUT': layer_union['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        layer_uniques = processing.run('native:multiparttosingleparts', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                
        if feedback.isCanceled():
            return {}
            
        # Ajouter les attributs de géométrie
        alg_params = {
            'CALC_METHOD': 0,
            'INPUT': layer_uniques['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        layer_geom = processing.run('qgis:exportaddgeometrycolumns', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                      
        if feedback.isCanceled():
            return {}
                
        # Ajouter un champ auto-incrémenté
        alg_params = {
            'FIELD_NAME': 'ZONE_ID',
            'GROUP_FIELDS': None,
            'INPUT': layer_geom['OUTPUT'],
            'SORT_ASCENDING': True,
            'SORT_EXPRESSION': '',
            'SORT_NULLS_FIRST': False,
            'START': 1,
            'OUTPUT': parameters['OUTPUT']
        }
        layer_output = processing.run('native:addautoincrementalfield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)['OUTPUT']
        
                         
        if feedback.isCanceled():
            return {}
                
        return{self.OUTPUT : layer_output} 
   
    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "V - Merging two zonings"

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
            'Allows to merge two zonings of the same field into one single zoning.'
            'The final zoning can be considered as a microzoning that combines the'
            'zones of both initial zonings.'
            '\n provided by ASPEXIT\n'
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
        return RecroisementZones()
