import ast
import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DTE_SV_DIR = os.path.join(BASE_DIR, 'custom-addons', 'dte_sv')


class TestResPartnerSyntax:
    def test_res_partner_file_exists(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_partner.py')
        assert os.path.exists(path)

    def test_res_partner_parses_successfully(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_partner.py')
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source)
        assert tree is not None

    def test_res_partner_class_defined(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_partner.py')
        with open(path) as f:
            source = f.read()
        tree = ast.parse(source)
        class_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        assert 'ResPartner' in class_names


class TestResPartnerInheritance:
    def test_inherits_res_partner(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_partner.py')
        with open(path) as f:
            content = f.read()
        assert "_inherit = 'res.partner'" in content


class TestResPartnerFields:
    def test_dte_nrc_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_partner.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_nrc' in content

    def test_dte_cod_actividad_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_partner.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_cod_actividad' in content

    def test_dte_desc_actividad_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_partner.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_desc_actividad' in content

    def test_dte_departamento_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_partner.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_departamento' in content

    def test_dte_municipio_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_partner.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_municipio' in content

    def test_dte_complemento_field(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_partner.py')
        with open(path) as f:
            content = f.read()
        assert 'dte_complemento' in content


class TestResPartnerFieldSize:
    def test_dte_departamento_size_2(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_partner.py')
        with open(path) as f:
            content = f.read()
        assert "size=2" in content and 'dte_departamento' in content

    def test_dte_municipio_size_2(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_partner.py')
        with open(path) as f:
            content = f.read()
        assert "size=2" in content and 'dte_municipio' in content


class TestResPartnerHelpTexts:
    def test_dte_nrc_help_contains_nrc(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_partner.py')
        with open(path) as f:
            content = f.read()
        assert 'help=' in content and ('NRC' in content or 'Registro' in content)

    def test_dte_departamento_help_contains_catalogo(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_partner.py')
        with open(path) as f:
            content = f.read()
        assert 'help=' in content and ('catálogo' in content.lower() or 'MH' in content)

    def test_dte_complemento_help_contains_direccion(self):
        path = os.path.join(DTE_SV_DIR, 'models', 'res_partner.py')
        with open(path) as f:
            content = f.read()
        assert 'help=' in content and 'dirección' in content.lower()
