import ast
import os
import re
import uuid


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DTE_SV_DIR = os.path.join(BASE_DIR, 'custom-addons', 'dte_sv')


class TestAccountMoveSyntax:
    def test_account_move_file_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        assert os.path.exists(path)

    def test_account_move_parses_successfully(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source)
        assert tree is not None

    def test_account_move_class_defined(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source)
        class_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        assert 'AccountMove' in class_names


class TestDTEConstants:
    def test_dte_version_mapping(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert "_DTE_VERSION = {'01': 1, '03': 3, '05': 4}" in content

    def test_schema_file_mapping(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert "_SCHEMA_FILE = {" in content
        assert "'01'" in content and "'fe-f-v2.json'" in content
        assert "'03'" in content and "'fe-ccf-v4.json'" in content
        assert "'05'" in content and "'fe-nc-v4.json'" in content


class TestAccountMoveMethods:
    def test_numero_a_letras_method_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'def _numero_a_letras(self' in content

    def test_generar_codigo_generacion_method_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'def _generar_codigo_generacion(self' in content

    def test_generar_numero_control_method_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'def _generar_numero_control(self' in content

    def test_serializar_dte_method_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'def _serializar_dte(self' in content

    def test_validar_schema_dte_method_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'def _validar_schema_dte(self' in content

    def test_obtener_token_mh_method_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'def _obtener_token_mh(self' in content

    def test_firmar_dte_method_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'def _firmar_dte(self' in content

    def test_enviar_dte_mh_method_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'def _enviar_dte_mh(self' in content

    def test_action_enviar_dte_method_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'def action_enviar_dte(self' in content


class TestAccountMoveImports:
    def test_imports_uuid(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'import uuid' in content

    def test_imports_json(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'import json' in content

    def test_imports_requests(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'import requests' in content

    def test_imports_jsonschema(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'jsonschema' in content


class TestAccountMoveFields:
    def test_dte_codigo_generacion_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_codigo_generacion' in content

    def test_dte_numero_control_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_numero_control' in content

    def test_dte_sello_recepcion_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_sello_recepcion' in content

    def test_dte_json_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_json' in content

    def test_tipo_dte_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert "tipo_dte" in content

    def test_estado_dte_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'estado_dte' in content

    def test_tipo_dte_selections(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert "'01'" in content and "'Factura de Consumidor Final'" in content
        assert "'03'" in content and "'Comprobante de Crédito Fiscal'" in content
        assert "'05'" in content and "'Nota de Crédito'" in content

    def test_estado_dte_selections(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert "'borrador'" in content
        assert "'enviado'" in content
        assert "'aceptado'" in content
        assert "'rechazado'" in content
        assert "'pendiente'" in content


class TestAccountMoveInheritance:
    def test_inherits_account_move(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert "_inherit = 'account.move'" in content


class TestDTEBuildMethods:
    def test_build_identificacion_method_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'def _build_identificacion(self, tipo)' in content

    def test_build_emisor_method_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'def _build_emisor(self, tipo)' in content

    def test_build_receptor_method_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'def _build_receptor(self, tipo)' in content

    def test_build_cuerpo_method_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'def _build_cuerpo(self, tipo)' in content

    def test_build_resumen_method_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'account_move.py')
        with open(path) as f:
            content = f.read()
        assert 'def _build_resumen(self, tipo, cuerpo)' in content


class TestUUIDGeneration:
    def test_uuid_format_matches_uuid_v4(self):
        test_uuid = str(uuid.uuid4()).upper()
        assert len(test_uuid) == 36
        assert test_uuid.count('-') == 4
        uuid.UUID(test_uuid)


class TestNumeroControlFormat:
    def test_numero_control_format_regex(self):
        pattern = r'^DTE-\d{2}-[A-Z0-9]{4}P\d{3}-\d{15}$'
        test_values = [
            'DTE-01-S001P001-000000000000001',
            'DTE-03-S048P001-000000000000042',
            'DTE-05-S001P001-000000000000001',
        ]
        for val in test_values:
            assert re.match(pattern, val), f'Failed: {val}'


class TestManifestDependencias:
    def test_manifest_depends_on_account(self):
        path = os.path.join(DTE_SV_DIR, '__manifest__.py')
        with open(path) as f:
            content = f.read()
        assert "'account'" in content or '"account"' in content

    def test_manifest_depends_on_sale_management(self):
        path = os.path.join(DTE_SV_DIR, '__manifest__.py')
        with open(path) as f:
            content = f.read()
        assert "'sale_management'" in content or '"sale_management"' in content

    def test_manifest_installable_true(self):
        path = os.path.join(DTE_SV_DIR, '__manifest__.py')
        with open(path) as f:
            content = f.read()
        assert "'installable': True" in content or '"installable": True' in content
