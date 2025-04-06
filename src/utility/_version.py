import importlib
import importlib.util
__package_name__="project-visualization-tool-GDeLuisi"
__version__=importlib.metadata.version(__package_name__) if importlib.util.find_spec(__package_name__) else "Version not found"