import typer
from rich import print as rprint
from src.core.container import AppContainer

config_app = typer.Typer(help="Manage configuration and environment variables")

def extract_env_fields(model_cls, prefix=""):
    """Recursively extract fields from a Pydantic model to generate .env format."""
    lines = []
    for field_name, field_info in model_cls.model_fields.items():
        description = field_info.description or ""
        default_val = field_info.default if field_info.default is not ... else ""
        
        # If field type is a nested model
        import inspect
        if inspect.isclass(field_info.annotation) and hasattr(field_info.annotation, "model_fields"):
            lines.extend(extract_env_fields(field_info.annotation, prefix=f"{prefix}{field_name.upper()}__"))
        else:
            env_var = f"{prefix}{field_name.upper()}"
            if description:
                lines.append(f"# {description}")
            lines.append(f"{env_var}={default_val}")
    return lines

@config_app.command(name="generate-env")
def generate_env(
    output: str = typer.Option(".env.example", "--output", "-o", help="Output file path"),
    overwrite: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists")
):
    """Generate a template environment file dynamically."""
    import os
    if os.path.exists(output) and not overwrite:
        rprint(f"[yellow]File {output} already exists. Use -f to overwrite.[/]")
        raise typer.Exit(1)
        
    container = AppContainer()
    lines = [
        "# ==========================================",
        "# Auto-generated ComicMgr Configuration",
        "# ==========================================",
        ""
    ]
    
    # 1. Core Config
    lines.append("# [Core Application Settings]")
    lines.extend(extract_env_fields(container.config.__class__, prefix="APP_"))
    lines.append("")
    
    # 2. Providers Config
    lines.append("# ==========================================")
    lines.append("# [Provider Specific Settings]")
    lines.append("# ==========================================")
    
    for provider_id, provider_instance in container.providers.items():
        p_class = type(provider_instance)
        config_class = getattr(p_class, 'get_config_class', lambda: None)()
        if config_class:
            lines.append(f"")
            lines.append(f"# --- Provider: {provider_instance.provider_name} ({provider_id}) ---")
            prefix = getattr(config_class.model_config, "env_prefix", f"{provider_id.upper()}_")
            lines.extend(extract_env_fields(config_class, prefix=prefix))
            
    with open(output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    rprint(f"[green]Successfully generated configuration template at {output}[/]")
