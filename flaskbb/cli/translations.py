# -*- coding: utf-8 -*-
"""
    flaskbb.cli.translations
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains all translation commands.

    :copyright: (c) 2016 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import click

from flaskbb.cli.main import flaskbb
from flaskbb.cli.utils import validate_plugin
from flaskbb.utils.translations import (add_translations, compile_translations,
                                        update_translations,
                                        add_plugin_translations,
                                        compile_plugin_translations,
                                        update_plugin_translations)


@flaskbb.group()
def translations():
    """Translations command sub group."""
    pass


@translations.command("new")
@click.option("--plugin", "-p", type=click.STRING,
              help="Adds a new language to a plugin.")
@click.argument("lang")
def new_translation(lang, plugin):
    """Adds a new language to the translations. "lang" is the language code
    of the language, like, "de_AT"."""
    if plugin:
        validate_plugin(plugin)
        click.secho("[+] Adding new language {} for plugin {}..."
                    .format(lang, plugin), fg="cyan")
        add_plugin_translations(plugin, lang)
    else:
        click.secho("[+] Adding new language {}...".format(lang), fg="cyan")
        add_translations(lang)


@translations.command("update")
@click.option("is_all", "--all", "-a", default=False, is_flag=True,
              help="Updates the plugin translations as well.")
@click.option("--plugin", "-p", type=click.STRING,
              help="Updates the language of the given plugin.")
def update_translation(is_all, plugin):
    """Updates all translations."""
    if plugin is not None:
        validate_plugin(plugin)
        click.secho("[+] Updating language files for plugin {}..."
                    .format(plugin), fg="cyan")
        update_plugin_translations(plugin)
    else:
        click.secho("[+] Updating language files...", fg="cyan")
        update_translations(include_plugins=is_all)


@translations.command("compile")
@click.option("is_all", "--all", "-a", default=False, is_flag=True,
              help="Compiles the plugin translations as well.")
@click.option("--plugin", "-p", type=click.STRING,
              help="Compiles the translations for a given plugin.")
def compile_translation(is_all, plugin):
    """Compiles the translations."""
    if plugin is not None:
        validate_plugin(plugin)
        click.secho("[+] Compiling language files for plugin {}..."
                    .format(plugin), fg="cyan")
        compile_plugin_translations(plugin)
    else:
        click.secho("[+] Compiling language files...", fg="cyan")
        compile_translations(include_plugins=is_all)
