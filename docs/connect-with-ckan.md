# Ideas for connect with CKAN

CKAN has a [harvest extension](https://github.com/ckan/ckanext-harvest). We must preserve for UI and log analysis. Maybe we can delete all the others harvest extension after migrate them to the new harvester.  

## Schedule

The previous harvester [uses supervisor to run tasks in background](https://github.com/ckan/ckanext-harvest/blob/master/config/supervisor/ckan_harvesting.conf). Then the ext [uses cron to run them periodically](https://github.com/ckan/ckanext-harvest/blob/master/README.rst#setting-up-the-harvesters-on-a-production-server).  

For the new harvester we plan to gather and execute all the task from Airflow. This tool could read all the harvests sources and put them in a schedule reading its _frequency_ property.  

The new harvester reads the harvest sources via API and plan how to do it outside CKAN. This tools will need just an API key with package creation permissions.  

## Logs

Now you can check the logs at ://CKAN/api/3/action/harvest_log_list  
With the new harvester we are working to improve logging. We have a structured JSON logs to re-use (for example rendering results as HTML to easy understanding).  

## Decoupled software

The new harvester is an external tool. This allows to:
 - Use other harvesters in the future. This includes for example the use of different programmign languages.
 - Harvest this resources to other platforms, not just to CKAN 
 - Run the harvesters in a different infrastructure
 - Create and fix harvesters without needing a CKAN instance
 - This harvester is a step forward to solve the Python version deprecation problem

## Remove or upgrade extensions?

These extensions fulfill functions that must be replaced if they are removed.
Some data transformations occurs after they are saved as CKAN package so is not enough to adapt this data before sending to _package_create_ function.

### Harvester Base
The harvester base extension:
 - adds a form to create a harvest source.
 - add forms to check the harvest results.
 - Save harvester jobs to a database table for future process
 - [Define the structure for other harvesters to inherit](https://github.com/ckan/ckanext-harvest/blob/master/ckanext/harvest/interfaces.py).
 - Generate several CLI commands for harvesting.
 - Includes a CKAN harvester
 - Give some API call (e.g. _harvest_log_list_). This includes reports and statuses.
 - [Define actions from after/befor create/update/view/search](https://github.com/ckan/ckanext-harvest/blob/master/ckanext/harvest/plugin.py#L28).

### Spatial

The spatial extension:
 - [Get spatial data and save it in PostGIS](https://github.com/GSA/ckanext-spatial/blob/datagov/ckanext/spatial/plugin.py#L99).
 - add extra info (maps) for packages with some [HTML snipets](https://github.com/gsa/ckanext-spatial/tree/master/ckanext/spatial/templates/spatial/snippets).  
 - [add new API calls](https://github.com/GSA/ckanext-spatial/blob/ce4f03bcd2000f98de1a9534dce92de674eb9806/ckanext/spatial/plugin.py#L393) and [geo queries](https://github.com/GSA/ckanext-spatial/blob/ce4f03bcd2000f98de1a9534dce92de674eb9806/ckanext/spatial/plugin.py#L306)