import json
import os
import click

from agent import source, check_prerequisites
from agent.modules.tools import infinite_retry
from jsonschema import ValidationError, SchemaError
from agent.cli import prompt


def autocomplete(ctx, args, incomplete) -> list:
    return list(map(
        lambda s: s.name,
        source.repository.find_by_name_beginning(incomplete)
    ))


@click.group(name='source')
def source_group():
    pass


@click.command(name='list')
def list_sources():
    for name in source.repository.get_all_names():
        click.echo(name)


@click.command()
@click.option('-a', '--advanced', is_flag=True)
@click.option('-f', '--file', type=click.File())
def create(advanced, file):
    _check_prerequisites()
    _create_from_file(file) if file else _prompt(advanced)


@click.command()
@click.argument('name', autocompletion=autocomplete, required=False)
@click.option('-a', '--advanced', is_flag=True)
@click.option('-f', '--file', type=click.File())
def edit(name, advanced, file):
    _check_prerequisites()
    if not file and not name:
        raise click.UsageError('Specify source name or file path')
    if file:
        _edit_using_file(file)
        return

    source_ = source.repository.get_by_name(name)
    source_ = prompt.source.get_prompter(source_).prompt(source_.config, advanced=advanced)
    source.manager.update(source_)


def _check_prerequisites():
    errors = check_prerequisites()
    if errors:
        raise click.ClickException("\n".join(errors))


@click.command()
@click.argument('name', autocompletion=autocomplete)
def delete(name):
    source.repository.delete_by_name(name)


@click.command()
@click.option('-d', '--dir-path', type=click.Path(exists=True))
def export(dir_path):
    if not dir_path:
        dir_path = 'sources'
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

    sources = source.repository.get_all()
    for source_ in sources:
        config = [source_.to_dict()]
        with open(os.path.join(dir_path, source_.name + '.json'), 'w+') as f:
            json.dump(config, f)

    click.echo(f'All sources exported to {dir_path} directory')


@infinite_retry
def _prompt_source_name():
    source_name = click.prompt('Enter unique name for this source config', type=click.STRING).strip()
    source.manager.check_source_name(source_name)
    return source_name


def _create_from_file(file):
    try:
        source.json_builder.create_from_file(file)
    except (ValidationError, SchemaError) as e:
        raise click.ClickException(str(e))


def _prompt(advanced: bool):
    source_type = _prompt_source_type()
    source_name = _prompt_source_name()
    prompter = prompt.source.get_prompter(
        source.manager.create_source_obj(source_name, source_type)
    )
    source.repository.save(
        prompter.prompt(source.manager.get_previous_source_config(source_type), advanced)
    )
    click.secho('Source config created', fg='green')


def _edit_using_file(file):
    try:
        source.json_builder.edit_using_file(file)
    except (ValidationError, SchemaError) as e:
        raise click.UsageError(str(e))


def _prompt_source_type():
    return click.prompt('Choose source', type=click.Choice(source.types.keys())).strip()


source_group.add_command(create)
source_group.add_command(list_sources)
source_group.add_command(delete)
source_group.add_command(edit)
source_group.add_command(export)
