from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models
from django.db.models.fields.related import ForeignKey, ManyToManyField, OneToOneField
from django.contrib.contenttypes.fields import GenericRelation
import inspect
import sys


class Command(BaseCommand):
    help = "Export all model definitions with automatic reflection annotations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--app",
            type=str,
            default="core",
            help="App name to export models from (default: core)",
        )
        parser.add_argument(
            "--format",
            type=str,
            choices=["markdown", "json", "yaml"],
            default="markdown",
            help="Output format (default: markdown)",
        )
        parser.add_argument(
            "--include-fields",
            action="store_true",
            help="Include detailed field information",
        )
        parser.add_argument(
            "--include-methods",
            action="store_true",
            help="Include model methods and properties",
        )

    def handle(self, *args, **options):
        app_name = options["app"]
        output_format = options["format"]
        include_fields = options["include_fields"]
        include_methods = options["include_methods"]

        try:
            app_config = apps.get_app_config(app_name)
            models_list = list(app_config.get_models())

            if output_format == "markdown":
                self.export_markdown(models_list, include_fields, include_methods)
            elif output_format == "json":
                self.export_json(models_list, include_fields, include_methods)
            elif output_format == "yaml":
                self.export_yaml(models_list, include_fields, include_methods)

        except LookupError:
            self.stdout.write(self.style.ERROR(f'App "{app_name}" not found.'))
            sys.exit(1)

    def export_markdown(self, models_list, include_fields, include_methods):
        """Export models in Markdown format"""
        self.stdout.write("# Django Models Documentation")
        self.stdout.write("")
        self.stdout.write(f"Generated on: {self.get_current_time()}")
        self.stdout.write(f"Total models: {len(models_list)}")
        self.stdout.write("")

        for model in models_list:
            self.export_model_markdown(model, include_fields, include_methods)

    def export_model_markdown(self, model, include_fields, include_methods):
        """Export single model in Markdown format"""
        # Model header
        self.stdout.write(f"## {model.__name__}")
        self.stdout.write("")

        # Model metadata
        self.stdout.write("### Model Information")
        self.stdout.write(f"- **App Label**: {model._meta.app_label}")
        self.stdout.write(f"- **Table Name**: `{model._meta.db_table}`")
        self.stdout.write(f"- **Verbose Name**: `{model._meta.verbose_name}`")
        self.stdout.write(
            f"- **Verbose Name Plural**: `{model._meta.verbose_name_plural}`"
        )
        self.stdout.write(f"- **Abstract**: {model._meta.abstract}")

        # Model docstring
        if model.__doc__ and model.__doc__.strip():
            self.stdout.write(f"- **Description**: {model.__doc__.strip()}")

        self.stdout.write("")

        # Fields
        if include_fields:
            self.stdout.write("### Fields")
            self.stdout.write("")

            for field in model._meta.get_fields():
                self.export_field_markdown(field)

            self.stdout.write("")

        # Relationships
        relationships = self.get_relationships(model)
        if relationships:
            self.stdout.write("### Relationships")
            self.stdout.write("")

            for rel_type, rel_info in relationships.items():
                self.stdout.write(f"#### {rel_type}")
                for rel in rel_info:
                    self.stdout.write(
                        f"- **{rel['name']}**: `{rel['to']}` ({rel['type']})"
                    )
                    if rel.get("related_name"):
                        self.stdout.write(f"  - Related Name: `{rel['related_name']}`")
                    if rel.get("on_delete"):
                        self.stdout.write(f"  - On Delete: `{rel['on_delete']}`")
                self.stdout.write("")

        # Methods
        if include_methods:
            methods = self.get_model_methods(model)
            if methods:
                self.stdout.write("### Methods")
                self.stdout.write("")

                for method in methods:
                    self.stdout.write(f"#### {method['name']}")
                    self.stdout.write(f"```python")
                    self.stdout.write(f"def {method['signature']}")
                    if method.get("docstring"):
                        self.stdout.write(f'    """{method["docstring"]}"""')
                    self.stdout.write("```")
                    self.stdout.write("")

        # Meta information
        if hasattr(model, "_meta") and model._meta:
            self.stdout.write("### Meta Information")
            self.stdout.write("")
            meta_attrs = self.get_meta_attributes(model)
            if meta_attrs:
                for attr, value in meta_attrs.items():
                    self.stdout.write(f"- **{attr}**: `{value}`")
            else:
                self.stdout.write("- No custom Meta attributes defined")
            self.stdout.write("")

        self.stdout.write("---")
        self.stdout.write("")

    def export_field_markdown(self, field):
        """Export single field in Markdown format"""
        field_type = type(field).__name__
        field_name = field.name

        # Basic field info
        self.stdout.write(f"#### {field_name}")
        self.stdout.write(f"- **Type**: `{field_type}`")

        # Field-specific attributes
        attrs = {}

        # Common field attributes
        if hasattr(field, "max_length") and field.max_length:
            attrs["max_length"] = field.max_length
        if hasattr(field, "null") and field.null:
            attrs["null"] = True
        if hasattr(field, "blank") and field.blank:
            attrs["blank"] = True
        if hasattr(field, "default") and field.default is not models.NOT_PROVIDED:
            attrs["default"] = repr(field.default)
        if hasattr(field, "choices") and field.choices:
            attrs["choices"] = list(field.choices)
        if hasattr(field, "primary_key") and field.primary_key:
            attrs["primary_key"] = True
        if hasattr(field, "unique") and field.unique:
            attrs["unique"] = True
        if hasattr(field, "db_index") and field.db_index:
            attrs["db_index"] = True
        if hasattr(field, "verbose_name") and field.verbose_name:
            attrs["verbose_name"] = field.verbose_name
        if hasattr(field, "help_text") and field.help_text:
            attrs["help_text"] = field.help_text

        # Relationship-specific attributes
        if isinstance(field, (ForeignKey, ManyToManyField, OneToOneField)):
            attrs["to"] = str(field.remote_field.model)
            if (
                hasattr(field.remote_field, "related_name")
                and field.remote_field.related_name
            ):
                attrs["related_name"] = field.remote_field.related_name
            if (
                hasattr(field.remote_field, "on_delete")
                and field.remote_field.on_delete
            ):
                attrs["on_delete"] = field.remote_field.on_delete.__name__

        # Output attributes
        if attrs:
            for attr, value in attrs.items():
                self.stdout.write(f"  - **{attr}**: {value}")

        # Field help text
        if hasattr(field, "help_text") and field.help_text:
            self.stdout.write(f"  - **Help Text**: {field.help_text}")

        self.stdout.write("")

    def get_relationships(self, model):
        """Get all relationships for a model"""
        relationships = {
            "Foreign Keys": [],
            "Many to Many": [],
            "One to One": [],
            "Generic Relations": [],
            "Reverse Foreign Keys": [],
            "Reverse Many to Many": [],
        }

        for field in model._meta.get_fields():
            if isinstance(field, ForeignKey):
                relationships["Foreign Keys"].append(
                    {
                        "name": field.name,
                        "to": str(field.remote_field.model),
                        "type": "ForeignKey",
                        "related_name": getattr(
                            field.remote_field, "related_name", None
                        ),
                        "on_delete": (
                            getattr(field.remote_field, "on_delete", None).__name__
                            if getattr(field.remote_field, "on_delete", None)
                            else None
                        ),
                    }
                )
            elif isinstance(field, ManyToManyField):
                relationships["Many to Many"].append(
                    {
                        "name": field.name,
                        "to": str(field.remote_field.model),
                        "type": "ManyToManyField",
                        "related_name": getattr(
                            field.remote_field, "related_name", None
                        ),
                    }
                )
            elif isinstance(field, OneToOneField):
                relationships["One to One"].append(
                    {
                        "name": field.name,
                        "to": str(field.remote_field.model),
                        "type": "OneToOneField",
                        "related_name": getattr(
                            field.remote_field, "related_name", None
                        ),
                    }
                )
            elif isinstance(field, GenericRelation):
                relationships["Generic Relations"].append(
                    {
                        "name": field.name,
                        "to": str(field.related_model),
                        "type": "GenericRelation",
                    }
                )

        # Remove empty relationship types
        return {k: v for k, v in relationships.items() if v}

    def get_model_methods(self, model):
        """Get all methods defined on the model"""
        methods = []

        for name, method in inspect.getmembers(model, predicate=inspect.isfunction):
            if not name.startswith("_") or name in [
                "__str__",
                "__unicode__",
                "__repr__",
            ]:
                try:
                    signature = inspect.signature(method)
                    docstring = inspect.getdoc(method) or ""

                    methods.append(
                        {
                            "name": name,
                            "signature": f"{name}{signature}",
                            "docstring": docstring,
                        }
                    )
                except (ValueError, TypeError):
                    # Skip methods that can't be inspected
                    continue

        # Also include properties
        for name, prop in inspect.getmembers(model, predicate=inspect.isdatadescriptor):
            if isinstance(prop, property) and not name.startswith("_"):
                docstring = inspect.getdoc(prop.fget) if prop.fget else ""
                methods.append(
                    {
                        "name": name,
                        "signature": f"{name} (property)",
                        "docstring": docstring or "Property",
                    }
                )

        return methods

    def get_meta_attributes(self, model):
        """Get Meta class attributes"""
        meta_attrs = {}

        if hasattr(model, "_meta"):
            meta = model._meta

            # Common Meta attributes
            attrs_to_check = [
                "ordering",
                "verbose_name",
                "verbose_name_plural",
                "db_table",
                "db_tablespace",
                "abstract",
                "app_label",
                "constraints",
                "indexes",
                "unique_together",
                "index_together",
                "permissions",
                "default_permissions",
                "proxy",
                "managed",
                "default_related_name",
                "select_on_save",
                "required_db_features",
                "required_db_vendor",
                "swappable",
                "auto_created",
            ]

            for attr in attrs_to_check:
                value = getattr(meta, attr, None)
                if value is not None and value != []:
                    meta_attrs[attr] = value

        return meta_attrs

    def export_json(self, models_list, include_fields, include_methods):
        """Export models in JSON format"""
        import json

        data = {
            "generated_on": self.get_current_time(),
            "total_models": len(models_list),
            "models": [],
        }

        for model in models_list:
            model_data = self.get_model_data(model, include_fields, include_methods)
            data["models"].append(model_data)

        self.stdout.write(json.dumps(data, indent=2, ensure_ascii=False))

    def export_yaml(self, models_list, include_fields, include_methods):
        """Export models in YAML format"""
        try:
            import yaml
        except ImportError:
            self.stdout.write(
                self.style.ERROR(
                    "PyYAML is required for YAML export. Install it with: pip install PyYAML"
                )
            )
            return

        data = {
            "generated_on": self.get_current_time(),
            "total_models": len(models_list),
            "models": [],
        }

        for model in models_list:
            model_data = self.get_model_data(model, include_fields, include_methods)
            data["models"].append(model_data)

        self.stdout.write(yaml.dump(data, default_flow_style=False, allow_unicode=True))

    def get_model_data(self, model, include_fields, include_methods):
        """Get model data as dictionary"""
        data = {
            "name": model.__name__,
            "app_label": model._meta.app_label,
            "table_name": model._meta.db_table,
            "verbose_name": str(model._meta.verbose_name),
            "verbose_name_plural": str(model._meta.verbose_name_plural),
            "abstract": model._meta.abstract,
        }

        if model.__doc__ and model.__doc__.strip():
            data["description"] = model.__doc__.strip()

        if include_fields:
            data["fields"] = []
            for field in model._meta.get_fields():
                field_data = self.get_field_data(field)
                data["fields"].append(field_data)

        relationships = self.get_relationships(model)
        if relationships:
            data["relationships"] = relationships

        if include_methods:
            data["methods"] = self.get_model_methods(model)

        meta_attrs = self.get_meta_attributes(model)
        if meta_attrs:
            data["meta"] = meta_attrs

        return data

    def get_field_data(self, field):
        """Get field data as dictionary"""
        data = {
            "name": field.name,
            "type": type(field).__name__,
        }

        # Common field attributes
        attrs = {}
        if hasattr(field, "max_length") and field.max_length:
            attrs["max_length"] = field.max_length
        if hasattr(field, "null") and field.null:
            attrs["null"] = True
        if hasattr(field, "blank") and field.blank:
            attrs["blank"] = True
        if hasattr(field, "default") and field.default is not models.NOT_PROVIDED:
            attrs["default"] = repr(field.default)
        if hasattr(field, "choices") and field.choices:
            attrs["choices"] = list(field.choices)
        if hasattr(field, "primary_key") and field.primary_key:
            attrs["primary_key"] = True
        if hasattr(field, "unique") and field.unique:
            attrs["unique"] = True
        if hasattr(field, "db_index") and field.db_index:
            attrs["db_index"] = True
        if hasattr(field, "verbose_name") and field.verbose_name:
            attrs["verbose_name"] = field.verbose_name
        if hasattr(field, "help_text") and field.help_text:
            attrs["help_text"] = field.help_text

        # Relationship-specific attributes
        if isinstance(field, (ForeignKey, ManyToManyField, OneToOneField)):
            attrs["to"] = str(field.remote_field.model)
            if (
                hasattr(field.remote_field, "related_name")
                and field.remote_field.related_name
            ):
                attrs["related_name"] = field.remote_field.related_name
            if (
                hasattr(field.remote_field, "on_delete")
                and field.remote_field.on_delete
            ):
                attrs["on_delete"] = field.remote_field.on_delete.__name__

        if attrs:
            data["attributes"] = attrs

        return data

    def get_current_time(self):
        """Get current timestamp"""
        from django.utils import timezone

        return timezone.now().strftime("%Y-%m-%d %H:%M:%S %Z")
