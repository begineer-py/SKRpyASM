from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models
from django.db.models.fields.related import ForeignKey, ManyToManyField, OneToOneField
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib import admin
from rest_framework import serializers
import inspect
import sys
import os


class Command(BaseCommand):
    help = "Advanced model reflection tool with admin and serializer generation"

    def add_arguments(self, parser):
        parser.add_argument(
            "--app",
            type=str,
            default="core",
            help="App name to reflect models from (default: core)",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="./model_output",
            help="Output directory for generated files",
        )
        parser.add_argument(
            "--generate-admin",
            action="store_true",
            help="Generate Django admin configuration",
        )
        parser.add_argument(
            "--generate-serializers",
            action="store_true",
            help="Generate DRF serializers",
        )
        parser.add_argument(
            "--generate-factories",
            action="store_true",
            help="Generate Factory Boy factories",
        )
        parser.add_argument(
            "--generate-tests", action="store_true", help="Generate test templates"
        )
        parser.add_argument(
            "--include-inheritance",
            action="store_true",
            help="Include model inheritance analysis",
        )

    def handle(self, *args, **options):
        app_name = options["app"]
        output_dir = options["output_dir"]
        generate_admin = options["generate_admin"]
        generate_serializers = options["generate_serializers"]
        generate_factories = options["generate_factories"]
        generate_tests = options["generate_tests"]
        include_inheritance = options["include_inheritance"]

        try:
            app_config = apps.get_app_config(app_name)
            models_list = list(app_config.get_models())

            # Create output directory
            os.makedirs(output_dir, exist_ok=True)

            # Generate comprehensive documentation
            self.generate_documentation(models_list, output_dir, include_inheritance)

            # Generate additional files if requested
            if generate_admin:
                self.generate_admin_config(models_list, output_dir)

            if generate_serializers:
                self.generate_serializers(models_list, output_dir)

            if generate_factories:
                self.generate_factories(models_list, output_dir)

            if generate_tests:
                self.generate_test_templates(models_list, output_dir)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully generated model reflection for {len(models_list)} models in {output_dir}"
                )
            )

        except LookupError:
            self.stdout.write(self.style.ERROR(f'App "{app_name}" not found.'))
            sys.exit(1)

    def generate_documentation(self, models_list, output_dir, include_inheritance):
        """Generate comprehensive model documentation"""
        doc_file = os.path.join(output_dir, "models_documentation.md")

        with open(doc_file, "w", encoding="utf-8") as f:
            f.write("# Django Models Comprehensive Documentation\n\n")
            f.write(f"Generated on: {self.get_current_time()}\n")
            f.write(f"Total models: {len(models_list)}\n\n")

            # Model inheritance analysis
            if include_inheritance:
                f.write("## Model Inheritance Analysis\n\n")
                inheritance_map = self.analyze_inheritance(models_list)
                for model, parents in inheritance_map.items():
                    if parents:
                        f.write(f"- **{model}** inherits from: {', '.join(parents)}\n")
                f.write("\n")

            # Model statistics
            f.write("## Model Statistics\n\n")
            stats = self.get_model_statistics(models_list)
            for stat, value in stats.items():
                f.write(f"- **{stat}**: {value}\n")
            f.write("\n")

            # Detailed model documentation
            for model in models_list:
                self.write_model_documentation(f, model, include_inheritance)
                f.write("---\n\n")

    def analyze_inheritance(self, models_list):
        """Analyze model inheritance relationships"""
        inheritance_map = {}

        for model in models_list:
            model_name = model.__name__
            parents = []

            # Get all base classes except models.Model
            for base in model.__bases__:
                if hasattr(base, "_meta") and base != models.Model:
                    parents.append(base.__name__)

            if parents:
                inheritance_map[model_name] = parents

        return inheritance_map

    def get_model_statistics(self, models_list):
        """Get comprehensive model statistics"""
        stats = {
            "Total Models": len(models_list),
            "Abstract Models": 0,
            "Concrete Models": 0,
            "Proxy Models": 0,
            "Total Fields": 0,
            "Foreign Keys": 0,
            "Many to Many": 0,
            "One to One": 0,
        }

        for model in models_list:
            if model._meta.abstract:
                stats["Abstract Models"] += 1
            elif model._meta.proxy:
                stats["Proxy Models"] += 1
            else:
                stats["Concrete Models"] += 1

            for field in model._meta.get_fields():
                if hasattr(field, "field"):
                    field = field.field

                stats["Total Fields"] += 1

                if isinstance(field, ForeignKey):
                    stats["Foreign Keys"] += 1
                elif isinstance(field, ManyToManyField):
                    stats["Many to Many"] += 1
                elif isinstance(field, OneToOneField):
                    stats["One to One"] += 1

        return stats

    def write_model_documentation(self, f, model, include_inheritance):
        """Write detailed documentation for a single model"""
        f.write(f"## {model.__name__}\n\n")

        # Basic information
        f.write("### Model Information\n")
        f.write(f"- **App Label**: `{model._meta.app_label}`\n")
        f.write(f"- **Table Name**: `{model._meta.db_table}`\n")
        f.write(f"- **Verbose Name**: `{model._meta.verbose_name}`\n")
        f.write(f"- **Verbose Name Plural**: `{model._meta.verbose_name_plural}`\n")
        f.write(f"- **Abstract**: {model._meta.abstract}\n")
        f.write(f"- **Proxy**: {model._meta.proxy}\n")

        if model.__doc__ and model.__doc__.strip():
            f.write(f"- **Description**: {model.__doc__.strip()}\n")

        # Inheritance information
        if include_inheritance:
            parents = [
                base.__name__
                for base in model.__bases__
                if hasattr(base, "_meta") and base != models.Model
            ]
            if parents:
                f.write(f"- **Inherits From**: {', '.join(parents)}\n")

        # Children models
        children = [child.__name__ for child in models_list if model in child.__bases__]
        if children:
            f.write(f"- **Child Models**: {', '.join(children)}\n")

        f.write("\n")

        # Fields
        f.write("### Fields\n\n")
        fields = model._meta.get_fields()

        # Group fields by type
        field_groups = {
            "Primary Keys": [],
            "Foreign Keys": [],
            "Many to Many": [],
            "One to One": [],
            "Generic Relations": [],
            "Regular Fields": [],
        }

        for field in fields:
            if hasattr(field, "field"):
                field = field.field

            if hasattr(field, "primary_key") and field.primary_key:
                field_groups["Primary Keys"].append(field)
            elif isinstance(field, ForeignKey):
                field_groups["Foreign Keys"].append(field)
            elif isinstance(field, ManyToManyField):
                field_groups["Many to Many"].append(field)
            elif isinstance(field, OneToOneField):
                field_groups["One to One"].append(field)
            elif isinstance(field, GenericRelation):
                field_groups["Generic Relations"].append(field)
            else:
                field_groups["Regular Fields"].append(field)

        # Write field groups
        for group_name, group_fields in field_groups.items():
            if group_fields:
                f.write(f"#### {group_name}\n\n")
                for field in group_fields:
                    self.write_field_documentation(f, field)
                f.write("\n")

        # Methods
        methods = self.get_model_methods(model)
        if methods:
            f.write("### Methods\n\n")
            for method in methods:
                f.write(f"#### {method['name']}\n")
                f.write("```python\n")
                f.write(f"def {method['signature']}\n")
                if method.get("docstring"):
                    f.write(f'    """{method["docstring"]}"""\n')
                f.write("```\n\n")

        # Meta information
        meta_attrs = self.get_meta_attributes(model)
        if meta_attrs:
            f.write("### Meta Configuration\n\n")
            for attr, value in meta_attrs.items():
                f.write(f"- **{attr}**: `{value}`\n")
            f.write("\n")

        # Relationships summary
        relationships = self.get_relationships(model)
        if any(relationships.values()):
            f.write("### Relationships Summary\n\n")
            for rel_type, rels in relationships.items():
                if rels:
                    f.write(f"#### {rel_type} ({len(rels)})\n")
                    for rel in rels:
                        f.write(f"- **{rel['name']}** → `{rel['to']}`\n")
                    f.write("\n")

    def write_field_documentation(self, f, field):
        """Write detailed field documentation"""
        field_name = field.name
        field_type = type(field).__name__

        f.write(f"**{field_name}** (`{field_type}`)\n\n")

        # Field attributes
        attrs = self.get_field_attributes(field)
        if attrs:
            for attr, value in attrs.items():
                f.write(f"  - **{attr}**: {value}\n")

        # Help text
        if hasattr(field, "help_text") and field.help_text:
            f.write(f"  - **Help Text**: {field.help_text}\n")

        f.write("\n")

    def get_field_attributes(self, field):
        """Get all field attributes"""
        attrs = {}

        # Common attributes
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

        # Relationship attributes
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

        return attrs

    def generate_admin_config(self, models_list, output_dir):
        """Generate Django admin configuration"""
        admin_file = os.path.join(output_dir, "admin.py")

        with open(admin_file, "w", encoding="utf-8") as f:
            f.write("# Generated Django Admin Configuration\n")
            f.write("# Auto-generated by model_reflector management command\n\n")
            f.write("from django.contrib import admin\n")
            f.write("from django.db import models\n")
            f.write("from .models import (\n")

            # Import models
            model_names = [model.__name__ for model in models_list]
            for name in model_names:
                f.write(f"    {name},\n")
            f.write(")\n\n")

            # Generate admin classes
            for model in models_list:
                self.write_model_admin(f, model)

            # Register models
            f.write("# Register models\n")
            for model in models_list:
                admin_class_name = f"{model.__name__}Admin"
                f.write(f"admin.site.register({model.__name__}, {admin_class_name})\n")

    def write_model_admin(self, f, model):
        """Write admin class for a model"""
        class_name = f"{model.__name__}Admin"

        f.write(f"\n@admin.register({model.__name__})\n")
        f.write(f"class {class_name}(admin.ModelAdmin):\n")

        # List display
        list_display_fields = self.get_list_display_fields(model)
        if list_display_fields:
            f.write(f"    list_display = {list_display_fields}\n")

        # List filter
        list_filter_fields = self.get_list_filter_fields(model)
        if list_filter_fields:
            f.write(f"    list_filter = {list_filter_fields}\n")

        # Search fields
        search_fields = self.get_search_fields(model)
        if search_fields:
            f.write(f"    search_fields = {search_fields}\n")

        # Raw ID fields for foreign keys
        raw_id_fields = self.get_raw_id_fields(model)
        if raw_id_fields:
            f.write(f"    raw_id_fields = {raw_id_fields}\n")

        # Readonly fields
        readonly_fields = self.get_readonly_fields(model)
        if readonly_fields:
            f.write(f"    readonly_fields = {readonly_fields}\n")

        # Fieldsets
        fieldsets = self.get_admin_fieldsets(model)
        if fieldsets:
            f.write(f"    fieldsets = {fieldsets}\n")

        f.write("\n")

    def get_list_display_fields(self, model):
        """Get appropriate fields for list_display"""
        fields = []

        # Try to find common display fields
        common_fields = ["name", "title", "id", "created_at", "updated_at", "status"]

        for field_name in common_fields:
            try:
                field = model._meta.get_field(field_name)
                if not isinstance(field, (ManyToManyField, ForeignKey)):
                    fields.append(field_name)
                    if len(fields) >= 3:  # Limit to 3 fields
                        break
            except:
                continue

        if not fields:
            # Fallback to first few non-relationship fields
            for field in model._meta.get_fields():
                if hasattr(field, "field"):
                    field = field.field
                if not isinstance(field, (ManyToManyField, GenericRelation)):
                    fields.append(field.name)
                    if len(fields) >= 2:
                        break

        return tuple(fields) if fields else ("__str__",)

    def get_list_filter_fields(self, model):
        """Get appropriate fields for list_filter"""
        fields = []

        # Add choice fields, boolean fields, and foreign keys
        for field in model._meta.get_fields():
            if hasattr(field, "field"):
                field = field.field

            if hasattr(field, "choices") and field.choices:
                fields.append(field.name)
            elif isinstance(field, models.BooleanField):
                fields.append(field.name)
            elif isinstance(field, (ForeignKey, models.DateTimeField)):
                fields.append(field.name)

        return tuple(fields) if fields else ()

    def get_search_fields(self, model):
        """Get appropriate fields for search"""
        fields = []

        # Add CharField and TextField fields
        for field in model._meta.get_fields():
            if hasattr(field, "field"):
                field = field.field

            if isinstance(field, (models.CharField, models.TextField)):
                fields.append(field.name)
                if len(fields) >= 3:  # Limit to 3 fields
                    break

        return tuple(fields) if fields else ()

    def get_raw_id_fields(self, model):
        """Get foreign key fields for raw_id_fields"""
        fields = []

        for field in model._meta.get_fields():
            if hasattr(field, "field"):
                field = field.field

            if isinstance(field, ForeignKey):
                fields.append(field.name)

        return tuple(fields) if fields else ()

    def get_readonly_fields(self, model):
        """Get appropriate readonly fields"""
        fields = []

        # Add auto fields and computed fields
        for field in model._meta.get_fields():
            if hasattr(field, "field"):
                field = field.field

            if isinstance(field, models.AutoField):
                fields.append(field.name)
            elif hasattr(field, "auto_now_add") and field.auto_now_add:
                fields.append(field.name)
            elif hasattr(field, "auto_now") and field.auto_now:
                fields.append(field.name)

        return tuple(fields) if fields else ()

    def get_admin_fieldsets(self, model):
        """Generate fieldsets for admin"""
        # This is a simplified version - you could make it more sophisticated
        return None

    def generate_serializers(self, models_list, output_dir):
        """Generate DRF serializers"""
        serializers_file = os.path.join(output_dir, "serializers.py")

        with open(serializers_file, "w", encoding="utf-8") as f:
            f.write("# Generated DRF Serializers\n")
            f.write("# Auto-generated by model_reflector management command\n\n")
            f.write("from rest_framework import serializers\n")
            f.write("from .models import (\n")

            # Import models
            model_names = [model.__name__ for model in models_list]
            for name in model_names:
                f.write(f"    {name},\n")
            f.write(")\n\n")

            # Generate serializers
            for model in models_list:
                self.write_model_serializer(f, model)

    def write_model_serializer(self, f, model):
        """Write serializer class for a model"""
        class_name = f"{model.__name__}Serializer"

        f.write(f"\nclass {class_name}(serializers.ModelSerializer):\n")
        f.write(f"    class Meta:\n")
        f.write(f"        model = {model.__name__}\n")
        f.write(f"        fields = '__all__'\n")

        # Add custom validation if needed
        f.write("\n")

    def generate_factories(self, models_list, output_dir):
        """Generate Factory Boy factories"""
        factories_file = os.path.join(output_dir, "factories.py")

        with open(factories_file, "w", encoding="utf-8") as f:
            f.write("# Generated Factory Boy Factories\n")
            f.write("# Auto-generated by model_reflector management command\n\n")
            f.write("import factory\n")
            f.write("from factory import fuzzy\n")
            f.write("from .models import (\n")

            # Import models
            model_names = [model.__name__ for model in models_list]
            for name in model_names:
                f.write(f"    {name},\n")
            f.write(")\n\n")

            # Generate factories
            for model in models_list:
                self.write_model_factory(f, model)

    def write_model_factory(self, f, model):
        """Write factory class for a model"""
        class_name = f"{model.__name__}Factory"

        f.write(f"\nclass {class_name}(factory.django.DjangoModelFactory):\n")
        f.write(f"    class Meta:\n")
        f.write(f"        model = {model.__name__}\n")

        # Add sample field definitions
        for field in model._meta.get_fields():
            if hasattr(field, "field"):
                field = field.field

            if isinstance(field, models.CharField):
                if hasattr(field, "max_length") and field.max_length:
                    f.write(
                        f"    {field.name} = factory.Faker('text', max_nb_chars={field.max_length})\n"
                    )
                else:
                    f.write(f"    {field.name} = factory.Faker('word')\n")
            elif isinstance(field, models.TextField):
                f.write(f"    {field.name} = factory.Faker('paragraph')\n")
            elif isinstance(field, models.IntegerField):
                f.write(f"    {field.name} = factory.Faker('random_int')\n")
            elif isinstance(field, models.EmailField):
                f.write(f"    {field.name} = factory.Faker('email')\n")
            elif isinstance(field, models.URLField):
                f.write(f"    {field.name} = factory.Faker('url')\n")
            elif isinstance(field, models.BooleanField):
                f.write(f"    {field.name} = factory.Faker('boolean')\n")
            elif isinstance(field, models.DateTimeField):
                f.write(f"    {field.name} = factory.Faker('date_time')\n")

        f.write("\n")

    def generate_test_templates(self, models_list, output_dir):
        """Generate test templates"""
        tests_file = os.path.join(output_dir, "test_models.py")

        with open(tests_file, "w", encoding="utf-8") as f:
            f.write("# Generated Model Tests\n")
            f.write("# Auto-generated by model_reflector management command\n\n")
            f.write("from django.test import TestCase\n")
            f.write("from .models import (\n")

            # Import models
            model_names = [model.__name__ for model in models_list]
            for name in model_names:
                f.write(f"    {name},\n")
            f.write(")\n")
            f.write("from .factories import (\n")
            for name in model_names:
                f.write(f"    {name}Factory,\n")
            f.write(")\n\n")

            # Generate test classes
            for model in models_list:
                self.write_model_tests(f, model)

    def write_model_tests(self, f, model):
        """Write test class for a model"""
        class_name = f"{model.__name__}Test"

        f.write(f"\nclass {class_name}(TestCase):\n")
        f.write(f"    def test_{model.__name__.lower()}_creation(self):\n")
        f.write(f"        {model.__name__.lower()} = {model.__name__}Factory()\n")
        f.write(
            f"        self.assertTrue(isinstance({model.__name__.lower()}, {model.__name__}))\n"
        )
        f.write(f"        self.assertIsNotNone({model.__name__.lower()}.id)\n")

        f.write(f"\n    def test_{model.__name__.lower()}_str(self):\n")
        f.write(f"        {model.__name__.lower()} = {model.__name__}Factory()\n")
        f.write(f"        self.assertIsInstance(str({model.__name__.lower()}), str)\n")

        f.write("\n")

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
                    continue

        return methods

    def get_meta_attributes(self, model):
        """Get Meta class attributes"""
        meta_attrs = {}

        if hasattr(model, "_meta"):
            meta = model._meta

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

        return {k: v for k, v in relationships.items() if v}

    def get_current_time(self):
        """Get current timestamp"""
        from django.utils import timezone

        return timezone.now().strftime("%Y-%m-%d %H:%M:%S %Z")
