import json
import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, 'custom-addons', 'dte_sv', 'static', 'schemas')


class TestSchemasJSONValidity:
    def test_fe_f_v2_is_valid_json(self):
        path = os.path.join(SCHEMAS_DIR, 'fe-f-v2.json')
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_fe_ccf_v4_is_valid_json(self):
        path = os.path.join(SCHEMAS_DIR, 'fe-ccf-v4.json')
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_fe_nc_v4_is_valid_json(self):
        path = os.path.join(SCHEMAS_DIR, 'fe-nc-v4.json')
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)


class TestSchemaStructure:
    def test_fe_f_v2_has_definitions_or_properties(self):
        path = os.path.join(SCHEMAS_DIR, 'fe-f-v2.json')
        with open(path) as f:
            schema = json.load(f)
        assert 'definitions' in schema or 'properties' in schema

    def test_fe_ccf_v4_has_definitions_or_properties(self):
        path = os.path.join(SCHEMAS_DIR, 'fe-ccf-v4.json')
        with open(path) as f:
            schema = json.load(f)
        assert 'definitions' in schema or 'properties' in schema

    def test_fe_nc_v4_has_definitions_or_properties(self):
        path = os.path.join(SCHEMAS_DIR, 'fe-nc-v4.json')
        with open(path) as f:
            schema = json.load(f)
        assert 'definitions' in schema or 'properties' in schema


class TestSchemaFilesExist:
    def test_fe_f_v2_exists(self):
        assert os.path.exists(os.path.join(SCHEMAS_DIR, 'fe-f-v2.json'))

    def test_fe_ccf_v4_exists(self):
        assert os.path.exists(os.path.join(SCHEMAS_DIR, 'fe-ccf-v4.json'))

    def test_fe_nc_v4_exists(self):
        assert os.path.exists(os.path.join(SCHEMAS_DIR, 'fe-nc-v4.json'))


class TestDTETypesInSchemas:
    def test_fe_f_v2_contains_factura(self):
        path = os.path.join(SCHEMAS_DIR, 'fe-f-v2.json')
        with open(path) as f:
            content = f.read()
        assert '01' in content or 'factura' in content.lower()

    def test_fe_ccf_v4_contains_ccf(self):
        path = os.path.join(SCHEMAS_DIR, 'fe-ccf-v4.json')
        with open(path) as f:
            content = f.read()
        assert '03' in content or 'credito' in content.lower() or 'crédito' in content.lower()

    def test_fe_nc_v4_contains_nota_credito(self):
        path = os.path.join(SCHEMAS_DIR, 'fe-nc-v4.json')
        with open(path) as f:
            content = f.read()
        assert '05' in content or 'credito' in content.lower() or 'crédito' in content.lower()
