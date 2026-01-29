from core.plugins.registry import get_plugin, list_plugins, load_builtin_plugins


def test_plugins_registry_lists_builtins():
    load_builtin_plugins()
    plugins = list_plugins()
    names = [plugin.name for plugin in plugins]
    assert "importer_folder" in names
    assert "importer_folder_sync" in names
    assert "importer_zotero" in names
    assert "importer_arxiv" in names
    assert "importer_doi" in names
    assert "importer_url" in names
    assert "exporter_folder" in names
    assert "exporter_citations" in names
    assert get_plugin("importer_folder").name == "importer_folder"
