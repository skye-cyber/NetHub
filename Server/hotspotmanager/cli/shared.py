import click
from ap import APManagerCLI

# ==================== CLI Commands ====================


@click.group(invoke_without_command=True)
@click.option('--config', '-c', type=click.Path(exists=True),
              help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """AP Manager - Hotspot and Captive Portal Management"""
    ctx.ensure_object(dict)
    ctx.obj['cli'] = APManagerCLI()
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config

    # Load config
    ctx.obj['cli'].load_config(config)

    # Show help if no subcommand
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
