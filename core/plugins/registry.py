from __future__ import annotations

from typing import Dict

from core.plugins.base import PluginBase
from core.plugins.builtins.exporter_citations import ExportCitationsPlugin
from core.plugins.builtins.exporter_folder import ExportFolderPlugin
from core.plugins.builtins.importer_folder import ImportFolderPlugin
from core.plugins.builtins.importer_folder_sync import ImportFolderSyncPlugin
from core.plugins.builtins.importer_zotero import ImportZoteroPlugin
from core.plugins.builtins.importer_arxiv import ImportArxivPlugin
from core.plugins.builtins.importer_doi import ImportDoiPlugin
from core.plugins.builtins.importer_url import ImportUrlPlugin


_REGISTRY: Dict[str, PluginBase] = {}


def register(plugin: PluginBase) -> None:
    _REGISTRY[plugin.name] = plugin


def get_plugin(name: str) -> PluginBase:
    if name not in _REGISTRY:
        raise RuntimeError("Plugin not found.")
    return _REGISTRY[name]


def list_plugins() -> list[PluginBase]:
    return list(_REGISTRY.values())


def load_builtin_plugins() -> None:
    register(ImportFolderPlugin())
    register(ImportFolderSyncPlugin())
    register(ImportZoteroPlugin())
    register(ImportArxivPlugin())
    register(ImportDoiPlugin())
    register(ImportUrlPlugin())
    register(ExportFolderPlugin())
    register(ExportCitationsPlugin())
