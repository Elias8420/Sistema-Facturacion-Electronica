FROM odoo:17.0

COPY custom-addons/dte_sv /mnt/extra-addons/dte_sv

RUN pip install jsonschema num2words requests