import ast
import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DTE_SV_DIR = os.path.join(BASE_DIR, 'custom-addons', 'dte_sv')


class TestResCompanySyntax:
    def test_res_company_file_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        assert os.path.exists(path)

    def test_res_company_parses_successfully(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source)
        assert tree is not None

    def test_res_company_class_defined(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source)
        class_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        assert 'ResCompany' in class_names


class TestResCompanyInheritance:
    def test_inherits_res_company(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert "_inherit = 'res.company'" in content


class TestResCompanyFields:
    def test_dte_establecimiento_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_establecimiento' in content

    def test_dte_punto_venta_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_punto_venta' in content

    def test_dte_nrc_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_nrc' in content

    def test_dte_nombre_comercial_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_nombre_comercial' in content

    def test_dte_cod_actividad_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_cod_actividad' in content

    def test_dte_desc_actividad_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_desc_actividad' in content

    def test_dte_tipo_establecimiento_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_tipo_establecimiento' in content

    def test_dte_departamento_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_departamento' in content

    def test_dte_municipio_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_municipio' in content

    def test_dte_distrito_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_distrito' in content

    def test_dte_nit_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_nit' in content

    def test_dte_password_mh_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_password_mh' in content

    def test_dte_password_certificado_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_password_certificado' in content

    def test_dte_url_firmador_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_url_firmador' in content

    def test_dte_url_auth_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_url_auth' in content

    def test_dte_url_recepcion_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_url_recepcion' in content

    def test_dte_token_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_token' in content

    def test_dte_token_expiry_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_token_expiry' in content


class TestResCompanyDefaults:
    def test_dte_establecimiento_default_s001(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert "default='S001'" in content

    def test_dte_punto_venta_default_p001(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert "default='P001'" in content

    def test_dte_tipo_establecimiento_default_01(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert "default='01'" in content

    def test_dte_url_firmador_default_localhost(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert "default='http://localhost:8113'" in content

    def test_dte_url_auth_default_contains_mh(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'apitest.dtes.mh.gob.sv' in content

    def test_dte_url_recepcion_default_contains_mh(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'recepciondte' in content


class TestResCompanyHelpTexts:
    def test_dte_establecimiento_help(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'help=' in content and 'Establecimiento' in content

    def test_dte_nit_help(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'help=' in content and 'NIT' in content

    def test_dte_password_mh_help(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'help=' in content and 'Ministerio de Hacienda' in content

    def test_dte_token_readonly_help(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_company.py')
        with open(path) as f:
            content = f.read()
        assert 'help=' in content and 'Token' in content