from django.utils.module_loading import import_string


def get_source(slug: str):
    try:
        source_path = f"insights.sources.{slug}.usecases.query_execute.QueryExecutor"
        return import_string(source_path)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        print(f"Error: {e}")
        return None
